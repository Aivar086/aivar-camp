import datetime
from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from app.database import Base

class Trip(Base):
    __tablename__ = "trips"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    start_date = Column(String(50), nullable=True)
    end_date = Column(String(50), nullable=True)
    
    # Точки маршрута
    origin_name = Column(String(200), default="Мой дом / Старт")
    origin_lat = Column(Float, nullable=True)
    origin_lng = Column(Float, nullable=True)
    
    dest_name = Column(String(200), default="Точка стоянки / Водоем")
    dest_lat = Column(Float, nullable=False)
    dest_lng = Column(Float, nullable=False)
    
    distance_km = Column(Float, default=0.0)
    duration_minutes = Column(Integer, default=0)
    
    # Статус: 'planned' (запланировано) или 'completed' (завершено)
    status = Column(String(20), default="planned")
    
    # Заметки и отчет об улове
    notes = Column(Text, nullable=True)
    catch_notes = Column(Text, nullable=True)
    catch_weight_kg = Column(Float, default=0.0)
    catch_species = Column(String(200), nullable=True)
    
    # Количество участников и дней (для калькуляторов)
    participants_count = Column(Integer, default=2)
    duration_days = Column(Integer, default=3)
    
    # Параметры авто для калькулятора топлива (Казахстан: тенге)
    fuel_consumption = Column(Float, default=9.5) # л/100км
    fuel_price = Column(Float, default=230.0) # ₸/литр (АИ-92/95 в РК)
    
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    gear_items = relationship("GearItem", back_populates="trip", cascade="all, delete-orphan")
    trophies = relationship("Trophy", back_populates="trip", cascade="all, delete-orphan")
    waypoints = relationship("Waypoint", back_populates="trip", cascade="all, delete-orphan")
    food_items = relationship("FoodItem", back_populates="trip", cascade="all, delete-orphan")
    expenses = relationship("ExpenseItem", back_populates="trip", cascade="all, delete-orphan")

class GearItem(Base):
    __tablename__ = "gear_items"

    id = Column(Integer, primary_key=True, index=True)
    trip_id = Column(Integer, ForeignKey("trips.id"), nullable=False)
    category = Column(String(50), nullable=False)  # camp, fishing, kitchen, clothes, firstaid, other
    name = Column(String(200), nullable=False)
    is_packed = Column(Boolean, default=False)
    quantity = Column(String(50), default="1 шт")
    note = Column(String(200), nullable=True)

    trip = relationship("Trip", back_populates="gear_items")

class Trophy(Base):
    __tablename__ = "trophies"

    id = Column(Integer, primary_key=True, index=True)
    trip_id = Column(Integer, ForeignKey("trips.id"), nullable=False)
    species = Column(String(100), nullable=False) # Щука, Судак, Окунь, Карп и т.д.
    weight_kg = Column(Float, nullable=False, default=0.0)
    length_cm = Column(Float, nullable=True)
    lure_or_bait = Column(String(150), nullable=True) # На что поймана (джиг 4", воблер, опарыш)
    time_of_catch = Column(String(50), nullable=True) # Утро, вечер, 06:30
    depth_m = Column(Float, nullable=True)
    lat = Column(Float, nullable=True)
    lng = Column(Float, nullable=True)
    image_url = Column(String(500), nullable=True)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    trip = relationship("Trip", back_populates="trophies")

class Waypoint(Base):
    __tablename__ = "waypoints"

    id = Column(Integer, primary_key=True, index=True)
    trip_id = Column(Integer, ForeignKey("trips.id"), nullable=False)
    point_type = Column(String(50), default="camp") # camp (лагерь), fishing (рыбная точка/яма), spring (родник), boat (спуск лодки), wood (дрова), obstacle (препятствие)
    name = Column(String(150), nullable=False)
    lat = Column(Float, nullable=False)
    lng = Column(Float, nullable=False)
    description = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    trip = relationship("Trip", back_populates="waypoints")

class FoodItem(Base):
    __tablename__ = "food_items"

    id = Column(Integer, primary_key=True, index=True)
    trip_id = Column(Integer, ForeignKey("trips.id"), nullable=False)
    category = Column(String(50), default="groceries") # meat, grains, veggies, snacks, drinks, spices
    name = Column(String(150), nullable=False)
    amount = Column(String(50), nullable=False)
    is_bought = Column(Boolean, default=False)
    assigned_to = Column(String(100), nullable=True) # Кто покупает

    trip = relationship("Trip", back_populates="food_items")

class ExpenseItem(Base):
    __tablename__ = "expense_items"

    id = Column(Integer, primary_key=True, index=True)
    trip_id = Column(Integer, ForeignKey("trips.id"), nullable=False)
    title = Column(String(150), nullable=False)
    amount = Column(Float, nullable=False, default=0.0)
    paid_by = Column(String(100), default="Я")
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    trip = relationship("Trip", back_populates="expenses")

class UserInventoryItem(Base):
    __tablename__ = "user_inventory"

    id = Column(Integer, primary_key=True, index=True)
    category = Column(String(50), nullable=False)  # camp, fishing, kitchen, clothes, firstaid, boat, other
    name = Column(String(200), nullable=False)
    quantity = Column(String(50), default="1 шт")
    weight_kg = Column(Float, nullable=True)
    brand_or_model = Column(String(150), nullable=True) # Например: Палатка Tramp Cave 3, Спиннинг Major Craft
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

