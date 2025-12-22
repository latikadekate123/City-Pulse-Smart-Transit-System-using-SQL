-- =====================================================
-- CityPulse Transit System - Realistic Seed Data
-- =====================================================
-- Simulates real-world transit data:
-- - Anonymous fare cards (not registered users)
-- - Trip records from card taps
-- - 90 days of ridership data
-- - Peak/off-peak patterns
-- =====================================================

-- Clear existing data
TRUNCATE TABLE trips, fare_cards, schedules, routes, stations, zones, 
               travel_time_logs, service_availability 
               RESTART IDENTITY CASCADE;

-- ====================================
-- 1. ZONES
-- ====================================
INSERT INTO zones (zone_name, population_density, avg_income, area_type) VALUES
('Downtown Core', 8500.5, 75000, 'Commercial'),
('Business District', 6200.8, 82000, 'Commercial'),
('Residential North', 4300.2, 58000, 'Residential'),
('Residential South', 3900.5, 52000, 'Residential'),
('Suburban East', 2100.3, 48000, 'Residential'),
('Suburban West', 2400.7, 51000, 'Residential'),
('Industrial Zone', 1800.2, 44000, 'Industrial'),
('Tech Park', 3500.4, 95000, 'Commercial');

-- ====================================
-- 2. STATIONS
-- ====================================
INSERT INTO stations (station_name, zone_id, latitude, longitude, has_elevator, has_escalator, parking_available) VALUES
('Central Station', 1, 40.7580, -73.9855, TRUE, TRUE, TRUE),
('Business Plaza', 2, 40.7614, -73.9776, TRUE, TRUE, FALSE),
('North Park', 3, 40.7829, -73.9654, TRUE, TRUE, TRUE),
('South Gardens', 4, 40.7489, -73.9680, TRUE, FALSE, TRUE),
('East Terminal', 5, 40.7450, -73.9320, TRUE, FALSE, TRUE),
('West Junction', 6, 40.7590, -74.0060, TRUE, TRUE, FALSE),
('Industrial Hub', 7, 40.7320, -73.9950, FALSE, FALSE, TRUE),
('Tech Campus', 8, 40.7690, -73.9550, TRUE, TRUE, FALSE),
('Metro Central', 1, 40.7590, -73.9845, TRUE, TRUE, FALSE),
('Harbor Point', 4, 40.7410, -73.9700, TRUE, FALSE, TRUE),
('University Square', 3, 40.7780, -73.9730, TRUE, TRUE, FALSE),
('Airport Link', 5, 40.7480, -73.9280, TRUE, TRUE, TRUE);

-- ====================================
-- 3. ROUTES
-- ====================================
INSERT INTO routes (route_name, start_station_id, end_station_id, transport_type, max_capacity, wheelchair_accessible, distance_km, base_fare, active) VALUES
('Express 1', 1, 8, 'Metro', 200, TRUE, 8.5, 3.50, TRUE),
('Express 2', 1, 5, 'Metro', 200, TRUE, 12.3, 4.00, TRUE),
('Local A', 3, 4, 'Bus', 60, TRUE, 5.2, 2.00, TRUE),
('Local B', 6, 2, 'Bus', 60, TRUE, 6.8, 2.50, TRUE),
('Rapid 5', 2, 8, 'Metro', 180, TRUE, 7.1, 3.25, TRUE),
('Shuttle X', 7, 1, 'Bus', 40, FALSE, 9.4, 2.75, TRUE),
('Green Line', 3, 11, 'Tram', 120, TRUE, 4.5, 2.25, TRUE),
('Blue Line', 9, 10, 'Metro', 220, TRUE, 6.7, 3.00, TRUE),
('Airport Express', 1, 12, 'Metro', 150, TRUE, 15.8, 5.50, TRUE),
('Campus Connect', 11, 8, 'Bus', 50, TRUE, 3.2, 1.75, TRUE);

-- ====================================
-- 4. SCHEDULES (7 days, multiple times per day)
-- ====================================
DO $$
DECLARE
    r_id INT;
    dow INT;
    hr INT;
    min_val INT;
    duration_mins INT;
