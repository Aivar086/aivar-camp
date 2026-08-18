from fastapi import APIRouter, Depends, Form, HTTPException, Request
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from typing import Optional
import datetime

from app.database import get_db
from app.models import Trip
from app.services.ai_ranger import analyze_fishing_weather, ask_ranger_ai
from app.services.weather import get_weather_forecast
from app.services.astro import get_moon_phase

router = APIRouter(prefix="/api/ranger", tags=["AI Ranger"])

@router.post("/trip-tactics/{trip_id}")
async def get_trip_tactics(trip_id: int, db: Session = Depends(get_db)):
    trip = db.query(Trip).filter(Trip.id == trip_id).first()
    if not trip:
        raise HTTPException(status_code=404, detail="Поездка не найдена")

    weather = await get_weather_forecast(trip.dest_lat or 43.8950, trip.dest_lng or 77.0850, 7)
    days = weather.get("days", [])
    
    first_day = days[0] if days else {}
    t_max = first_day.get("temp_max", 25.0)
    t_min = first_day.get("temp_min", 15.0)
    pressure = first_day.get("pressure_mm", 755.0)
    wind = first_day.get("wind_speed", 10.0)
    precip_prob = first_day.get("precip_prob", 10)
    
    target_date = datetime.date.today()
    if trip.start_date:
        try:
            target_date = datetime.datetime.strptime(trip.start_date, "%Y-%m-%d").date()
        except Exception:
            pass
            
    moon = get_moon_phase(target_date)
    
    analysis = analyze_fishing_weather(
        temp_max=t_max,
        temp_min=t_min,
        pressure_mm=pressure,
        wind_speed=wind,
        precip_prob=precip_prob,
        moon_phase_name=moon["phase_name"],
        target_species=trip.catch_species or "Судак, Сазан, Щука"
    )
    
    return JSONResponse(analysis)

@router.post("/chat")
def ranger_chat(query: str = Form(...)):
    answer = ask_ranger_ai(query)
    return JSONResponse({"answer": answer})
