from fastapi import APIRouter, Depends, Form, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from typing import Optional
import os
import datetime

from app.database import get_db
from app.models import Trip, GearItem, Trophy, Waypoint, FoodItem, ExpenseItem, UserInventoryItem
from app.services.gear_presets import DEFAULT_GEAR_PRESETS
from app.services.routing import calculate_haversine_distance
from app.services.astro import get_moon_phase, calculate_sun_times
from app.services.kitchen_calc import generate_food_ration

templates = Jinja2Templates(directory=os.path.join(os.path.dirname(__file__), "..", "templates"))
router = APIRouter()

@router.get("/", response_class=HTMLResponse)
def index(request: Request, db: Session = Depends(get_db)):
    planned_trips = db.query(Trip).filter(Trip.status == "planned").order_by(Trip.start_date.asc(), Trip.id.desc()).all()
    completed_trips = db.query(Trip).filter(Trip.status == "completed").order_by(Trip.id.desc()).all()
    
    total_trips = db.query(Trip).count()
    total_catch = sum(t.catch_weight_kg or 0 for t in completed_trips)
    trophies_count = db.query(Trophy).count()
    
    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={
            "planned_trips": planned_trips,
            "completed_trips": completed_trips,
            "total_trips": total_trips,
            "total_catch": round(total_catch, 1),
            "trophies_count": trophies_count
        }
    )

@router.get("/trips/new", response_class=HTMLResponse)
def trip_create_page(request: Request, db: Session = Depends(get_db)):
    inventory_items = db.query(UserInventoryItem).all()
    return templates.TemplateResponse(
        request=request,
        name="trip_create.html",
        context={
            "inventory_count": len(inventory_items),
            "has_inventory": len(inventory_items) > 0
        }
    )

@router.post("/trips/new")
def trip_create(
    title: str = Form(...),
    description: Optional[str] = Form(None),
    start_date: Optional[str] = Form(None),
    end_date: Optional[str] = Form(None),
    origin_name: Optional[str] = Form("Мой дом"),
    origin_lat: Optional[float] = Form(43.2389),
    origin_lng: Optional[float] = Form(76.8897),
    dest_name: str = Form("Место стоянки"),
    dest_lat: float = Form(...),
    dest_lng: float = Form(...),
    distance_km: Optional[float] = Form(0.0),
    duration_minutes: Optional[int] = Form(0),
    participants_count: Optional[int] = Form(2),
    duration_days: Optional[int] = Form(3),
    include_default_gear: Optional[bool] = Form(True),
    db: Session = Depends(get_db)
):
    if not distance_km or distance_km == 0:
        if origin_lat and origin_lng:
            dist = calculate_haversine_distance(origin_lat, origin_lng, dest_lat, dest_lng)
            distance_km = round(dist * 1.3, 1)
            duration_minutes = round((distance_km / 65.0) * 60)

    trip = Trip(
        title=title.strip(),
        description=description.strip() if description else None,
        start_date=start_date,
        end_date=end_date,
        origin_name=origin_name.strip() if origin_name else "Старт",
        origin_lat=origin_lat,
        origin_lng=origin_lng,
        dest_name=dest_name.strip() if dest_name else "Берег / Лагерь",
        dest_lat=dest_lat,
        dest_lng=dest_lng,
        distance_km=distance_km or 0.0,
        duration_minutes=duration_minutes or 0,
        participants_count=participants_count or 2,
        duration_days=duration_days or 3,
        fuel_price=230.0,
        fuel_consumption=9.5,
        status="planned"
    )
    db.add(trip)
    db.commit()
    db.refresh(trip)

    # Автоматически загружаем снаряжение
    if include_default_gear:
        inventory_items = db.query(UserInventoryItem).all()
        
        # Если у пользователя есть свой личный Гараж — берем его личные вещи!
        if inventory_items:
            for inv in inventory_items:
                cat = inv.category if inv.category in ["camp", "fishing", "kitchen", "clothes", "firstaid"] else "other"
                full_name = f"{inv.name} ({inv.brand_or_model})" if inv.brand_or_model else inv.name
                db.add(GearItem(
                    trip_id=trip.id,
                    category=cat,
                    name=full_name,
                    quantity=inv.quantity or "1 шт",
                    note=inv.notes,
                    is_packed=False
                ))
        else:
            # Иначе загружаем базовые пресеты
            for cat, items in DEFAULT_GEAR_PRESETS.items():
                for it in items:
                    db.add(GearItem(
                        trip_id=trip.id,
                        category=cat,
                        name=it["name"],
                        quantity=it.get("quantity", "1 шт"),
                        note=it.get("note"),
                        is_packed=False
                    ))
        
        # Автоматически создаем базовую раскладку кухни
        food_ration = generate_food_ration(trip.participants_count, trip.duration_days)
        for f in food_ration:
            db.add(FoodItem(
                trip_id=trip.id,
                category=f["category"],
                name=f["name"],
                amount=f["amount"],
                assigned_to=f.get("assigned_to", "Все"),
                is_bought=False
            ))
            
        # Добавляем стартовую метку лагеря
        db.add(Waypoint(
            trip_id=trip.id,
            name=f"Лагерь: {trip.dest_name}",
            point_type="camp",
            lat=trip.dest_lat,
            lng=trip.dest_lng,
            description="Основная точка стоянки и палаток"
        ))
        
        db.commit()

    return RedirectResponse(url=f"/trips/{trip.id}", status_code=303)

