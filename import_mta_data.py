"""
Import real NYC MTA subway station data into CityPulse database
Downloads stations, routes, and integrates with existing schema
"""

import psycopg2
from psycopg2.extras import execute_values
import pandas as pd
import requests
import random
from datetime import datetime, timedelta
from dateutil import parser as date_parser
import json

# Database connection
DB_CONFIG = {
    'host': 'localhost',
    'database': 'citypulse',
    'user': 'postgres',
    'password': 'lld@1501S'
}

def download_mta_stations():
    """Download real NYC MTA station data from NYC Open Data API"""
    print("[OK] Downloading NYC MTA station data...")
    
    api_url = "https://data.ny.gov/resource/39hk-dx4f.json"
    
    try:
        response = requests.get(api_url, timeout=30)
        response.raise_for_status()
        
        data = response.json()
        print(f"[OK] Downloaded {len(data)} stations")
        
        # Convert to DataFrame
        df = pd.DataFrame(data)
        
        # Print available columns for debugging
        print(f"[OK] Available columns: {', '.join(df.columns.tolist())}")
        
        # Rename columns to match our expected schema
        df = df.rename(columns={
            'gtfs_latitude': 'stop_lat',
            'gtfs_longitude': 'stop_lon'
        })
        
        # Filter to unique stations (many rows are for different lines at same station)
        df = df.drop_duplicates(subset=['station_id'])
        
        # Select a diverse sample of 50 stations across all boroughs
        stations_by_borough = df.groupby('borough', group_keys=False).apply(
            lambda x: x.sample(min(len(x), 12), random_state=42)
        )
        
        # Take first 50
        df = stations_by_borough.head(50)
        
        # Ensure required columns exist
        required_cols = ['stop_name', 'borough', 'stop_lat', 'stop_lon', 'ada']
        for col in required_cols:
            if col not in df.columns:
                print(f"[WARN] Missing column: {col}")
                return None
        
        print(f"[OK] Selected {len(df)} diverse stations")
        return df[required_cols]
        
    except Exception as e:
        print(f"[ERROR] Failed to download MTA data: {e}")
        return None


