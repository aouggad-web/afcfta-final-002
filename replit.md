# ZLECAf Trade Calculator

## Overview
The ZLECAf Trade Calculator is an African Continental Free Trade Area (AfCFTA/ZLECAf) trade analysis platform. It offers tariff calculations, trade statistics, logistics information, production data, and AI-powered trade analysis for 54 African countries. Its core purpose is to provide accurate fiscal and regulatory data for customs calculations, ensuring transparency and facilitating trade across the continent.

## User Preferences
- Language: French preferred for technical discussions
- Focus: Fiscal/regulatory data accuracy for customs calculations
- Data priority: Individual tax components per product (not just DD + VAT totals)
- Validation reference: Algeria customs data (douane.gov.dz) for DAPS, DD, PRCT, TCS, TVA

## System Architecture
The platform features a Python FastAPI backend (port 8000) and a React frontend (port 5000), with API requests proxied from the frontend to the backend. While MongoDB is optional, the system primarily relies on a robust tariff data system.

**Key Architectural Decisions:**
-   **Tariff Data System (Enhanced v2):** Collected tariff data in JSON format (`enhanced_v2`) serves as the single source of truth, including individual tax components, fiscal advantages, and administrative formalities. A `TariffDataService` singleton loads all collected data into memory, with auto-collection triggered if data files are absent.
-   **ETL Modules:** Dedicated ETL modules manage country-specific tax details (e.g., Algeria's DAPS, DD, PRCT, TCS, TVA rates, fiscal advantages, and administrative formalities) and chapter-level tariffs, leveraging a comprehensive HS6 code database (WCO 2022).
-   **Web Crawling System:** A sophisticated web crawling system extracts authentic, national-level tariff data from various customs websites across Africa (e.g., Algeria's conformepro.dz, Morocco's douane.gov.ma/adil, Ghana's UNIPASS, EAC CET, Egyptariffs, Nigeria's ECOWAS CET, South Africa's SARS).
    -   Crawlers handle diverse website structures, session management, and rate limiting.
    -   Crawled data is stored in `backend/data/crawled/` and normalized by `CrawledDataService` into a common schema.
    -   The calculator prioritizes `crawled_authentic` data, falling back to `collected_verified (ETL)` and then `etl_fallback`.
-   **Security:** Implemented with CSP headers, rate limiting (120 req/min), CSRF protection, and other standard security headers (X-Content-Type-Options, X-Frame-Options, XSS-Protection, HSTS, Referrer-Policy, Permissions-Policy).
-   **UI/UX:** The frontend utilizes React with a focus on a clean, modern interface, including a compact dark green header, sticky navigation, and smooth transitions.
-   **Data Structure:** Tariff data includes detailed tax components (`taxes_detail[]`), `fiscal_advantages[]`, and `administrative_formalities[]` per product. HS codes are structured hierarchically (Section → Chapter → HS4 → HS6 → Sub-positions).

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
    -   customs.gov.ng (Nigeria ECOWAS CET PDFs)
    -   sars.gov.za (South Africa SARS)
-   **Data Sources (ETL):** WCO Harmonized System 2022 for HS6 codes, various national customs and tax authority data sources.
-   **Notification System:** Email, Slack (for alerts)
-   **Testing Framework:** Pytest (Python)