-- CREATING AND CONNECTING TO DATABASE

postgres=# CREATE DATABASE citypulse;
CREATE DATABASE

postgres=# \c citypulse
You are now connected to database "citypulse" as user "postgres".

-- CREATING TABLES

-- TRANSPORT ROUTES

citypulse=# CREATE TABLE transport_routes (
citypulse(#     route_id SERIAL PRIMARY KEY,
citypulse(#     route_name VARCHAR(50),
citypulse(#     transport_type VARCHAR(20),
citypulse(#     max_capacity INT
citypulse(# );
CREATE TABLE

-- PASSENGER LOGS

citypulse=# CREATE TABLE passenger_logs (
citypulse(#     log_id SERIAL PRIMARY KEY,
citypulse(#     route_id INT,
citypulse(#     timestamp TIMESTAMP,
citypulse(#     station_name VARCHAR(50),
citypulse(#     zone_id INT,
citypulse(#     passenger_count INT,
citypulse(#     FOREIGN KEY (route_id) REFERENCES transport_routes(route_id)
citypulse(# );
CREATE TABLE

-- ZONE METADATA

citypulse=# CREATE TABLE zone_metadata (
citypulse(#     zone_id SERIAL PRIMARY KEY,
citypulse(#     zone_name VARCHAR(50),
citypulse(#     population_density FLOAT,
citypulse(#     avg_income FLOAT
citypulse(# );
CREATE TABLE

-- USERS TABLE

citypulse=# CREATE TABLE users (
citypulse(#     user_id SERIAL PRIMARY KEY,
citypulse(#     name VARCHAR(50),
citypulse(#     email VARCHAR(100) UNIQUE
citypulse(# );
CREATE TABLE

-- BOOKINGS

citypulse=# CREATE TABLE bookings (
citypulse(#     booking_id SERIAL PRIMARY KEY,
citypulse(#     user_id INT,
citypulse(#     route_id INT,
citypulse(#     timestamp TIMESTAMP,
citypulse(#     FOREIGN KEY (user_id) REFERENCES users(user_id),
citypulse(#     FOREIGN KEY (route_id) REFERENCES transport_routes(route_id)
citypulse(# );
CREATE TABLE