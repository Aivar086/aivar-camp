from fastapi import APIRouter, Depends, Form, HTTPException, Request
from fastapi.responses import JSONResponse, RedirectResponse
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import GearItem, Trip
from app.services.gear_presets import DEFAULT_GEAR_PRESETS

router = APIRouter(tags=["Gear"])

@router.post("/gear/{item_id}/toggle")
def toggle_gear_item(item_id: int, db: Session = Depends(get_db)):
    """Переключить чекбокс 'Собрано' у предмета."""
    item = db.query(GearItem).filter(GearItem.id == item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Предмет не найден")
    
    item.is_packed = not item.is_packed
    db.commit()
    db.refresh(item)
    
    # Считаем общий прогресс сборов для этой поездки
    total = db.query(GearItem).filter(GearItem.trip_id == item.trip_id).count()
    packed = db.query(GearItem).filter(GearItem.trip_id == item.trip_id, GearItem.is_packed == True).count()
    percent = round((packed / total) * 100) if total > 0 else 0
    
    return {
        "status": "success",
        "item_id": item.id,
        "is_packed": item.is_packed,
        "total": total,
        "packed": packed,
        "percent": percent
    }

@router.post("/trips/{trip_id}/gear/add")
def add_gear_item(
    trip_id: int,
    category: str = Form(...),
    name: str = Form(...),
    quantity: str = Form("1 шт"),
    note: str = Form(""),
    db: Session = Depends(get_db)
):
    """Добавить новый пользовательский предмет в чек-лист."""
    trip = db.query(Trip).filter(Trip.id == trip_id).first()
    if not trip:
        raise HTTPException(status_code=404, detail="Поездка не найдена")
        
    new_item = GearItem(
        trip_id=trip_id,
        category=category,
        name=name.strip(),
        quantity=quantity.strip() if quantity else "1 шт",
        note=note.strip() if note else None,
        is_packed=False
    )
    db.add(new_item)
    db.commit()
    db.refresh(new_item)
    
    return RedirectResponse(url=f"/trips/{trip_id}#gear-section", status_code=303)

@router.post("/gear/{item_id}/delete")
def delete_gear_item(item_id: int, db: Session = Depends(get_db)):
    """Удалить предмет из чек-листа."""
    item = db.query(GearItem).filter(GearItem.id == item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Предмет не найден")
    trip_id = item.trip_id
    db.delete(item)
    db.commit()
    return RedirectResponse(url=f"/trips/{trip_id}#gear-section", status_code=303)

@router.post("/trips/{trip_id}/gear/load-presets")
def load_all_presets(trip_id: int, db: Session = Depends(get_db)):
    """Загрузить все базовые наборы снаряжения для поездки."""
    trip = db.query(Trip).filter(Trip.id == trip_id).first()
    if not trip:
        raise HTTPException(status_code=404, detail="Поездка не найдена")
        
    for cat, items in DEFAULT_GEAR_PRESETS.items():
        for it in items:
            # Проверим, нет ли уже такого предмета
            exists = db.query(GearItem).filter(
                GearItem.trip_id == trip_id,
                GearItem.category == cat,
                GearItem.name == it["name"]
            ).first()
            if not exists:
                db.add(GearItem(
                    trip_id=trip_id,
                    category=cat,
                    name=it["name"],
                    quantity=it.get("quantity", "1 шт"),
                    note=it.get("note"),
                    is_packed=False
                ))
    db.commit()
    return RedirectResponse(url=f"/trips/{trip_id}#gear-section", status_code=303)
