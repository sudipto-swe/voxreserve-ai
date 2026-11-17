# DATABASE SCHEMA & ENTITY RELATIONSHIPS

## Tables Overview

- `users`: Administrative and staff accounts with hashed credentials and roles (`admin`, `staff`, `customer`).
- `restaurants`: Restaurant metadata, address, contact, operating timezone, and dining policies.
- `restaurant_hours`: Daily operating hours, open time, close time, and closure flags.
- `tables`: Table inventory, numbers, min/max capacities, and seating areas (`indoor`, `booth`, `outdoor_patio`, `bar`, `private_dining`).
- `customers`: Customer records (name, verified phone number, optional email, notes).
- `reservations`: Bookings with status (`confirmed`, `cancelled`, `pending_confirmation`), start/end timestamps, and table assignments.
- `menu_categories` & `menu_items`: Categorized culinary dishes, pricing, dietary flags (`is_vegan`, `is_vegetarian`, `is_gluten_free`).
- `ingredients` & `allergens`: Detailed component breakdowns and allergen mapping (`menu_item_allergens`).
- `conversations` & `messages`: Session audit logs, role tracking, and audio transcription tags.
- `agent_tool_executions`: Full telemetry of every tool called by the AI, including input arguments, execution result, and status.
- `audit_logs`: Immutable security ledger for critical operations (creations, cancellations, logins).
