-- INSERT DATA

citypulse=# INSERT INTO transport_routes (route_name, transport_type, max_capacity)
citypulse-# VALUES
citypulse-# ('Route A', 'Bus Earth', 40),
citypulse-# ('Route B', 'Bus Mars', 70),
citypulse-# ('Route C', 'Bus Mercury', 90),
citypulse-# ('Route D', 'Bus Venus', 50),
citypulse-# ('Route E', 'Metro Up', 140),
citypulse-# ('Route F', 'Metro Down', 100),
citypulse-# ('Route G', 'Metro Main', 210);
INSERT 0 7

citypulse=# INSERT INTO zone_metadata (zone_name, population_density, avg_income)
citypulse-# VALUES
citypulse-# ('Zone 1', 4500.5, 55000),
citypulse-# ('Zone 2', 3200.2, 43000),
citypulse-# ('Zone 3', 6100.8, 47000),
citypulse-# ('Zone 4', 5900.8, 45000),
citypulse-# ('Zone 5', 4900.8, 50000);
INSERT 0 5

citypulse=# INSERT INTO passenger_logs (route_id, timestamp, station_name, zone_id, passenger_count)
citypulse-# VALUES
citypulse-# (1, '2025-07-07 07:30:00', 'Station Apollo', 1, 35),
citypulse-# (2, '2025-07-07 08:00:00', 'Station Galaxy', 2, 50),
citypulse-# (3, '2025-07-07 08:15:00', 'Station Helios', 3, 80),
citypulse-# (4, '2025-07-07 08:30:00', 'Station Aurora', 4, 45),
citypulse-# (5, '2025-07-07 08:45:00', 'Station Zenith', 5, 120),
citypulse-# (6, '2025-07-07 09:00:00', 'Station Luna', 1, 95),
citypulse-# (7, '2025-07-07 09:15:00', 'Station Orbit', 2, 180),
citypulse-# (1, '2025-07-07 09:30:00', 'Station Apollo', 1, 38),
citypulse-# (2, '2025-07-07 09:45:00', 'Station Galaxy', 2, 65),
citypulse-# (3, '2025-07-07 10:00:00', 'Station Helios', 3, 75),
citypulse-# (4, '2025-07-07 10:15:00', 'Station Aurora', 4, 50),
citypulse-# (5, '2025-07-07 10:30:00', 'Station Zenith', 5, 130),
citypulse-# (6, '2025-07-07 10:45:00', 'Station Luna', 1, 90),
citypulse-# (7, '2025-07-07 11:00:00', 'Station Orbit', 2, 160),
citypulse-# (1, '2025-07-07 11:15:00', 'Station Apollo', 1, 40);
INSERT 0 15

citypulse=# INSERT INTO users (name, email)
citypulse-# VALUES
citypulse-# ('Amit Rao', 'amit.rao@email.com'),
citypulse-# ('Latika D.', 'latika@email.com'),
citypulse-# ('Nina Patel', 'nina.p@email.com'),
citypulse-# ('Druv Shah', 'druv@email.com'),
citypulse-# ('Aly Dawn', 'aldawn@email.com');
INSERT 0 5

citypulse=# INSERT INTO bookings (user_id, route_id, timestamp)
citypulse-# VALUES
citypulse-# (2, 3, '2025-07-07 08:15:00'),
citypulse-# (1, 1, '2025-07-07 08:00:00'),
citypulse-# (4, 6, '2025-07-07 09:00:00'),
citypulse-# (2, 1, '2025-07-07 09:30:00'),
citypulse-# (3, 7, '2025-07-07 09:15:00'),
citypulse-# (5, 2, '2025-07-07 09:45:00'),
citypulse-# (1, 4, '2025-07-07 10:15:00');
INSERT 0 7