import json
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
from app.services.booking_engine import BookingEngine
from app.models.entities import (
    Restaurant, RestaurantHours, Table, MenuItem, MenuCategory, Allergen,
    MenuItemAllergen, Reservation, ReservationStatus, AgentToolExecution
)


TOOL_DEFINITIONS = [
    {
        "type": "function",
        "function": {
            "name": "check_availability",
            "description": "Check real database table availability for a given date, time, party size, and optional seating area.",
            "parameters": {
                "type": "object",
                "properties": {
                    "date": {
                        "type": "string",
                        "description": "Date in YYYY-MM-DD format (e.g. 2026-11-18)"
                    },
                    "time": {
                        "type": "string",
                        "description": "Time in 24h format HH:MM (e.g. 19:00)"
                    },
                    "party_size": {
                        "type": "integer",
                        "description": "Number of guests (1-20)"
                    },
                    "preferred_seating_area": {
                        "type": "string",
                        "enum": ["indoor", "outdoor_patio", "bar", "booth", "private_dining"],
                        "description": "Optional seating preference"
                    }
                },
                "required": ["date", "time", "party_size"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_restaurant_hours",
            "description": "Returns verified restaurant opening hours, closing hours, and reservation rules.",
            "parameters": {
                "type": "object",
                "properties": {},
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_menu",
            "description": "Returns available menu items categorized with descriptions, prices, dietary badges, and key ingredients.",
            "parameters": {
                "type": "object",
                "properties": {
                    "category": {
                        "type": "string",
                        "description": "Optional category filter like 'Starters', 'Mains', 'Desserts', 'Beverages'"
                    }
                },
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "check_allergens",
            "description": "Check dishes for allergens or dietary restrictions. Never guarantees safety if unknown; flags cross-contamination.",
            "parameters": {
                "type": "object",
                "properties": {
                    "menu_item_name": {
                        "type": "string",
                        "description": "Name of dish or partial dish name"
                    },
                    "allergen_name": {
                        "type": "string",
                        "description": "Specific allergen or intolerance (e.g., Peanuts, Dairy, Gluten, Shellfish)"
                    }
                },
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "create_reservation",
            "description": "Books a table in PostgreSQL. STRICT REQUIREMENT: Only execute when customer has provided Name, Phone, Date, Time, Party Size, and has given EXPLICIT CONFIRMATION.",
            "parameters": {
                "type": "object",
                "properties": {
                    "customer_name": {"type": "string", "description": "Customer full name"},
                    "customer_phone": {"type": "string", "description": "Customer contact phone number"},
                    "date": {"type": "string", "description": "Date YYYY-MM-DD"},
                    "time": {"type": "string", "description": "Time HH:MM (24h)"},
                    "party_size": {"type": "integer", "description": "Number of guests"},
                    "preferred_seating_area": {"type": "string", "description": "Optional seating area preference"},
                    "special_requests": {"type": "string", "description": "Allergies, high chair, birthday, etc."},
                    "customer_confirmed": {"type": "boolean", "description": "Must be true. Has customer explicitly confirmed?"}
                },
                "required": ["customer_name", "customer_phone", "date", "time", "party_size", "customer_confirmed"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_reservation",
            "description": "Retrieve verified reservation details using booking code and customer phone number.",
            "parameters": {
                "type": "object",
                "properties": {
                    "booking_code": {"type": "string", "description": "Booking code (e.g. VR-A1B2)"},
                    "customer_phone": {"type": "string", "description": "Customer phone for verification"}
                },
                "required": ["booking_code", "customer_phone"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "cancel_reservation",
            "description": "Cancel an existing reservation. Requires booking code and customer phone verification.",
            "parameters": {
                "type": "object",
                "properties": {
                    "booking_code": {"type": "string", "description": "Booking code (e.g. VR-A1B2)"},
                    "customer_phone": {"type": "string", "description": "Customer phone for verification"},
                    "reason": {"type": "string", "description": "Reason for cancellation"}
                },
                "required": ["booking_code", "customer_phone"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "modify_reservation",
            "description": "Modify reservation date, time, party size, or seating area with availability validation.",
            "parameters": {
                "type": "object",
                "properties": {
                    "booking_code": {"type": "string", "description": "Booking code"},
                    "customer_phone": {"type": "string", "description": "Customer phone for verification"},
                    "new_date": {"type": "string", "description": "Optional new date YYYY-MM-DD"},
                    "new_time": {"type": "string", "description": "Optional new time HH:MM"},
                    "new_party_size": {"type": "integer", "description": "Optional new party size"},
                    "new_seating_area": {"type": "string", "description": "Optional new seating area"}
                },
                "required": ["booking_code", "customer_phone"]
            }
        }
    }
]


class AgentToolRegistry:
    @staticmethod
    def execute_tool(
        tool_name: str,
        arguments: Dict[str, Any],
        db: Session,
        restaurant_id: int = 1,
        conversation_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Executes a registered tool against the database with input validation and audit logging.
        """
        success = True
        error_msg = None
        result: Dict[str, Any] = {}

        try:
            if tool_name == "check_availability":
                date = arguments.get("date")
                time = arguments.get("time")
                party_size = int(arguments.get("party_size", 2))
                area = arguments.get("preferred_seating_area")
                result = BookingEngine.check_availability(
                    db=db,
                    restaurant_id=restaurant_id,
                    date_str=date,
                    time_str=time,
                    party_size=party_size,
                    preferred_seating_area=area
                )

            elif tool_name == "get_restaurant_hours":
                hours_records = db.query(RestaurantHours).filter(
                    RestaurantHours.restaurant_id == restaurant_id
                ).order_by(RestaurantHours.day_of_week.asc()).all()
                
                days_map = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
                hours_list = []
                for h in hours_records:
                    hours_list.append({
                        "day": days_map[h.day_of_week],
                        "status": "Closed" if h.is_closed else f"{h.open_time.strftime('%I:%M %p')} - {h.close_time.strftime('%I:%M %p')}"
                    })
                
                restaurant = db.query(Restaurant).filter(Restaurant.id == restaurant_id).first()
                result = {
                    "restaurant_name": restaurant.name if restaurant else "Aura & Embers Bistro",
                    "timezone": restaurant.timezone if restaurant else "UTC",
                    "hours": hours_list,
                    "reservation_policy": restaurant.reservation_policy if restaurant else "90-minute dining window; 15-minute grace period."
                }

            elif tool_name == "get_menu":
                category_filter = arguments.get("category")
                query = db.query(MenuCategory).filter(MenuCategory.restaurant_id == restaurant_id)
                if category_filter:
                    query = query.filter(MenuCategory.name.ilike(f"%{category_filter}%"))
                
                categories = query.order_by(MenuCategory.display_order.asc()).all()
                menu_data = []
                for cat in categories:
                    items = []
                    for item in cat.items:
                        if item.is_available:
                            items.append({
                                "id": item.id,
                                "name": item.name,
                                "description": item.description,
                                "price": f"${item.price:.2f}",
                                "vegan": item.is_vegan,
                                "vegetarian": item.is_vegetarian,
                                "gluten_free": item.is_gluten_free,
                                "spicy_level": item.spicy_level,
                                "allergens": [a.allergen.name for a in item.allergens],
                                "ingredients": [i.name for i in item.ingredients]
                            })
                    menu_data.append({
                        "category": cat.name,
                        "items": items
                    })
                result = {"menu": menu_data}

            elif tool_name == "check_allergens":
                item_name = arguments.get("menu_item_name")
                allergen_name = arguments.get("allergen_name")
                
                query = db.query(MenuItem)
                if item_name:
                    query = query.filter(MenuItem.name.ilike(f"%{item_name}%"))
                
                items = query.all()
                allergen_reports = []
                
                for item in items:
                    direct_allergens = [a.allergen.name for a in item.allergens]
                    matching = []
                    if allergen_name:
                        matching = [a for a in direct_allergens if allergen_name.lower() in a.lower()]
                    
                    allergen_reports.append({
                        "item_name": item.name,
                        "allergens_present": direct_allergens,
                        "flagged_allergen_match": matching if allergen_name else direct_allergens,
                        "dietary_badges": {
                            "gluten_free": item.is_gluten_free,
                            "vegan": item.is_vegan,
                            "vegetarian": item.is_vegetarian
                        },
                        "cross_contamination_warning": "Please note our kitchen handles flour, dairy, nuts, and seafood. Alert your server of severe allergies."
                    })
                result = {
                    "checked_item": item_name or "All items",
                    "checked_allergen": allergen_name or "All allergens",
                    "results": allergen_reports,
                    "safety_disclaimer": "Safety note: We cannot guarantee an allergen-free environment due to shared prep stations. Inquire with manager on duty for severe anaphylactic conditions."
                }

            elif tool_name == "create_reservation":
                confirmed = arguments.get("customer_confirmed", False)
                if not confirmed:
                    result = {
                        "success": False,
                        "requires_confirmation": True,
                        "message": "Explicit confirmation required: Please ask the customer: 'Would you like me to book this table for [party] at [time] on [date] under [name]?'"
                    }
                else:
                    result = BookingEngine.create_reservation_transactional(
                        db=db,
                        restaurant_id=restaurant_id,
                        customer_name=arguments.get("customer_name"),
                        customer_phone=arguments.get("customer_phone"),
                        customer_email=arguments.get("customer_email"),
                        date_str=arguments.get("date"),
                        time_str=arguments.get("time"),
                        party_size=int(arguments.get("party_size")),
                        preferred_seating_area=arguments.get("preferred_seating_area"),
                        special_requests=arguments.get("special_requests"),
                        confirmed=True
                    )

            elif tool_name == "get_reservation":
                code = arguments.get("booking_code")
                phone = arguments.get("customer_phone")
                res = db.query(Reservation).filter(Reservation.booking_code == code).first()
                if not res or res.customer.phone != phone:
                    result = {"success": False, "error": "Reservation not found or phone number does not match."}
                else:
                    result = {
                        "success": True,
                        "booking_code": res.booking_code,
                        "customer_name": res.customer.full_name,
                        "party_size": res.party_size,
                        "date": res.start_time.strftime("%Y-%m-%d"),
                        "time": res.start_time.strftime("%H:%M"),
                        "table": res.table.table_number,
                        "seating_area": res.table.seating_area,
                        "status": res.status,
                        "special_requests": res.special_requests
                    }

            elif tool_name == "cancel_reservation":
                result = BookingEngine.cancel_reservation(
                    db=db,
                    booking_code=arguments.get("booking_code"),
                    customer_phone=arguments.get("customer_phone"),
                    reason=arguments.get("reason")
                )

            elif tool_name == "modify_reservation":
                result = BookingEngine.modify_reservation(
                    db=db,
                    booking_code=arguments.get("booking_code"),
                    customer_phone=arguments.get("customer_phone"),
                    new_date=arguments.get("new_date"),
                    new_time=arguments.get("new_time"),
                    new_party_size=int(arguments.get("new_party_size")) if arguments.get("new_party_size") else None,
                    new_seating_area=arguments.get("new_seating_area")
                )

            else:
                success = False
                error_msg = f"Unknown tool: {tool_name}"
                result = {"error": error_msg}

        except Exception as e:
            success = False
            error_msg = str(e)
            result = {"error": error_msg}

        # Log tool execution to database if conversation_id provided
        if conversation_id:
            try:
                tool_log = AgentToolExecution(
                    conversation_id=conversation_id,
                    tool_name=tool_name,
                    arguments_json=json.dumps(arguments),
                    result_json=json.dumps(result),
                    success=success,
                    error_message=error_msg
                )
                db.add(tool_log)
                db.commit()
            except Exception:
                db.rollback()

        return result