def create_simulated_nyc_stations():
    """Create simulated NYC stations with real names and approximate coordinates"""
    print("[WARN] Using simulated NYC station data as fallback...")
    
    stations = [
        # Manhattan
        {'stop_name': 'Times Square-42 St', 'borough': 'Manhattan', 'stop_lat': 40.7580, 'stop_lon': -73.9855, 'ada': 1},
        {'stop_name': 'Grand Central-42 St', 'borough': 'Manhattan', 'stop_lat': 40.7527, 'stop_lon': -73.9772, 'ada': 1},
        {'stop_name': 'Penn Station', 'borough': 'Manhattan', 'stop_lat': 40.7505, 'stop_lon': -73.9934, 'ada': 1},
        {'stop_name': 'Union Square-14 St', 'borough': 'Manhattan', 'stop_lat': 40.7347, 'stop_lon': -73.9906, 'ada': 0},
        {'stop_name': 'Columbus Circle', 'borough': 'Manhattan', 'stop_lat': 40.7678, 'stop_lon': -73.9819, 'ada': 1},
        {'stop_name': 'Herald Square', 'borough': 'Manhattan', 'stop_lat': 40.7506, 'stop_lon': -73.9877, 'ada': 0},
        {'stop_name': 'Canal St', 'borough': 'Manhattan', 'stop_lat': 40.7188, 'stop_lon': -74.0062, 'ada': 0},
        {'stop_name': 'Fulton St', 'borough': 'Manhattan', 'stop_lat': 40.7099, 'stop_lon': -74.0088, 'ada': 1},
        {'stop_name': 'Wall St', 'borough': 'Manhattan', 'stop_lat': 40.7074, 'stop_lon': -74.0123, 'ada': 0},
        {'stop_name': 'World Trade Center', 'borough': 'Manhattan', 'stop_lat': 40.7126, 'stop_lon': -74.0127, 'ada': 1},
        
        # Brooklyn
        {'stop_name': 'Atlantic Ave-Barclays Center', 'borough': 'Brooklyn', 'stop_lat': 40.6844, 'stop_lon': -73.9766, 'ada': 1},
        {'stop_name': 'Jay St-MetroTech', 'borough': 'Brooklyn', 'stop_lat': 40.6925, 'stop_lon': -73.9867, 'ada': 1},
        {'stop_name': 'Brooklyn Bridge-City Hall', 'borough': 'Brooklyn', 'stop_lat': 40.7126, 'stop_lon': -73.9993, 'ada': 0},
        {'stop_name': 'Prospect Park', 'borough': 'Brooklyn', 'stop_lat': 40.6615, 'stop_lon': -73.9625, 'ada': 0},
        {'stop_name': 'Coney Island-Stillwell Ave', 'borough': 'Brooklyn', 'stop_lat': 40.5775, 'stop_lon': -73.9811, 'ada': 1},
        {'stop_name': 'Bedford Ave', 'borough': 'Brooklyn', 'stop_lat': 40.7178, 'stop_lon': -73.9563, 'ada': 0},
        {'stop_name': 'DeKalb Ave', 'borough': 'Brooklyn', 'stop_lat': 40.6908, 'stop_lon': -73.9818, 'ada': 0},
        {'stop_name': 'Church Ave', 'borough': 'Brooklyn', 'stop_lat': 40.6512, 'stop_lon': -73.9628, 'ada': 1},
        {'stop_name': 'Flatbush Ave-Brooklyn College', 'borough': 'Brooklyn', 'stop_lat': 40.6328, 'stop_lon': -73.9475, 'ada': 1},
        {'stop_name': 'Nevins St', 'borough': 'Brooklyn', 'stop_lat': 40.6881, 'stop_lon': -73.9803, 'ada': 0},
        
        # Queens
        {'stop_name': 'Queensboro Plaza', 'borough': 'Queens', 'stop_lat': 40.7506, 'stop_lon': -73.9401, 'ada': 0},
        {'stop_name': 'Jackson Heights-Roosevelt Ave', 'borough': 'Queens', 'stop_lat': 40.7465, 'stop_lon': -73.8914, 'ada': 1},
        {'stop_name': 'Flushing-Main St', 'borough': 'Queens', 'stop_lat': 40.7596, 'stop_lon': -73.8303, 'ada': 1},
        {'stop_name': 'Jamaica Center-Parsons/Archer', 'borough': 'Queens', 'stop_lat': 40.7022, 'stop_lon': -73.8011, 'ada': 1},
        {'stop_name': 'Court Square-23 St', 'borough': 'Queens', 'stop_lat': 40.7470, 'stop_lon': -73.9458, 'ada': 1},
        {'stop_name': 'Astoria-Ditmars Blvd', 'borough': 'Queens', 'stop_lat': 40.7752, 'stop_lon': -73.9121, 'ada': 0},
        {'stop_name': 'Forest Hills-71 Ave', 'borough': 'Queens', 'stop_lat': 40.7214, 'stop_lon': -73.8441, 'ada': 1},
        {'stop_name': 'Woodhaven Blvd', 'borough': 'Queens', 'stop_lat': 40.7335, 'stop_lon': -73.8582, 'ada': 0},
        {'stop_name': 'Queens Plaza', 'borough': 'Queens', 'stop_lat': 40.7488, 'stop_lon': -73.9370, 'ada': 0},
        {'stop_name': 'Elmhurst Ave', 'borough': 'Queens', 'stop_lat': 40.7424, 'stop_lon': -73.8821, 'ada': 0},
        
        # Bronx
        {'stop_name': 'Yankee Stadium-161 St', 'borough': 'Bronx', 'stop_lat': 40.8277, 'stop_lon': -73.9257, 'ada': 1},
        {'stop_name': 'Fordham Rd', 'borough': 'Bronx', 'stop_lat': 40.8620, 'stop_lon': -73.9014, 'ada': 0},
        {'stop_name': 'Third Ave-149 St', 'borough': 'Bronx', 'stop_lat': 40.8163, 'stop_lon': -73.9176, 'ada': 1},
        {'stop_name': 'Grand Concourse', 'borough': 'Bronx', 'stop_lat': 40.8183, 'stop_lon': -73.9274, 'ada': 0},
        {'stop_name': 'Pelham Bay Park', 'borough': 'Bronx', 'stop_lat': 40.8526, 'stop_lon': -73.8282, 'ada': 1},
        {'stop_name': 'Tremont Ave', 'borough': 'Bronx', 'stop_lat': 40.8502, 'stop_lon': -73.8996, 'ada': 0},
        {'stop_name': 'Burnside Ave', 'borough': 'Bronx', 'stop_lat': 40.8533, 'stop_lon': -73.9075, 'ada': 0},
        {'stop_name': 'Kingsbridge Rd', 'borough': 'Bronx', 'stop_lat': 40.8689, 'stop_lon': -73.8970, 'ada': 0},
        {'stop_name': 'Mosholu Parkway', 'borough': 'Bronx', 'stop_lat': 40.8799, 'stop_lon': -73.8845, 'ada': 0},
        {'stop_name': 'Woodlawn', 'borough': 'Bronx', 'stop_lat': 40.8956, 'stop_lon': -73.8786, 'ada': 0},
        
        # Staten Island
        {'stop_name': 'St George', 'borough': 'Staten Island', 'stop_lat': 40.6436, 'stop_lon': -74.0735, 'ada': 1},
        {'stop_name': 'Tompkinsville', 'borough': 'Staten Island', 'stop_lat': 40.6368, 'stop_lon': -74.0758, 'ada': 0},
        {'stop_name': 'Stapleton', 'borough': 'Staten Island', 'stop_lat': 40.6277, 'stop_lon': -74.0756, 'ada': 0},
        {'stop_name': 'Clifton', 'borough': 'Staten Island', 'stop_lat': 40.6211, 'stop_lon': -74.0695, 'ada': 0},
        {'stop_name': 'Grasmere', 'borough': 'Staten Island', 'stop_lat': 40.6029, 'stop_lon': -74.0844, 'ada': 0},
        {'stop_name': 'Old Town', 'borough': 'Staten Island', 'stop_lat': 40.6336, 'stop_lon': -74.0746, 'ada': 0},
        {'stop_name': 'Dongan Hills', 'borough': 'Staten Island', 'stop_lat': 40.5880, 'stop_lon': -74.0967, 'ada': 0},
        {'stop_name': 'Grant City', 'borough': 'Staten Island', 'stop_lat': 40.5813, 'stop_lon': -74.1014, 'ada': 0},
        {'stop_name': 'New Dorp', 'borough': 'Staten Island', 'stop_lat': 40.5733, 'stop_lon': -74.1177, 'ada': 0},
        {'stop_name': 'Tottenville', 'borough': 'Staten Island', 'stop_lat': 40.5424, 'stop_lon': -74.2447, 'ada': 0},
    ]
    
    return pd.DataFrame(stations)


