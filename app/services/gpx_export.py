from typing import List
from app.models import Trip, Waypoint

def generate_gpx_content(trip: Trip, waypoints: List[Waypoint]) -> str:
    """
    Генерирует GPX 1.1 XML с маршрутом и вейпоинтами поездки.
    """
    lines = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<gpx version="1.1" creator="CampAndFishPlannerPro - https://github.com"',
        '  xmlns="http://www.topografix.com/GPX/1/1"',
        '  xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"',
        '  xsi:schemaLocation="http://www.topografix.com/GPX/1/1 http://www.topografix.com/GPX/1/1/gpx.xsd">',
        f'  <metadata><name>{trip.title}</name><desc>{trip.description or ""}</desc></metadata>',
    ]

    # Точка старта
    if trip.origin_lat and trip.origin_lng:
        lines.append(f'  <wpt lat="{trip.origin_lat}" lon="{trip.origin_lng}">')
        lines.append(f'    <name>{trip.origin_name or "Старт"}</name>')
        lines.append('    <sym>Home</sym>')
        lines.append('  </wpt>')

    # Точка лагеря
    lines.append(f'  <wpt lat="{trip.dest_lat}" lon="{trip.dest_lng}">')
    lines.append(f'    <name>{trip.dest_name or "Лагерь"}</name>')
    lines.append('    <sym>Campground</sym>')
    lines.append('  </wpt>')

    # Вейпоинты
    for wp in waypoints:
        sym_map = {
            "camp": "Campground",
            "fishing": "Fishing Area",
            "spring": "Drinking Water",
            "boat": "Boat Ramp",
            "wood": "Forest",
            "obstacle": "Danger Area"
        }
        sym = sym_map.get(wp.point_type, "Pin")
        lines.append(f'  <wpt lat="{wp.lat}" lon="{wp.lng}">')
        lines.append(f'    <name>{wp.name}</name>')
        if wp.description:
            lines.append(f'    <desc>{wp.description}</desc>')
        lines.append(f'    <sym>{sym}</sym>')
        lines.append('  </wpt>')

    # Трек
    lines.append('  <trk>')
    lines.append(f'    <name>Трек: {trip.title}</name>')
    lines.append('    <trkseg>')
    if trip.origin_lat and trip.origin_lng:
        lines.append(f'      <trkpt lat="{trip.origin_lat}" lon="{trip.origin_lng}"></trkpt>')
    lines.append(f'      <trkpt lat="{trip.dest_lat}" lon="{trip.dest_lng}"></trkpt>')
    lines.append('    </trkseg>')
    lines.append('  </trk>')

    lines.append('</gpx>')
    return '\n'.join(lines)
