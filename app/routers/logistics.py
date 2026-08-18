from fastapi import APIRouter, Depends, Form, HTTPException, Request, Response
from fastapi.responses import HTMLResponse, RedirectResponse, PlainTextResponse
from sqlalchemy.orm import Session
from typing import Optional

from app.database import get_db
from app.models import Trip, FoodItem, ExpenseItem, Waypoint
from app.services.kitchen_calc import generate_food_ration
from app.services.gpx_export import generate_gpx_content

router = APIRouter(tags=["Logistics"])

@router.post("/trips/{trip_id}/food/generate")
def generate_ration_for_trip(trip_id: int, db: Session = Depends(get_db)):
    trip = db.query(Trip).filter(Trip.id == trip_id).first()
    if not trip:
        raise HTTPException(status_code=404, detail="Поездка не найдена")

    # Удаляем старые автосгенерированные продукты
    db.query(FoodItem).filter(FoodItem.trip_id == trip_id).delete()
    
    ration = generate_food_ration(trip.participants_count or 2, trip.duration_days or 3)
    for item in ration:
        db.add(FoodItem(
            trip_id=trip_id,
            category=item["category"],
            name=item["name"],
            amount=item["amount"],
            assigned_to=item.get("assigned_to", "Все"),
            is_bought=False
        ))
    db.commit()
    return RedirectResponse(url=f"/trips/{trip_id}#food-section", status_code=303)

@router.post("/food/{item_id}/toggle")
def toggle_food_item(item_id: int, db: Session = Depends(get_db)):
    item = db.query(FoodItem).filter(FoodItem.id == item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Продукт не найден")
    item.is_bought = not item.is_bought
    db.commit()
    return {"status": "success", "is_bought": item.is_bought}

@router.post("/trips/{trip_id}/food/add")
def add_custom_food(
    trip_id: int,
    name: str = Form(...),
    amount: str = Form("1 кг"),
    category: str = Form("groceries"),
    assigned_to: Optional[str] = Form("Я"),
    db: Session = Depends(get_db)
):
    trip = db.query(Trip).filter(Trip.id == trip_id).first()
    if not trip:
        raise HTTPException(status_code=404, detail="Поездка не найдена")
    db.add(FoodItem(
        trip_id=trip_id,
        name=name.strip(),
        amount=amount.strip(),
        category=category,
        assigned_to=assigned_to.strip() if assigned_to else "Я",
        is_bought=False
    ))
    db.commit()
    return RedirectResponse(url=f"/trips/{trip_id}#food-section", status_code=303)

@router.post("/food/{item_id}/delete")
def delete_food_item(item_id: int, db: Session = Depends(get_db)):
    item = db.query(FoodItem).filter(FoodItem.id == item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Продукт не найден")
    trip_id = item.trip_id
    db.delete(item)
    db.commit()
    return RedirectResponse(url=f"/trips/{trip_id}#food-section", status_code=303)

@router.post("/trips/{trip_id}/expenses/add")
def add_expense(
    trip_id: int,
    title: str = Form(...),
    amount: float = Form(...),
    paid_by: Optional[str] = Form("Я"),
    db: Session = Depends(get_db)
):
    trip = db.query(Trip).filter(Trip.id == trip_id).first()
    if not trip:
        raise HTTPException(status_code=404, detail="Поездка не найдена")
    db.add(ExpenseItem(
        trip_id=trip_id,
        title=title.strip(),
        amount=amount,
        paid_by=paid_by.strip() if paid_by else "Я"
    ))
    db.commit()
    return RedirectResponse(url=f"/trips/{trip_id}#budget-section", status_code=303)

@router.post("/expenses/{expense_id}/delete")
def delete_expense(expense_id: int, db: Session = Depends(get_db)):
    exp = db.query(ExpenseItem).filter(ExpenseItem.id == expense_id).first()
    if not exp:
        raise HTTPException(status_code=404, detail="Расход не найден")
    trip_id = exp.trip_id
    db.delete(exp)
    db.commit()
    return RedirectResponse(url=f"/trips/{trip_id}#budget-section", status_code=303)

@router.post("/trips/{trip_id}/logistics/update-params")
def update_trip_params(
    trip_id: int,
    participants_count: int = Form(...),
    duration_days: int = Form(...),
    fuel_consumption: float = Form(...),
    fuel_price: float = Form(...),
    db: Session = Depends(get_db)
):
    trip = db.query(Trip).filter(Trip.id == trip_id).first()
    if not trip:
        raise HTTPException(status_code=404, detail="Поездка не найдена")
    trip.participants_count = max(1, participants_count)
    trip.duration_days = max(1, duration_days)
    trip.fuel_consumption = fuel_consumption
    trip.fuel_price = fuel_price
    db.commit()
    return RedirectResponse(url=f"/trips/{trip_id}#logistics-section", status_code=303)

@router.get("/trips/{trip_id}/export/gpx")
def export_trip_gpx(trip_id: int, db: Session = Depends(get_db)):
    trip = db.query(Trip).filter(Trip.id == trip_id).first()
    if not trip:
        raise HTTPException(status_code=404, detail="Поездка не найдена")
    waypoints = db.query(Waypoint).filter(Waypoint.trip_id == trip_id).all()
    gpx_xml = generate_gpx_content(trip, waypoints)
    
    filename = f"trip_{trip.id}_track.gpx"
    return Response(
        content=gpx_xml,
        media_type="application/gpx+xml",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'}
    )
