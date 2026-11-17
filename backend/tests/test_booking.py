import pytest
import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.database import Base
from app.models.entities import Restaurant, RestaurantHours, Table, Reservation, ReservationStatus, Customer
from app.services.booking_engine import BookingEngine
from app.tools.registry import AgentToolRegistry

# Use in-memory SQLite for high-speed deterministic test suite
TEST_DB_URL = "sqlite:///:memory:"

@pytest.fixture
def test_db():
    engine = create_engine(TEST_DB_URL, connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    TestingSession = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = TestingSession()

    # Seed minimal restaurant
    rest = Restaurant(
        name="Aura & Embers Bistro",
        address="450 Lumina Blvd",
        phone="+1 (415) 890-4422",
        timezone="America/Los_Angeles"
    )
    db.add(rest)
    db.commit()
    db.refresh(rest)

    # Add hours: Mon-Sun 17:00 to 23:00
    for d in range(7):
        db.add(RestaurantHours(
            restaurant_id=rest.id,
            day_of_week=d,
            open_time=datetime.time(17, 0),
            close_time=datetime.time(23, 0),
            is_closed=False
        ))

    # Add 2 tables: T1 (capacity 2-4), T2 (capacity 2-4)
    t1 = Table(restaurant_id=rest.id, table_number="T1", min_capacity=2, max_capacity=4, seating_area="indoor")
    t2 = Table(restaurant_id=rest.id, table_number="T2", min_capacity=2, max_capacity=4, seating_area="indoor")
    db.add_all([t1, t2])
    db.commit()

    yield db
    db.close()


def test_availability_and_booking_flow(test_db):
    tomorrow = (datetime.date.today() + datetime.timedelta(days=1)).strftime("%Y-%m-%d")

    # 1. Check availability for 4 guests at 19:00
    avail = BookingEngine.check_availability(test_db, 1, tomorrow, "19:00", 4)
    assert avail["available"] is True
    assert avail["available_tables_count"] == 2

    # 2. Prevent booking without explicit customer confirmation
    res_no_conf = BookingEngine.create_reservation_transactional(
        db=test_db,
        restaurant_id=1,
        customer_name="Alice Smith",
        customer_phone="+1555111222",
        customer_email="alice@test.com",
        date_str=tomorrow,
        time_str="19:00",
        party_size=4,
        confirmed=False
    )
    assert res_no_conf["success"] is False
    assert res_no_conf["requires_confirmation"] is True

    # 3. Create booking with confirmation
    res1 = BookingEngine.create_reservation_transactional(
        db=test_db,
        restaurant_id=1,
        customer_name="Alice Smith",
        customer_phone="+1555111222",
        customer_email="alice@test.com",
        date_str=tomorrow,
        time_str="19:00",
        party_size=4,
        confirmed=True
    )
    assert res1["success"] is True
    assert "booking_code" in res1
    code1 = res1["booking_code"]

    # 4. Book second table
    res2 = BookingEngine.create_reservation_transactional(
        db=test_db,
        restaurant_id=1,
        customer_name="Bob Jones",
        customer_phone="+1555333444",
        customer_email="bob@test.com",
        date_str=tomorrow,
        time_str="19:00",
        party_size=4,
        confirmed=True
    )
    assert res2["success"] is True

    # 5. Third booking at the same slot must fail (all 2 tables occupied)
    res3 = BookingEngine.create_reservation_transactional(
        db=test_db,
        restaurant_id=1,
        customer_name="Charlie Brown",
        customer_phone="+1555555666",
        customer_email="charlie@test.com",
        date_str=tomorrow,
        time_str="19:00",
        party_size=4,
        confirmed=True
    )
    assert res3["success"] is False
    assert "No tables currently available" in res3["error"]

    # 6. Cancellation with incorrect phone must be rejected (Security requirement)
    cancel_bad = BookingEngine.cancel_reservation(test_db, code1, "+1000000000")
    assert cancel_bad["success"] is False
    assert "Authentication failed" in cancel_bad["error"]

    # 7. Cancellation with correct phone succeeds
    cancel_ok = BookingEngine.cancel_reservation(test_db, code1, "+1555111222")
    assert cancel_ok["success"] is True

    # 8. Slot is now available again for Charlie
    res4 = BookingEngine.create_reservation_transactional(
        db=test_db,
        restaurant_id=1,
        customer_name="Charlie Brown",
        customer_phone="+1555555666",
        customer_email="charlie@test.com",
        date_str=tomorrow,
        time_str="19:00",
        party_size=4,
        confirmed=True
    )
    assert res4["success"] is True


def test_tool_registry_execution(test_db):
    tomorrow = (datetime.date.today() + datetime.timedelta(days=1)).strftime("%Y-%m-%d")

    # Test hours tool
    hours_res = AgentToolRegistry.execute_tool("get_restaurant_hours", {}, test_db, 1)
    assert "hours" in hours_res
    assert len(hours_res["hours"]) == 7

    # Test availability tool
    avail_res = AgentToolRegistry.execute_tool(
        "check_availability",
        {"date": tomorrow, "time": "18:00", "party_size": 2},
        test_db, 1
    )
    assert avail_res["available"] is True
