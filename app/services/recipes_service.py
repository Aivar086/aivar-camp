import json
import os
from sqlalchemy.orm import Session
from app.models import Recipe

CATEGORIES_MAP = {
    "kazan": {"title": "Казан классический", "icon": "🍲"},
    "afghan_kazan": {"title": "Афганский казан", "icon": "⚡"},
    "mangal": {"title": "Мангал & Гриль", "icon": "🍢"},
    "skovoroda": {"title": "Садж & Сковорода", "icon": "🍳"},
    "fish": {"title": "Рыба & Уха", "icon": "🐟"},
    "tea_dessert": {"title": "Чай & Напитки", "icon": "☕"}
}

def seed_recipes_if_needed(db: Session):
    count = db.query(Recipe).count()
    if count == 0:
        json_path = os.path.join(os.path.dirname(__file__), "recipes_catalog.json")
        if os.path.exists(json_path):
            with open(json_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            for it in data:
                db.add(Recipe(
                    slug=it.get("slug"),
                    title=it.get("title"),
                    category=it.get("category", "kazan"),
                    category_title=it.get("category_title", "Блюда в казане"),
                    icon=it.get("icon", "🍲"),
                    time=it.get("time", "1 час"),
                    difficulty=it.get("difficulty", "Легко"),
                    description=it.get("description"),
                    servings_base=it.get("servings_base", 4),
                    ingredients_json=json.dumps(it.get("ingredients", []), ensure_ascii=False),
                    steps_json=json.dumps(it.get("steps", []), ensure_ascii=False),
                    is_custom=False
                ))
            db.commit()

def get_all_recipes(db: Session, category: str = None, search: str = None):
    seed_recipes_if_needed(db)
    query = db.query(Recipe)
    if category and category != "all":
        query = query.filter(Recipe.category == category)
    
    recipes_db = query.order_by(Recipe.is_custom.desc(), Recipe.id.asc()).all()
    result = []
    search_term = search.strip().lower() if search else None

    for r in recipes_db:
        try:
            ingredients = json.loads(r.ingredients_json)
        except Exception:
            ingredients = []
        try:
            steps = json.loads(r.steps_json)
        except Exception:
            steps = []
            
        # Фильтрация по поисковой строке
        if search_term:
            match_title = search_term in (r.title or "").lower()
            match_desc = search_term in (r.description or "").lower()
            match_ing = any(search_term in ing.get("name", "").lower() for ing in ingredients)
            if not (match_title or match_desc or match_ing):
                continue

        result.append({
            "id": r.id,
            "slug": r.slug,
            "title": r.title,
            "category": r.category,
            "category_title": r.category_title,
            "icon": r.icon,
            "time": r.time,
            "difficulty": r.difficulty,
            "description": r.description,
            "servings_base": r.servings_base,
            "ingredients_per_person": ingredients,
            "steps": steps,
            "is_custom": r.is_custom
        })
    return result

def get_recipe_by_db_id(db: Session, recipe_id: int):
    r = db.query(Recipe).filter(Recipe.id == recipe_id).first()
    if not r:
        return None
    try:
        ingredients = json.loads(r.ingredients_json)
    except Exception:
        ingredients = []
    try:
        steps = json.loads(r.steps_json)
    except Exception:
        steps = []
    return {
        "id": r.id,
        "slug": r.slug,
        "title": r.title,
        "category": r.category,
        "category_title": r.category_title,
        "icon": r.icon,
        "time": r.time,
        "difficulty": r.difficulty,
        "description": r.description,
        "servings_base": r.servings_base,
        "ingredients_per_person": ingredients,
        "steps": steps,
        "is_custom": r.is_custom
    }
