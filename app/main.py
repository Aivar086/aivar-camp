from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
import os

from app.database import engine, Base
from app.routers import trips, gear, api, trophies, waypoints, logistics, guide, inventory

# Автоматическое создание / обновление таблиц базы данных при запуске
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Aivar Camp — Кемпинг & Рыбалка в Казахстане",
    description="Комплексный сервис для организации выездов: маршруты, рыболовная погода, барометр, фазы Луны, тайминги солнца, калькуляторы кухни и топлива, чек-листы и журнал трофеев.",
    version="2.2.0"
)

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
app.include_router(trips.router)
app.include_router(gear.router)
app.include_router(inventory.router)
app.include_router(trophies.router)
app.include_router(waypoints.router)
app.include_router(logistics.router)
app.include_router(guide.router)
app.include_router(api.router)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