@router.get("/trips/{trip_id}", response_class=HTMLResponse)
async def trip_detail(trip_id: int, request: Request, db: Session = Depends(get_db)):
    trip = db.query(Trip).filter(Trip.id == trip_id).first()
    if not trip:
        raise HTTPException(status_code=404, detail="Поездка не найдена")

    gear_items = db.query(GearItem).filter(GearItem.trip_id == trip_id).all()
    trophies = db.query(Trophy).filter(Trophy.trip_id == trip_id).order_by(Trophy.weight_kg.desc()).all()
    waypoints = db.query(Waypoint).filter(Waypoint.trip_id == trip_id).all()
    food_items = db.query(FoodItem).filter(FoodItem.trip_id == trip_id).all()
    expenses = db.query(ExpenseItem).filter(ExpenseItem.trip_id == trip_id).all()
    
    # Категории снаряжения
    categories_meta = {
        "camp": {"title": "Лагерь и Палатка", "icon": "fa-campground", "color": "emerald"},
        "fishing": {"title": "Рыбалка и Снасти", "icon": "fa-fish", "color": "blue"},
        "kitchen": {"title": "Походная Кухня", "icon": "fa-utensils", "color": "amber"},
        "clothes": {"title": "Одежда и Экипировка", "icon": "fa-shirt", "color": "indigo"},
        "firstaid": {"title": "Аптечка и Безопасность", "icon": "fa-kit-medical", "color": "rose"},
        "other": {"title": "Прочее снаряжение", "icon": "fa-box-archive", "color": "gray"}
    }
    
    grouped_gear = {k: [] for k in categories_meta.keys()}
    total_count = len(gear_items)
    packed_count = sum(1 for it in gear_items if it.is_packed)
    progress_percent = round((packed_count / total_count * 100)) if total_count > 0 else 0

    for item in gear_items:
        cat = item.category if item.category in grouped_gear else "other"
        grouped_gear[cat].append(item)

    # Расчет астрономии (Луна и Солнце)
    target_date = datetime.date.today()
    if trip.start_date:
        try:
            target_date = datetime.datetime.strptime(trip.start_date, "%Y-%m-%d").date()
        except Exception:
            pass

    moon_info = get_moon_phase(target_date)
    sun_info = calculate_sun_times(trip.dest_lat, trip.dest_lng, target_date)

    # Калькулятор топлива и бюджета (в тенге ₸)
    # Дистанция туда-обратно с учетом +15% на грунтовки и маневры
    roundtrip_km = round((trip.distance_km * 2) * 1.15, 1)
    fuel_liters = round((roundtrip_km / 100.0) * (trip.fuel_consumption or 9.5), 1)
    fuel_cost = round(fuel_liters * (trip.fuel_price or 230.0))
    
    other_expenses_total = sum(e.amount for e in expenses)
    total_budget = round(fuel_cost + other_expenses_total)
    cost_per_person = round(total_budget / max(1, trip.participants_count or 1))

    # Категории продуктов
    food_categories = {
        "drinks": "Напитки и вода",
        "meat": "Мясо и тушенка",
        "grains": "Крупы и макароны",
        "veggies": "Овощи и зелень",
        "spices": "Специи и масло",
        "snacks": "Сладости и снеки",
        "groceries": "Прочее"
    }

    food_total = len(food_items)
    food_bought = sum(1 for f in food_items if f.is_bought)

    # Загружаем прогноз погоды и барометр клева на сервере для мгновенного отображения
    from app.services.weather import get_weather_forecast
    try:
        weather_res = await get_weather_forecast(trip.dest_lat or 43.8950, trip.dest_lng or 77.0850, 7)
    except Exception as e:
        weather_res = {"status": "error", "days": []}

    return templates.TemplateResponse(
        request=request,
        name="trip_detail.html",
        context={
            "trip": trip,
            "grouped_gear": grouped_gear,
            "categories_meta": categories_meta,
            "total_count": total_count,
            "packed_count": packed_count,
            "progress_percent": progress_percent,
            "trophies": trophies,
            "waypoints": waypoints,
            "food_items": food_items,
            "food_categories": food_categories,
            "food_total": food_total,
            "food_bought": food_bought,
            "expenses": expenses,
            "moon_info": moon_info,
            "sun_info": sun_info,
            "weather_data": weather_res,
            "roundtrip_km": roundtrip_km,
            "fuel_liters": fuel_liters,
            "fuel_cost": fuel_cost,
            "other_expenses_total": other_expenses_total,
            "total_budget": total_budget,
            "cost_per_person": cost_per_person
        }
    )