BEGIN
    FOR r_id IN 1..10 LOOP
        duration_mins := 25 + (r_id % 10); -- 25-34 minutes travel time
        
        FOR dow IN 0..6 LOOP
            -- Peak morning hours (6-9 AM) - every 15 minutes
            FOR hr IN 6..9 LOOP
                FOR min_val IN 0..45 BY 15 LOOP
                    INSERT INTO schedules (route_id, day_of_week, departure_time, arrival_time, is_peak_hour)
                    VALUES (r_id, dow, 
                            make_time(hr, min_val, 0), 
                            (make_time(hr, min_val, 0) + (duration_mins || ' minutes')::INTERVAL)::TIME,
                            TRUE);
                END LOOP;
            END LOOP;
            
            -- Off-peak (10 AM - 4 PM) - every 30 minutes
            FOR hr IN 10..16 LOOP
                FOR min_val IN 0..30 BY 30 LOOP
                    INSERT INTO schedules (route_id, day_of_week, departure_time, arrival_time, is_peak_hour)
                    VALUES (r_id, dow, 
                            make_time(hr, min_val, 0), 
                            (make_time(hr, min_val, 0) + (duration_mins + 3 || ' minutes')::INTERVAL)::TIME,
                            FALSE);
                END LOOP;
            END LOOP;
            
            -- Evening peak (5-8 PM) - every 15 minutes
            FOR hr IN 17..20 LOOP
                FOR min_val IN 0..45 BY 15 LOOP
                    INSERT INTO schedules (route_id, day_of_week, departure_time, arrival_time, is_peak_hour)
                    VALUES (r_id, dow, 
                            make_time(hr, min_val, 0), 
                            (make_time(hr, min_val, 0) + (duration_mins + 2 || ' minutes')::INTERVAL)::TIME,
                            TRUE);
                END LOOP;
            END LOOP;
        END LOOP;
    END LOOP;
END $$;

-- ====================================
-- 5. FARE CARDS (Anonymous Smart Cards)
-- ====================================
-- Generate 1000 fare cards across different types
INSERT INTO fare_cards (card_number, card_type, issue_date, balance, total_trips, is_active, last_used)
SELECT 
    'CARD_' || LPAD(i::TEXT, 6, '0'),
    CASE 
        WHEN i % 100 < 65 THEN 'Regular'
        WHEN i % 100 < 85 THEN 'Student'
        WHEN i % 100 < 95 THEN 'Senior'
        ELSE 'Accessibility'
    END,
    CURRENT_DATE - (floor(random() * 1825)::INT || ' days')::INTERVAL,
    20.00 + random() * 80,
    0,
    random() > 0.05,
    CURRENT_DATE - (floor(random() * 90)::INT || ' days')::INTERVAL
FROM generate_series(1, 1000) AS i;

-- ====================================
-- 6. TRIPS (90 days of ridership data)
-- ====================================
-- Generate 10,000 realistic trips
INSERT INTO trips (
    card_id, route_id, entry_station_id, exit_station_id,
    tap_in_time, tap_out_time, fare_paid, payment_method,
    trip_date, is_peak_hour
)
SELECT 
    1 + floor(random() * 1000)::INT, -- card_id from 1-1000
    1 + floor(random() * 10)::INT, -- route_id from 1-10
    1 + floor(random() * 12)::INT, -- entry station
    1 + floor(random() * 12)::INT, -- exit station
    trip_date + make_time(hour_val, floor(random() * 60)::INT, 0),
    trip_date + make_time(hour_val, floor(random() * 60)::INT, 0) + '30 minutes'::INTERVAL,
    2.00 + random() * 4, -- fare between $2-$6
    (ARRAY['Card', 'Card', 'Card', 'Mobile', 'Cash'])[1 + floor(random() * 5)::INT],
    trip_date,
    hour_val IN (7,8,9,17,18,19) -- Peak hours
FROM (
    SELECT 
        generate_series(
            CURRENT_DATE - INTERVAL '90 days',
            CURRENT_DATE - INTERVAL '1 day',
            INTERVAL '1 day'
        )::DATE AS trip_date,
        CASE 
            WHEN random() < 0.30 THEN 7 + floor(random() * 3)::INT
            WHEN random() < 0.65 THEN 17 + floor(random() * 3)::INT
            ELSE 10 + floor(random() * 7)::INT
        END AS hour_val
    FROM generate_series(1, 120) -- ~120 trips per day on average
) sub;

-- Update fare card statistics
UPDATE fare_cards fc
SET 
    total_trips = (SELECT COUNT(*) FROM trips WHERE card_id = fc.card_id),
    last_used = (SELECT MAX(trip_date) FROM trips WHERE card_id = fc.card_id)
WHERE EXISTS (SELECT 1 FROM trips WHERE card_id = fc.card_id);

