from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, HTMLResponse, RedirectResponse
import os
import json

from app.database import engine, Base, SessionLocal
from app.models import UserInventoryItem, Trip
from app.routers import trips, gear, api, trophies, waypoints, logistics, guide, inventory, ai_ranger, auth
from app.routers.auth import is_authorized, get_user_role, COOKIE_AUTH_ROLE, ROLE_CAPTAIN, ROLE_GUEST

# Автоматическое создание / обновление таблиц базы данных при запуске
Base.metadata.create_all(bind=engine)

def auto_seed_user_inventory():
    db = SessionLocal()
    try:
        count = db.query(UserInventoryItem).count()
        if count == 0:
            json_path = os.path.join(os.path.dirname(__file__), "services", "user_inventory.json")
            if os.path.exists(json_path):
                with open(json_path, "r", encoding="utf-8") as f:
                    items = json.load(f)
                for it in items:
                    db.add(UserInventoryItem(
                        category=it.get("category", "other"),
                        name=it.get("name"),
                        brand_or_model=it.get("brand_or_model"),
                        quantity=it.get("quantity", "1 шт"),
                        weight_kg=it.get("weight_kg"),
                        notes=it.get("notes")
                    ))
                db.commit()
    except Exception as e:
        print("Auto-seed error:", e)
    finally:
        db.close()

auto_seed_user_inventory()

app = FastAPI(
    title="Aivar Camp — Кемпинг & Рыбалка в Казахстане",
    description="Комплексный сервис для организации выездов: маршруты, рыболовная погода, барометр, фазы Луны, тайминги солнца, калькуляторы кухни и топлива, чек-листы и журнал трофеев.",
    version="2.3.0"
)

# Middleware полной приватности сайта
@app.middleware("http")
async def private_access_middleware(request: Request, call_next):
    path = request.url.path
    
    # Разрешенные публичные пути: статика, фавиконки, вход
    public_prefixes = ["/static", "/favicon.ico", "/apple-touch-icon", "/login", "/auth/login"]
    if any(path.startswith(prefix) for prefix in public_prefixes):
        return await call_next(request)
        
    # Проверка ключа в URL (?key=...)
    key_param = request.query_params.get("key")
    if key_param:
        role = get_user_role(request)
        if role in [ROLE_CAPTAIN, ROLE_GUEST]:
            response = await call_next(request)
            response.set_cookie(
                key=COOKIE_AUTH_ROLE,
                value=role,
                max_age=60 * 60 * 24 * 90,
                httponly=True,
                samesite="lax"
            )
            return response
            
    # Проверка наличия прав (кука)
    if not is_authorized(request):
        # Если это API запрос — возвращаем 401
        if path.startswith("/api/"):
            return HTMLResponse(status_code=401, content='{"error": "Unauthorized"}')
        # Для страниц — перенаправляем на экран закрытого входа
        return RedirectResponse(url=f"/login?redirect_url={path}", status_code=303)
        
    return await call_next(request)

# Подключение статических файлов
static_dir = os.path.join(os.path.dirname(__file__), "static")
if not os.path.exists(static_dir):
    os.makedirs(static_dir, exist_ok=True)

app.mount("/static", StaticFiles(directory=static_dir), name="static")

@app.get("/favicon.ico", include_in_schema=False)
@app.get("/apple-touch-icon.png", include_in_schema=False)
@app.get("/apple-touch-icon-precomposed.png", include_in_schema=False)
def get_favicon():
    logo_path = os.path.join(static_dir, "img", "logo.png")
    if os.path.exists(logo_path):
        return FileResponse(logo_path)
    return HTMLResponse(status_code=204)

# Подключение маршрутов
app.include_router(auth.router)
app.include_router(trips.router)
app.include_router(gear.router)
app.include_router(inventory.router)
app.include_router(trophies.router)
app.include_router(waypoints.router)
app.include_router(logistics.router)
app.include_router(guide.router)
app.include_router(ai_ranger.router)
app.include_router(api.router)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
