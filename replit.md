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
│   ├── services/      # Business logic services
│   ├── etl/           # Data extraction/transformation
│   ├── crawlers/      # Web scrapers
│   └── notifications/ # Alert system
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

## Running
The `start.sh` script launches both backend (uvicorn) and frontend (craco) concurrently.

## Recent Changes
- 2026-02-07: Initial Replit setup - configured ports, CORS, proxy, made MongoDB optional
