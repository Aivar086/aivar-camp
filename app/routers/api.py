from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
import httpx
from app.database import get_db
from app.services.weather import get_weather_forecast
from app.services.routing import calculate_route

router = APIRouter(prefix="/api", tags=["API"])

@router.get("/weather")
async def fetch_weather(lat: float = Query(...), lng: float = Query(...), days: int = Query(7)):
    """Получить прогноз погоды для указанных координат."""
    data = await get_weather_forecast(lat, lng, days)
    return data

@router.get("/route")
async def fetch_route(
    start_lat: float = Query(...),
    start_lng: float = Query(...),
    end_lat: float = Query(...),
    end_lng: float = Query(...)
):
    """Рассчитать автомобильный маршрут, километраж и время."""
    data = await calculate_route(start_lat, start_lng, end_lat, end_lng)
    return data

@router.get("/geocode")
async def geocode_place(q: str = Query(..., min_length=2)):
    """Поиск населенного пункта / реки / озера по названию через Nominatim (OSM)."""
    url = "https://nominatim.openstreetmap.org/search"
    headers = {
        "User-Agent": "CampingFishingPlanner/1.0 (contact@campingfish.local)"
    }
    params = {
        "q": q,
        "format": "json",
        "limit": 5,
        "addressdetails": 1
    }
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            resp = await client.get(url, params=params, headers=headers)
            if resp.status_code == 200:
                results = []
                for item in resp.json():
                    results.append({
                        "name": item.get("display_name"),
                        "lat": float(item.get("lat")),
                        "lng": float(item.get("lon")),
                        "type": item.get("type")
                    })
                return {"status": "success", "results": results}
    except Exception as e:
        print(f"Geocoding error: {e}")
        
    return {"status": "error", "results": []}

@router.get("/reverse-geocode")
async def reverse_geocode_place(lat: float = Query(...), lng: float = Query(...)):
    """Определение названия города/улицы по координатам пользователя."""
    url = "https://nominatim.openstreetmap.org/reverse"
    headers = {
        "User-Agent": "CampingFishingPlanner/1.0 (contact@campingfish.local)"
    }
    params = {
        "lat": lat,
        "lon": lng,
        "format": "json",
        "zoom": 14,
        "addressdetails": 1
    }
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            resp = await client.get(url, params=params, headers=headers)
            if resp.status_code == 200:
                data = resp.json()
                addr = data.get("address", {})
                city = addr.get("city") or addr.get("town") or addr.get("village") or addr.get("state") or "Мое местоположение"
                display = data.get("display_name", city)
                return {"status": "success", "city": city, "display_name": display}
    except Exception as e:
        print(f"Reverse geocoding error: {e}")
        
    return {"status": "fallback", "city": "Мое местоположение"}
