import datetime
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List, Dict, Any, Optional

from app.core.database import get_db
from app.models.entities import (
    User, UserRole, Restaurant, RestaurantHours, Table, Customer,
    Reservation, ReservationStatus, MenuCategory, MenuItem, Allergen,
    Conversation, Message, AgentToolExecution, AuditLog
)
from app.schemas.dto import (
    UserCreate, UserLogin, UserOut, TokenOut, TableCreate, TableOut,
    ReservationCreate, ReservationModify, ReservationCancel, ReservationOut,
    MenuCategoryOut, MenuItemOut, AllergenOut
)
from app.core.security import verify_password, get_password_hash, create_access_token, decode_access_token
from app.services.booking_engine import BookingEngine

api_router = APIRouter()


# ---------------- AUTHENTICATION ---------------- #
@api_router.post("/auth/register", response_model=UserOut)
def register_user(user_in: UserCreate, db: Session = Depends(get_db)):
    existing = db.query(User).filter(User.email == user_in.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    hashed = get_password_hash(user_in.password)
    new_user = User(
        email=user_in.email,
        hashed_password=hashed,
        full_name=user_in.full_name,
        role=user_in.role
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user


@api_router.post("/auth/login", response_model=TokenOut)
def login_user(login_data: UserLogin, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == login_data.email).first()
    if not user or not verify_password(login_data.password, user.hashed_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password")
    
    token = create_access_token({"sub": user.email, "role": user.role, "id": user.id})
    return {"access_token": token, "token_type": "bearer", "user": user}


# ---------------- RESTAURANT PUBLIC DETAILS ---------------- #
@api_router.get("/restaurant")
def get_restaurant_info(db: Session = Depends(get_db)):
    rest = db.query(Restaurant).first()
    if not rest:
        raise HTTPException(status_code=404, detail="Restaurant details not found")
    
    hours = db.query(RestaurantHours).filter(RestaurantHours.restaurant_id == rest.id).order_by(RestaurantHours.day_of_week).all()
    days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    hours_out = [
        {
            "day": days[h.day_of_week],
            "open": h.open_time.strftime("%I:%M %p"),
            "close": h.close_time.strftime("%I:%M %p"),
            "is_closed": h.is_closed
        }
        for h in hours
    ]
    return {
        "id": rest.id,
        "name": rest.name,
        "description": rest.description,
        "address": rest.address,
        "phone": rest.phone,
        "email": rest.email,
        "timezone": rest.timezone,
        "reservation_policy": rest.reservation_policy,
        "hours": hours_out
    }


# ---------------- MENU & ALLERGENS ---------------- #
@api_router.get("/menu", response_model=List[MenuCategoryOut])
def get_menu(db: Session = Depends(get_db)):
    categories = db.query(MenuCategory).order_by(MenuCategory.display_order.asc()).all()
    result = []
    for cat in categories:
        items = []
        for i in cat.items:
            items.append(MenuItemOut(
                id=i.id,
                name=i.name,
                description=i.description,
                price=i.price,
                is_available=i.is_available,
                is_vegan=i.is_vegan,
                is_vegetarian=i.is_vegetarian,
                is_gluten_free=i.is_gluten_free,
                spicy_level=i.spicy_level,
                category_id=cat.id,
                category_name=cat.name,
                allergens=[a.allergen.name for a in i.allergens],
                ingredients=[ing.name for ing in i.ingredients]
            ))
        result.append(MenuCategoryOut(
            id=cat.id,
            name=cat.name,
            display_order=cat.display_order,
            items=items
        ))
    return result


@api_router.get("/allergens", response_model=List[AllergenOut])
def get_allergens(db: Session = Depends(get_db)):
    return db.query(Allergen).all()


# ---------------- RESERVATIONS & AVAILABILITY ---------------- #
@api_router.get("/availability")
def check_availability(
    date: str,
    time: str,
    party_size: int,
    seating_area: Optional[str] = None,
    db: Session = Depends(get_db)
):
    return BookingEngine.check_availability(
        db=db,
        restaurant_id=1,
        date_str=date,
        time_str=time,
        party_size=party_size,
        preferred_seating_area=seating_area
    )


@api_router.post("/reservations")
def create_reservation(data: ReservationCreate, db: Session = Depends(get_db)):
    res = BookingEngine.create_reservation_transactional(
        db=db,
        restaurant_id=1,
        customer_name=data.customer_name,
        customer_phone=data.customer_phone,
        customer_email=data.customer_email,
        date_str=data.date,
        time_str=data.time,
        party_size=data.party_size,
        preferred_seating_area=data.seating_area,
        special_requests=data.special_requests,
        confirmed=True
    )
    if not res.get("success"):
        raise HTTPException(status_code=400, detail=res.get("error", "Failed to create reservation"))
    return res


@api_router.get("/reservations/{booking_code}")
def get_reservation(booking_code: str, phone: str, db: Session = Depends(get_db)):
    res = db.query(Reservation).filter(Reservation.booking_code == booking_code).first()
    if not res or res.customer.phone != phone:
        raise HTTPException(status_code=404, detail="Reservation not found or phone number does not match")
    return {
        "booking_code": res.booking_code,
        "customer_name": res.customer.full_name,
        "customer_phone": res.customer.phone,
        "table_number": res.table.table_number,
        "seating_area": res.table.seating_area,
        "party_size": res.party_size,
        "start_time": res.start_time,
        "end_time": res.end_time,
        "status": res.status,
        "special_requests": res.special_requests
    }


@api_router.post("/reservations/modify")
def modify_reservation(data: ReservationModify, db: Session = Depends(get_db)):
    res = BookingEngine.modify_reservation(
        db=db,
        booking_code=data.booking_code,
        customer_phone=data.customer_phone,
        new_date=data.new_date,
        new_time=data.new_time,
        new_party_size=data.new_party_size,
        new_seating_area=data.new_seating_area,
        special_requests=data.special_requests
    )
    if not res.get("success"):
        raise HTTPException(status_code=400, detail=res.get("error", "Failed to modify reservation"))
    return res


@api_router.post("/reservations/cancel")
def cancel_reservation(data: ReservationCancel, db: Session = Depends(get_db)):
    res = BookingEngine.cancel_reservation(
        db=db,
        booking_code=data.booking_code,
        customer_phone=data.customer_phone,
        reason=data.reason
    )
    if not res.get("success"):
        raise HTTPException(status_code=400, detail=res.get("error", "Failed to cancel reservation"))
    return res


# ---------------- ADMIN & ANALYTICS DASHBOARD ---------------- #
@api_router.get("/admin/analytics")
def get_admin_analytics(db: Session = Depends(get_db)):
    total_reservations = db.query(func.count(Reservation.id)).scalar() or 0
    confirmed_reservations = db.query(func.count(Reservation.id)).filter(
        Reservation.status == ReservationStatus.CONFIRMED.value
    ).scalar() or 0
    cancelled_reservations = db.query(func.count(Reservation.id)).filter(
        Reservation.status == ReservationStatus.CANCELLED.value
    ).scalar() or 0
    
    cancellation_rate = round((cancelled_reservations / total_reservations * 100), 1) if total_reservations > 0 else 0.0

    total_customers = db.query(func.count(Customer.id)).scalar() or 0
    total_tables = db.query(func.count(Table.id)).scalar() or 0
    
    # Tool execution stats
    total_tool_calls = db.query(func.count(AgentToolExecution.id)).scalar() or 0
    successful_tool_calls = db.query(func.count(AgentToolExecution.id)).filter(
        AgentToolExecution.success == True
    ).scalar() or 0
    tool_success_rate = round((successful_tool_calls / total_tool_calls * 100), 1) if total_tool_calls > 0 else 100.0

    # Hourly distribution of bookings
    recent_reservations = db.query(Reservation).order_by(Reservation.created_at.desc()).limit(10).all()
    recent_list = [
        {
            "id": r.id,
            "booking_code": r.booking_code,
            "customer_name": r.customer.full_name,
            "customer_phone": r.customer.phone,
            "party_size": r.party_size,
            "time": r.start_time.strftime("%Y-%m-%d %H:%M"),
            "table": r.table.table_number,
            "status": r.status
        }
        for r in recent_reservations
    ]

    return {
        "total_reservations": total_reservations,
        "confirmed_reservations": confirmed_reservations,
        "cancelled_reservations": cancelled_reservations,
        "cancellation_rate": f"{cancellation_rate}%",
        "total_customers": total_customers,
        "total_tables": total_tables,
        "total_tool_calls": total_tool_calls,
        "tool_success_rate": f"{tool_success_rate}%",
        "recent_reservations": recent_list
    }


@api_router.get("/admin/tables", response_model=List[TableOut])
def list_tables(db: Session = Depends(get_db)):
    return db.query(Table).all()


@api_router.post("/admin/tables", response_model=TableOut)
def create_table(tbl_in: TableCreate, db: Session = Depends(get_db)):
    new_tbl = Table(**tbl_in.dict())
    db.add(new_tbl)
    db.commit()
    db.refresh(new_tbl)
    return new_tbl


@api_router.get("/admin/conversations")
def list_conversations(db: Session = Depends(get_db)):
    convs = db.query(Conversation).order_by(Conversation.started_at.desc()).limit(20).all()
    out = []
    for c in convs:
        out.append({
            "id": c.id,
            "started_at": c.started_at,
            "message_count": len(c.messages),
            "tool_call_count": len(c.tool_executions),
            "status": c.status
        })
    return out


@api_router.get("/admin/conversations/{conv_id}")
def inspect_conversation(conv_id: str, db: Session = Depends(get_db)):
    conv = db.query(Conversation).filter(Conversation.id == conv_id).first()
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found")
    
    msgs = [
        {"role": m.role, "content": m.content, "time": m.created_at, "is_audio": m.audio_transcribed}
        for m in conv.messages
    ]
    tools = [
        {
            "tool_name": t.tool_name,
            "arguments": t.arguments_json,
            "result": t.result_json,
            "success": t.success,
            "executed_at": t.executed_at
        }
        for t in conv.tool_executions
    ]
    return {
        "id": conv.id,
        "started_at": conv.started_at,
        "messages": msgs,
        "tools": tools
    }
