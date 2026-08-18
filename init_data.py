import os
import json
from app.database import engine, Base, SessionLocal
from app.models import Trip, GearItem, Trophy, Waypoint, FoodItem, ExpenseItem, UserInventoryItem
from app.services.kitchen_calc import generate_food_ration

Base.metadata.drop_all(bind=engine)
Base.metadata.create_all(bind=engine)

db = SessionLocal()

# Заполняем "Мой Личный Гараж" реальным списком пользователя
json_path = os.path.join(os.path.dirname(__file__), "app", "services", "user_inventory.json")
if os.path.exists(json_path):
    with open(json_path, "r", encoding="utf-8") as f:
        inventory_sample = json.load(f)
else:
    inventory_sample = []

for it in inventory_sample:
    db.add(UserInventoryItem(
        category=it.get("category", "other"),
        name=it.get("name"),
        brand_or_model=it.get("brand_or_model"),
        quantity=it.get("quantity", "1 шт"),
        weight_kg=it.get("weight_kg"),
        notes=it.get("notes")
    ))

# 1. Казахстанская активная поездка (Капчагайское водохранилище / Балхаш)
t1 = Trip(
    title='Выезд на Капчагай (Конаев) за судаком и сазаном',
    description='3 дня дикого кемпинга на песчаном берегу. Джиг с лодки по бровкам на рассвете, вечерний фидер на кукурузу и шашлык у костра.',
    start_date='2026-08-22',
    end_date='2026-08-25',
    origin_name='Алматы (Саин / Толе би)',
    origin_lat=43.2389,
    origin_lng=76.8897,
    dest_name='Капчагайское вдхр. (песчаные косы за Конаевым)',
    dest_lat=43.8950,
    dest_lng=77.0850,
    distance_km=85.0,
    duration_minutes=75,
    participants_count=3,
    duration_days=3,
    fuel_consumption=10.0,
    fuel_price=230.0, # 230 ₸/литр
    status='planned'
)
db.add(t1)
db.commit()
db.refresh(t1)

# Снаряжение для поездки
for inv in inventory_sample:
    db.add(GearItem(
        trip_id=t1.id,
        category=inv["cat"] if inv["cat"] in ["camp", "fishing", "kitchen", "clothes", "firstaid"] else "other",
        name=f"{inv['name']} ({inv['model']})" if inv.get("model") else inv["name"],
        quantity=inv.get("qty", "1 шт"),
        note=inv.get("notes"),
        is_packed=False
    ))

# Раскладка продуктов
food_ration = generate_food_ration(t1.participants_count, t1.duration_days)
for f in food_ration:
    db.add(FoodItem(
        trip_id=t1.id,
        category=f['category'],
        name=f['name'],
        amount=f['amount'],
        assigned_to=f.get('assigned_to', 'Все'),
        is_bought=False
    ))

# Точки на карте Капчагая
db.add(Waypoint(
    trip_id=t1.id,
    name='Песчаный лагерь и шатер',
    point_type='camp',
    lat=43.8950,
    lng=77.0850,
    description='Песчаный пологий берег, удобный подъезд для кроссовера'
))
db.add(Waypoint(
    trip_id=t1.id,
    name='Судачья бровка 6-8м',
    point_type='fishing',
    lat=43.9020,
    lng=77.0950,
    description='Свал в глубину, твердое дно с ракушкой'
))
db.add(Waypoint(
    trip_id=t1.id,
    name='Спуск лодки (песчаный слип)',
    point_type='boat',
    lat=43.8920,
    lng=77.0810,
    description='Твердый песок, без ила'
))

# Чеки в тенге
db.add(ExpenseItem(
    trip_id=t1.id,
    title='Мясо на шашлык (баранина/говядина) и угли',
    amount=18500.0,
    paid_by='Данияр'
))
db.add(ExpenseItem(
    trip_id=t1.id,
    title='Прикормка (кукуруза, жмых) и силиконовые приманки',
    amount=9400.0,
    paid_by='Я'
))

# 2. Завершенная поездка (Балхаш / река Или)
t2 = Trip(
    title='Трофейная рыбалка на озере Балхаш (дельта реки Или)',
    description='Отличный выезд, море эмоций, поймали крупного жереха и сазана.',
    start_date='2026-07-15',
    end_date='2026-07-18',
    origin_name='Алматы',
    origin_lat=43.2389,
    origin_lng=76.8897,
    dest_name='Дельта реки Или / Озеро Балхаш',
    dest_lat=45.3500,
    dest_lng=74.5000,
    distance_km=360.0,
    duration_minutes=310,
    participants_count=3,
    duration_days=4,
    fuel_consumption=11.0,
    fuel_price=230.0,
    status='completed',
    catch_species='Жерех, Сазан, Сом, Судак',
    catch_weight_kg=16.8,
    catch_notes='Жерех активно бил малька на струе на пилькеры 28г. Сазан взял на макушатник ночью.'
)
db.add(t2)
db.commit()
db.refresh(t2)

# Трофеи в тенге/кг
db.add(Trophy(
    trip_id=t2.id,
    species='Жерех трофейный',
    weight_kg=4.2,
    length_cm=72.0,
    lure_or_bait='Кастмастер 28г (серебро с синей полосой)',
    time_of_catch='Утренняя зорька, 06:20',
    depth_m=1.5,
    lat=45.3500,
    lng=74.5000,
    notes='Взят на сильном течении на всплеск.'
))
db.add(Trophy(
    trip_id=t2.id,
    species='Сазан дикий',
    weight_kg=6.5,
    length_cm=68.0,
    lure_or_bait='Кукуруза с запахом клубники + макуха',
    time_of_catch='Ночь, 01:45',
    depth_m=4.5,
    lat=45.3500,
    lng=74.5000,
    notes='Мощное вываживание более 15 минут.'
))

db.commit()
db.close()
print("KAZAKHSTAN_LOCALIZED_DATABASE_INITIALIZED_OK")
