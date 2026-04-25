# CityPulse - Smart Transit System 🚇

Hey there! Welcome to CityPulse - my take on making public transit data actually useful and easy to understand.

## What's This All About?

Ever wished you could see real-time transit info that actually helps you plan your commute? That's exactly what I built here. CityPulse pulls together route data, service status, and travel patterns into one clean dashboard that both commuters and transit planners can actually use.

I'm using real NYC MTA station data with 90 days of simulated trips, delays, and service updates to show how a modern transit analytics platform should work.

## What Can You Do With It?

**Route Explorer** - Browse all 15 NYC transit routes (subway lines 1-6, A/C/E/L/N/Q, and buses M15/M34/B41). Click on any route to see schedules, passenger counts, and delay info.

**Travel Trends** - See how travel times change throughout the day and week. I track everything - from weather impacts to peak hour congestion.

**Service Status** - Check which routes are active, delayed, under maintenance, or out of service right now. No more guessing if your train is running!

**Analytics Dashboard** - Dig into the data with charts showing weather impacts, reliability trends, and performance metrics.

## The Tech Stack

I built this with:
- **Python 3.13** for the backend logic
- **PostgreSQL 17** to handle all the transit data
- **Streamlit** for the web interface
- **Plotly** for interactive charts
- **Real NYC MTA data** from the official API

## Getting It Running

**1. Set up your database**
```bash
psql -U postgres -c "CREATE DATABASE citypulse;"
psql -U postgres -d citypulse -f tablesCity.sql
```

**2. Import the NYC transit data**
```bash
python import_mta_data.py
```
This pulls real station data from NYC MTA and generates realistic trip data for 50 stations across all 5 boroughs.

**3. Install Python packages**
```bash
pip install -r requirements.txt
```

**4. Update database credentials**
Edit `db_manager.py` with your PostgreSQL password.

**5. Launch the dashboard**
```bash
streamlit run app.py
```

## The Data

Here's what's in the database:
- **50 NYC Stations** - Real locations across Manhattan, Brooklyn, Queens, Bronx, and Staten Island
- **15 Routes** - Mix of subway lines and bus routes
- **11,000+ Trips** - 90 days of realistic travel patterns
- **2,000 Fare Cards** - Regular, Student, and Senior passes
- **Service Status** - 30 days of operational data with actual maintenance and delay reasons

Everything's designed to feel realistic - peak hour traffic, weather delays, random maintenance windows, the works.

## What I Learned

This project taught me a lot about:
- Working with real-world APIs (NYC MTA Open Data)
- Designing normalized database schemas
- Building responsive web dashboards
- Creating meaningful data visualizations
- Writing clean, maintainable Python code

## Files Worth Checking Out

- `app.py` - The main dashboard app
- `db_manager.py` - All the database queries and connections
- `import_mta_data.py` - Script that pulls MTA data and generates realistic transit records
- `tablesCity.sql` - Database schema with 10 tables
- `queriesCity.sql` - Sample analytics queries

## Why I Built This

I wanted to create something that shows I can work with real data sources, design relational databases, and build user-friendly interfaces. Plus, I'm genuinely interested in how cities can use data to improve public transportation.

## Let's Connect

I'm always happy to chat about data projects, SQL optimization, or transit systems!

**GitHub**: latikadekate123

---

*Note: While I'm using real NYC MTA station data, all trip records, delays, and service statuses are simulated for demonstration purposes.*
