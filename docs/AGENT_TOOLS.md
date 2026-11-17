# AGENT TOOLS & REGISTRY SPECIFICATION

The AI assistant executes verified backend capabilities through a registered schema. The model cannot execute raw SQL or fabricate booking codes.

## Available Tools

### 1. `check_availability`
- **Purpose**: Checks verified database availability for table capacity, operating hours, and existing reservations.
- **Parameters**:
  - `date` (string, YYYY-MM-DD): The reservation date.
  - `time` (string, HH:MM 24h): Desired dining time.
  - `party_size` (integer): Number of guests (1-20).
  - `preferred_seating_area` (optional string): `indoor`, `outdoor_patio`, `bar`, `booth`, `private_dining`.
- **Returns**: Available status, matching tables, and adjacent alternative slots (+/- 30, 60, 90 mins).

### 2. `get_restaurant_hours`
- **Purpose**: Retrieves official operating schedule and dining window policies.
- **Returns**: Day-by-day opening and closing hours, timezone, and cutoff policies.

### 3. `get_menu`
- **Purpose**: Retrieves categorised food dishes, prices, dietary badges, and ingredients.
- **Parameters**: `category` (optional string filter).

### 4. `check_allergens`
- **Purpose**: Checks dishes for explicit allergens (Gluten, Dairy, Peanuts, Tree Nuts, Shellfish, etc.).
- **Safety Policy**: Never guarantees safety if unknown; attaches cross-contamination warnings.

### 5. `create_reservation`
- **Purpose**: Commits a verified table booking to the database.
- **Strict Requirement**: `customer_confirmed: true`. The agent is blocked from calling this without explicit user consent.
- **Parameters**: `customer_name`, `customer_phone`, `date`, `time`, `party_size`, `customer_confirmed`, `special_requests`.

### 6. `get_reservation`
- **Purpose**: Fetches booking status given `booking_code` and matching `customer_phone`.

### 7. `cancel_reservation`
- **Purpose**: Cancels a booking after verifying customer ownership.

### 8. `modify_reservation`
- **Purpose**: Changes time, date, party size, or seating area after checking availability.