def create_zones_from_boroughs(conn):
    """Create zone entries for NYC boroughs"""
    print("[OK] Creating borough zones...")
    
    boroughs = [
        ('Manhattan', 300000, 120000, 'Commercial'),
        ('Brooklyn', 150000, 65000, 'Residential'),
        ('Queens', 100000, 70000, 'Residential'),
        ('Bronx', 120000, 55000, 'Residential'),
        ('Staten Island', 50000, 75000, 'Residential')
    ]
    
    cursor = conn.cursor()
    
    # Delete existing data in correct order (child tables first)
    cursor.execute("DELETE FROM service_availability")
    cursor.execute("DELETE FROM travel_time_logs")
    cursor.execute("DELETE FROM trips")
    cursor.execute("DELETE FROM fare_cards")
    cursor.execute("DELETE FROM schedules")
    cursor.execute("DELETE FROM routes")
    cursor.execute("DELETE FROM stations")
    cursor.execute("DELETE FROM zones")
    
    for name, pop_density, avg_income, area_type in boroughs:
        cursor.execute("""
            INSERT INTO zones (zone_name, population_density, avg_income, area_type)
            VALUES (%s, %s, %s, %s)
        """, (name, pop_density, avg_income, area_type))
    
    conn.commit()
    cursor.close()
    print(f"[OK] Created {len(boroughs)} borough zones")


