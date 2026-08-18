import httpx
import math
from typing import Dict, Any, Tuple

def calculate_haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Вычисляет прямое расстояние между двумя координатами в км."""
    R = 6371.0  # Радиус Земли в км
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = (math.sin(dlat / 2) ** 2 +
         math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) *
         math.sin(dlon / 2) ** 2)
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return round(R * c, 1)

async def calculate_route(start_lat: float, start_lng: float, end_lat: float, end_lng: float) -> Dict[str, Any]:
    """
    Рассчитывает маршрут по дорогам через публичный OSRM API.
    Возвращает геометрию маршрута (для Leaflet), расстояние в км и время в пути.
    """
    # Публичный OSRM сервер (car routing)
    url = f"https://router.project-osrm.org/route/v1/driving/{start_lng},{start_lat};{end_lng},{end_lat}?overview=full&geometries=geojson"
    
    try:
        async with httpx.AsyncClient(timeout=8.0) as client:
            resp = await client.get(url)
            if resp.status_code == 200:
                data = resp.json()
                if data.get("code") == "Ok" and data.get("routes"):
                    route = data["routes"][0]
                    dist_km = round(route["distance"] / 1000.0, 1)
                    duration_sec = route["duration"]
                    duration_min = round(duration_sec / 60.0)
                    
                    return {
                        "status": "success",
                        "distance_km": dist_km,
                        "duration_minutes": duration_min,
                        "geometry": route["geometry"]
                    }
    except Exception as e:
        print(f"OSRM routing failed, fallback to straight line calculation: {e}")
        
    # Запасной вариант: прямое расстояние * дорожный коэффициент 1.3
    straight_km = calculate_haversine_distance(start_lat, start_lng, end_lat, end_lng)
    estimated_road_km = round(straight_km * 1.3, 1)
    # Средняя скорость для загородных дорог ~ 60-70 км/ч
    est_minutes = round((estimated_road_km / 65.0) * 60)
    
    return {
        "status": "fallback",
        "distance_km": estimated_road_km,
        "duration_minutes": est_minutes,
        "geometry": {
            "type": "LineString",
            "coordinates": [[start_lng, start_lat], [end_lng, end_lat]]
        }
    }
