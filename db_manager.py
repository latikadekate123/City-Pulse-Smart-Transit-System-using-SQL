"""
CityPulse Database Manager
Handles all database connections and queries
"""

import psycopg2
from psycopg2 import pool
from psycopg2.extras import RealDictCursor
import pandas as pd
from typing import List, Dict, Tuple, Optional
from datetime import datetime, date, time
import os
from contextlib import contextmanager


class DatabaseManager:
    """Manages PostgreSQL database connections and queries for CityPulse"""
    
    def __init__(self, dbname: str = "citypulse", user: str = "postgres", 
                 password: str = "lld@1501S", host: str = "localhost", port: str = "5432"):
        """
        Initialize database connection pool
        
        Args:
            dbname: Database name
            user: Database user
            password: Database password
            host: Database host
            port: Database port
        """
        self.connection_pool = psycopg2.pool.SimpleConnectionPool(
            1, 10,  # Min and max connections
            dbname=dbname,
            user=user,
            password=password,
            host=host,
            port=port
        )
        
        if self.connection_pool:
            print(f"[OK] Connected to CityPulse database")
    
    @contextmanager
    def get_connection(self):
        """Context manager for database connections"""
        conn = self.connection_pool.getconn()
        try:
            yield conn
        finally:
            self.connection_pool.putconn(conn)
    
    def execute_query(self, query: str, params: tuple = None, fetch: bool = True) -> List[Dict]:
        """
        Execute a SQL query and return results as list of dictionaries
        
        Args:
            query: SQL query string
            params: Query parameters
            fetch: Whether to fetch results
            
        Returns:
            List of dictionaries with query results
        """
        with self.get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute(query, params)
                if fetch:
                    results = cursor.fetchall()
                    return [dict(row) for row in results]
                else:
                    conn.commit()
                    return []
    
    def query_to_dataframe(self, query: str, params: tuple = None) -> pd.DataFrame:
        """
        Execute query and return results as pandas DataFrame
        
        Args:
            query: SQL query string
            params: Query parameters
            
        Returns:
            Pandas DataFrame with query results
        """
        with self.get_connection() as conn:
            return pd.read_sql_query(query, conn, params=params)
    
    # ====================================
    # ROUTE QUERIES
    # ====================================
    
    def get_all_routes(self, wheelchair_only: bool = False) -> pd.DataFrame:
        """Get all available routes with details"""
        query = """
            SELECT 
                r.route_id,
                r.route_name,
                r.transport_type,
                s1.station_name as start_station,
                s2.station_name as end_station,
                r.distance_km,
                r.base_fare,
                r.max_capacity,
                r.wheelchair_accessible,
                ROUND(AVG(ttl.avg_travel_time)::numeric, 2) as avg_travel_time_min,
                ROUND(AVG(ttl.delay_minutes)::numeric, 2) as avg_delay_min
            FROM routes r
            JOIN stations s1 ON r.start_station_id = s1.station_id
            JOIN stations s2 ON r.end_station_id = s2.station_id
            LEFT JOIN travel_time_logs ttl ON r.route_id = ttl.route_id
            WHERE 1=1
        """
        
        if wheelchair_only:
            query += " AND r.wheelchair_accessible = TRUE"
        
        query += """
            GROUP BY r.route_id, r.route_name, r.transport_type, s1.station_name, 
                     s2.station_name, r.distance_km, r.base_fare, r.max_capacity, r.wheelchair_accessible
            ORDER BY r.route_name
        """
        
        return self.query_to_dataframe(query)
    
    def get_route_by_stations(self, start_station: str, end_station: str, 
                             max_travel_time: int = None, wheelchair_accessible: bool = False) -> pd.DataFrame:
        """
        Find routes between two stations with optional filters
        
        Args:
            start_station: Starting station name
            end_station: Ending station name
            max_travel_time: Maximum acceptable travel time in minutes
            wheelchair_accessible: Filter for wheelchair accessible routes only
        """
        query = """
            SELECT 
                r.route_id,
                r.route_name,
                r.transport_type,
                s1.station_name as start_station,
                s2.station_name as end_station,
                r.distance_km,
                r.base_fare,
                r.wheelchair_accessible,
                ROUND(AVG(ttl.avg_travel_time)::numeric, 2) as avg_travel_time_min,
                ROUND(AVG(ttl.delay_minutes)::numeric, 2) as avg_delay_min,
                COUNT(CASE WHEN sa.is_operational = TRUE THEN 1 END) as active_services,
                COUNT(CASE WHEN sa.is_operational = FALSE THEN 1 END) as delayed_services
            FROM routes r
            JOIN stations s1 ON r.start_station_id = s1.station_id
            JOIN stations s2 ON r.end_station_id = s2.station_id
            LEFT JOIN travel_time_logs ttl ON r.route_id = ttl.route_id
            LEFT JOIN service_availability sa ON r.route_id = sa.route_id 
                AND sa.check_time >= CURRENT_TIMESTAMP - INTERVAL '7 days'
            WHERE s1.station_name = %s AND s2.station_name = %s
        """
        
        params = [start_station, end_station]
        
        if wheelchair_accessible:
            query += " AND r.wheelchair_accessible = TRUE"
        
        query += """
            GROUP BY r.route_id, r.route_name, r.transport_type, s1.station_name, 
                     s2.station_name, r.distance_km, r.base_fare, r.wheelchair_accessible
        """
        
        if max_travel_time:
            query += " HAVING AVG(ttl.avg_travel_time) <= %s"
            params.append(max_travel_time)
        
        query += " ORDER BY avg_travel_time_min"
        
        return self.query_to_dataframe(query, tuple(params))
    
    def get_alternative_routes(self, start_station: str, end_station: str, 
                              max_transfers: int = 1, wheelchair_accessible: bool = False) -> list:
        """
        Find alternative routes with transfers when no direct route exists
        
        Args:
            start_station: Starting station name
            end_station: Ending station name
            max_transfers: Maximum number of transfers allowed (default 1)
            wheelchair_accessible: Filter for wheelchair accessible routes only
        
        Returns:
            List of dictionaries containing route combinations
        """
        # Find one-transfer routes (A -> B -> C)
        query = """
            WITH transfer_routes AS (
                SELECT 
                    r1.route_id as route1_id,
                    r1.route_name as route1_name,
                    r1.transport_type as transport1_type,
                    s1.station_name as start_station,
                    s2.station_name as transfer_station,
                    r1.distance_km as distance1_km,
                    r1.base_fare as fare1,
                    r1.wheelchair_accessible as accessible1,
                    ROUND(AVG(ttl1.avg_travel_time)::numeric, 2) as travel_time1,
                    ROUND(AVG(ttl1.delay_minutes)::numeric, 2) as delay1,
                    
                    r2.route_id as route2_id,
                    r2.route_name as route2_name,
                    r2.transport_type as transport2_type,
                    s3.station_name as end_station,
                    r2.distance_km as distance2_km,
                    r2.base_fare as fare2,
                    r2.wheelchair_accessible as accessible2,
                    ROUND(AVG(ttl2.avg_travel_time)::numeric, 2) as travel_time2,
                    ROUND(AVG(ttl2.delay_minutes)::numeric, 2) as delay2
                    
                FROM routes r1
                JOIN stations s1 ON r1.start_station_id = s1.station_id
                JOIN stations s2 ON r1.end_station_id = s2.station_id
                LEFT JOIN travel_time_logs ttl1 ON r1.route_id = ttl1.route_id
                
                JOIN routes r2 ON r2.start_station_id = s2.station_id
                JOIN stations s3 ON r2.end_station_id = s3.station_id
                LEFT JOIN travel_time_logs ttl2 ON r2.route_id = ttl2.route_id
                
                WHERE s1.station_name = %s 
                    AND s3.station_name = %s
                    AND r1.route_id != r2.route_id
        """
        
        params = [start_station, end_station]
        
        if wheelchair_accessible:
            query += " AND r1.wheelchair_accessible = TRUE AND r2.wheelchair_accessible = TRUE"
        
        query += """
                GROUP BY r1.route_id, r1.route_name, r1.transport_type, s1.station_name,
                         s2.station_name, r1.distance_km, r1.base_fare, r1.wheelchair_accessible,
                         r2.route_id, r2.route_name, r2.transport_type, s3.station_name,
                         r2.distance_km, r2.base_fare, r2.wheelchair_accessible
            )
            SELECT 
                route1_name,
                transport1_type,
                start_station,
                transfer_station,
                distance1_km,
                fare1,
                route2_name,
                transport2_type,
                end_station,
                distance2_km,
                fare2,
                distance1_km + distance2_km as total_distance_km,
                fare1 + fare2 as total_fare,
                travel_time1 + travel_time2 + 5 as total_travel_time_min,
                delay1 + delay2 as total_delay_min,
                accessible1 AND accessible2 as wheelchair_accessible
            FROM transfer_routes
            ORDER BY total_travel_time_min
        """
        
        df = self.query_to_dataframe(query, tuple(params))
        
        if df.empty:
            return []
        
        # Convert to list of dictionaries
        return df.to_dict('records')
    
    def get_available_end_stations(self, start_station: str, wheelchair_accessible: bool = False) -> list:
        """Get list of stations that can be reached from a given start station"""
        query = """
            SELECT DISTINCT s2.station_name
            FROM routes r
            JOIN stations s1 ON r.start_station_id = s1.station_id
            JOIN stations s2 ON r.end_station_id = s2.station_id
            WHERE s1.station_name = %s
        """
        
        params = [start_station]
        
        if wheelchair_accessible:
            query += " AND r.wheelchair_accessible = TRUE"
        
        query += " ORDER BY s2.station_name"
        
        results = self.execute_query(query, tuple(params))
        return [row['station_name'] for row in results] if results else []
    
    def get_route_schedules(self, route_id: int, limit: int = 10) -> pd.DataFrame:
        """Get schedule information for a route"""
        route_id = int(route_id)
        
        query = """
            SELECT 
                day_of_week as day,
                departure_time,
                arrival_time,
                is_peak_hour,
                EXTRACT(EPOCH FROM (arrival_time - departure_time))/60 as duration_min
            FROM schedules
            WHERE route_id = %s
            ORDER BY 
                CASE day_of_week
                    WHEN 'Monday' THEN 1
                    WHEN 'Tuesday' THEN 2
                    WHEN 'Wednesday' THEN 3
                    WHEN 'Thursday' THEN 4
                    WHEN 'Friday' THEN 5
                    WHEN 'Saturday' THEN 6
                    WHEN 'Sunday' THEN 7
                END,
                departure_time
            LIMIT %s
        """
        
        return self.query_to_dataframe(query, (route_id, limit))
    
    def get_route_stats(self, route_id: int) -> Dict:
        """Get detailed statistics for a specific route"""
        # Convert to Python int to avoid numpy.int64 issues
        route_id = int(route_id)
        
        query = """
            SELECT 
                r.route_id,
                r.route_name,
                r.transport_type,
                r.distance_km,
                r.max_capacity,
                COUNT(DISTINCT ttl.log_date) as days_tracked,
                ROUND(AVG(ttl.avg_travel_time)::numeric, 2) as avg_duration_min,
                ROUND(AVG(ttl.delay_minutes)::numeric, 2) as avg_delay_min,
                ROUND(AVG(CASE WHEN ttl.is_peak_hour THEN ttl.delay_minutes END)::numeric, 2) as peak_delay_min,
                ROUND(AVG(CASE WHEN NOT ttl.is_peak_hour THEN ttl.delay_minutes END)::numeric, 2) as offpeak_delay_min,
                MAX(ttl.delay_minutes) as max_delay_min,
                ROUND(AVG(ttl.passenger_count)::numeric, 2) as avg_passengers,
                ROUND((AVG(ttl.passenger_count) / r.max_capacity * 100)::numeric, 2) as utilization_percent
            FROM routes r
            LEFT JOIN travel_time_logs ttl ON r.route_id = ttl.route_id
            WHERE r.route_id = %s
            GROUP BY r.route_id, r.route_name, r.transport_type, r.distance_km, r.max_capacity
        """
        
        results = self.execute_query(query, (route_id,))
        return results[0] if results else {}
    
    # ====================================
    # TRAVEL TIME ANALYTICS
    # ====================================
    
    def get_travel_time_trends(self, route_id: int, days: int = 30) -> pd.DataFrame:
        """Get travel time trends for a route over specified days"""
        # Convert to Python int to avoid numpy.int64 issues
        route_id = int(route_id)
        days = int(days)
        
        query = f"""
            SELECT 
                log_date,
                ROUND(AVG(avg_travel_time)::numeric, 2) as avg_duration,
                ROUND(AVG(delay_minutes)::numeric, 2) as avg_delay,
                ROUND(AVG(passenger_count)::numeric, 2) as avg_passengers,
                COUNT(*) as trip_count
            FROM travel_time_logs
            WHERE route_id = %s 
                AND log_date >= CURRENT_DATE - INTERVAL '{days} days'
            GROUP BY log_date
            ORDER BY log_date
        """
        
        return self.query_to_dataframe(query, (route_id,))
    
    def get_peak_vs_offpeak_performance(self) -> pd.DataFrame:
        """Compare peak hour vs off-peak hour performance across all routes"""
        query = """
            SELECT 
                r.route_name,
                r.transport_type,
                ROUND(AVG(CASE WHEN ttl.is_peak_hour THEN ttl.avg_travel_time END)::numeric, 2) as peak_duration,
                ROUND(AVG(CASE WHEN NOT ttl.is_peak_hour THEN ttl.avg_travel_time END)::numeric, 2) as offpeak_duration,
                ROUND(AVG(CASE WHEN ttl.is_peak_hour THEN ttl.delay_minutes END)::numeric, 2) as peak_delay,
                ROUND(AVG(CASE WHEN NOT ttl.is_peak_hour THEN ttl.delay_minutes END)::numeric, 2) as offpeak_delay,
                ROUND(AVG(CASE WHEN ttl.is_peak_hour THEN ttl.passenger_count END)::numeric, 2) as peak_passengers,
                ROUND(AVG(CASE WHEN NOT ttl.is_peak_hour THEN ttl.passenger_count END)::numeric, 2) as offpeak_passengers
            FROM routes r
            JOIN travel_time_logs ttl ON r.route_id = ttl.route_id
            GROUP BY r.route_name, r.transport_type
            ORDER BY peak_delay DESC
        """
        
        return self.query_to_dataframe(query)
    
    def get_weather_impact(self, route_id: int = None) -> pd.DataFrame:
        """Analyze impact of weather on delays"""
        # Convert to Python int to avoid numpy.int64 issues
        if route_id is not None:
            route_id = int(route_id)
        
        query = """
            SELECT 
                weather_condition,
                COUNT(*) as trip_count,
                ROUND(AVG(avg_travel_time)::numeric, 2) as avg_duration,
                ROUND(AVG(delay_minutes)::numeric, 2) as avg_delay,
                MAX(delay_minutes) as max_delay
            FROM travel_time_logs
            WHERE 1=1
        """
        
        params = None
        if route_id:
            query += " AND route_id = %s"
            params = (route_id,)
        
        query += """
            GROUP BY weather_condition
            ORDER BY avg_delay DESC
        """
        
        return self.query_to_dataframe(query, params)
    
    # ====================================
    # SERVICE AVAILABILITY
    # ====================================
    
    def get_current_service_status(self) -> pd.DataFrame:
        """Get current service status for all routes"""
        query = """
            WITH latest_status AS (
                SELECT 
                    route_id,
                    is_operational,
                    delay_minutes,
                    reason,
                    check_time,
                    ROW_NUMBER() OVER (PARTITION BY route_id ORDER BY check_time DESC) as rn
                FROM service_availability
            )
            SELECT 
                r.route_id,
                r.route_name,
                r.transport_type,
                COALESCE(ls.is_operational, true) as is_operational,
                COALESCE(ls.delay_minutes, 0) as delay_minutes,
                COALESCE(ls.reason, 'Normal Service') as reason,
                ls.check_time
            FROM routes r
            LEFT JOIN latest_status ls ON r.route_id = ls.route_id AND ls.rn = 1
            ORDER BY r.route_name
        """
        
        return self.query_to_dataframe(query)
    
    def get_service_reliability(self, days: int = 30) -> pd.DataFrame:
        """Calculate service reliability metrics"""
        days = int(days)  # Convert to Python int
        
        query = f"""
            SELECT 
                r.route_id,
                r.route_name,
                r.transport_type,
                COUNT(*) as total_checks,
                COUNT(CASE WHEN sa.is_operational = TRUE THEN 1 END) as active_count,
                COUNT(CASE WHEN sa.is_operational = FALSE AND sa.delay_minutes > 0 THEN 1 END) as delayed_count,
                COUNT(CASE WHEN sa.is_operational = FALSE AND sa.delay_minutes = 0 THEN 1 END) as cancelled_count,
                ROUND((COUNT(CASE WHEN sa.is_operational = TRUE THEN 1 END) * 100.0 / COUNT(*))::numeric, 2) as reliability_percent,
                ROUND(AVG(CASE WHEN sa.is_operational = FALSE AND sa.delay_minutes > 0 THEN sa.delay_minutes END)::numeric, 2) as avg_delay_when_delayed
            FROM routes r
            JOIN service_availability sa ON r.route_id = sa.route_id
            WHERE sa.check_time >= CURRENT_TIMESTAMP - INTERVAL '{days} days'
            GROUP BY r.route_id, r.route_name, r.transport_type
            ORDER BY reliability_percent DESC
        """
        
        return self.query_to_dataframe(query)
    
    # ====================================
    # STATIONS
    # ====================================
    
    def get_all_stations(self, wheelchair_only: bool = False) -> List[str]:
        """Get list of all station names"""
        query = "SELECT DISTINCT station_name FROM stations WHERE 1=1"
        
        if wheelchair_only:
            query += " AND wheelchair_accessible = TRUE"
        
        query += " ORDER BY station_name"
        
        results = self.execute_query(query)
        return [row['station_name'] for row in results]
    
    def get_station_details(self, station_name: str) -> Dict:
        """Get detailed information about a station"""
        query = """
            SELECT 
                s.station_id,
                s.station_name,
                z.zone_name,
                s.wheelchair_accessible,
                s.has_elevator,
                COUNT(DISTINCT r1.route_id) as outgoing_routes,
                COUNT(DISTINCT r2.route_id) as incoming_routes
            FROM stations s
            JOIN zone_metadata z ON s.zone_id = z.zone_id
            LEFT JOIN routes r1 ON s.station_id = r1.start_station_id
            LEFT JOIN routes r2 ON s.station_id = r2.end_station_id
            WHERE s.station_name = %s
            GROUP BY s.station_id, s.station_name, z.zone_name, s.wheelchair_accessible, s.has_elevator
        """
        
        results = self.execute_query(query, (station_name,))
        return results[0] if results else {}
    
    # ====================================
    # TABLEAU EXPORT
    # ====================================
    
    def export_for_tableau(self, output_path: str = "processed_route_data.csv") -> str:
        """
        Export comprehensive route data for Tableau visualization
        
        Args:
            output_path: Path to save CSV file
            
        Returns:
            Path to exported file
        """
        query = """
            SELECT 
                ttl.log_id,
                ttl.log_date,
                ttl.log_time,
                EXTRACT(DOW FROM ttl.log_date) as day_of_week,
                EXTRACT(HOUR FROM ttl.log_time) as hour_of_day,
                r.route_id,
                r.route_name,
                r.transport_type,
                s1.station_name as start_station,
                s2.station_name as end_station,
                s1.zone_id as start_zone_id,
                z1.zone_name as start_zone,
                s2.zone_id as end_zone_id,
                z2.zone_name as end_zone,
                r.distance_km,
                r.base_fare,
                r.max_capacity,
                r.wheelchair_accessible,
                ttl.scheduled_duration_minutes,
                ttl.avg_travel_time,
                ttl.delay_minutes,
                ttl.passenger_count,
                ROUND((ttl.passenger_count::numeric / r.max_capacity * 100), 2) as capacity_utilization_percent,
                ttl.weather_condition,
                ttl.is_peak_hour,
                CASE 
                    WHEN ttl.delay_minutes <= 0 THEN 'On Time'
                    WHEN ttl.delay_minutes <= 5 THEN 'Slight Delay'
                    WHEN ttl.delay_minutes <= 15 THEN 'Moderate Delay'
                    ELSE 'Severe Delay'
                END as delay_category,
                sa.is_operational as service_status,
                sa.delay_minutes as service_delay_minutes,
                sa.reason as service_issue_reason
            FROM travel_time_logs ttl
            JOIN routes r ON ttl.route_id = r.route_id
            JOIN stations s1 ON r.start_station_id = s1.station_id
            JOIN stations s2 ON r.end_station_id = s2.station_id
            JOIN zone_metadata z1 ON s1.zone_id = z1.zone_id
            JOIN zone_metadata z2 ON s2.zone_id = z2.zone_id
            LEFT JOIN service_availability sa ON r.route_id = sa.route_id 
                AND DATE(sa.check_time) = ttl.log_date 
                AND DATE_TRUNC('hour', sa.check_time) = DATE_TRUNC('hour', (ttl.log_date + ttl.log_time)::timestamp)
            ORDER BY ttl.log_date DESC, ttl.log_time DESC
        """
        
        df = self.query_to_dataframe(query)
        df.to_csv(output_path, index=False)
        
        print(f"[OK] Exported {len(df)} records to {output_path}")
        return output_path
    
    def close(self):
        """Close all database connections"""
        if self.connection_pool:
            self.connection_pool.closeall()
            print("[OK] Database connections closed")


# Convenience functions for quick usage
def get_db_manager() -> DatabaseManager:
    """Get a DatabaseManager instance"""
    return DatabaseManager()


if __name__ == "__main__":
    # Test the database connection
    db = DatabaseManager()
    
    print("\n=== Testing Database Connection ===")
    routes = db.get_all_routes()
    print(f"\nFound {len(routes)} routes in database")
    print("\nSample routes:")
    print(routes.head())
    
    print("\n=== Testing Export Functionality ===")
    db.export_for_tableau("test_export.csv")
    
    db.close()
