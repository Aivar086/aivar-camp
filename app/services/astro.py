import math
import datetime
from typing import Dict, Any

def get_moon_phase(date_obj: datetime.date) -> Dict[str, Any]:
    """
    Вычисляет фазу Луны и её рыболовное влияние.
    Синодический месяц ~ 29.530588853 дней.
    """
    # Опорное новолуние: 6 января 2000 года
    ref_date = datetime.date(2000, 1, 6)
    days_diff = (date_obj - ref_date).days
    phase_val = (days_diff % 29.530588853) / 29.530588853
    age_days = round(phase_val * 29.53, 1)

    if phase_val < 0.03 or phase_val > 0.97:
        phase_name = "Новолуние"
        icon = "🌑"
        fishing_rating = "Средний клев"
        tip = "В новолуние ночи темные, ночной хищник (судак) держится ближе к отмелям."
    elif 0.03 <= phase_val < 0.22:
        phase_name = "Молодая растущая Луна"
        icon = "🌒"
        fishing_rating = "Отличный активный клев"
        tip = "Растущая луна — один из самых благоприятных периодов для ловли щуки, окуня и мирной рыбы."
    elif 0.22 <= phase_val < 0.28:
        phase_name = "Первая четверть"
        icon = "🌓"
        fishing_rating = "Хороший клев"
        tip = "Стабильная активность рыбы на утренней и вечерней зорьках."
    elif 0.28 <= phase_val < 0.47:
        phase_name = "Прибывающая Луна"
        icon = "🌔"
        fishing_rating = "Высокая активность"
        tip = "Рыба активно кормится перед полнолунием. Хорошо работают яркие приманки."
    elif 0.47 <= phase_val < 0.53:
        phase_name = "Полнолуние"
        icon = "🌕"
        fishing_rating = "Непредсказуемый / Ночной клев"
        tip = "В полнолуние рыба часто кормится ночью при лунном свете, а днем клев может затихать."
    elif 0.53 <= phase_val < 0.72:
        phase_name = "Убывающая Луна"
        icon = "🌖"
        fishing_rating = "Умеренный клев"
        tip = "Клев постепенно стабилизируется. Ищите рыбу на перепадах глубин."
    elif 0.72 <= phase_val < 0.78:
        phase_name = "Последняя четверть"
        icon = "🌗"
        fishing_rating = "Нормальный клев"
        tip = "Хорошие результаты дают естественные натуральные наживки и спокойная подача."
    else:
        phase_name = "Старая Луна"
        icon = "🌘"
        fishing_rating = "Пассивный клев"
        tip = "Перед новолунием активность снижается, экспериментируйте с размером приманок в сторону уменьшения."

    illumination = round((0.5 * (1 - math.cos(2 * math.pi * phase_val))) * 100)

    return {
        "phase_name": phase_name,
        "icon": icon,
        "age_days": age_days,
        "illumination_percent": illumination,
        "fishing_rating": fishing_rating,
        "tip": tip
    }

def calculate_sun_times(lat: float, lng: float, date_obj: datetime.date) -> Dict[str, str]:
    """
    Приближенный расчет времени восхода, заката и сумерек для выбранной точки.
    """
    day_of_year = date_obj.timetuple().tm_yday
    
    # Склонение солнца
    declination = 23.45 * math.sin(math.radians((360 / 365) * (day_of_year - 81)))
    
    lat_rad = math.radians(lat)
    dec_rad = math.radians(declination)
    
    # Часовой угол
    try:
        cos_hour_angle = (math.sin(math.radians(-0.83)) - math.sin(lat_rad) * math.sin(dec_rad)) / (math.cos(lat_rad) * math.cos(dec_rad))
        cos_hour_angle = max(-1.0, min(1.0, cos_hour_angle))
        hour_angle = math.degrees(math.acos(cos_hour_angle))
    except Exception:
        hour_angle = 90.0

    solar_noon_utc = 12.0 - (lng / 15.0)
    # Примерный часовой пояс
    tz_offset = round(lng / 15.0)
    
    sunrise_hours = (solar_noon_utc - (hour_angle / 15.0)) + tz_offset
    sunset_hours = (solar_noon_utc + (hour_angle / 15.0)) + tz_offset
    
    def format_time(h_float: float) -> str:
        h_float = h_float % 24
        hours = int(h_float)
        minutes = int((h_float - hours) * 60)
        return f"{hours:02d}:{minutes:02d}"

    sunrise_str = format_time(sunrise_hours)
    sunset_str = format_time(sunset_hours)
    dawn_str = format_time(sunrise_hours - 0.6) # Утренняя зорька / сумерки
    dusk_str = format_time(sunset_hours + 0.6) # Вечерняя зорька
    golden_hour_str = format_time(sunset_hours - 0.8) # Золотой час

    day_length_hours = int((sunset_hours - sunrise_hours) % 24)
    day_length_mins = int(((sunset_hours - sunrise_hours) % 1) * 60)

    return {
        "dawn": dawn_str,
        "sunrise": sunrise_str,
        "sunset": sunset_str,
        "dusk": dusk_str,
        "golden_hour": golden_hour_str,
        "day_length": f"{day_length_hours}ч {day_length_mins}м"
    }
