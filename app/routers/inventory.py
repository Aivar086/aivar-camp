from fastapi import APIRouter, Depends, Form, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from typing import Optional, List
import os

from app.database import get_db
from app.models import UserInventoryItem, GearItem, Trip
from app.services.gear_presets import DEFAULT_GEAR_PRESETS

templates = Jinja2Templates(directory=os.path.join(os.path.dirname(__file__), "..", "templates"))
router = APIRouter(tags=["Inventory"])

CATEGORIES_META = {
    "camp": {"title": "Лагерь и Палатка", "icon": "fa-campground", "color": "emerald"},
    "fishing": {"title": "Рыбалка и Снасти", "icon": "fa-fish", "color": "blue"},
    "boat": {"title": "Лодка и Мотор", "icon": "fa-ship", "color": "cyan"},
    "kitchen": {"title": "Походная Кухня", "icon": "fa-utensils", "color": "amber"},
    "clothes": {"title": "Одежда и Обувь", "icon": "fa-shirt", "color": "indigo"},
    "firstaid": {"title": "Аптечка и Безопасность", "icon": "fa-kit-medical", "color": "rose"},
    "other": {"title": "Инструменты и Прочее", "icon": "fa-toolbox", "color": "gray"}
}

@router.get("/inventory", response_class=HTMLResponse)
def inventory_page(request: Request, db: Session = Depends(get_db)):
    items = db.query(UserInventoryItem).order_by(UserInventoryItem.category.asc(), UserInventoryItem.id.desc()).all()
    
    grouped = {k: [] for k in CATEGORIES_META.keys()}
    total_count = len(items)
    total_weight = sum(it.weight_kg or 0.0 for it in items)

    for it in items:
        cat = it.category if it.category in grouped else "other"
        grouped[cat].append(it)

    return templates.TemplateResponse(
        request=request,
        name="inventory.html",
        context={
            "grouped_inventory": grouped,
            "categories_meta": CATEGORIES_META,
            "total_count": total_count,
            "total_weight": round(total_weight, 1)
        }
    )

@router.post("/inventory/add")
def add_inventory_item(
    category: str = Form(...),
    name: str = Form(...),
    brand_or_model: Optional[str] = Form(None),
    quantity: str = Form("1 шт"),
    weight_kg: Optional[float] = Form(None),
    notes: Optional[str] = Form(None),
    db: Session = Depends(get_db)
):
    item = UserInventoryItem(
        category=category,
        name=name.strip(),
        brand_or_model=brand_or_model.strip() if brand_or_model else None,
        quantity=quantity.strip() if quantity else "1 шт",
        weight_kg=weight_kg,
        notes=notes.strip() if notes else None
    )
    db.add(item)
    db.commit()
    return RedirectResponse(url="/inventory", status_code=303)

@router.post("/inventory/{item_id}/edit")
def edit_inventory_item(
    item_id: int,
    category: str = Form(...),
    name: str = Form(...),
    brand_or_model: Optional[str] = Form(None),
    quantity: str = Form("1 шт"),
    weight_kg: Optional[float] = Form(None),
    notes: Optional[str] = Form(None),
    db: Session = Depends(get_db)
):
    item = db.query(UserInventoryItem).filter(UserInventoryItem.id == item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Предмет не найден")

    item.category = category
    item.name = name.strip()
    item.brand_or_model = brand_or_model.strip() if brand_or_model else None
    item.quantity = quantity.strip() if quantity else "1 шт"
    item.weight_kg = weight_kg
    item.notes = notes.strip() if notes else None

    db.commit()
    return RedirectResponse(url="/inventory", status_code=303)

@router.post("/inventory/{item_id}/delete")
def delete_inventory_item(item_id: int, db: Session = Depends(get_db)):
    item = db.query(UserInventoryItem).filter(UserInventoryItem.id == item_id).first()
    if item:
        db.delete(item)
        db.commit()
    return RedirectResponse(url="/inventory", status_code=303)

@router.post("/inventory/clear-all")
def clear_all_inventory(db: Session = Depends(get_db)):
    db.query(UserInventoryItem).delete()
    db.commit()
    return RedirectResponse(url="/inventory", status_code=303)

@router.post("/inventory/populate-defaults")
def populate_default_inventory(db: Session = Depends(get_db)):
    for cat, items in DEFAULT_GEAR_PRESETS.items():
        for it in items:
            exists = db.query(UserInventoryItem).filter(
                UserInventoryItem.category == cat,
                UserInventoryItem.name == it["name"]
            ).first()
            if not exists:
                db.add(UserInventoryItem(
                    category=cat,
                    name=it["name"],
                    quantity=it.get("quantity", "1 шт"),
                    notes=it.get("note")
                ))
    db.commit()
    return RedirectResponse(url="/inventory", status_code=303)

@router.post("/trips/{trip_id}/gear/import-from-inventory")
def import_inventory_to_trip(trip_id: int, db: Session = Depends(get_db)):
    trip = db.query(Trip).filter(Trip.id == trip_id).first()
    if not trip:
        raise HTTPException(status_code=404, detail="Поездка не найдена")

    inventory_items = db.query(UserInventoryItem).all()
    for inv in inventory_items:
        exists = db.query(GearItem).filter(
            GearItem.trip_id == trip_id,
            GearItem.name == inv.name
        ).first()
        if not exists:
            db.add(GearItem(
                trip_id=trip_id,
                category=inv.category if inv.category in ["camp", "fishing", "kitchen", "clothes", "firstaid"] else "other",
                name=f"{inv.name} ({inv.brand_or_model})" if inv.brand_or_model else inv.name,
                quantity=inv.quantity or "1 шт",
                note=inv.notes,
                is_packed=False
            ))
    db.commit()
    return RedirectResponse(url=f"/trips/{trip_id}#gear-section", status_code=303)

@router.post("/trips/{trip_id}/gear/clear-all")
def clear_trip_gear(trip_id: int, db: Session = Depends(get_db)):
    db.query(GearItem).filter(GearItem.trip_id == trip_id).delete()
    db.commit()
    return RedirectResponse(url=f"/trips/{trip_id}#gear-section", status_code=303)