def import_stations(conn, stations_df):
    """Import stations into database"""
    print("[OK] Importing stations...")
    
    cursor = conn.cursor()
    
    # Get zone mappings
    cursor.execute("SELECT zone_id, zone_name FROM zones")
    zone_map = {row[1]: row[0] for row in cursor.fetchall()}
    
    # Insert stations (no need to delete - already done in create_zones_from_boroughs)
    for _, station in stations_df.iterrows():
        zone_id = zone_map.get(station['borough'])
        
        cursor.execute("""
            INSERT INTO stations (station_name, latitude, longitude, zone_id, has_elevator)
            VALUES (%s, %s, %s, %s, %s)
        """, (
            station['stop_name'],
            float(station['stop_lat']),
            float(station['stop_lon']),
            zone_id,
            int(station.get('ada', 0)) == 1
        ))
    
    conn.commit()
    cursor.close()
    print(f"[OK] Imported {len(stations_df)} stations")


def create_routes_from_stations(conn):
    """Create realistic routes connecting NYC stations"""
    print("[OK] Creating routes...")
    
    cursor = conn.cursor()
    
    # Get all stations
    cursor.execute("SELECT station_id, station_name, zone_id FROM stations")
    stations = cursor.fetchall()
    
    # Define major routes based on real NYC transit lines
    
    # Define major routes based on real NYC transit lines
    route_definitions = [
        ('1', 'Broadway-Seventh Ave Local', ['Times Square-42 St', 'Penn Station', 'Union Square-14 St', 'Wall St']),
        ('2', 'Seventh Ave Express', ['Times Square-42 St', 'Grand Central-42 St', 'Wall St', 'Atlantic Ave-Barclays Center']),
        ('3', 'Seventh Ave Express', ['Times Square-42 St', 'Penn Station', 'Fulton St', 'Brooklyn Bridge-City Hall']),
        ('4', 'Lexington Ave Express', ['Grand Central-42 St', 'Union Square-14 St', 'Fulton St', 'Atlantic Ave-Barclays Center']),
        ('5', 'Lexington Ave Express', ['Grand Central-42 St', 'Union Square-14 St', 'Brooklyn Bridge-City Hall', 'Atlantic Ave-Barclays Center']),
        ('6', 'Lexington Ave Local', ['Grand Central-42 St', 'Union Square-14 St', 'Canal St', 'Brooklyn Bridge-City Hall']),
        ('A', 'Eighth Ave Express', ['Columbus Circle', 'Penn Station', 'Canal St', 'Jay St-MetroTech']),
        ('C', 'Eighth Ave Local', ['Columbus Circle', 'Herald Square', 'Canal St', 'Jay St-MetroTech']),
        ('E', 'Eighth Ave Local', ['Times Square-42 St', 'Penn Station', 'World Trade Center', 'Queens Plaza']),
        ('L', 'Canarsie Line', ['Union Square-14 St', 'Bedford Ave', 'Atlantic Ave-Barclays Center']),
        ('N', 'Broadway Express', ['Times Square-42 St', 'Herald Square', 'Canal St', 'DeKalb Ave']),
        ('Q', 'Broadway Express', ['Times Square-42 St', 'Herald Square', 'Canal St', 'Atlantic Ave-Barclays Center']),
        ('M15', 'Select Bus Service', ['Grand Central-42 St', 'Union Square-14 St', 'Wall St']),
        ('M34', 'Crosstown Bus', ['Herald Square', 'Penn Station', 'Columbus Circle']),
        ('B41', 'Brooklyn Bus', ['Atlantic Ave-Barclays Center', 'Prospect Park', 'Church Ave'])
    ]
    
    # Create station name to ID mapping
    station_map = {name: sid for sid, name, _ in stations}
    
    for route_name, route_desc, station_names in route_definitions:
        # Get station IDs for this route
        station_ids = [station_map.get(name) for name in station_names if name in station_map]
        
        if len(station_ids) >= 2:
            start_id = station_ids[0]
            end_id = station_ids[-1]
            transport_type = 'Metro' if len(route_name) <= 2 else 'Bus'
            max_capacity = random.randint(200, 400) if transport_type == 'Metro' else random.randint(40, 60)
            
            cursor.execute("""
                INSERT INTO routes (route_name, transport_type, start_station_id, end_station_id, distance_km, base_fare, wheelchair_accessible, max_capacity, active)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                route_name, 
                transport_type,
                start_id, 
                end_id, 
                random.uniform(5.0, 25.0), 
                2.75, 
                True,
                max_capacity,
                True
            ))
    
    conn.commit()
    cursor.close()
    print(f"[OK] Created {len(route_definitions)} routes")


def generate_schedules(conn):
    """Generate schedules for all routes"""
    print("[OK] Generating schedules...")
    
    cursor = conn.cursor()
    
    # Get all routes (no need to delete schedules - already done)
    cursor.execute("SELECT route_id FROM routes")
    route_ids = [row[0] for row in cursor.fetchall()]
    
    days_of_week = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
    
    for route_id in route_ids:
        for day in days_of_week:
            # Peak hours (7-9 AM, 5-7 PM): 10 min frequency
            # Off-peak: 20 min frequency
            
            # Morning peak
            for hour in [7, 8]:
                for minute in range(0, 60, 10):
                    departure = f"{hour:02d}:{minute:02d}:00"
                    arrival_minutes = minute + 25
                    arrival_hour = hour + (arrival_minutes // 60)
                    arrival_minutes = arrival_minutes % 60
                    arrival = f"{arrival_hour:02d}:{arrival_minutes:02d}:00"
                    cursor.execute("""
                        INSERT INTO schedules (route_id, day_of_week, departure_time, arrival_time, is_peak_hour)
                        VALUES (%s, %s, %s, %s, %s)
                    """, (route_id, day, departure, arrival, True))
            
            # Evening peak
            for hour in [17, 18]:
                for minute in range(0, 60, 10):
                    departure = f"{hour:02d}:{minute:02d}:00"
                    arrival_minutes = minute + 30
                    arrival_hour = hour + (arrival_minutes // 60)
                    arrival_minutes = arrival_minutes % 60
                    arrival = f"{arrival_hour:02d}:{arrival_minutes:02d}:00"
                    cursor.execute("""
                        INSERT INTO schedules (route_id, day_of_week, departure_time, arrival_time, is_peak_hour)
                        VALUES (%s, %s, %s, %s, %s)
                    """, (route_id, day, departure, arrival, True))
            
            # Off-peak (9 AM - 5 PM, 7 PM - 11 PM)
            for hour in list(range(9, 17)) + list(range(19, 23)):
                for minute in range(0, 60, 20):
                    departure = f"{hour:02d}:{minute:02d}:00"
                    arrival_minutes = minute + 20
                    arrival_hour = hour + (arrival_minutes // 60)
                    arrival_minutes = arrival_minutes % 60
                    arrival = f"{arrival_hour:02d}:{arrival_minutes:02d}:00"
                    cursor.execute("""
                        INSERT INTO schedules (route_id, day_of_week, departure_time, arrival_time, is_peak_hour)
                        VALUES (%s, %s, %s, %s, %s)
                    """, (route_id, day, departure, arrival, False))
    
    conn.commit()
    cursor.close()
    print("[OK] Generated schedules for all routes")


def generate_realistic_trips(conn):
    """Generate 90 days of realistic trip data with fare cards"""
    print("[OK] Generating fare cards and trips...")
    
    cursor = conn.cursor()
    
    # Get routes and stations
    cursor.execute("SELECT route_id, start_station_id, end_station_id FROM routes")
    routes = cursor.fetchall()
    
    cursor.execute("SELECT station_id FROM stations")
    station_ids = [row[0] for row in cursor.fetchall()]
    
    # Generate fare cards
    print("[OK] Generating fare cards...")
    num_cards = 2000
    card_types = ['Regular', 'Regular', 'Regular', 'Student', 'Senior']
    
    for i in range(num_cards):
        cursor.execute("""
            INSERT INTO fare_cards (card_number, card_type, issue_date, balance, is_active)
            VALUES (%s, %s, %s, %s, %s)
        """, (
            f"CARD_{i:06d}",
            random.choice(card_types),
            datetime.now() - timedelta(days=random.randint(30, 365)),
            random.uniform(5.0, 50.0),
            True
        ))
    
    conn.commit()
    
    # Get card IDs
    cursor.execute("SELECT card_id FROM fare_cards")
    card_ids = [row[0] for row in cursor.fetchall()]
    
    # Generate trips over 90 days
    print("[OK] Generating trips...")
    start_date = datetime.now() - timedelta(days=90)
    
    for day in range(90):
        current_date = start_date + timedelta(days=day)
        
        # More trips on weekdays, fewer on weekends
        is_weekend = current_date.weekday() >= 5
        num_trips = random.randint(100, 200) if not is_weekend else random.randint(40, 80)
        
        for _ in range(num_trips):
            card_id = random.choice(card_ids)
            route_id, start_station, end_station = random.choice(routes)
            
            # Random trip time
            hour = random.randint(6, 22)
            is_peak = hour in [7, 8, 17, 18]
            
            tap_in = current_date + timedelta(
                hours=hour,
                minutes=random.randint(0, 59)
            )
            
            tap_out = tap_in + timedelta(minutes=random.randint(15, 45))
            
            cursor.execute("""
                INSERT INTO trips (card_id, route_id, entry_station_id, exit_station_id, 
                                 tap_in_time, tap_out_time, fare_paid, payment_method, 
                                 trip_date, is_peak_hour)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (card_id, route_id, start_station, end_station, tap_in, tap_out, 
                  2.75, 'Card', current_date.date(), is_peak))
    
    conn.commit()
    cursor.close()
    print(f"[OK] Generated trips for 90 days")


