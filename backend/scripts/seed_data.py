import datetime
from sqlalchemy.orm import Session
from app.core.database import SessionLocal, Base, engine
from app.core.security import get_password_hash
from app.models.entities import (
    User, UserRole, Restaurant, RestaurantHours, Table, SeatingArea,
    Customer, Reservation, ReservationStatus, MenuCategory, MenuItem,
    Ingredient, Allergen, MenuItemAllergen
)


def seed_database():
    Base.metadata.create_all(bind=engine)
    db: Session = SessionLocal()

    try:
        # Check if already seeded
        if db.query(Restaurant).first():
            print("Database already contains data. Skipping seeding.")
            return

        print("Seeding initial data for Aura & Embers Bistro...")

        # 1. Admin & Staff User
        admin_user = User(
            email="admin@auraandembers.com",
            hashed_password=get_password_hash("AdminPass2026!"),
            full_name="Chef Marcus Vance",
            role=UserRole.ADMIN.value
        )
        staff_user = User(
            email="host@auraandembers.com",
            hashed_password=get_password_hash("StaffPass2026!"),
            full_name="Elena Rostova",
            role=UserRole.STAFF.value
        )
        db.add_all([admin_user, staff_user])
        db.commit()

        # 2. Restaurant Profile
        restaurant = Restaurant(
            name="Aura & Embers Bistro",
            description="Contemporary wood-fired dining featuring seasonal hearth fare, craft mixology, and warm hospitality.",
            address="450 Lumina Blvd, Waterfront District, San Francisco, CA 94107",
            phone="+1 (415) 890-4422",
            email="reservations@auraandembers.com",
            timezone="America/Los_Angeles",
            reservation_policy="Standard dining allocations are 90 minutes for parties of 1-4, and 120 minutes for larger parties. A 15-minute grace period applies."
        )
        db.add(restaurant)
        db.commit()
        db.refresh(restaurant)

        # 3. Operating Hours (Monday - Sunday)
        # Weekdays: 17:00 - 23:00, Weekends: 17:00 - 00:00
        for day in range(7):
            close_h = 0 if day in [4, 5] else 23  # Fri/Sat open until midnight
            hours = RestaurantHours(
                restaurant_id=restaurant.id,
                day_of_week=day,
                open_time=datetime.time(17, 0),
                close_time=datetime.time(close_h, 0),
                is_closed=False
            )
            db.add(hours)
        db.commit()

        # 4. Tables with diverse seating areas and capacities
        tables_data = [
            ("T-01", 1, 2, SeatingArea.BOOTH.value),
            ("T-02", 1, 2, SeatingArea.BOOTH.value),
            ("T-03", 2, 4, SeatingArea.INDOOR.value),
            ("T-04", 2, 4, SeatingArea.INDOOR.value),
            ("T-05", 2, 4, SeatingArea.OUTDOOR_PATIO.value),
            ("T-06", 2, 4, SeatingArea.OUTDOOR_PATIO.value),
            ("T-07", 4, 6, SeatingArea.INDOOR.value),
            ("T-08", 4, 6, SeatingArea.BOOTH.value),
            ("T-09", 6, 10, SeatingArea.PRIVATE_DINING.value),
            ("BAR-1", 1, 2, SeatingArea.BAR.value),
            ("BAR-2", 1, 2, SeatingArea.BAR.value)
        ]
        created_tables = []
        for num, min_c, max_c, area in tables_data:
            tbl = Table(
                restaurant_id=restaurant.id,
                table_number=num,
                min_capacity=min_c,
                max_capacity=max_c,
                seating_area=area,
                is_active=True
            )
            db.add(tbl)
            created_tables.append(tbl)
        db.commit()

        # 5. Allergens
        allergens_dict = {}
        allergen_names = [
            ("Dairy", "Milk, butter, heavy cream, parmesan, and aged cheeses."),
            ("Gluten", "Wheat, barley, rye flour in bread, pasta, and roux."),
            ("Peanuts", "Peanut oils, crushed peanuts, satay sauce."),
            ("Tree Nuts", "Walnuts, almonds, pine nuts, hazelnuts."),
            ("Shellfish", "Shrimp, lobster, scallops, crab."),
            ("Eggs", "Egg yolks, aioli, meringue, fresh pasta."),
            ("Soy", "Soy sauce, edamame, fermented bean paste.")
        ]
        for name, desc in allergen_names:
            al = Allergen(name=name, description=desc)
            db.add(al)
            allergens_dict[name] = al
        db.commit()

        # 6. Menu Categories & Items
        starters = MenuCategory(restaurant_id=restaurant.id, name="Starters & Small Plates", display_order=1)
        mains = MenuCategory(restaurant_id=restaurant.id, name="Wood-Fired Hearth Mains", display_order=2)
        desserts = MenuCategory(restaurant_id=restaurant.id, name="Artisanal Desserts", display_order=3)
        beverages = MenuCategory(restaurant_id=restaurant.id, name="Signature Libations", display_order=4)
        db.add_all([starters, mains, desserts, beverages])
        db.commit()

        # Menu Items details: (Category, Name, Desc, Price, Vegan, Veg, GF, Spicy, Allergens, Ingredients)
        dishes = [
            (
                starters, "Wood-Roasted Charred Octopus",
                "Spanish octopus roasted with smoked paprika potatoes, pickled shallots, and saffron emulsion.",
                22.00, False, False, True, 1, ["Shellfish"],
                ["Spanish Octopus", "Fingerling Potatoes", "Smoked Paprika", "Saffron Emulsion", "Pickled Shallots"]
            ),
            (
                starters, "Truffled Burrata Crostini",
                "Creamy Puglia burrata, wild blossom honey, shaved black truffles, and grilled sourdough.",
                19.50, False, True, False, 0, ["Dairy", "Gluten"],
                ["Puglia Burrata", "Grilled Artisanal Sourdough", "Black Truffle", "Wild Honey", "Micro Basil"]
            ),
            (
                starters, "Hearth Roasted Romanesco (Vegan)",
                "Golden romanesco roasted with chili crisp, toasted hazelnuts, and lemon tahini whip.",
                16.00, True, True, True, 1, ["Tree Nuts"],
                ["Romanesco Cauliflower", "Tahini Whip", "Chili Crisp", "Toasted Hazelnuts", "Pomegranate Seeds"]
            ),
            (
                mains, "Oak-Smoked Prime Ribeye (16oz)",
                "Dry-aged California Angus, bone marrow herb crust, charred broccolini, and shallot demi-glace.",
                58.00, False, False, True, 0, ["Dairy"],
                ["Prime Angus Ribeye", "Bone Marrow", "Garlic Butter", "Charred Broccolini", "Red Wine Demi"]
            ),
            (
                mains, "Wild King Salmon en Papillote",
                "Pacific King Salmon with Meyer lemon, braised fennel, caper berries, and dill fume.",
                39.00, False, False, True, 0, [],
                ["Wild King Salmon", "Fennel", "Meyer Lemon", "Capers", "Fresh Dill", "Extra Virgin Olive Oil"]
            ),
            (
                mains, "Handmade Porcini & Truffle Tagliolini",
                "Fresh semolina pasta tossed in cave-aged parmesan, slow-braised wild porcini, and summer truffle butter.",
                32.00, False, True, False, 0, ["Dairy", "Gluten", "Eggs"],
                ["Egg Tagliolini", "Porcini Mushrooms", "Parmigiano-Reggiano", "Butter", "Black Truffles"]
            ),
            (
                desserts, "Smoked Dark Chocolate Fondant",
                "Valrhona 72% lava cake, bourbon sea salt caramel, and Madagascar vanilla bean gelato.",
                15.00, False, True, False, 0, ["Dairy", "Gluten", "Eggs"],
                ["Valrhona Dark Chocolate", "Butter", "Eggs", "Flour", "Bourbon Caramel", "Vanilla Gelato"]
            ),
            (
                desserts, "Meyer Lemon & Thyme Tart",
                "Crisp almond sable crust, tart citrus curd, torched italian meringue, and candied zest.",
                14.00, False, True, False, 0, ["Dairy", "Gluten", "Eggs", "Tree Nuts"],
                ["Almond Flour", "Meyer Lemon Curd", "Eggs", "Sugar Meringue", "Fresh Thyme"]
            ),
            (
                beverages, "Smoked Rosemary Old Fashioned",
                "Small-batch bourbon, demerara, angostura bitters, flamed rosemary sprig, and orange peel.",
                18.00, True, True, True, 0, [],
                ["Bourbon Whiskey", "Demerara Sugar", "Angostura Bitters", "Charred Rosemary Sprig"]
            )
        ]

        for cat, name, desc, price, veg_n, veg, gf, sp, algs, ings in dishes:
            item = MenuItem(
                category_id=cat.id,
                name=name,
                description=desc,
                price=price,
                is_available=True,
                is_vegan=veg_n,
                is_vegetarian=veg,
                is_gluten_free=gf,
                spicy_level=sp
            )
            db.add(item)
            db.flush()

            for ing_name in ings:
                db.add(Ingredient(menu_item_id=item.id, name=ing_name))

            for alg_name in algs:
                if alg_name in allergens_dict:
                    db.add(MenuItemAllergen(
                        menu_item_id=item.id,
                        allergen_id=allergens_dict[alg_name].id,
                        severity_note="Contains ingredient"
                    ))
        db.commit()

        # 7. Seed Sample Customer & Verified Reservation
        sample_cust = Customer(
            full_name="Sophia Loren",
            phone="+1 (555) 789-0123",
            email="sophia@example.com"
        )
        db.add(sample_cust)
        db.flush()

        # Book T-03 for tomorrow at 19:00
        tomorrow = datetime.date.today() + datetime.timedelta(days=1)
        res_start = datetime.datetime.combine(tomorrow, datetime.time(19, 0))
        res_end = res_start + datetime.timedelta(minutes=90)
        
        sample_res = Reservation(
            booking_code="VR-INIT01",
            restaurant_id=restaurant.id,
            table_id=created_tables[2].id,  # T-03
            customer_id=sample_cust.id,
            party_size=2,
            start_time=res_start,
            end_time=res_end,
            status=ReservationStatus.CONFIRMED.value,
            special_requests="Anniversary dinner; quiet window seating preferred."
        )
        db.add(sample_res)
        db.commit()

        print("Seeding completed successfully! Default admin: admin@auraandembers.com / AdminPass2026!")

    except Exception as e:
        db.rollback()
        print(f"Error seeding database: {e}")
        raise e
    finally:
        db.close()


if __name__ == "__main__":
    seed_database()
