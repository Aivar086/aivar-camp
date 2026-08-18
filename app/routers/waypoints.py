from fastapi import APIRouter, Depends, Form, HTTPException, Request
from fastapi.responses import JSONResponse, RedirectResponse
from sqlalchemy.orm import Session
from typing import Optional

from app.database import get_db
from app.models import Waypoint, Trip

router = APIRouter(tags=["Waypoints"])

@router.get("/api/trips/{trip_id}/waypoints")
def get_trip_waypoints(trip_id: int, db: Session = Depends(get_db)):
    points = db.query(Waypoint).filter(Waypoint.trip_id == trip_id).all()
    return [
        {
            "id": p.id,
            "name": p.name,
            "type": p.point_type,
            "lat": p.lat,
            "lng": p.lng,
            "description": p.description
        } for p in points
    ]

@router.post("/trips/{trip_id}/waypoints/add")
def add_waypoint(
    trip_id: int,
    name: str = Form(...),
    point_type: str = Form("camp"),
    lat: float = Form(...),
    lng: float = Form(...),
    description: Optional[str] = Form(None),
    db: Session = Depends(get_db)
):
    trip = db.query(Trip).filter(Trip.id == trip_id).first()
    if not trip:
        raise HTTPException(status_code=404, detail="Поездка не найдена")

    wp = Waypoint(
        trip_id=trip_id,
        name=name.strip(),
        point_type=point_type,
        lat=lat,
        lng=lng,
        description=description.strip() if description else None
    )
    db.add(wp)
    db.commit()
    return RedirectResponse(url=f"/trips/{trip_id}#map-section", status_code=303)

@router.post("/waypoints/{wp_id}/delete")
def delete_waypoint(wp_id: int, db: Session = Depends(get_db)):
    wp = db.query(Waypoint).filter(Waypoint.id == wp_id).first()
    if not wp:
        raise HTTPException(status_code=404, detail="Точка не найдена")
    trip_id = wp.trip_id
    db.delete(wp)
    db.commit()
    return RedirectResponse(url=f"/trips/{trip_id}#map-section", status_code=303)
