import httpx
from typing import Dict, Any, Optional

async def get_weather_forecast(lat: float, lng: float, days: int = 7) -> Dict[str, Any]:
    """
    Получает прогноз погоды через бесплатный Open-Meteo API.
    Включает температуру, осадки, ветер, давление (гПа -> мм рт. ст.) и код погоды.
    """
    url = "https://api.open-meteo.com/v1/forecast"
    params = {
        "latitude": lat,
        "longitude": lng,
        "daily": [
            "weathercode",
            "temperature_2m_max",
            "temperature_2m_min",
            "precipitation_sum",
            "precipitation_probability_max",
            "windspeed_10m_max",
            "winddirection_10m_dominant",
            "surface_pressure_mean"
        ],
        "hourly": [
            "temperature_2m",
            "precipitation_probability",
            "precipitation",
            "surface_pressure",
            "windspeed_10m",
            "weathercode"
        ],
        "timezone": "auto",
        "forecast_days": min(days, 14)
    }

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(url, params=params)
            if resp.status_code == 200:
                data = resp.json()
                return process_weather_data(data)
    except Exception as e:
        print(f"Error fetching weather: {e}")
    
    return {"status": "error", "message": "Не удалось загрузить погоду"}

def get_weather_desc(code: int) -> tuple[str, str]:
    """Возвращает текстовое описание и иконку для WMO weather code."""
    codes = {
        0: ("Ясно, без осадков", "☀️"),
        1: ("Преимущественно ясно", "🌤️"),
        2: ("Переменная облачность", "⛅"),
        3: ("Пасмурно", "☁️"),
        45: ("Туман", "🌫️"),
        48: ("Изморозь / туман", "🌫️"),
        51: ("Небольшая морось", "🌦️"),
        53: ("Умеренная морось", "🌧️"),
        55: ("Плотная морось", "🌧️"),
        61: ("Небольшой дождь", "🌦️"),
        63: ("Умеренный дождь", "🌧️"),
        65: ("Сильный ливень", "⛈️"),
        71: ("Небольшой снег", "🌨️"),
        73: ("Снегопад", "❄️"),
        75: ("Сильный снег", "❄️"),
        80: ("Кратковременный ливень", "🌦️"),
        81: ("Ливень", "🌧️"),
        82: ("Шквальный ливень", "⛈️"),
        95: ("Гроза", "⚡"),
        96: ("Гроза с градом", "⛈️"),
    }
    return codes.get(code, ("Облачно", "⛅"))

def evaluate_fishing_conditions(temp_max: float, wind_speed: float, pressure_mm: float, precip_prob: int) -> dict:
    """
    Оценивает условия для рыбалки и кемпинга на основе давления, ветра и температуры.
    Нормальное давление ~ 750-760 мм рт. ст.
    """
    score = 100
    tips = []
    
    # Давление
    if 752 <= pressure_mm <= 762:
        tips.append("🎯 Давление стабильное и близко к норме — отличный показатель для стабильного клева хищника и мирной рыбы.")
    elif pressure_mm < 748:
        score -= 20
        tips.append("📉 Пониженное давление — хищник (щука, окунь) может активизироваться перед ненастьем, но мирная рыба вялая.")
    elif pressure_mm > 765:
        score -= 15
        tips.append("📈 Повышенное давление — рыба уходит на глубину или в укрытия. Ищите в ямах и бровках.")
        
    # Ветер
    if wind_speed < 12:
        tips.append("💨 Слабый комфортный ветер — удобно ставить лагерь и ловить на поплавок / фидер.")
    elif 12 <= wind_speed <= 25:
        score -= 10
        tips.append("🌬️ Умеренный ветер — создает прибойную волну у берега, где любит кормиться рыба. Укрепите растяжки палатки.")
    else:
        score -= 35
        tips.append("⚠️ Сильный порывистый ветер! Выход на лодке опасен, ставьте палатку в подветренной стороне леса.")
        
    # Осадки
    if precip_prob > 60:
        score -= 20
        tips.append("🌧️ Высокая вероятность дождя — возьмите тент, дождевики и гермомешки для вещей.")
        
    rating = "Отличные" if score >= 80 else ("Хорошие" if score >= 60 else "Умеренные / Сложные")
    badge_color = "emerald" if score >= 80 else ("amber" if score >= 60 else "rose")

    return {
        "score": max(20, score),
        "rating": rating,
        "badge_color": badge_color,
        "tips": tips
    }

def process_weather_data(raw: Dict[str, Any]) -> Dict[str, Any]:
    daily = raw.get("daily", {})
    dates = daily.get("time", [])
    days_list = []
    
    for i, dt in enumerate(dates):
        code = daily.get("weathercode", [0])[i] if i < len(daily.get("weathercode", [])) else 0
        desc, icon = get_weather_desc(code)
        
        t_max = round(daily.get("temperature_2m_max", [0])[i], 1)
        t_min = round(daily.get("temperature_2m_min", [0])[i], 1)
        precip = round(daily.get("precipitation_sum", [0])[i], 1)
        precip_prob = daily.get("precipitation_probability_max", [0])[i] or 0
        wind = round(daily.get("windspeed_10m_max", [0])[i], 1)
        
        # Перевод давления из hPa в мм рт. ст. (1 hPa = 0.750062 мм рт. ст.)
        pressure_hpa = daily.get("surface_pressure_mean", [1013.25])[i] if i < len(daily.get("surface_pressure_mean", [])) else 1013.25
        pressure_mm = round(pressure_hpa * 0.750062, 1)
        
        fish_eval = evaluate_fishing_conditions(t_max, wind, pressure_mm, precip_prob)
        
        days_list.append({
            "date": dt,
            "desc": desc,
            "icon": icon,
            "temp_max": t_max,
            "temp_min": t_min,
            "precipitation": precip,
            "precip_prob": precip_prob,
            "wind_speed": wind,
            "pressure_mm": pressure_mm,
            "fishing": fish_eval
        })
        
    return {
        "status": "success",
        "days": days_list,
        "current_lat": raw.get("latitude"),
        "current_lng": raw.get("longitude")
    }
