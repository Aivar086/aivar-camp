from app.database import engine, Base, SessionLocal
from app.models import Trip, GearItem, Trophy, Waypoint, FoodItem, ExpenseItem, UserInventoryItem
from app.services.gear_presets import DEFAULT_GEAR_PRESETS
from app.services.kitchen_calc import generate_food_ration

Base.metadata.drop_all(bind=engine)
Base.metadata.create_all(bind=engine)

db = SessionLocal()

# Заполняем "Мой Личный Гараж" пользователя для старта
inventory_sample = [
    # Лагерь
    {"cat": "camp", "name": "Палатка кемпинговая 3-местная", "model": "Tramp Cave 3 (водостойкость 8000мм)", "qty": "1 шт", "weight": 5.2, "notes": "В зеленом чехле, полный комплект колышков"},
    {"cat": "camp", "name": "Спальный мешок зимний/демисезон", "model": "Alexika Mountain (-5°C)", "qty": "2 шт", "weight": 2.1, "notes": "Комфорт до -5 градусов"},
    {"cat": "camp", "name": "Самонадувающийся коврик 5см", "model": "Naturehike", "qty": "2 шт", "weight": 1.4, "notes": "Отличная теплоизоляция"},
    {"cat": "camp", "name": "Тент кемпинговый от солнца и дождя", "model": "4х4 метра с люверсами", "qty": "1 шт", "weight": 2.0, "notes": "Веревка 25м в комплекте"},
    {"cat": "camp", "name": "Кемпинговые складные стулья", "model": "С подстаканниками", "qty": "3 шт", "weight": 4.5, "notes": "До 120 кг"},
    {"cat": "camp", "name": "Налобный фонарь с аккумулятором", "model": "Fenix HL60R (Type-C)", "qty": "2 шт", "weight": 0.3, "notes": "Заряжен на 100%"},
    
    # Рыбалка
    {"cat": "fishing", "name": "Спиннинг джиговый 2.44м", "model": "Major Craft Soul Stick 10-42g", "qty": "1 шт", "weight": 0.13, "notes": "Основной спиннинг на судака и щуку"},
    {"cat": "fishing", "name": "Катушка безынерционная 3000", "model": "Shimano Stradic FL 3000 (шнур #1.2)", "qty": "1 шт", "weight": 0.23, "notes": "Шнур 8-жилка Varivas"},
    {"cat": "fishing", "name": "Фидерное удилище 3.9м (до 120г)", "model": "Zemex Iron Feeder", "qty": "2 шт", "weight": 0.28, "notes": "Для сазана и леща на течении"},
    {"cat": "fishing", "name": "Коробка с силиконовыми приманками", "model": "Keitech, Relax, виброхвосты 4-5\"", "qty": "2 шт", "weight": 1.5, "notes": "Джиг-головки 14-26г"},
    {"cat": "fishing", "name": "Подсачек складной прорезиненный", "model": "Большая голова 65см", "qty": "1 шт", "weight": 0.9, "notes": "Не цепляет крючки"},
    {"cat": "fishing", "name": "Электронный безмен и рулетка", "model": "До 50 кг (точность 10г)", "qty": "1 шт", "weight": 0.2, "notes": "В боковом кармане сумки"},
    
    # Лодка
    {"cat": "boat", "name": "Надувная ПВХ лодка 3.3м с транцем", "model": "Aquamania с жестким дном (слань)", "qty": "1 шт", "weight": 34.0, "notes": "В багажнике авто"},
    {"cat": "boat", "name": "Лодочный мотор 9.8 л.с.", "model": "Tohatsu 9.8 2-тактный", "qty": "1 шт", "weight": 26.0, "notes": "Бак 12л + смесь с маслом 1:50"},
    {"cat": "boat", "name": "Спасательные жилеты сертифицированные", "model": "Свисток + светоотражатели", "qty": "3 шт", "weight": 1.5, "notes": "Обязательно надевать на воде!"},
    {"cat": "boat", "name": "Якорь-гриб 5.5 кг + трос 20м", "model": "Чугун в пластике", "qty": "1 шт", "weight": 6.0, "notes": "Держит на течении"},
    
    # Кухня
    {"cat": "kitchen", "name": "Походная газовая плитка в кейсе", "model": "С переходником под цанговый баллон", "qty": "1 шт", "weight": 1.6, "notes": "Запас газа 4 баллона"},
    {"cat": "kitchen", "name": "Казан чугунный 8 литров с крышкой", "model": "Узбекский шлифованный", "qty": "1 шт", "weight": 6.8, "notes": "Для плова, ухи и дичи"},
    {"cat": "kitchen", "name": "Чайник походный алюминиевый 1.5л", "model": "Fire-Maple", "qty": "1 шт", "weight": 0.25, "notes": "Быстрый нагрев"},
]

for it in inventory_sample:
    db.add(UserInventoryItem(
        category=it["cat"],
        name=it["name"],
        brand_or_model=it.get("model"),
        quantity=it.get("qty", "1 шт"),
        weight_kg=it.get("weight"),
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
