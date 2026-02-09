# ZLECAf Trade Calculator

## Overview
A comprehensive African Continental Free Trade Area (AfCFTA/ZLECAf) trade analysis platform. It provides tariff calculations, trade statistics, logistics information, production data, and AI-powered trade analysis for 54 African countries.

## Architecture
- **Backend**: Python FastAPI server running on port 8000 (localhost)
- **Frontend**: React (CRA with CRACO) running on port 5000 (0.0.0.0)
- **Database**: MongoDB (optional - app works without it for most features)
- **Proxy**: Frontend proxies `/api` requests to backend via CRA proxy config
- **Security**: CSP headers, Rate Limiting (120 req/min), CSRF protection middleware

## Project Structure
```
├── backend/           # FastAPI backend
│   ├── server.py      # Main server file
│   ├── models.py      # Pydantic response models
│   ├── middlewares/    # Security middlewares (CSP, CSRF, Rate Limit)
│   ├── routes/        # API route modules
│   │   ├── tariff_data.py  # Tariff data collection + monitoring endpoints
│   │   └── crawl.py        # Crawl orchestration endpoints
│   ├── services/      # Business logic services
│   │   ├── tariff_data_collector.py # Tariff data consolidation engine (enhanced v2)
│   │   ├── tariff_data_service.py   # Singleton data service with tax detail support
│   │   └── crawl_orchestrator.py    # Crawl job management
│   ├── etl/           # Data extraction/transformation
│   │   ├── country_taxes_algeria.py  # Algeria-specific taxes (DAPS, DD, PRCT, TCS, TVA)
│   │   ├── country_tariffs.py        # Chapter-level tariffs per country
│   │   ├── country_tariffs_complete.py # Complete tariff system with VAT, other taxes
│   │   ├── country_hs6_detailed*.py   # Country-specific HS6 sub-positions
│   │   └── hs6_csv_database.py        # 5,762 HS6 codes from WCO 2022
│   ├── crawlers/      # Web scrapers + generic tariff collector
│   ├── routers/       # Export router (CSV, Excel, JSON)
│   ├── notifications/ # Alert system (Email, Slack)
│   ├── tests/         # Unit tests (pytest)
│   └── data/tariffs/  # Generated tariff JSON files (54 countries, enhanced_v2 format)
├── frontend/          # React frontend
│   ├── src/           # React source code
│   │   └── components/tools/MonitoringDashboard.jsx  # Tariff monitoring UI
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

## Tariff Data System (Enhanced v2)
- **Architecture**: Collected tariff data (JSON files) is the single source of truth for the calculator
- **Data Format**: `enhanced_v2` - includes individual tax components, fiscal advantages, administrative formalities
- **Data Service**: `TariffDataService` singleton loads all collected data into memory at startup
- **Auto-collection**: If no data files exist on startup, runs initial collection automatically
- **Source data**: ETL modules with chapter-level tariffs (54 countries), HS6 detailed rates, VAT rates, other taxes
- **Country-specific tax modules**: Algeria has dedicated module (`country_taxes_algeria.py`) with:
  - Product-level DAPS rates (30-200% on ~1095 products)
  - Product-level DD rates (overrides chapter defaults)
  - PRCT (2%), TCS (3% on food/agricultural products)
  - TVA standard (19%) and reduced (9%)
  - Administrative formalities by product category
  - Fiscal advantages (ZLECAf DD exemption)
- **HS6 Database**: 5,762 product codes from WCO Harmonized System 2022
- **Sub-positions**: HS8/HS10/HS12 generated from SUB_POSITION_TYPES definitions + real COUNTRY_HS6_DETAILED data
- **Collection**: `POST /api/tariff-data/collect` generates JSON files per country
- **Data per country**: ~5,831 HS6 lines + ~16,000 sub-positions = ~22,000 positions per country
- **Total**: 314,874 HS6 lines + 871,565 sub-positions = 1,186,439 positions across 54 countries
- **Enhanced JSON per line**: `taxes_detail[]`, `fiscal_advantages[]`, `administrative_formalities[]`, `total_taxes_pct`
- **Calculator integration**: `/api/calculate-tariff` uses collected data as primary source, ETL as fallback
- **Calculator response**: Now includes `taxes_detail`, `fiscal_advantages`, `administrative_formalities`, `data_source`
- **Status endpoint**: `GET /api/tariff-data/status` shows data source info
- **API**: `/api/tariff-data/{country_code}` with chapter/HS6 filters and pagination
- **Scheduler**: Annual collection (January)

## Security
- **CSP**: Content-Security-Policy with nonce-based script execution
- **Rate Limiting**: 120 requests/minute per IP with burst protection (20/sec)
- **Security Headers**: X-Content-Type-Options, X-Frame-Options, XSS-Protection, HSTS, Referrer-Policy, Permissions-Policy
- **CSRF**: Double-submit cookie pattern (available but not enforced in dev)

## Testing
- Unit tests: `cd backend && python -m pytest tests/ -v`
- 20 tests covering: data collector, sub-positions, middlewares, save/load, VAT accuracy, 54-country coverage

## Running
The `start.sh` script launches both backend (uvicorn) and frontend (craco) concurrently.

## Web Crawling System
- **Algeria scraper**: `backend/crawlers/countries/algeria_conformepro_scraper.py` - Extracts 15,947 national sub-positions (10-digit HS codes) from conformepro.dz
  - 4-level hierarchy: Section (21) → Chapitre (97) → Rangée (HS4) → Sous-position (HS8/HS10)
  - Extracts: DD, TVA, TCS, PRCT, DAPS rates + fiscal advantages + administrative formalities
  - Rate limiting: 1.5s between requests
  - Progressive save during crawl
- **Crawl API routes**: 
  - `POST /api/crawl/start/{country_code}` - Start crawl (async background task)
  - `GET /api/crawl/status/{country_code}` - Check crawl progress
  - `GET /api/crawl/data/{country_code}` - View crawled data (paginated, filterable)
  - `GET /api/crawl/sources` - Available and planned crawlers
- **Crawled data stored in**: `backend/data/crawled/` (JSON files per country)
- **Morocco scraper**: `backend/crawlers/countries/morocco_douane_scraper.py` - Extracts national positions (10-digit HS codes) from douane.gov.ma/adil
  - Session-based ASP site: requires new HTTP session per chapter
  - Positions list via info_0.asp, taxes via info_2.asp, formalities via info_4.asp
  - Taxes: DI (Droit d'Importation), TPI (Taxe Parafiscale), TVA, TIC
  - Rate limiting: 2s between requests
  - ~96 chapters × ~100-900 positions/chapter
- **Planned crawlers**: Côte d'Ivoire (guce.gouv.ci), Cameroon, Senegal, South Africa, Kenya

## Recent Changes
- 2026-02-09: Built Morocco web crawler for douane.gov.ma/adil - extracts 10-digit positions with DI, TPI, TVA, TIC taxes and import formalities. Session-per-chapter approach bypasses ASP session constraints.
- 2026-02-09: Tunisia crawler operational - 11-digit NDP codes with DD, TVA, RPD, DC, FODEC, preferential tariffs, regulatory requirements
- 2026-02-09: Built Algeria web crawler for conformepro.dz - extracts real national sub-positions with exact designations, tax rates (DD, TVA, TCS, PRCT), fiscal advantages and formalities. Added crawl management API (start/status/data/sources endpoints)
- 2026-02-08: CSV export restructured to match douane.gov.dz hierarchy: Section (21) → Chapitre (97) → Rangée (HS4, 1229 headings from WCO 2022) → HS6 → Sub-positions. 12-column format with separate DAPS/DD/PRCT/TCS/TVA columns, utilization groups per chapter, corrected total calculation
- 2026-02-07: Enhanced tariff data format v2 - individual tax components (DAPS, DD, PRCT, TCS, TVA), fiscal advantages (ZLECAf exemptions), administrative formalities per product
- 2026-02-07: Created Algeria-specific tax module with verified rates: DAPS 30-200%, DD overrides per product, PRCT 2%, TCS 3%, TVA 19%/9%
- 2026-02-07: Calculator now returns taxes_detail[], fiscal_advantages[], administrative_formalities[] in response
- 2026-02-07: Connected collected tariff data to calculator - TariffDataService as single source of truth, auto-collection on startup, ETL fallback
- 2026-02-07: Added security middlewares (CSP, Rate Limiting, CSRF), monitoring dashboard, expanded sub-positions (1.18M total positions), unit tests (20 passing)
- 2026-02-07: Built tariff data collection system - 314,874 tariff lines for 54 countries with DD, VAT, other taxes
- 2026-02-07: Created crawl orchestration system with API routes, notification integration
- 2026-02-07: Initial Replit setup - configured ports, CORS, proxy, made MongoDB optional

## User Preferences
- Language: French preferred for technical discussions
- Focus: Fiscal/regulatory data accuracy for customs calculations
- Data priority: Individual tax components per product (not just DD + VAT totals)
- Validation reference: Algeria customs data (douane.gov.dz) for DAPS, DD, PRCT, TCS, TVA