-- ====================================
-- 7. TRAVEL TIME LOGS (Past 90 days)
-- ====================================
DO $$
DECLARE
    r_id INT;
    log_dt DATE;
    base_duration INT;
    weather VARCHAR(20);
    pass_count INT;
    delay INT;
BEGIN
    FOR r_id IN 1..10 LOOP
        base_duration := 25 + (r_id * 2);
        
        FOR log_dt IN SELECT generate_series(
            CURRENT_DATE - INTERVAL '90 days',
            CURRENT_DATE - INTERVAL '1 day',
            INTERVAL '1 day'
        )::DATE LOOP
            
            weather := (ARRAY['Clear', 'Clear', 'Clear', 'Rain', 'Fog'])[1 + floor(random() * 5)::INT];
            pass_count := 150 + floor(random() * 200)::INT;
            delay := CASE 
                WHEN weather = 'Rain' THEN floor(random() * 10)::INT
                WHEN weather = 'Fog' THEN floor(random() * 15)::INT
                ELSE floor(random() * 5)::INT
            END;
            
            -- Peak hour log
            INSERT INTO travel_time_logs (route_id, log_date, avg_travel_time, passenger_count, is_peak_hour, weather_condition, delay_minutes)
            VALUES (r_id, log_dt, base_duration + delay, pass_count + 50, TRUE, weather, delay);
            
            -- Off-peak hour log
            INSERT INTO travel_time_logs (route_id, log_date, avg_travel_time, passenger_count, is_peak_hour, weather_condition, delay_minutes)
            VALUES (r_id, log_dt, base_duration - 3, pass_count - 50, FALSE, weather, floor(delay / 2)::INT);
        END LOOP;
    END LOOP;
END $$;

-- ====================================
-- 8. SERVICE AVAILABILITY (Current status with variety)
-- ====================================
INSERT INTO service_availability (route_id, is_operational, current_capacity, delay_minutes, reason)
SELECT 
    route_id,
    CASE 
        WHEN route_id % 7 = 0 THEN FALSE  -- Out of service
        WHEN route_id % 5 = 0 THEN FALSE  -- Out of service (maintenance)
        WHEN route_id % 3 = 0 THEN TRUE   -- Delayed but operational
        ELSE TRUE                          -- Normal operation
    END,
    CASE 
        WHEN route_id % 7 = 0 THEN 0
        WHEN route_id % 5 = 0 THEN 0
        ELSE floor(max_capacity * (0.6 + random() * 0.4))::INT
    END,
    CASE 
        WHEN route_id % 7 = 0 THEN 0                    -- Out of service
        WHEN route_id % 5 = 0 THEN 0                    -- Out of service
        WHEN route_id % 3 = 0 THEN floor(15 + random() * 30)::INT  -- Delayed (15-45 min)
        ELSE floor(random() * 8)::INT                    -- Minor delays (0-7 min)
    END,
    CASE 
        WHEN route_id % 7 = 0 THEN 'Signal Equipment Failure'
        WHEN route_id % 5 = 0 THEN 'Scheduled Maintenance'
        WHEN route_id % 3 = 0 THEN 
            CASE 
                WHEN random() > 0.5 THEN 'Heavy Traffic Congestion'
                ELSE 'Track Inspection'
            END
        WHEN random() > 0.8 THEN 'Weather Delay'
        ELSE NULL
    END
FROM routes;

-- ====================================
-- SUMMARY
-- ====================================
DO $$
DECLARE
    zone_count INT;
    station_count INT;
    route_count INT;
    card_count INT;
    trip_count INT;
    active_cards INT;
BEGIN
    SELECT COUNT(*) INTO zone_count FROM zones;
    SELECT COUNT(*) INTO station_count FROM stations;
    SELECT COUNT(*) INTO route_count FROM routes;
    SELECT COUNT(*) INTO card_count FROM fare_cards;
    SELECT COUNT(*) INTO trip_count FROM trips;
    SELECT COUNT(*) INTO active_cards FROM fare_cards WHERE is_active = TRUE;
    
    RAISE NOTICE '========================================';
    RAISE NOTICE 'CityPulse Data Load Complete!';
    RAISE NOTICE '========================================';
    RAISE NOTICE 'Zones: %', zone_count;
    RAISE NOTICE 'Stations: %', station_count;
    RAISE NOTICE 'Routes: %', route_count;
    RAISE NOTICE 'Fare Cards Issued: %', card_count;
    RAISE NOTICE 'Active Fare Cards: %', active_cards;
    RAISE NOTICE 'Total Trips (90 days): %', trip_count;
    RAISE NOTICE '========================================';
END $$;
