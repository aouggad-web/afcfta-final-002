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
- **Ghana UNIPASS scraper**: `backend/crawlers/countries/ghana_unipass_scraper.py` - Extracts HS10 positions from UNIPASS/ICUMS
  - Source: external.unipassghana.com - POST-based pagination
  - 6,447 positions with 5 tax columns: Import Duty, VAT, Excise, Export Duty, NHIL
  - ECOWAS CET 5-band system (0%, 5%, 10%, 20%, 35%)
  - Progressive save + resume capability
- **EAC CET scraper**: `backend/crawlers/countries/eac_cet_scraper.py` - Extracts HS8 from EAC CET 2022 PDF
  - Source: kra.go.ke - EAC Common External Tariff PDF
  - 5,984 positions for 7 EAC countries (KEN, TZA, UGA, RWA, BDI, SSD, COD)
  - Taxes: CET Import Duty, IDF (3.5%), RDL (2%), VAT (16-18%)
  - EAC CET 3-band + sensitive items (0%, 10%, 25%, 35%)
- **Planned crawlers**: Côte d'Ivoire (guce.gouv.ci), Cameroon, Senegal
- **Nigeria CET scraper**: `backend/crawlers/countries/nigeria_cet_scraper.py` - Extracts HS10 positions from ECOWAS CET PDFs
  - Source: customs.gov.ng - 97 chapter PDFs
  - PyMuPDF find_tables() for structured extraction
  - Taxes: ID (Import Duty), VAT, IAT (Import Adjustment Tax), EXC (Excise Duty)
  - 6,363 positions across 96 chapters
- **South Africa SARS scraper**: `backend/crawlers/countries/southafrica_sars_scraper.py` - Extracts SACU tariff from single PDF
  - Source: sars.gov.za - Schedule 1 Part 1 (703 pages)
  - HS8 codes with 6 duty columns: General, EU/UK, EFTA, SADC, MERCOSUR, AfCFTA
  - 8,589 positions per SACU country (ZAF, BWA, LSO, SWZ, NAM)
  - Compound rates supported (e.g., "25% or 220c/kg")

## Crawled Data Integration
- **CrawledDataService**: `backend/services/crawled_data_service.py` - Singleton service loading authentic crawled data
  - Loads from `backend/data/crawled/*_tariffs.json` at startup
  - Normalizes 7 different country formats (DZA/TUN/MAR/NGA/SACU/EAC/GHA) into common schema
  - Indexes by exact HS code and HS6 prefix for fast lookup
  - 144,964 authentic positions indexed across 17 countries:
    - DZA: 17,115 (conformepro.dz)
    - TUN: 17,512 (douane.gov.tn)
    - MAR: 13,114 (douane.gov.ma)
    - NGA: 6,363 (customs.gov.ng - ECOWAS CET)
    - ZAF/BWA/LSO/SWZ/NAM: 8,589 each (sars.gov.za - SACU)
    - KEN/TZA/UGA/RWA/BDI/SSD/COD: 5,984 each (EAC CET 2022)
    - GHA: 6,447 (unipassghana.com - UNIPASS/ICUMS)
- **Calculator priority**: crawled_authentic → collected_verified (ETL) → etl_fallback
- **Data source field**: `data_source` in response indicates origin ("crawled_authentic" for verified data)
- **API endpoints**:
  - `GET /api/crawled-data/status` - Service status and loaded countries
  - `POST /api/crawled-data/reload` - Reload after new crawl completes
  - `GET /api/crawled-data/lookup/{country}/{hs_code}` - Direct lookup
  - `GET /api/crawled-data/search/{country}?q=...` - Search by code or designation

## Recent Changes
- 2026-02-18: Added Ghana UNIPASS scraper - 6,447 HS10 positions with 5 taxes (Import Duty, VAT, Excise, Export Duty, NHIL) from external.unipassghana.com. Progressive save + resume capability.
- 2026-02-18: Added EAC CET scraper - 5,984 HS8 positions for 7 EAC countries (KEN, TZA, UGA, RWA, BDI, SSD, COD) from EAC CET 2022 PDF. CET 3-band + IDF + RDL + VAT.
- 2026-02-18: Updated CrawledDataService with `_normalize_eac_gha()` for EAC/GHA formats. Total: 144,964 authentic positions across 17 countries.
- 2026-02-17: Updated all statistics to 2024 data - OEC/BACI API now covers 2018-2024, default year changed to 2024 across all endpoints, trade products data updated (growth_2023_2024), 2023 data preserved for comparison
- 2026-02-17: UI modernization - compact dark green header, sticky underline navigation tabs, smoother transitions, discrete scrollbar, cleaner layout with custom CSS (no Radix Tabs dependency in App shell)
- 2026-02-17: Added Nigeria CET scraper (6,363 HS10 positions from 97 PDF chapters) and South Africa SARS/SACU scraper (8,589 HS8 positions for 5 SACU countries). Total: 97,036 authentic positions across 9 countries.
- 2026-02-17: Updated CrawledDataService with `_normalize_standard()` for NGA/SACU formats, supporting all 9 countries
- 2026-02-11: Integrated 47,741 authentic crawled positions into calculator - CrawledDataService with 3-tier priority (crawled → ETL → fallback), new API endpoints for lookup/search/reload
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
