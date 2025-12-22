-- QUERIES

-- table lists

citypulse=# \dt

              List of relations
 Schema |       Name       | Type  |  Owner
--------+------------------+-------+----------
 public | bookings         | table | postgres
 public | passenger_logs   | table | postgres
 public | transport_routes | table | postgres
 public | users            | table | postgres
 public | zone_metadata    | table | postgres
(5 rows)

 -- Check available seats before booking for Route A at 08:00

citypulse=# SELECT r.route_name, r.max_capacity - COALESCE(SUM(p.passenger_count), 0) - COALESCE(COUNT(b.booking_id), 0) AS seats_available
citypulse-# FROM  transport_routes r
citypulse-# LEFT JOIN passenger_logs p ON r.route_id = p.route_id AND p.timestamp = '2025-07-07 08:00:00'
citypulse-# LEFT JOIN  bookings b ON r.route_id = b.route_id AND b.timestamp = '2025-07-07 08:00:00'
citypulse-# WHERE r.route_name = 'Route A'
citypulse-# GROUP BY r.route_name, r.max_capacity;

 route_name | seats_available
------------+-----------------
 Route A    |              40
(1 row)

-- View all the bookings

citypulse=# SELECT b.booking_id, u.name, r.route_name, b.timestamp
citypulse-# FROM bookings b
citypulse-# JOIN users u ON b.user_id = u.user_id
citypulse-# JOIN transport_routes r ON b.route_id = r.route_id
citypulse-# ORDER BY b.timestamp;

 booking_id |    name    | route_name |      timestamp
------------+------------+------------+---------------------
          2 | Amit Rao   | Route A    | 2025-07-07 08:00:00
          1 | Latika D.  | Route C    | 2025-07-07 08:15:00
          3 | Druv Shah  | Route F    | 2025-07-07 09:00:00
          5 | Nina Patel | Route G    | 2025-07-07 09:15:00
          4 | Latika D.  | Route A    | 2025-07-07 09:30:00
          6 | Aly Dawn   | Route B    | 2025-07-07 09:45:00
          7 | Amit Rao   | Route D    | 2025-07-07 10:15:00
(7 rows)

 -- Seat availability

citypulse=# WITH available AS (
citypulse(#     SELECT r.max_capacity - COUNT(b.booking_id) AS seats_left
citypulse(#     FROM transport_routes r
citypulse(#     JOIN bookings b ON r.route_id = b.route_id
citypulse(#     WHERE r.route_id = 1 AND b.timestamp = '2025-07-07 08:00:00'
citypulse(#     GROUP BY r.max_capacity
citypulse(# )
citypulse-# SELECT
citypulse-#     CASE
citypulse-#         WHEN seats_left > 0 THEN 'Seat available! Proceed to book.'
citypulse-#         ELSE 'Sorry, no seats left.'
citypulse-#     END AS booking_status
citypulse-# FROM available;
          booking_status
----------------------------------
 Seat available! Proceed to book.
(1 row)

-- To check if overloaded

citypulse=# SELECT
citypulse-#     r.route_name,
citypulse-#     l.timestamp,
citypulse-#     SUM(l.passenger_count) + COUNT(b.booking_id) AS total_passengers,
citypulse-#     r.max_capacity,
citypulse-#     (r.max_capacity - (SUM(l.passenger_count) + COUNT(b.booking_id))) AS available_seats
citypulse-# FROM
citypulse-#     transport_routes r
citypulse-# LEFT JOIN passenger_logs l ON r.route_id = l.route_id
citypulse-# LEFT JOIN bookings b ON r.route_id = b.route_id AND l.timestamp = b.timestamp
citypulse-# GROUP BY r.route_name, l.timestamp, r.max_capacity
citypulse-# HAVING SUM(l.passenger_count) + COUNT(b.booking_id) > r.max_capacity;

 route_name |      timestamp      | total_passengers | max_capacity | available_seats
------------+---------------------+------------------+--------------+-----------------
 Route D    | 2025-07-07 10:15:00 |               51 |           50 |              -1
(1 row)