"""
Tableau Export Utility
Generates comprehensive CSV exports optimized for Tableau visualization
"""

import pandas as pd
from db_manager import DatabaseManager
from datetime import datetime
import os


def generate_tableau_export(output_dir: str = "tableau_exports"):
    """
    Generate multiple CSV files optimized for Tableau dashboards
    
    Args:
        output_dir: Directory to save exported CSV files
    """
    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)
    
    db = DatabaseManager()
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    print("=" * 60)
    print("CityPulse - Tableau Data Export")
    print("=" * 60)
    
    # ====================================
    # 1. Main Route Performance Export
    # ====================================
    print("\n📊 Exporting main route performance data...")
    
    main_export_path = os.path.join(output_dir, f"route_performance_{timestamp}.csv")
    db.export_for_tableau(main_export_path)
    
    # ====================================
    # 2. Route Summary Export
    # ====================================
    print("\n📈 Exporting route summary data...")
    
    routes_query = """
        SELECT 
            r.route_id,
            r.route_name,
            r.transport_type,
            s1.station_name as start_station,
            s2.station_name as end_station,
            z1.zone_name as start_zone,
            z2.zone_name as end_zone,
            r.distance_km,
            r.base_fare,
            r.max_capacity,
            r.wheelchair_accessible,
            COUNT(DISTINCT ttl.log_date) as days_with_data,
            ROUND(AVG(ttl.actual_duration_minutes)::numeric, 2) as avg_duration_min,
            ROUND(AVG(ttl.scheduled_duration_minutes)::numeric, 2) as scheduled_duration_min,
            ROUND(AVG(ttl.delay_minutes)::numeric, 2) as avg_delay_min,
            ROUND(STDDEV(ttl.delay_minutes)::numeric, 2) as delay_std_dev,
            MAX(ttl.delay_minutes) as max_delay_min,
            MIN(ttl.delay_minutes) as min_delay_min,
            ROUND(AVG(ttl.passenger_count)::numeric, 2) as avg_passengers,
            ROUND((AVG(ttl.passenger_count) / r.max_capacity * 100)::numeric, 2) as avg_utilization_percent,
            MAX(ttl.passenger_count) as max_passengers,
            COUNT(CASE WHEN ttl.passenger_count >= r.max_capacity * 0.9 THEN 1 END) as near_capacity_trips,
            COUNT(CASE WHEN ttl.is_peak_hour THEN 1 END) as peak_hour_trips,
            COUNT(CASE WHEN NOT ttl.is_peak_hour THEN 1 END) as offpeak_trips
        FROM routes r
        JOIN stations s1 ON r.start_station_id = s1.station_id
        JOIN stations s2 ON r.end_station_id = s2.station_id
        JOIN zone_metadata z1 ON s1.zone_id = z1.zone_id
        JOIN zone_metadata z2 ON s2.zone_id = z2.zone_id
        LEFT JOIN travel_time_logs ttl ON r.route_id = ttl.route_id
        GROUP BY r.route_id, r.route_name, r.transport_type, s1.station_name, 
                 s2.station_name, z1.zone_name, z2.zone_name, r.distance_km, 
                 r.base_fare, r.max_capacity, r.wheelchair_accessible
        ORDER BY r.route_name
    """
    
    routes_df = db.query_to_dataframe(routes_query)
    routes_summary_path = os.path.join(output_dir, f"route_summary_{timestamp}.csv")
    routes_df.to_csv(routes_summary_path, index=False)
    print(f"  ✓ Saved {len(routes_df)} routes to {routes_summary_path}")
    
    # ====================================
    # 3. Daily Aggregated Metrics
    # ====================================
    print("\n📅 Exporting daily aggregated metrics...")
    
    daily_query = """
        SELECT 
            ttl.log_date,
            EXTRACT(DOW FROM ttl.log_date) as day_of_week,
            EXTRACT(YEAR FROM ttl.log_date) as year,
            EXTRACT(MONTH FROM ttl.log_date) as month,
            EXTRACT(DAY FROM ttl.log_date) as day,
            r.route_id,
            r.route_name,
            r.transport_type,
            COUNT(*) as total_trips,
            COUNT(CASE WHEN ttl.is_peak_hour THEN 1 END) as peak_trips,
            ROUND(AVG(ttl.actual_duration_minutes)::numeric, 2) as avg_duration,
            ROUND(AVG(ttl.delay_minutes)::numeric, 2) as avg_delay,
            ROUND(AVG(CASE WHEN ttl.is_peak_hour THEN ttl.delay_minutes END)::numeric, 2) as peak_delay,
            ROUND(AVG(CASE WHEN NOT ttl.is_peak_hour THEN ttl.delay_minutes END)::numeric, 2) as offpeak_delay,
            ROUND(AVG(ttl.passenger_count)::numeric, 2) as avg_passengers,
            MAX(ttl.passenger_count) as max_passengers,
            ROUND(SUM(ttl.passenger_count)::numeric, 0) as total_passengers,
            MAX(ttl.weather_condition) as predominant_weather
        FROM travel_time_logs ttl
        JOIN routes r ON ttl.route_id = r.route_id
        GROUP BY ttl.log_date, r.route_id, r.route_name, r.transport_type
        ORDER BY ttl.log_date DESC, r.route_name
    """
    
    daily_df = db.query_to_dataframe(daily_query)
    daily_path = os.path.join(output_dir, f"daily_metrics_{timestamp}.csv")
    daily_df.to_csv(daily_path, index=False)
    print(f"  ✓ Saved {len(daily_df)} daily records to {daily_path}")
    
    # ====================================
    # 4. Hourly Patterns
    # ====================================
    print("\n⏰ Exporting hourly patterns...")
    
    hourly_query = """
        SELECT 
            EXTRACT(HOUR FROM ttl.log_time) as hour_of_day,
            r.route_id,
            r.route_name,
            r.transport_type,
            ttl.is_peak_hour,
            COUNT(*) as trip_count,
            ROUND(AVG(ttl.actual_duration_minutes)::numeric, 2) as avg_duration,
            ROUND(AVG(ttl.delay_minutes)::numeric, 2) as avg_delay,
            ROUND(AVG(ttl.passenger_count)::numeric, 2) as avg_passengers,
            ROUND((AVG(ttl.passenger_count) / r.max_capacity * 100)::numeric, 2) as avg_utilization
        FROM travel_time_logs ttl
        JOIN routes r ON ttl.route_id = r.route_id
        GROUP BY EXTRACT(HOUR FROM ttl.log_time), r.route_id, r.route_name, 
                 r.transport_type, r.max_capacity, ttl.is_peak_hour
        ORDER BY hour_of_day, r.route_name
    """
    
    hourly_df = db.query_to_dataframe(hourly_query)
    hourly_path = os.path.join(output_dir, f"hourly_patterns_{timestamp}.csv")
    hourly_df.to_csv(hourly_path, index=False)
    print(f"  ✓ Saved {len(hourly_df)} hourly pattern records to {hourly_path}")
    
    # ====================================
    # 5. Weather Impact Analysis
    # ====================================
    print("\n🌤️ Exporting weather impact data...")
    
    weather_query = """
        SELECT 
            r.route_id,
            r.route_name,
            r.transport_type,
            ttl.weather_condition,
            COUNT(*) as trip_count,
            ROUND(AVG(ttl.actual_duration_minutes)::numeric, 2) as avg_duration,
            ROUND(AVG(ttl.delay_minutes)::numeric, 2) as avg_delay,
            ROUND(STDDEV(ttl.delay_minutes)::numeric, 2) as delay_std_dev,
            MAX(ttl.delay_minutes) as max_delay,
            ROUND(AVG(ttl.passenger_count)::numeric, 2) as avg_passengers
        FROM travel_time_logs ttl
        JOIN routes r ON ttl.route_id = r.route_id
        WHERE ttl.weather_condition IS NOT NULL
        GROUP BY r.route_id, r.route_name, r.transport_type, ttl.weather_condition
        ORDER BY r.route_name, avg_delay DESC
    """
    
    weather_df = db.query_to_dataframe(weather_query)
    weather_path = os.path.join(output_dir, f"weather_impact_{timestamp}.csv")
    weather_df.to_csv(weather_path, index=False)
    print(f"  ✓ Saved {len(weather_df)} weather impact records to {weather_path}")
    
    # ====================================
    # 6. Service Availability Summary
    # ====================================
    print("\n🚦 Exporting service availability data...")
    
    availability_query = """
        SELECT 
            sa.check_date,
            EXTRACT(DOW FROM sa.check_date) as day_of_week,
            EXTRACT(HOUR FROM sa.check_time) as hour,
            r.route_id,
            r.route_name,
            r.transport_type,
            sa.status,
            sa.delay_minutes,
            sa.reason,
            COUNT(*) as status_count
        FROM service_availability sa
        JOIN routes r ON sa.route_id = r.route_id
        WHERE sa.check_date >= CURRENT_DATE - INTERVAL '90 days'
        GROUP BY sa.check_date, EXTRACT(DOW FROM sa.check_date), 
                 EXTRACT(HOUR FROM sa.check_time), r.route_id, r.route_name, 
                 r.transport_type, sa.status, sa.delay_minutes, sa.reason
        ORDER BY sa.check_date DESC, r.route_name
    """
    
    availability_df = db.query_to_dataframe(availability_query)
    availability_path = os.path.join(output_dir, f"service_availability_{timestamp}.csv")
    availability_df.to_csv(availability_path, index=False)
    print(f"  ✓ Saved {len(availability_df)} availability records to {availability_path}")
    
    # ====================================
    # 7. Station Information
    # ====================================
    print("\n🚏 Exporting station information...")
    
    stations_query = """
        SELECT 
            s.station_id,
            s.station_name,
            z.zone_name,
            z.population_density,
            z.avg_income,
            s.latitude,
            s.longitude,
            s.wheelchair_accessible,
            s.has_elevator,
            COUNT(DISTINCT r1.route_id) as outgoing_routes,
            COUNT(DISTINCT r2.route_id) as incoming_routes,
            COUNT(DISTINCT r1.route_id) + COUNT(DISTINCT r2.route_id) as total_connections
        FROM stations s
        JOIN zone_metadata z ON s.zone_id = z.zone_id
        LEFT JOIN routes r1 ON s.station_id = r1.start_station_id
        LEFT JOIN routes r2 ON s.station_id = r2.end_station_id
        GROUP BY s.station_id, s.station_name, z.zone_name, z.population_density, 
                 z.avg_income, s.latitude, s.longitude, s.wheelchair_accessible, s.has_elevator
        ORDER BY total_connections DESC, s.station_name
    """
    
    stations_df = db.query_to_dataframe(stations_query)
    stations_path = os.path.join(output_dir, f"stations_{timestamp}.csv")
    stations_df.to_csv(stations_path, index=False)
    print(f"  ✓ Saved {len(stations_df)} stations to {stations_path}")
    
    # ====================================
    # Summary
    # ====================================
    print("\n" + "=" * 60)
    print("✅ Export Complete!")
    print("=" * 60)
    print(f"\nFiles saved in: {output_dir}/")
    print("\nExported Files:")
    print(f"  1. {os.path.basename(main_export_path)} - Main detailed route performance")
    print(f"  2. {os.path.basename(routes_summary_path)} - Route summary statistics")
    print(f"  3. {os.path.basename(daily_path)} - Daily aggregated metrics")
    print(f"  4. {os.path.basename(hourly_path)} - Hourly usage patterns")
    print(f"  5. {os.path.basename(weather_path)} - Weather impact analysis")
    print(f"  6. {os.path.basename(availability_path)} - Service availability tracking")
    print(f"  7. {os.path.basename(stations_path)} - Station information")
    
    print("\n📊 Tableau Dashboard Suggestions:")
    print("  • Use route_summary for overall route performance KPIs")
    print("  • Use daily_metrics for time series trend analysis")
    print("  • Use hourly_patterns for heat maps of peak times")
    print("  • Use weather_impact for correlation analysis")
    print("  • Use service_availability for reliability dashboards")
    print("  • Use stations for geographic mapping")
    
    db.close()
    
    return output_dir


if __name__ == "__main__":
    output_directory = generate_tableau_export()
    print(f"\n✨ All exports ready for Tableau in: {output_directory}")
