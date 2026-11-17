# BOOKING & AVAILABILITY ENGINE

## Concurrency and Overlap Rules
A table conflict occurs when:
```
existing_reservation.start_time < requested_booking.end_time
AND
existing_reservation.end_time > requested_booking.start_time
```

## Anti-Double-Booking Protection
1. **Initial Availability Query**: Filters eligible tables by capacity, seating area, and open hours.
2. **Transactional Re-validation**: Inside `create_reservation_transactional`, the database transaction checks candidate tables again inside an atomic transaction block (`with db.begin_nested()`).
3. **Table Optimization**: Tables with capacity closest to the party size are chosen first to preserve large tables for bigger groups.
4. **Human-Readable Booking Codes**: Codes like `VR-A1B2C3` are generated using cryptographic tokens.
