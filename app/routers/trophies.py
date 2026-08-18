from fastapi import APIRouter, Depends, Form, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from typing import Optional
import os

from app.database import get_db
from app.models import Trophy, Trip

templates = Jinja2Templates(directory=os.path.join(os.path.dirname(__file__), "..", "templates"))
router = APIRouter(tags=["Trophies"])

@router.get("/trophies", response_class=HTMLResponse)
def trophies_gallery(request: Request, db: Session = Depends(get_db)):
    all_trophies = db.query(Trophy).order_by(Trophy.weight_kg.desc(), Trophy.id.desc()).all()
    total_weight = sum(t.weight_kg for t in all_trophies)
    trophy_count = len(all_trophies)
    
    return templates.TemplateResponse(
        request=request,
        name="trophies.html",
        context={
            "trophies": all_trophies,
            "total_weight": round(total_weight, 1),
            "trophy_count": trophy_count
        }
    )

@router.post("/trips/{trip_id}/trophies/add")
def add_trophy(
    trip_id: int,
    species: str = Form(...),
    weight_kg: float = Form(...),
    length_cm: Optional[float] = Form(None),
    lure_or_bait: Optional[str] = Form(None),
    time_of_catch: Optional[str] = Form(None),
    depth_m: Optional[float] = Form(None),
    image_url: Optional[str] = Form(None),
    notes: Optional[str] = Form(None),
    db: Session = Depends(get_db)
):
    trip = db.query(Trip).filter(Trip.id == trip_id).first()
    if not trip:
        raise HTTPException(status_code=404, detail="Поездка не найдена")

    trophy = Trophy(
        trip_id=trip_id,
        species=species.strip(),
        weight_kg=weight_kg,
        length_cm=length_cm,
        lure_or_bait=lure_or_bait.strip() if lure_or_bait else None,
        time_of_catch=time_of_catch.strip() if time_of_catch else None,
        depth_m=depth_m,
        image_url=image_url.strip() if image_url else None,
        notes=notes.strip() if notes else None,
        lat=trip.dest_lat,
        lng=trip.dest_lng
    )
    db.add(trophy)
    
    # Также обновляем общий счетчик улова в поездке
    trip.catch_weight_kg = (trip.catch_weight_kg or 0.0) + weight_kg
    if not trip.catch_species:
        trip.catch_species = species
    elif species not in trip.catch_species:
        trip.catch_species += f", {species}"
        
    db.commit()
    return RedirectResponse(url=f"/trips/{trip_id}#trophies-section", status_code=303)

@router.post("/trophies/{trophy_id}/delete")
def delete_trophy(trophy_id: int, db: Session = Depends(get_db)):
    trophy = db.query(Trophy).filter(Trophy.id == trophy_id).first()
    if not trophy:
        raise HTTPException(status_code=404, detail="Трофей не найден")
    trip_id = trophy.trip_id
    db.delete(trophy)
    db.commit()
    return RedirectResponse(url=f"/trips/{trip_id}#trophies-section", status_code=303)
