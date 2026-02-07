# ZLECAf Trade Calculator

## Overview
A comprehensive African Continental Free Trade Area (AfCFTA/ZLECAf) trade analysis platform. It provides tariff calculations, trade statistics, logistics information, production data, and AI-powered trade analysis for 54 African countries.

## Architecture
- **Backend**: Python FastAPI server running on port 8000 (localhost)
- **Frontend**: React (CRA with CRACO) running on port 5000 (0.0.0.0)
- **Database**: MongoDB (optional - app works without it for most features)
- **Proxy**: Frontend proxies `/api` requests to backend via CRA proxy config

## Project Structure
```
├── backend/           # FastAPI backend
│   ├── server.py      # Main server file
│   ├── routes/        # API route modules
│   │   ├── tariff_data.py  # Tariff data collection endpoints
│   │   └── crawl.py        # Crawl orchestration endpoints
│   ├── services/      # Business logic services
│   │   ├── crawl_orchestrator.py    # Crawl job management
│   │   └── tariff_data_collector.py # Tariff data consolidation engine
│   ├── etl/           # Data extraction/transformation (HS6, tariffs, taxes)
│   ├── crawlers/      # Web scrapers + generic tariff collector
│   ├── routers/       # Export router (CSV, Excel, JSON)
│   ├── notifications/ # Alert system (Email, Slack)
│   └── data/tariffs/  # Generated tariff JSON files (54 countries, ~157MB)
├── frontend/          # React frontend
│   ├── src/           # React source code
│   ├── public/        # Static assets
│   └── craco.config.js # Build config (dev server on 5000, allowedHosts: all)
├── start.sh           # Startup script (runs both backend and frontend)
└── requirements.txt   # Python dependencies
```

## Key Configuration
- Frontend dev server: port 5000, host 0.0.0.0, allowedHosts: all
- Backend: port 8000, localhost only
- REACT_APP_BACKEND_URL: empty string (uses proxy)
- Frontend proxy: forwards API calls to http://localhost:8000

## Tariff Data System
- **Source data**: ETL modules with chapter-level tariffs (54 countries), HS6 detailed rates (NGA, CIV, ZAF, KEN + regional groupings), VAT rates, other taxes
- **HS6 Database**: 5,762 product codes from WCO Harmonized System 2022
- **Collection**: `POST /api/tariff-data/collect` generates JSON files per country
- **Data per country**: ~5,831 tariff lines with DD rate, ZLECAf rate, VAT, other taxes, sub-positions
- **Total**: 314,874 tariff lines across 54 countries
- **API**: `/api/tariff-data/{country_code}` with chapter/HS6 filters and pagination

## Running
The `start.sh` script launches both backend (uvicorn) and frontend (craco) concurrently.

## Recent Changes
- 2026-02-07: Built tariff data collection system - 314,874 tariff lines for 54 countries with DD, VAT, other taxes
- 2026-02-07: Created crawl orchestration system with API routes, notification integration
- 2026-02-07: Fixed import paths, wired export/crawl/notification modules into server
- 2026-02-07: Initial Replit setup - configured ports, CORS, proxy, made MongoDB optional

## User Preferences
- Language: French preferred for technical discussions
- Focus: Fiscal/regulatory data accuracy for customs calculations
