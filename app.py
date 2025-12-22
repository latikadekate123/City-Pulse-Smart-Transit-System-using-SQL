"""
CityPulse - Smart Route & Availability Dashboard
Interactive Streamlit application for exploring transit routes, 
analyzing travel patterns, and monitoring service availability.
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
from db_manager import DatabaseManager
import os

# Page configuration
st.set_page_config(
    page_title="CityPulse Dashboard",
    page_icon="🚇",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
    <style>
    .main-header {
        font-size: 2.5rem;
        font-weight: 700;
        color: #1f77b4;
        margin-bottom: 0.5rem;
    }
    .sub-header {
        font-size: 1.2rem;
        color: #666;
        margin-bottom: 2rem;
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 0.5rem 0;
    }
    .stTabs [data-baseweb="tab-list"] {
        gap: 2rem;
    }
    </style>
""", unsafe_allow_html=True)

# Initialize database manager
@st.cache_resource
def get_database():
    """Initialize and cache database connection"""
    return DatabaseManager()

# Load data with caching
@st.cache_data(ttl=300)  # Cache for 5 minutes
def load_routes(_db, wheelchair_only=False):
    """Load all routes from database"""
    return _db.get_all_routes(wheelchair_only)

@st.cache_data(ttl=300)
def load_stations(_db, wheelchair_only=False):
    """Load all station names"""
    return _db.get_all_stations(wheelchair_only)

@st.cache_data(ttl=300)
def load_service_status(_db):
    """Load current service status"""
    return _db.get_current_service_status()

@st.cache_data(ttl=300)
def load_peak_performance(_db):
    """Load peak vs off-peak performance"""
    return _db.get_peak_vs_offpeak_performance()


