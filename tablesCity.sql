-- =====================================================
-- CityPulse Transit System - Realistic Schema
-- =====================================================
-- This schema models a real-world public transit system
-- Data is collected through fare card taps, not user registration
-- =====================================================

-- Clean up existing tables
DROP TABLE IF EXISTS trips CASCADE;
DROP TABLE IF EXISTS fare_cards CASCADE;
DROP TABLE IF EXISTS schedules CASCADE;
DROP TABLE IF EXISTS routes CASCADE;
DROP TABLE IF EXISTS stations CASCADE;
DROP TABLE IF EXISTS zones CASCADE;
DROP TABLE IF EXISTS travel_time_logs CASCADE;
DROP TABLE IF EXISTS service_availability CASCADE;

-- =====================================================
-- CORE TABLES
-- =====================================================

-- Zones: Geographic areas with demographic data
CREATE TABLE zones (
    zone_id SERIAL PRIMARY KEY,
    zone_name VARCHAR(50) NOT NULL,
    population_density FLOAT,
    avg_income FLOAT,
    area_type VARCHAR(20) -- Residential, Commercial, Industrial
);

-- Stations: Transit stops/stations
CREATE TABLE stations (
    station_id SERIAL PRIMARY KEY,
    station_name VARCHAR(100) NOT NULL UNIQUE,
    zone_id INTEGER REFERENCES zones(zone_id),
    latitude DECIMAL(10, 6),
    longitude DECIMAL(10, 6),
    has_elevator BOOLEAN DEFAULT FALSE,
    has_escalator BOOLEAN DEFAULT FALSE,
    parking_available BOOLEAN DEFAULT FALSE
);

-- Routes: Transit lines connecting stations
CREATE TABLE routes (
    route_id SERIAL PRIMARY KEY,
    route_name VARCHAR(50) NOT NULL,
    transport_type VARCHAR(20) NOT NULL, -- Bus, Metro, Tram
    start_station_id INTEGER REFERENCES stations(station_id),
    end_station_id INTEGER REFERENCES stations(station_id),
    distance_km DECIMAL(5, 2),
    base_fare DECIMAL(10, 2),
    wheelchair_accessible BOOLEAN DEFAULT TRUE,
    max_capacity INTEGER,
    active BOOLEAN DEFAULT TRUE
);

-- Schedules: Route timetables
CREATE TABLE schedules (
    schedule_id SERIAL PRIMARY KEY,
    route_id INTEGER REFERENCES routes(route_id),
    day_of_week VARCHAR(10),
    departure_time TIME,
    arrival_time TIME,
    is_peak_hour BOOLEAN DEFAULT FALSE
);

-- =====================================================
-- FARE CARD & TRIP TRACKING (Realistic Data Collection)
-- =====================================================

-- Fare Cards: Anonymous smart cards issued to commuters
CREATE TABLE fare_cards (
    card_id SERIAL PRIMARY KEY,
    card_number VARCHAR(20) UNIQUE NOT NULL, -- CARD_000001, CARD_000002, etc.
    card_type VARCHAR(20) NOT NULL, -- Regular, Student, Senior, Accessibility
    issue_date DATE NOT NULL DEFAULT CURRENT_DATE,
    last_used DATE,
    balance DECIMAL(10, 2) DEFAULT 0.00,
    total_trips INTEGER DEFAULT 0,
    is_active BOOLEAN DEFAULT TRUE
);

-- Trips: Individual ride records from fare card taps
CREATE TABLE trips (
    trip_id SERIAL PRIMARY KEY,
    card_id INTEGER REFERENCES fare_cards(card_id),
    route_id INTEGER REFERENCES routes(route_id),
    entry_station_id INTEGER REFERENCES stations(station_id),
    exit_station_id INTEGER REFERENCES stations(station_id),
    tap_in_time TIMESTAMP NOT NULL,
    tap_out_time TIMESTAMP,
    fare_paid DECIMAL(10, 2),
    payment_method VARCHAR(20), -- Card, Cash, Mobile
    trip_date DATE NOT NULL,
    is_peak_hour BOOLEAN DEFAULT FALSE
);

