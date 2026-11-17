import datetime
from sqlalchemy import (
    Column, Integer, String, Text, Boolean, Float, DateTime, ForeignKey, Time, Enum as SQLEnum
)
from sqlalchemy.orm import relationship
import enum
from app.core.database import Base


class UserRole(str, enum.Enum):
    ADMIN = "admin"
    STAFF = "staff"
    CUSTOMER = "customer"


class ReservationStatus(str, enum.Enum):
    PENDING_CONFIRMATION = "pending_confirmation"
    CONFIRMED = "confirmed"
    CANCELLED = "cancelled"
    COMPLETED = "completed"
    NO_SHOW = "no_show"


class SeatingArea(str, enum.Enum):
    INDOOR = "indoor"
    OUTDOOR_PATIO = "outdoor_patio"
    BAR = "bar"
    BOOTH = "booth"
    PRIVATE_DINING = "private_dining"


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(255), nullable=False)
    role = Column(String(50), default=UserRole.CUSTOMER.value, nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    is_active = Column(Boolean, default=True)


class Restaurant(Base):
    __tablename__ = "restaurants"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    address = Column(String(255), nullable=False)
    phone = Column(String(50), nullable=False)
    email = Column(String(100), nullable=True)
    timezone = Column(String(50), default="UTC")
    reservation_policy = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    hours = relationship("RestaurantHours", back_populates="restaurant", cascade="all, delete-orphan")
    tables = relationship("Table", back_populates="restaurant", cascade="all, delete-orphan")
    menu_categories = relationship("MenuCategory", back_populates="restaurant", cascade="all, delete-orphan")


class RestaurantHours(Base):
    __tablename__ = "restaurant_hours"

    id = Column(Integer, primary_key=True, index=True)
    restaurant_id = Column(Integer, ForeignKey("restaurants.id"), nullable=False)
    day_of_week = Column(Integer, nullable=False)  # 0=Monday, 6=Sunday
    open_time = Column(Time, nullable=False)
    close_time = Column(Time, nullable=False)
    is_closed = Column(Boolean, default=False)

    restaurant = relationship("Restaurant", back_populates="hours")


class Table(Base):
    __tablename__ = "tables"

    id = Column(Integer, primary_key=True, index=True)
    restaurant_id = Column(Integer, ForeignKey("restaurants.id"), nullable=False)
    table_number = Column(String(50), nullable=False)
    min_capacity = Column(Integer, default=1)
    max_capacity = Column(Integer, nullable=False)
    seating_area = Column(String(50), default=SeatingArea.INDOOR.value)
    is_active = Column(Boolean, default=True)

    restaurant = relationship("Restaurant", back_populates="tables")
    reservations = relationship("Reservation", back_populates="table")


class Customer(Base):
    __tablename__ = "customers"

    id = Column(Integer, primary_key=True, index=True)
    full_name = Column(String(255), nullable=False)
    phone = Column(String(50), index=True, nullable=False)
    email = Column(String(255), index=True, nullable=True)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    reservations = relationship("Reservation", back_populates="customer")


class Reservation(Base):
    __tablename__ = "reservations"

    id = Column(Integer, primary_key=True, index=True)
    booking_code = Column(String(20), unique=True, index=True, nullable=False)
    restaurant_id = Column(Integer, ForeignKey("restaurants.id"), nullable=False)
    table_id = Column(Integer, ForeignKey("tables.id"), nullable=False)
    customer_id = Column(Integer, ForeignKey("customers.id"), nullable=False)
    
    party_size = Column(Integer, nullable=False)
    start_time = Column(DateTime, nullable=False, index=True)
    end_time = Column(DateTime, nullable=False, index=True)
    
    status = Column(String(50), default=ReservationStatus.CONFIRMED.value, nullable=False)
    special_requests = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

    table = relationship("Table", back_populates="reservations")
    customer = relationship("Customer", back_populates="reservations")


class MenuCategory(Base):
    __tablename__ = "menu_categories"

    id = Column(Integer, primary_key=True, index=True)
    restaurant_id = Column(Integer, ForeignKey("restaurants.id"), nullable=False)
    name = Column(String(100), nullable=False)
    display_order = Column(Integer, default=0)

    restaurant = relationship("Restaurant", back_populates="menu_categories")
    items = relationship("MenuItem", back_populates="category", cascade="all, delete-orphan")


class MenuItem(Base):
    __tablename__ = "menu_items"

    id = Column(Integer, primary_key=True, index=True)
    category_id = Column(Integer, ForeignKey("menu_categories.id"), nullable=False)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    price = Column(Float, nullable=False)
    is_available = Column(Boolean, default=True)
    is_vegan = Column(Boolean, default=False)
    is_vegetarian = Column(Boolean, default=False)
    is_gluten_free = Column(Boolean, default=False)
    spicy_level = Column(Integer, default=0)

    category = relationship("MenuCategory", back_populates="items")
    ingredients = relationship("Ingredient", back_populates="menu_item", cascade="all, delete-orphan")
    allergens = relationship("MenuItemAllergen", back_populates="menu_item", cascade="all, delete-orphan")


class Ingredient(Base):
    __tablename__ = "ingredients"

    id = Column(Integer, primary_key=True, index=True)
    menu_item_id = Column(Integer, ForeignKey("menu_items.id"), nullable=False)
    name = Column(String(255), nullable=False)

    menu_item = relationship("MenuItem", back_populates="ingredients")


class Allergen(Base):
    __tablename__ = "allergens"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, nullable=False)  # e.g., Peanuts, Dairy, Gluten, Shellfish, Soy, Eggs, Tree Nuts
    description = Column(Text, nullable=True)

    menu_items = relationship("MenuItemAllergen", back_populates="allergen")


