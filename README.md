# 🚇 CityPulse — Smart Transit Analytics System
 
> A full-stack data engineering and analytics platform for real-time NYC MTA transit intelligence
 
[![Python](https://img.shields.io/badge/Python-3.10-blue)](https://python.org)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-15-blue)](https://postgresql.org)
[![Streamlit](https://img.shields.io/badge/Streamlit-App-red)](https://streamlit.io)
 
---
 
## 📌 Project Overview
 
CityPulse is an end-to-end **transit data pipeline and interactive analytics dashboard** built using real-time NYC MTA API data. It enables users to explore delay patterns, station performance, and peak hour trends across the New York City subway system.
 
**Problem:** Transit agencies lack easy-to-use tools to visualize delay patterns and performance across hundreds of stations in real time.  
**Solution:** An automated ETL pipeline + interactive dashboard that ingests live transit data, stores it in a relational database, and surfaces actionable insights through visual analytics.
 
---
 
## 📊 Key Results & Highlights
 
- 📡 Integrated **live MTA API** to ingest real-time subway delay and trip data
- 🗄️ Designed a **10-table normalized PostgreSQL schema** covering trips, stations, delays, routes, and time dimensions
- ⚡ Built automated **ETL pipeline** for continuous data ingestion and transformation
- 📈 Identified **peak-hour delay clusters** across 50+ NYC stations through pattern analysis
- 🖥️ Deployed interactive **Streamlit dashboard** with Plotly charts + Tableau visualizations
- 🔍 Enabled filtering by line, station, time-of-day, and delay severity
---
 
## 🛠️ Tech Stack
 
| Layer | Technology |
|-------|-----------|
| Data Ingestion | Python, MTA REST API |
| Database | PostgreSQL (10-table normalized schema) |
| Data Processing | Python, Pandas, SQLAlchemy |
| Visualization | Streamlit, Plotly, Tableau |
| Version Control | Git, GitHub |
 
---
 
## 🗂️ Project Architecture
 
```
MTA API → ETL Pipeline (Python) → PostgreSQL DB → Streamlit Dashboard
                                       ↓
                               Tableau Reports
```
 
---
 
## 🚀 How to Run
 
```bash
# Clone the repository
git clone https://github.com/latikadekate123/City-Pulse-Smart-Transit-System-using-SQL.git
cd City-Pulse-Smart-Transit-System-using-SQL
 
# Install dependencies
pip install -r requirements.txt
 
# Set up PostgreSQL database
psql -U postgres -f schema.sql
 
# Run the Streamlit app
streamlit run app.py
```
 
---
 
## 📁 Repository Structure
 
```
├── data/               # Sample data and API response examples
├── sql/                # Database schema and query files
├── etl/                # Data ingestion and transformation scripts
├── app.py              # Streamlit dashboard
├── requirements.txt    # Python dependencies
└── README.md
```
 
---
 
## 💡 Key Learnings
 
- Designing normalized relational schemas for time-series transit data
- Building real-time API data pipelines with error handling and retries
- Creating interactive dashboards that communicate complex patterns simply
- Writing complex analytical SQL queries (window functions, CTEs, aggregations)
---
 
## 🔗 Links
 
- 🔴 **Live Demo:** *(Add your Streamlit Cloud or Render link here)*
- 📊 **Tableau Dashboard:** *(Add your Tableau Public link here)*
- 💼 **LinkedIn:** [Latika Dekate](https://www.linkedin.com/in/latika-dekate/)
