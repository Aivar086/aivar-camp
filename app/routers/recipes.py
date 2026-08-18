from fastapi import APIRouter, Depends, Form, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
import os
import json

from app.database import get_db
from app.models import Trip, FoodItem, Recipe
from app.services.recipes_service import get_all_recipes, get_recipe_by_db_id, CATEGORIES_MAP
from app.routers.auth import is_captain

templates = Jinja2Templates(directory=os.path.join(os.path.dirname(__file__), "..", "templates"))
router = APIRouter(tags=["Recipes"])

@router.get("/recipes", response_class=HTMLResponse)
def recipes_list(
    request: Request,
    category: str = "all",
    search: str = None,
    trip_id: int = None,
    db: Session = Depends(get_db)
):
    recipes = get_all_recipes(db, category=category, search=search)
    active_trips = db.query(Trip).filter(Trip.status == "planned").all()
    selected_trip = db.query(Trip).filter(Trip.id == trip_id).first() if trip_id else None
    
    return templates.TemplateResponse(
        request=request,
        name="recipes.html",
        context={
            "recipes": recipes,
            "active_trips": active_trips,
            "selected_trip": selected_trip,
            "current_category": category,
            "search_query": search or "",
            "categories_map": CATEGORIES_MAP
        }
    )

@router.post("/recipes/add")
def add_custom_recipe(
    request: Request,
    title: str = Form(...),
    category: str = Form("kazan"),
    time: str = Form("1 час"),
    difficulty: str = Form("Легко"),
    description: str = Form(""),
    ingredients_text: str = Form(...), # Строки вида: "Мясо говядина: 0.3 кг" или просто список
    steps_text: str = Form(...),       # Построчные шаги
    db: Session = Depends(get_db)
):
    if not is_captain(request):
        raise HTTPException(status_code=403, detail="Только капитан Aivar может добавлять рецепты")

    cat_info = CATEGORIES_MAP.get(category, {"title": "Блюда в казане", "icon": "🍲"})
    
    # Парсинг ингредиентов
    ingredients_list = []
    for line in ingredients_text.strip().split("\n"):
        line = line.strip()
        if not line:
            continue
        # Попробуем распарсить "Название: 0.25 кг" или "Название - 1 шт"
        parts = line.split(":") if ":" in line else line.split("-")
        if len(parts) >= 2:
            name = parts[0].strip()
            amount_raw = parts[1].strip()
            # Попробуем выделить число
            tokens = amount_raw.split()
            try:
                num = float(tokens[0].replace(",", "."))
                unit = " ".join(tokens[1:]) if len(tokens) > 1 else "порц."
            except Exception:
                num = 1.0
                unit = amount_raw
            ingredients_list.append({"name": name, "amount_num": num, "unit": unit, "category": "groceries"})
        else:
            ingredients_list.append({"name": line, "amount_num": 1.0, "unit": "порц.", "category": "groceries"})

    # Парсинг шагов
    steps_list = [s.strip() for s in steps_text.strip().split("\n") if s.strip()]

    new_recipe = Recipe(
        title=title.strip(),
        category=category,
        category_title=cat_info["title"],
        icon=cat_info["icon"],
        time=time.strip(),
        difficulty=difficulty.strip(),
        description=description.strip(),
        servings_base=4,
        ingredients_json=json.dumps(ingredients_list, ensure_ascii=False),
        steps_json=json.dumps(steps_list, ensure_ascii=False),
        is_custom=True
    )
    db.add(new_recipe)
    db.commit()
    return RedirectResponse(url=f"/recipes?category={category}", status_code=303)

@router.post("/recipes/{id}/delete")
def delete_custom_recipe(id: int, request: Request, db: Session = Depends(get_db)):
    if not is_captain(request):
        raise HTTPException(status_code=403, detail="Только капитан может удалять рецепты")
    
    rec = db.query(Recipe).filter(Recipe.id == id, Recipe.is_custom == True).first()
    if rec:
        db.delete(rec)
        db.commit()
    return RedirectResponse(url="/recipes", status_code=303)

@router.post("/trips/{trip_id}/recipes/import")
def import_recipe_to_trip(
    trip_id: int,
    request: Request,
    recipe_id: int = Form(...),
    servings: int = Form(4),
    assigned_to: str = Form("Общий котёл"),
    db: Session = Depends(get_db)
):
    if not is_captain(request):
        raise HTTPException(status_code=403, detail="Только капитан может добавлять продукты в поездку")

    trip = db.query(Trip).filter(Trip.id == trip_id).first()
    if not trip:
        raise HTTPException(status_code=404, detail="Поездка не найдена")

    recipe = get_recipe_by_db_id(db, recipe_id)
    if not recipe:
        raise HTTPException(status_code=404, detail="Рецепт не найден")

    # Масштабируем ингредиенты под количество человек
    for ing in recipe["ingredients_per_person"]:
        total_num = round(ing.get("amount_num", 1) * servings, 2)
        if total_num == int(total_num):
            total_num = int(total_num)
            
        unit = ing.get("unit", "шт")
        amount_str = f"{total_num} {unit}"
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
