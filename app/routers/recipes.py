from fastapi import APIRouter, Depends, Form, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
import os

from app.database import get_db
from app.models import Trip, FoodItem
from app.services.recipes_data import CAMP_RECIPES, get_recipe_by_id
from app.routers.auth import is_captain

templates = Jinja2Templates(directory=os.path.join(os.path.dirname(__file__), "..", "templates"))
router = APIRouter(tags=["Recipes"])

@router.get("/recipes", response_class=HTMLResponse)
def recipes_list(request: Request, trip_id: int = None, db: Session = Depends(get_db)):
    active_trips = db.query(Trip).filter(Trip.status == "planned").all()
    selected_trip = db.query(Trip).filter(Trip.id == trip_id).first() if trip_id else None
    
    return templates.TemplateResponse(
        request=request,
        name="recipes.html",
        context={
            "recipes": CAMP_RECIPES,
            "active_trips": active_trips,
            "selected_trip": selected_trip
        }
    )

@router.post("/trips/{trip_id}/recipes/import")
def import_recipe_to_trip(
    trip_id: int,
    request: Request,
    recipe_id: str = Form(...),
    servings: int = Form(4),
    assigned_to: str = Form("Общий котёл"),
    db: Session = Depends(get_db)
):
    if not is_captain(request):
        raise HTTPException(status_code=403, detail="Только капитан может добавлять продукты в поездку")

    trip = db.query(Trip).filter(Trip.id == trip_id).first()
    if not trip:
        raise HTTPException(status_code=404, detail="Поездка не найдена")

    recipe = get_recipe_by_id(recipe_id)
    if not recipe:
        raise HTTPException(status_code=404, detail="Рецепт не найден")

    # Масштабируем ингредиенты под количество человек
    for ing in recipe["ingredients_per_person"]:
        total_num = round(ing["amount_num"] * servings, 2)
        if total_num == int(total_num):
            total_num = int(total_num)
            
        amount_str = f"{total_num} {ing['unit']}"
        item_name = f"{ing['name']} (для «{recipe['title']}»)"

        db.add(FoodItem(
            trip_id=trip_id,
            category=ing.get("category", "groceries"),
            name=item_name,
            amount=amount_str,
            assigned_to=assigned_to,
            is_bought=False
        ))
        
    db.commit()
    return RedirectResponse(url=f"/trips/{trip_id}#food-section", status_code=303)
