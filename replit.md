# ZLECAf Trade Calculator

## Overview
The ZLECAf Trade Calculator is an African Continental Free Trade Area (AfCFTA/ZLECAf) trade analysis platform. It offers tariff calculations, trade statistics, logistics information, production data, and AI-powered trade analysis for 54 African countries. Its core purpose is to provide accurate fiscal and regulatory data for customs calculations, ensuring transparency and facilitating trade across the continent.

## User Preferences
- Language: French preferred for technical discussions
- Focus: Fiscal/regulatory data accuracy for customs calculations
- Data priority: Individual tax components per product (not just DD + VAT totals)
- Validation reference: Algeria customs data (douane.gov.dz) for DAPS, DD, PRCT, TCS, TVA

## Repository Structure
```
backend/          ← FastAPI application (Python)
data/
├── json/         ← African trade/logistics JSON datasets (35 files)
├── csv/          ← ZLECAf CSV datasets (6 files)
└── xlsx/         ← ZLECAf Excel files (3 files)
engine/
└── crawlers/     ← TypeScript crawler utilities
scripts/          ← Utility & maintenance Python scripts
frontend/         ← React application (CRACO, port 5000)
SECURITY_CHECKLIST.md ← Security audit tracking
```

## System Architecture
The platform features a Python FastAPI backend (port 8000) and a React frontend (port 5000), with API requests proxied from the frontend to the backend. While MongoDB is optional, the system primarily relies on a robust tariff data system.

**Key Architectural Decisions:**
-   **Tariff Data System (Enhanced v2):** Collected tariff data in JSON format (`enhanced_v2`) serves as the single source of truth, including individual tax components, fiscal advantages, and administrative formalities. A `TariffDataService` singleton loads all collected data into memory, with auto-collection triggered if data files are absent.
-   **ETL Modules:** Dedicated ETL modules manage country-specific tax details (e.g., Algeria's DAPS, DD, PRCT, TCS, TVA rates, fiscal advantages, and administrative formalities) and chapter-level tariffs, leveraging a comprehensive HS6 code database (WCO 2022).
-   **Web Crawling System:** A sophisticated web crawling system extracts authentic, national-level tariff data from various customs websites across Africa (e.g., Algeria's conformepro.dz, Morocco's douane.gov.ma/adil, Ghana's UNIPASS, EAC CET, Egyptariffs, Nigeria's ECOWAS CET, South Africa's SARS).
    -   Crawlers handle diverse website structures, session management, and rate limiting.
    -   Crawled data is stored in `backend/data/crawled/` and normalized by `CrawledDataService` into a common schema.
    -   The calculator prioritizes `crawled_authentic` data, falling back to `collected_verified (ETL)` and then `etl_fallback`.
-   **Lazy Loading (CrawledDataService):** `crawled_data_service.py` now uses per-country lazy loading — at startup it only scans 54 `*_tariffs.json` files (~880 MB total) and registers paths; each country's data loads into memory only on first request. This prevents startup OOM kills.
-   **Auth (MongoDB optional):** `auth.py` `require_auth()` now returns a public-tier context when MongoDB is unavailable (`_db is None`), allowing all tariff endpoints to serve without a DB. API-key auth only activates when MongoDB is configured.
-   **DZA Tariff Calculation:** `authentic_tariff_service.py` now correctly calculates the full Algerian fiscal stack: DAPS (base=CIF) + DD (base=CIF) + PRCT (base=CIF) → VAT (base=CIF+DAPS+DD). DAPS and PRCT are extracted from `taxes_detail` and `other_taxes_rate` respectively, surfaced as `individual_taxes[]` in API responses.
-   **Algeria National Positions:** `backend/data/crawled/DZA_tariffs.json` consolidates 17,115 10-digit national positions from conformepro.dz with correct DAPS/DD rates per chapter (ch.76 aluminum: DAPS=60%, DD=30%). `backend/data/DZA_tariffs.json` (used by `authentic_tariff_service`) has matching corrected rates with `taxes_detail` in dict format.
-   **Security:** Implemented with CSP headers, rate limiting (120 req/min), CSRF protection, and other standard security headers (X-Content-Type-Options, X-Frame-Options, XSS-Protection, HSTS, Referrer-Policy, Permissions-Policy).
-   **UI/UX:** The frontend utilizes React with a focus on a clean, modern interface, including a compact dark green header, sticky navigation, and smooth transitions.
-   **Data Structure:** Tariff data includes detailed tax components (`taxes_detail{}` dict keyed by tax code), `fiscal_advantages[]`, and `administrative_formalities[]` per product. HS codes are structured hierarchically (Section → Chapter → HS4 → HS6 → Sub-positions up to 10 digits for DZA).

## External Dependencies
-   **Backend Framework:** FastAPI (Python)
-   **Frontend Framework:** React (with CRACO for configuration)
-   **Database:** MongoDB (optional)
-   **Web Scraping Libraries:** PyMuPDF (for PDF extraction)
-   **Data Sources (Crawled):**
    -   conformepro.dz (Algeria)
    -   douane.gov.ma/adil (Morocco)
    -   external.unipassghana.com (Ghana UNIPASS/ICUMS)
    -   kra.go.ke (EAC CET PDF)
    -   egyptariffs.com (Egyptian Customs Authority)
    -   customs.erca.gov.et (Ethiopian Customs Commission - ECC)
    -   guce.gouv.ci (Côte d'Ivoire GUCE - Guichet Unique du Commerce Extérieur)
    -   customs.gov.ng (Nigeria ECOWAS CET PDFs)
    -   sars.gov.za (South Africa SARS)
    -   douanes.sn + TEC CEDEAO (Senegal - ECOWAS TEC with national taxes)
    -   CEMAC Tarif des Douanes PDF (Cameroon - CEMAC CET)
    -   ECOWAS TEC + national taxes (Benin, Burkina Faso, Mali, Niger, Togo, Guinea)
    -   CEMAC TEC + national taxes (Gabon, Congo-Brazzaville, Chad, Central African Republic)
-   **Data Sources (ETL):** WCO Harmonized System 2022 for HS6 codes, various national customs and tax authority data sources.
-   **Notification System:** Email, Slack (for alerts)
-   **Testing Framework:** Pytest (Python)