-- =====================================================
-- OPERATIONAL DATA
-- =====================================================

-- Travel Time Logs: Historical performance data
CREATE TABLE travel_time_logs (
    log_id SERIAL PRIMARY KEY,
    route_id INTEGER REFERENCES routes(route_id),
    log_date DATE NOT NULL,
    avg_travel_time DECIMAL(5, 2),
    passenger_count INTEGER,
    is_peak_hour BOOLEAN DEFAULT FALSE,
    weather_condition VARCHAR(20),
    delay_minutes INTEGER DEFAULT 0
);

-- Service Availability: Real-time service status
CREATE TABLE service_availability (
    availability_id SERIAL PRIMARY KEY,
    route_id INTEGER REFERENCES routes(route_id),
    check_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_operational BOOLEAN DEFAULT TRUE,
    current_capacity INTEGER,
    delay_minutes INTEGER DEFAULT 0,
    reason VARCHAR(100)
);

-- =====================================================
-- INDEXES FOR PERFORMANCE
-- =====================================================

CREATE INDEX idx_trips_card_id ON trips(card_id);
CREATE INDEX idx_trips_route_id ON trips(route_id);
CREATE INDEX idx_trips_date ON trips(trip_date);
CREATE INDEX idx_trips_tap_in ON trips(tap_in_time);
CREATE INDEX idx_fare_cards_type ON fare_cards(card_type);
CREATE INDEX idx_fare_cards_active ON fare_cards(is_active);
CREATE INDEX idx_travel_logs_route ON travel_time_logs(route_id);
CREATE INDEX idx_travel_logs_date ON travel_time_logs(log_date);
CREATE INDEX idx_service_route ON service_availability(route_id);

-- =====================================================
-- VIEWS FOR ANALYTICS
-- =====================================================

-- Daily Ridership Summary
CREATE VIEW daily_ridership AS
SELECT 
    trip_date,
    COUNT(*) as total_trips,
    COUNT(DISTINCT card_id) as unique_riders,
    SUM(fare_paid) as total_revenue,
    AVG(fare_paid) as avg_fare
FROM trips
GROUP BY trip_date
ORDER BY trip_date DESC;

-- Route Performance
CREATE VIEW route_performance AS
SELECT 
    r.route_id,
    r.route_name,
    r.transport_type,
    COUNT(t.trip_id) as total_trips,
    SUM(t.fare_paid) as total_revenue,
    AVG(t.fare_paid) as avg_fare,
    COUNT(DISTINCT t.card_id) as unique_riders
FROM routes r
LEFT JOIN trips t ON r.route_id = t.route_id
GROUP BY r.route_id, r.route_name, r.transport_type;

-- Card Type Usage
CREATE VIEW card_type_usage AS
SELECT 
    fc.card_type,
    COUNT(DISTINCT fc.card_id) as total_cards,
    COUNT(t.trip_id) as total_trips,
    SUM(t.fare_paid) as total_revenue
FROM fare_cards fc
LEFT JOIN trips t ON fc.card_id = t.card_id
GROUP BY fc.card_type;

-- Peak Hour Analysis
CREATE VIEW peak_hour_analysis AS
SELECT 
    EXTRACT(HOUR FROM tap_in_time) as hour,
    COUNT(*) as trip_count,
    AVG(fare_paid) as avg_fare,
    COUNT(DISTINCT card_id) as unique_riders
FROM trips
GROUP BY EXTRACT(HOUR FROM tap_in_time)
ORDER BY hour;

-- =====================================================
-- COMMENTS FOR DOCUMENTATION
-- =====================================================

COMMENT ON TABLE fare_cards IS 'Anonymous smart cards issued to transit riders - no personal information stored';
COMMENT ON TABLE trips IS 'Individual ride records captured from fare card taps at entry/exit points';
COMMENT ON TABLE routes IS 'Transit routes connecting different stations in the network';
COMMENT ON TABLE stations IS 'Physical transit stops/stations with accessibility features';
COMMENT ON TABLE zones IS 'Geographic zones with demographic information for planning';
COMMENT ON TABLE travel_time_logs IS 'Historical performance data for route analysis';