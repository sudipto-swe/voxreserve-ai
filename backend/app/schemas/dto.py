from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List
from datetime import datetime, time


class UserBase(BaseModel):
    email: EmailStr
    full_name: str
    role: str = "customer"


class UserCreate(UserBase):
    password: str


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserOut(UserBase):
    id: int
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


class TokenOut(BaseModel):
    access_token: str
    token_type: str
    user: UserOut


class RestaurantHoursOut(BaseModel):
    id: int
    day_of_week: int
    open_time: time
    close_time: time
    is_closed: bool

    class Config:
        from_attributes = True


class TableBase(BaseModel):
    table_number: str
    min_capacity: int = 1
    max_capacity: int
    seating_area: str = "indoor"
    is_active: bool = True


class TableCreate(TableBase):
    restaurant_id: int = 1


class TableOut(TableBase):
    id: int
    restaurant_id: int

    class Config:
        from_attributes = True


class ReservationCreate(BaseModel):
    customer_name: str
    customer_phone: str
    customer_email: Optional[EmailStr] = None
    date: str  # YYYY-MM-DD
    time: str  # HH:MM
    party_size: int = Field(ge=1, le=20)
    seating_area: Optional[str] = None
    special_requests: Optional[str] = None


class ReservationModify(BaseModel):
    booking_code: str
    customer_phone: str
    new_date: Optional[str] = None
    new_time: Optional[str] = None
    new_party_size: Optional[int] = None
    new_seating_area: Optional[str] = None
    special_requests: Optional[str] = None


class ReservationCancel(BaseModel):
    booking_code: str
    customer_phone: str
    reason: Optional[str] = None


class ReservationOut(BaseModel):
    id: int
    booking_code: str
    customer_name: str
    customer_phone: str
    table_number: str
    seating_area: str
    party_size: int
    start_time: datetime
    end_time: datetime
    status: str
    special_requests: Optional[str]

    class Config:
        from_attributes = True


class AllergenOut(BaseModel):
    id: int
    name: str
    description: Optional[str]

    class Config:
        from_attributes = True


class MenuItemOut(BaseModel):
    id: int
    name: str
    description: Optional[str]
    price: float
    is_available: bool
    is_vegan: bool
    is_vegetarian: bool
    is_gluten_free: bool
    spicy_level: int
    category_id: int
    category_name: Optional[str] = None
    allergens: List[str] = []
    ingredients: List[str] = []

    class Config:
        from_attributes = True


class MenuCategoryOut(BaseModel):
    id: int
    name: str
    display_order: int
    items: List[MenuItemOut] = []

    class Config:
        from_attributes = True