def main():
    """Main application function"""
    
    # Header
    st.markdown('<div class="main-header">🚇 CityPulse Dashboard</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-header">Smart Route & Availability Insights</div>', unsafe_allow_html=True)
    
    # Initialize database
    try:
        db = get_database()
    except Exception as e:
        st.error(f"❌ Database connection failed: {str(e)}")
        st.info("Please ensure PostgreSQL is running and credentials in db_manager.py are correct.")
        return
    
    # Sidebar - Global Filters
    st.sidebar.title("🔍 Filters & Settings")
    
    # Wheelchair accessibility filter
    wheelchair_required = st.sidebar.checkbox(
        "♿ Wheelchair Accessible Only",
        value=False,
        help="Show only wheelchair accessible routes and stations"
    )
    
    # Max travel time filter
    max_travel_time = st.sidebar.slider(
        "⏱️ Max Travel Time (minutes)",
        min_value=10,
        max_value=120,
        value=60,
        step=5,
        help="Filter routes by maximum acceptable travel time"
    )
    
    # Transport type filter
    transport_types = st.sidebar.multiselect(
        "🚌 Transport Types",
        options=["Bus", "Metro", "Tram"],
        default=["Bus", "Metro", "Tram"],
        help="Select transport types to display"
    )
    
    st.sidebar.markdown("---")
    
    # Data export section
    st.sidebar.subheader("📊 Export Data")
    if st.sidebar.button("Export for Tableau", use_container_width=True):
        with st.spinner("Exporting data..."):
            try:
                output_path = db.export_for_tableau("processed_route_data.csv")
                st.sidebar.success(f"✅ Data exported to {output_path}")
                
                # Provide download button
                with open(output_path, 'rb') as f:
                    st.sidebar.download_button(
                        label="📥 Download CSV",
                        data=f,
                        file_name="processed_route_data.csv",
                        mime="text/csv",
                        use_container_width=True
                    )
            except Exception as e:
                st.sidebar.error(f"Export failed: {str(e)}")
    
    # Main content - Tabs
    tab1, tab2, tab3, tab4 = st.tabs([
        "🗺️ Route Explorer", 
        "📈 Travel Trends", 
        "🚦 Service Status",
        "📊 Analytics"
    ])
    
    # ====================================
    # TAB 1: ROUTE EXPLORER
    # ====================================
    with tab1:
        st.header("Route Explorer")
        st.markdown("Browse all available routes and click on any route to see detailed information.")
        
        # Get all routes
        all_routes = db.get_all_routes(wheelchair_required)
        
        if not all_routes.empty:
            # Filter by transport type
            all_routes = all_routes[all_routes['transport_type'].isin(transport_types)]
            
            if not all_routes.empty:
                st.success(f"✅ {len(all_routes)} route(s) available")
                
                # Display routes as clickable cards
                for idx, route in all_routes.iterrows():
                            with st.expander(
                                f"🚉 {route['route_name']} ({route['transport_type']}) - "
                                f"~{route['avg_travel_time_min']:.0f} min",
                                expanded=(idx == 0)
                            ):
                                col1, col2, col3, col4 = st.columns(4)
                                
                                with col1:
                                    st.metric("💰 Fare", f"${route['base_fare']:.2f}")
                                
                                with col2:
                                    st.metric("📏 Distance", f"{route['distance_km']:.1f} km")
                                
                                with col3:
                                    delay_color = "🟢" if route['avg_delay_min'] < 5 else "🟡" if route['avg_delay_min'] < 10 else "🔴"
                                    st.metric(f"{delay_color} Avg Delay", f"{route['avg_delay_min']:.1f} min")
                                
                                with col4:
                                    accessible = "✅" if route['wheelchair_accessible'] else "❌"
                                    st.metric("♿ Accessible", accessible)
                                
                                # Get detailed stats
                                stats = db.get_route_stats(route['route_id'])
                                
                                col1, col2, col3 = st.columns(3)
                                with col1:
                                    st.metric("👥 Avg Passengers", f"{stats.get('avg_passengers') or 0:.0f}")
                                with col2:
                                    utilization = stats.get('utilization_percent') or 0
                                    st.metric("📊 Utilization", f"{utilization:.1f}%")
                                with col3:
                                    st.metric("🚨 Max Delay", f"{stats.get('max_delay_min') or 0:.0f} min")
                                
                                # Show route schedules
                                with st.expander("📅 View Schedule Times"):
                                    schedules = db.get_route_schedules(route['route_id'], limit=20)
                                    if not schedules.empty:
                                        st.dataframe(
                                            schedules[['day', 'departure_time', 'arrival_time', 'duration_min', 'is_peak_hour']],
                                            hide_index=True,
                                            use_container_width=True
                                        )
                                    else:
                                        st.info("No schedule information available")
            else:
                st.info("No routes match the selected transport types.")
        else:
            st.info("No routes available.")
    
    # ====================================
    # TAB 2: ANALYTICS
    # ====================================
    # TAB 2: ANALYTICS
    # ====================================
    with tab2:
        st.header("Travel Time Trends & Patterns")
        
        # Route selection for trend analysis
        all_routes = load_routes(db, False)
        selected_route_name = st.selectbox(
            "📍 Select Route for Analysis",
            options=all_routes['route_name'].unique(),
            help="Choose a route to view detailed travel time trends"
        )
        
        if selected_route_name:
            route_info = all_routes[all_routes['route_name'] == selected_route_name].iloc[0]
            route_id = route_info['route_id']
            
            # Display route info
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("🚌 Type", route_info['transport_type'])
            with col2:
                st.metric("⏱️ Avg Time", f"{route_info['avg_travel_time_min']:.1f} min")
            with col3:
                st.metric("⏰ Avg Delay", f"{route_info['avg_delay_min']:.1f} min")
            with col4:
                st.metric("📏 Distance", f"{route_info['distance_km']:.1f} km")
            
            st.markdown("---")
            
            # Time range selector
            days_back = st.select_slider(
                "📅 Time Period",
                options=[7, 14, 30, 60, 90],
                value=30,
                format_func=lambda x: f"Last {x} days"
            )
            
            # Load trend data
            trend_data = db.get_travel_time_trends(route_id, days_back)
            
            if not trend_data.empty:
                # Travel time trend chart
                st.subheader("⏱️ Daily Average Travel Time")
                
                fig_time = go.Figure()
                
                fig_time.add_trace(go.Scatter(
                    x=trend_data['log_date'],
                    y=trend_data['avg_duration'],
                    mode='lines+markers',
                    name='Average Duration',
                    line=dict(color='#1f77b4', width=2),
                    marker=dict(size=6)
                ))
                
                fig_time.update_layout(
                    xaxis_title="Date",
                    yaxis_title="Duration (minutes)",
                    hovermode='x unified',
                    height=400
                )
                
                st.plotly_chart(fig_time, use_container_width=True)
                
                # Delay trend chart
                st.subheader("⏰ Daily Average Delays")
                
                fig_delay = go.Figure()
                
                fig_delay.add_trace(go.Scatter(
                    x=trend_data['log_date'],
                    y=trend_data['avg_delay'],
                    mode='lines+markers',
                    name='Average Delay',
                    line=dict(color='#ff7f0e', width=2),
                    marker=dict(size=6),
                    fill='tozeroy',
                    fillcolor='rgba(255, 127, 14, 0.2)'
                ))
                
                fig_delay.update_layout(
                    xaxis_title="Date",
                    yaxis_title="Delay (minutes)",
                    hovermode='x unified',
                    height=400
                )
                
                st.plotly_chart(fig_delay, use_container_width=True)
                
                # Passenger count trend
                st.subheader("👥 Passenger Count Trends")
                
                fig_passengers = px.area(
                    trend_data,
                    x='log_date',
                    y='avg_passengers',
                    title='',
                    labels={'log_date': 'Date', 'avg_passengers': 'Average Passengers'}
                )
                
                fig_passengers.update_traces(line_color='#2ca02c', fillcolor='rgba(44, 160, 44, 0.3)')
                fig_passengers.update_layout(height=400, hovermode='x unified')
                
                st.plotly_chart(fig_passengers, use_container_width=True)
                
            else:
                st.info("No trend data available for this route.")
            
            # Weather impact analysis
            st.markdown("---")
            st.subheader("🌤️ Weather Impact Analysis")
            
            weather_data = db.get_weather_impact(route_id)
            
            if not weather_data.empty:
                col1, col2 = st.columns(2)
                
                with col1:
                    fig_weather = px.bar(
                        weather_data,
                        x='weather_condition',
                        y='avg_delay',
                        title='Average Delay by Weather Condition',
                        labels={'weather_condition': 'Weather', 'avg_delay': 'Avg Delay (min)'},
                        color='avg_delay',
                        color_continuous_scale='Reds'
                    )
                    st.plotly_chart(fig_weather, use_container_width=True)
                
                with col2:
                    fig_trips = px.pie(
                        weather_data,
                        values='trip_count',
                        names='weather_condition',
                        title='Trip Distribution by Weather'
                    )
                    st.plotly_chart(fig_trips, use_container_width=True)
    
    # ====================================
    # TAB 3: SERVICE STATUS
    # ====================================
    with tab3:
        st.header("Real-Time Service Status")
        
        service_status = load_service_status(db)
        
        if not service_status.empty:
            # Add status column with better categorization
            def categorize_status(row):
                if pd.notna(row['reason']) and 'Maintenance' in row['reason']:
                    return 'Maintenance'
                elif row['is_operational']:
                    if pd.notna(row['delay_minutes']) and row['delay_minutes'] > 0:
                        return 'Delayed'
                    else:
                        return 'Active'
                else:
                    return 'Out of Service'
            
            service_status['status'] = service_status.apply(categorize_status, axis=1)
            
            # Status summary
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                active_count = len(service_status[service_status['status'] == 'Active'])
                st.metric("✅ Active", active_count)
            
            with col2:
                delayed_count = len(service_status[service_status['status'] == 'Delayed'])
                st.metric("⏰ Delayed", delayed_count)
            
            with col3:
                cancelled_count = len(service_status[service_status['status'] == 'Out of Service'])
                st.metric("❌ Out of Service", cancelled_count)
            
            with col4:
                maintenance_count = len(service_status[service_status['status'] == 'Maintenance'])
                st.metric("🔧 Maintenance", maintenance_count)
            
            st.markdown("---")
            
            # Filter by status
            status_filter = st.multiselect(
                "Filter by Status",
                options=service_status['status'].unique(),
                default=service_status['status'].unique()
            )
            
            filtered_status = service_status[service_status['status'].isin(status_filter)]
            
            # Display as clickable table
            st.subheader("Current Service Status")
            
            # Prepare display dataframe
            display_df = filtered_status[['route_name', 'transport_type', 'status', 'delay_minutes', 'reason']].copy()
            display_df['delay_minutes'] = display_df['delay_minutes'].fillna(0).astype(int)
            display_df.columns = ['Route', 'Type', 'Status', 'Delay (min)', 'Reason']
            
            # Display clickable dataframe
            st.dataframe(
                display_df,
                hide_index=True,
                use_container_width=True,
                height=400
            )
            
            st.info("💡 Click on 'Route Explorer' tab to see detailed information for each route.")
            
            st.markdown("---")
            
            # Service reliability
            st.subheader("📊 Service Reliability (Last 30 Days)")
            
            reliability = db.get_service_reliability(30)
            
            if not reliability.empty:
                fig_reliability = px.bar(
                    reliability.sort_values('reliability_percent', ascending=True),
                    y='route_name',
                    x='reliability_percent',
                    orientation='h',
                    title='',
                    labels={'route_name': 'Route', 'reliability_percent': 'Reliability %'},
                    color='reliability_percent',
                    color_continuous_scale='RdYlGn',
                    range_color=[0, 100]
                )
                
                fig_reliability.update_layout(height=400, showlegend=False)
                st.plotly_chart(fig_reliability, use_container_width=True)
        else:
            st.info("No service status data available.")
    
    # ====================================
    # TAB 4: ANALYTICS
    # ====================================
    with tab4:
        st.header("Advanced Analytics")
        
        # Peak vs Off-Peak comparison
        st.subheader("🕐 Peak vs Off-Peak Performance")
        
        peak_data = load_peak_performance(db)
        
        if not peak_data.empty:
            # Filter by transport type
            peak_data = peak_data[peak_data['transport_type'].isin(transport_types)]
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("**⏰ Delay Comparison**")
                
                fig_peak_delay = go.Figure()
                
                fig_peak_delay.add_trace(go.Bar(
                    name='Peak Hours',
                    x=peak_data['route_name'],
                    y=peak_data['peak_delay'],
                    marker_color='#ff7f0e'
                ))
                
                fig_peak_delay.add_trace(go.Bar(
                    name='Off-Peak Hours',
                    x=peak_data['route_name'],
                    y=peak_data['offpeak_delay'],
                    marker_color='#1f77b4'
                ))
                
                fig_peak_delay.update_layout(
                    barmode='group',
                    xaxis_title='Route',
                    yaxis_title='Average Delay (min)',
                    height=400
                )
                
                st.plotly_chart(fig_peak_delay, use_container_width=True)
            
            with col2:
                st.markdown("**👥 Passenger Load Comparison**")
                
                fig_peak_passengers = go.Figure()
                
                fig_peak_passengers.add_trace(go.Bar(
                    name='Peak Hours',
                    x=peak_data['route_name'],
                    y=peak_data['peak_passengers'],
                    marker_color='#d62728'
                ))
                
                fig_peak_passengers.add_trace(go.Bar(
                    name='Off-Peak Hours',
                    x=peak_data['route_name'],
                    y=peak_data['offpeak_passengers'],
                    marker_color='#2ca02c'
                ))
                
                fig_peak_passengers.update_layout(
                    barmode='group',
                    xaxis_title='Route',
                    yaxis_title='Average Passengers',
                    height=400
                )
                
                st.plotly_chart(fig_peak_passengers, use_container_width=True)
            
            # Detailed table
            st.markdown("**📊 Detailed Metrics**")
            st.dataframe(
                peak_data[[
                    'route_name', 'transport_type', 
                    'peak_delay', 'offpeak_delay',
                    'peak_passengers', 'offpeak_passengers'
                ]].round(2),
                use_container_width=True,
                hide_index=True
            )
        else:
            st.info("No analytics data available.")
        
        st.markdown("---")
        
        # Overall system metrics
        st.subheader("🌐 System-Wide Metrics")
        
        all_routes = load_routes(db, False)
        
        if not all_routes.empty:
            col1, col2, col3 = st.columns(3)
            
            with col1:
                total_capacity = all_routes['max_capacity'].sum()
                st.metric("🚉 Total System Capacity", f"{total_capacity:,}")
            
            with col2:
                avg_utilization = all_routes['avg_travel_time_min'].mean()
                st.metric("⏱️ Average Travel Time", f"{avg_utilization:.1f} min")
            
            with col3:
                total_distance = all_routes['distance_km'].sum()
                st.metric("📏 Total Network Distance", f"{total_distance:.1f} km")
            
            # Transport type distribution
            col1, col2 = st.columns(2)
            
            with col1:
                type_counts = all_routes['transport_type'].value_counts()
                fig_types = px.pie(
                    values=type_counts.values,
                    names=type_counts.index,
                    title='Routes by Transport Type'
                )
                st.plotly_chart(fig_types, use_container_width=True)
            
            with col2:
                fig_fare_dist = px.histogram(
                    all_routes,
                    x='base_fare',
                    nbins=20,
                    title='Fare Distribution',
                    labels={'base_fare': 'Base Fare ($)', 'count': 'Number of Routes'}
                )
                st.plotly_chart(fig_fare_dist, use_container_width=True)


if __name__ == "__main__":
    main()
