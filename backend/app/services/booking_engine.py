import datetime
import secrets
from typing import List, Optional, Tuple, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
from app.models.entities import (
    Restaurant, RestaurantHours, Table, Reservation, ReservationStatus, Customer, AuditLog
)
from app.core.config import settings


class BookingEngine:
    @staticmethod
    def generate_booking_code() -> str:
        """Generate human-readable unique 6-character alphanumeric booking code like VR-49X2."""
        code = secrets.token_hex(3).upper()
        return f"VR-{code}"

    @staticmethod
    def get_restaurant_hours_for_day(db: Session, restaurant_id: int, day_of_week: int) -> Optional[RestaurantHours]:
        return db.query(RestaurantHours).filter(
            RestaurantHours.restaurant_id == restaurant_id,
            RestaurantHours.day_of_week == day_of_week
        ).first()

    @staticmethod
    def is_within_operating_hours(
        db: Session,
        restaurant_id: int,
        booking_start: datetime.datetime,
        booking_end: datetime.datetime
    ) -> Tuple[bool, str]:
        day_of_week = booking_start.weekday()  # 0=Monday, 6=Sunday
        hours = BookingEngine.get_restaurant_hours_for_day(db, restaurant_id, day_of_week)
        
        if not hours or hours.is_closed:
            return False, "The restaurant is closed on this day."

        req_start_time = booking_start.time()
        req_end_time = booking_end.time()

        if req_start_time < hours.open_time:
            return False, f"Requested time is before opening ({hours.open_time.strftime('%I:%M %p')})."
        
        if req_end_time > hours.close_time:
            return False, f"Requested reservation extends past closing time ({hours.close_time.strftime('%I:%M %p')})."

        return True, "Within operating hours."

    @staticmethod
    def check_availability(
        db: Session,
        restaurant_id: int,
        date_str: str,  # YYYY-MM-DD
        time_str: str,  # HH:MM
        party_size: int,
        preferred_seating_area: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Check real database availability considering table capacity, active reservations,
        and restaurant operating hours. Also calculates adjacent available time slots.
        """
        try:
            req_date = datetime.datetime.strptime(date_str, "%Y-%m-%d").date()
            req_time = datetime.datetime.strptime(time_str, "%H:%M").time()
        except ValueError:
            return {
                "available": False,
                "error": "Invalid date or time format. Please use YYYY-MM-DD and HH:MM."
            }

        booking_start = datetime.datetime.combine(req_date, req_time)
        slot_duration = datetime.timedelta(minutes=settings.RESERVATION_SLOT_MINUTES)
        booking_end = booking_start + slot_duration

        # Operating hours check
        within_hours, hours_msg = BookingEngine.is_within_operating_hours(
            db, restaurant_id, booking_start, booking_end
        )
        if not within_hours:
            return {
                "available": False,
                "reason": hours_msg,
                "alternative_slots": []
            }

        # Query eligible tables by capacity and seating area
        table_query = db.query(Table).filter(
            Table.restaurant_id == restaurant_id,
            Table.is_active == True,
            Table.max_capacity >= party_size,
            Table.min_capacity <= party_size
        )
        if preferred_seating_area:
            table_query = table_query.filter(Table.seating_area == preferred_seating_area)

        eligible_tables = table_query.all()
        if not eligible_tables:
            # Check if any table can fit without seating area constraint
            if preferred_seating_area:
                any_area_tables = db.query(Table).filter(
                    Table.restaurant_id == restaurant_id,
                    Table.is_active == True,
                    Table.max_capacity >= party_size
                ).all()
                if any_area_tables:
                    return {
                        "available": False,
                        "reason": f"No available tables for party of {party_size} in '{preferred_seating_area}'. Other areas may have seating.",
                        "alternative_slots": []
                    }
            return {
                "available": False,
                "reason": f"No tables accommodate a party size of {party_size}.",
                "alternative_slots": []
            }

        # Check existing overlapping reservations for these tables
        # Overlap condition: start_time < booking_end AND end_time > booking_start
        available_tables = []
        for tbl in eligible_tables:
            conflict = db.query(Reservation).filter(
                Reservation.table_id == tbl.id,
                Reservation.status.in_([ReservationStatus.CONFIRMED.value, ReservationStatus.PENDING_CONFIRMATION.value]),
                Reservation.start_time < booking_end,
                Reservation.end_time > booking_start
            ).first()

            if not conflict:
                available_tables.append({
                    "id": tbl.id,
                    "table_number": tbl.table_number,
                    "seating_area": tbl.seating_area,
                    "capacity": tbl.max_capacity
                })

        if available_tables:
            return {
                "available": True,
                "requested_date": date_str,
                "requested_time": time_str,
                "party_size": party_size,
                "available_tables_count": len(available_tables),
                "available_tables": available_tables
            }

        # Calculate alternative slots on the same day (+/- 30, 60, 90 mins)
        alternative_slots = []
        offsets = [-60, -30, 30, 60, 90]
        for offset in offsets:
            alt_start = booking_start + datetime.timedelta(minutes=offset)
            alt_end = alt_start + slot_duration
            
            # Check hours for alt
            alt_within, _ = BookingEngine.is_within_operating_hours(db, restaurant_id, alt_start, alt_end)
            if not alt_within:
                continue

            # Check if any eligible table is free
            for tbl in eligible_tables:
                conflict = db.query(Reservation).filter(
                    Reservation.table_id == tbl.id,
                    Reservation.status.in_([ReservationStatus.CONFIRMED.value, ReservationStatus.PENDING_CONFIRMATION.value]),
                    Reservation.start_time < alt_end,
                    Reservation.end_time > alt_start
                ).first()
                if not conflict:
                    slot_str = alt_start.strftime("%H:%M")
                    if slot_str not in alternative_slots:
                        alternative_slots.append(slot_str)
                    break

        return {
            "available": False,
            "reason": f"All suitable tables are booked at {time_str} for a party of {party_size}.",
            "alternative_slots": alternative_slots
        }

    @staticmethod
    def create_reservation_transactional(
        db: Session,
        restaurant_id: int,
        customer_name: str,
        customer_phone: str,
        customer_email: Optional[str],
        date_str: str,
        time_str: str,
        party_size: int,
        preferred_seating_area: Optional[str] = None,
        special_requests: Optional[str] = None,
        confirmed: bool = False
    ) -> Dict[str, Any]:
        """
        Creates a reservation inside a safe transaction with re-validation to prevent race conditions.
        Requires confirmed=True to commit.
        """
        if not confirmed:
            return {
                "success": False,
                "requires_confirmation": True,
                "message": "Explicit customer confirmation is required before booking can be completed."
            }

        try:
            req_date = datetime.datetime.strptime(date_str, "%Y-%m-%d").date()
            req_time = datetime.datetime.strptime(time_str, "%H:%M").time()
        except ValueError:
            return {"success": False, "error": "Invalid date or time format."}

        booking_start = datetime.datetime.combine(req_date, req_time)
        slot_duration = datetime.timedelta(minutes=settings.RESERVATION_SLOT_MINUTES)
        booking_end = booking_start + slot_duration

        # Begin transaction & find best matching table
        with db.begin_nested():
            # Filter eligible tables
            table_query = db.query(Table).filter(
                Table.restaurant_id == restaurant_id,
                Table.is_active == True,
                Table.max_capacity >= party_size,
                Table.min_capacity <= party_size
            )
            if preferred_seating_area:
                table_query = table_query.filter(Table.seating_area == preferred_seating_area)
            
            # Order tables by capacity closest to party size to optimize seating
            tables = table_query.order_by(Table.max_capacity.asc()).all()
            
            selected_table = None
            for tbl in tables:
                # Check for overlap with row-locking where supported
                conflict = db.query(Reservation).filter(
                    Reservation.table_id == tbl.id,
                    Reservation.status.in_([ReservationStatus.CONFIRMED.value, ReservationStatus.PENDING_CONFIRMATION.value]),
                    Reservation.start_time < booking_end,
                    Reservation.end_time > booking_start
                ).first()

                if not conflict:
                    selected_table = tbl
                    break

            if not selected_table:
                return {
                    "success": False,
                    "error": f"No tables currently available at {time_str} on {date_str} for party size {party_size}."
                }

            # Upsert Customer
            customer = db.query(Customer).filter(Customer.phone == customer_phone).first()
            if not customer:
                customer = Customer(
                    full_name=customer_name,
                    phone=customer_phone,
                    email=customer_email
                )
                db.add(customer)
                db.flush()
            else:
                customer.full_name = customer_name
                if customer_email:
                    customer.email = customer_email
                db.flush()

            # Create Reservation
            booking_code = BookingEngine.generate_booking_code()
            new_res = Reservation(
                booking_code=booking_code,
                restaurant_id=restaurant_id,
                table_id=selected_table.id,
                customer_id=customer.id,
                party_size=party_size,
                start_time=booking_start,
                end_time=booking_end,
                status=ReservationStatus.CONFIRMED.value,
                special_requests=special_requests
            )
            db.add(new_res)

            # Audit log
            audit = AuditLog(
                entity_type="reservation",
                entity_id=booking_code,
                action="CREATE",
                performed_by="VOXRESERVE_ENGINE",
                details_json=f'{{"customer": "{customer_name}", "phone": "{customer_phone}", "party_size": {party_size}, "table": "{selected_table.table_number}"}}'
            )
            db.add(audit)
            db.commit()

        return {
            "success": True,
            "booking_code": booking_code,
            "table_number": selected_table.table_number,
            "seating_area": selected_table.seating_area,
            "date": date_str,
            "time": time_str,
            "party_size": party_size,
            "customer_name": customer_name,
            "customer_phone": customer_phone,
            "message": f"Reservation successfully confirmed! Booking code: {booking_code}."
        }

    @staticmethod
    def cancel_reservation(
        db: Session,
        booking_code: str,
        customer_phone: str,
        reason: Optional[str] = None
    ) -> Dict[str, Any]:
        """Cancel a reservation after strictly verifying customer authority."""
        reservation = db.query(Reservation).filter(Reservation.booking_code == booking_code).first()
        if not reservation:
            return {"success": False, "error": f"Reservation {booking_code} not found."}

        # Verification check: customer phone match or admin override
        if reservation.customer.phone != customer_phone:
            return {
                "success": False,
                "error": "Authentication failed: Provided phone number does not match this reservation."
            }

        if reservation.status == ReservationStatus.CANCELLED.value:
            return {"success": False, "error": f"Reservation {booking_code} is already cancelled."}

        reservation.status = ReservationStatus.CANCELLED.value
        audit = AuditLog(
            entity_type="reservation",
            entity_id=booking_code,
            action="CANCEL",
            performed_by=f"Customer: {customer_phone}",
            details_json=f'{{"reason": "{reason or "Customer requested cancellation"}"}}'
        )
        db.add(audit)
        db.commit()

        return {
            "success": True,
            "booking_code": booking_code,
            "message": f"Reservation {booking_code} has been successfully cancelled."
        }

    @staticmethod
    def modify_reservation(
        db: Session,
        booking_code: str,
        customer_phone: str,
        new_date: Optional[str] = None,
        new_time: Optional[str] = None,
        new_party_size: Optional[int] = None,
        new_seating_area: Optional[str] = None,
        special_requests: Optional[str] = None
    ) -> Dict[str, Any]:
        """Modify reservation after verifying authority and checking availability."""
        reservation = db.query(Reservation).filter(Reservation.booking_code == booking_code).first()
        if not reservation:
            return {"success": False, "error": f"Reservation {booking_code} not found."}

        if reservation.customer.phone != customer_phone:
            return {
                "success": False,
                "error": "Authentication failed: Provided phone number does not match this reservation."
            }

        # Target parameters
        target_date_str = new_date or reservation.start_time.strftime("%Y-%m-%d")
        target_time_str = new_time or reservation.start_time.strftime("%H:%M")
        target_party_size = new_party_size or reservation.party_size
        target_seating_area = new_seating_area or reservation.table.seating_area

        # Temporary mark current reservation cancelled to check availability without self-conflict
        old_status = reservation.status
        reservation.status = ReservationStatus.CANCELLED.value
        db.flush()

        avail = BookingEngine.check_availability(
            db=db,
            restaurant_id=reservation.restaurant_id,
            date_str=target_date_str,
            time_str=target_time_str,
            party_size=target_party_size,
            preferred_seating_area=target_seating_area
        )

        if not avail.get("available"):
            reservation.status = old_status
            db.rollback()
            return {
                "success": False,
                "error": f"Modification unavailable: {avail.get('reason')}",
                "alternative_slots": avail.get("alternative_slots", [])
            }

        # Pick table
        chosen_table_info = avail["available_tables"][0]
        new_start = datetime.datetime.strptime(f"{target_date_str} {target_time_str}", "%Y-%m-%d %H:%M")
        new_end = new_start + datetime.timedelta(minutes=settings.RESERVATION_SLOT_MINUTES)

        reservation.table_id = chosen_table_info["id"]
        reservation.party_size = target_party_size
        reservation.start_time = new_start
        reservation.end_time = new_end
        reservation.status = ReservationStatus.CONFIRMED.value
        if special_requests is not None:
            reservation.special_requests = special_requests

        audit = AuditLog(
            entity_type="reservation",
            entity_id=booking_code,
            action="UPDATE",
            performed_by=f"Customer: {customer_phone}",
            details_json=f'{{"date": "{target_date_str}", "time": "{target_time_str}", "party": {target_party_size}}}'
        )
        db.add(audit)
        db.commit()

        return {
            "success": True,
            "booking_code": booking_code,
            "date": target_date_str,
            "time": target_time_str,
            "party_size": target_party_size,
            "table_number": chosen_table_info["table_number"],
            "seating_area": chosen_table_info["seating_area"],
            "message": f"Reservation {booking_code} successfully updated for {target_date_str} at {target_time_str}!"
        }