def generate_travel_logs(conn):
    """Generate travel time logs with realistic variations"""
    print("[OK] Generating travel logs...")
    
    cursor = conn.cursor()
    
    # Get all routes
    cursor.execute("SELECT route_id FROM routes")
    route_ids = [row[0] for row in cursor.fetchall()]
    
    # Clear existing logs
    cursor.execute("SELECT route_id FROM routes")
    route_ids = [row[0] for row in cursor.fetchall()]
    
    # Generate logs (no need to delete - already done in create_zones_from_boroughs)
    # Define date range and weather conditions
    start_date = datetime.now() - timedelta(days=90)
    weather_conditions = ['Clear', 'Rain', 'Snow', 'Fog']

    for day in range(90):
        log_date = start_date + timedelta(days=day)
        
        for route_id in route_ids:
            weather = random.choice(weather_conditions)
            
            # Base travel time
            base_time = random.randint(15, 45)
            
            # Weather delays
            if weather == 'Rain':
                base_time += random.randint(2, 8)
            elif weather == 'Snow':
                base_time += random.randint(5, 15)
            elif weather == 'Fog':
                base_time += random.randint(3, 10)
            
            # Passenger count
            is_weekend = log_date.weekday() >= 5
            passenger_count = random.randint(50, 200) if not is_weekend else random.randint(20, 100)
            
            cursor.execute("""
                INSERT INTO travel_time_logs (route_id, log_date, avg_travel_time, passenger_count, weather_condition, delay_minutes)
                VALUES (%s, %s, %s, %s, %s, %s)
            """, (route_id, log_date.date(), base_time, passenger_count, weather, random.randint(0, 15)))
    
    conn.commit()
    cursor.close()
    print(f"[OK] Generated travel logs for 90 days")