class MenuItemAllergen(Base):
    __tablename__ = "menu_item_allergens"

    id = Column(Integer, primary_key=True, index=True)
    menu_item_id = Column(Integer, ForeignKey("menu_items.id"), nullable=False)
    allergen_id = Column(Integer, ForeignKey("allergens.id"), nullable=False)
    severity_note = Column(String(255), nullable=True)  # e.g., "Contains direct allergen", "Cross-contamination risk"

    menu_item = relationship("MenuItem", back_populates="allergens")
    allergen = relationship("Allergen", back_populates="menu_items")


class Conversation(Base):
    __tablename__ = "conversations"

    id = Column(String(100), primary_key=True, index=True)  # UUID or Session ID
    customer_phone = Column(String(50), nullable=True)
    started_at = Column(DateTime, default=datetime.datetime.utcnow)
    ended_at = Column(DateTime, nullable=True)
    status = Column(String(50), default="active")  # active, completed, abandoned

    messages = relationship("Message", back_populates="conversation", cascade="all, delete-orphan")
    tool_executions = relationship("AgentToolExecution", back_populates="conversation", cascade="all, delete-orphan")


class Message(Base):
    __tablename__ = "messages"

    id = Column(Integer, primary_key=True, index=True)
    conversation_id = Column(String(100), ForeignKey("conversations.id"), nullable=False)
    role = Column(String(20), nullable=False)  # user, assistant, system, tool
    content = Column(Text, nullable=False)
    audio_transcribed = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    conversation = relationship("Conversation", back_populates="messages")


class AgentToolExecution(Base):
    __tablename__ = "agent_tool_executions"

    id = Column(Integer, primary_key=True, index=True)
    conversation_id = Column(String(100), ForeignKey("conversations.id"), nullable=False)
    tool_name = Column(String(100), nullable=False)
    arguments_json = Column(Text, nullable=False)
    result_json = Column(Text, nullable=True)
    success = Column(Boolean, default=True)
    error_message = Column(Text, nullable=True)
    executed_at = Column(DateTime, default=datetime.datetime.utcnow)

    conversation = relationship("Conversation", back_populates="tool_executions")


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    entity_type = Column(String(100), nullable=False)  # reservation, table, menu_item, auth
    entity_id = Column(String(100), nullable=True)
    action = Column(String(100), nullable=False)  # CREATE, UPDATE, CANCEL, LOGIN
    performed_by = Column(String(255), nullable=True)  # user email or 'AI_AGENT'
    details_json = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