@router.post("/trips/{trip_id}/status")
def update_trip_status(
    trip_id: int,
    status: str = Form(...),
    db: Session = Depends(get_db)
):
    trip = db.query(Trip).filter(Trip.id == trip_id).first()
    if not trip:
        raise HTTPException(status_code=404, detail="Поездка не найдена")
    trip.status = status
    db.commit()
    return RedirectResponse(url=f"/trips/{trip_id}", status_code=303)

@router.post("/trips/{trip_id}/catch-report")
def save_catch_report(
    trip_id: int,
    catch_notes: Optional[str] = Form(None),
    catch_weight_kg: Optional[float] = Form(0.0),
    catch_species: Optional[str] = Form(None),
    notes: Optional[str] = Form(None),
    db: Session = Depends(get_db)
):
    trip = db.query(Trip).filter(Trip.id == trip_id).first()
    if not trip:
        raise HTTPException(status_code=404, detail="Поездка не найдена")
    
    trip.catch_notes = catch_notes
    trip.catch_weight_kg = catch_weight_kg or 0.0
    trip.catch_species = catch_species
    if notes is not None:
        trip.notes = notes
    db.commit()
    
    return RedirectResponse(url=f"/trips/{trip_id}#report-section", status_code=303)

@router.post("/trips/{trip_id}/delete")
def delete_trip(trip_id: int, db: Session = Depends(get_db)):
    trip = db.query(Trip).filter(Trip.id == trip_id).first()
    if not trip:
        raise HTTPException(status_code=404, detail="Поездка не найдена")
    db.delete(trip)
    db.commit()
    return RedirectResponse(url="/", status_code=303)

@router.get("/history", response_class=HTMLResponse)
def history_page(request: Request, db: Session = Depends(get_db)):
    completed_trips = db.query(Trip).filter(Trip.status == "completed").order_by(Trip.id.desc()).all()
    total_catch = sum(t.catch_weight_kg or 0 for t in completed_trips)
    return templates.TemplateResponse(
        request=request,
        name="history.html",
        context={
            "completed_trips": completed_trips,
            "total_catch": round(total_catch, 1)
        }
    )

@router.get("/gear-presets", response_class=HTMLResponse)
def presets_page(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="gear_templates.html",
        context={
            "presets": DEFAULT_GEAR_PRESETS
        }
    )