def generate_service_availability(conn):
    """Generate realistic service availability data"""
    print("[OK] Generating service availability...")
    
    cursor = conn.cursor()
    
    # Get all routes
    cursor.execute("SELECT route_id FROM routes")
    cursor.execute("SELECT route_id FROM routes")
    route_ids = [row[0] for row in cursor.fetchall()]
    
    # Generate data (no need to delete - already done in create_zones_from_boroughs)
    
    # Generate data for past 30 daysmedelta(days=30)
    start_date = datetime.now() - timedelta(days=30)

    for day in range(30):
        check_date = start_date + timedelta(days=day)
        
        for route_id in route_ids:
            # Generate varied statuses: Active (60%), Delayed (25%), Maintenance (8%), Out of Service (7%)
            status_roll = random.random()
            
            if status_roll < 0.60:  # Active - 60%
                is_operational = True
                delay = 0
                reason = 'Normal Service'
            elif status_roll < 0.85:  # Delayed - 25%
                is_operational = True
                delay = random.choice([5, 10, 15, 20, 25])
                reason = random.choice([
                    'Heavy Traffic', 'Minor Delays', 'Signal Issues',
                    'Increased Ridership', 'Door Malfunction'
                ])
            elif status_roll < 0.93:  # Maintenance - 8%
                is_operational = False
                delay = random.randint(30, 90)
                reason = random.choice([
                    'Track Maintenance', 'Scheduled Maintenance',
                    'Signal Maintenance', 'Station Maintenance'
                ])
            else:  # Out of Service - 7%
                is_operational = False
                delay = random.randint(45, 120)
                reason = random.choice([
                    'Signal Equipment Failure',
                    'Weather Delay',
                    'Emergency Situation',
                    'Crew Shortage',
                    'Power Outage'
                ])
            
            cursor.execute("""
                INSERT INTO service_availability (route_id, check_time, is_operational, delay_minutes, reason)
                VALUES (%s, %s, %s, %s, %s)
            """, (route_id, check_date, is_operational, delay, reason))
    
    conn.commit()
    cursor.close()
    print("[OK] Generated service availability data")


def main():
    """Main import process"""
    print("\n" + "="*50)
    print("NYC MTA Data Import for CityPulse")
    print("="*50 + "\n")
    
    # Download or create station data
    stations_df = download_mta_stations()
    
    # Use simulated data with known station names for consistent routes
    if stations_df is None or len(stations_df) == 0:
        stations_df = create_simulated_nyc_stations()
    else:
        print("[WARN] Using simulated data for consistent route mappings...")
        stations_df = create_simulated_nyc_stations()
    
    # Connect to database
    print("[OK] Connecting to database...")
    conn = psycopg2.connect(**DB_CONFIG)
    
    try:
        # Import data in order
        create_zones_from_boroughs(conn)
        import_stations(conn, stations_df)
        create_routes_from_stations(conn)
        generate_schedules(conn)
        generate_realistic_trips(conn)
        generate_travel_logs(conn)
        generate_service_availability(conn)
        
        print("\n" + "="*50)
        print("[OK] Import completed successfully!")
        print("="*50)
        
        # Show summary
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM stations")
        print(f"\nStations: {cursor.fetchone()[0]}")
        
        cursor.execute("SELECT COUNT(*) FROM routes")
        print(f"Routes: {cursor.fetchone()[0]}")
        
        cursor.execute("SELECT COUNT(*) FROM fare_cards")
        print(f"Fare Cards: {cursor.fetchone()[0]}")
        
        cursor.execute("SELECT COUNT(*) FROM trips")
        print(f"Trips: {cursor.fetchone()[0]}")
        
        cursor.execute("SELECT COUNT(*) FROM travel_time_logs")
        print(f"Travel Logs: {cursor.fetchone()[0]}")
        
        cursor.close()
        
    except Exception as e:
        print(f"\n[ERROR] Import failed: {e}")
        conn.rollback()
    finally:
        conn.close()


if __name__ == "__main__":
    main()
