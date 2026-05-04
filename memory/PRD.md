# PRD — ZLECAf Trade Calculator (afcfta-final-002)

## Original Problem Statement
Import from GitHub repository `aouggad-web/afcfta-final-002`, set it up to run, and continue building features / fix bugs.

## Source
- Repo: https://github.com/aouggad-web/afcfta-final-002 (public)
- Imported on: 2026-05-04

## Architecture
- Backend: FastAPI (`/app/backend/server.py`, version 3.0.0) — modular routes under `backend/routes/`, services under `backend/services/`, ETL under `backend/etl/`, crawlers under `backend/crawlers/`
- Frontend: React 19 + CRA + craco + Tailwind + Radix UI + i18next (`/app/frontend`)
- Database: MongoDB (`mongodb://localhost:27017`, DB `test_database`)
- Other: Optional Redis cache, optional PostgreSQL for tariff data, APScheduler for exchange rates
- Routing: All backend routes prefixed with `/api`; frontend uses `REACT_APP_BACKEND_URL`

## Imported Capabilities
- 54 African countries tariff data (`backend/data/*_tariffs.json`)
- HS6 / HS4 catalog and rules of origin (`backend/data/hs6_database.json`)
- Calculator (basic + enhanced v2/v3) with country/national positions
- Country profiles with World Bank Outlook indicators (PIB, IDH, inflation, chômage, dette, etc.)
- Trade data (WTO, OEC, World Bank, UNCTAD, FAOSTAT, Comtrade)
- Logistics: ports / airports / land transport, fees, operators
- Banking system (registry, FX, payments, trade finance, regulatory)
- Notifications (Email + Slack)
- Data export (CSV/Excel)
- Auth via API keys (`X-API-Key` header), admin keys management
- Crawlers for tariff updates / Scheduler for exchange rates
- PWA: service worker, offline page, manifest

## Sessions / Iterations Done

### 2026-05-04 (Day 1)
1. **Import & setup**: cloned repo into `/app`, preserved `.git`/`.emergent`/`.env`, ran `pip install -r requirements.txt`, `yarn install` (added missing `craco`), services up.
2. **Backend connection fix**: All API routes required `X-API-Key`; created seed of default frontend API key in MongoDB on startup (env: `FRONTEND_API_KEY`), injected `X-API-Key` header default in axios + monkey-patched `fetch()` in `index.js` (env: `REACT_APP_API_KEY`).
3. **Calculator HS6 search fix**: `TariffSearchEngine` was looking in `/app/tariff_engine/normalized/` (empty); added fallback that loads from `/app/backend/data/hs6_database.json` + per-country tariff files. Sanitized NaN values for JSON serialization.
4. **National positions selector fix**: When PostgreSQL endpoint returns 503, fallback now goes to `/api/authentic-tariffs/...` instead of `/api/hs6/smart-search` (which doesn't return sub-positions).
5. **Country profile WB data fix**: Restored real economic CSV files (`ZLECAf_ENRICHI_2024_COMMERCE.csv` and `ZLECAF_54_PAYS_DONNEES_COMPLETES.csv`) from commit `7596094` (a later commit had replaced them with empty 2-line stubs).
6. **Country Profiles Tab regression fix**: Applied PR #79 (`f08cc18`) — replaces `field && ...` with `field != null && ...` to correctly render `0` values.
7. **Projets Structurants extension**: extended from 15 → 54 countries (full AfCFTA coverage) with verified mega-projects 2025-2030 from first-tier sources.
8. **Projets Structurants update for 15 existing countries**: refreshed with 2025-2026 verified statuses (sources: APS, AFP, Reuters, World Bank, AfDB, Rosatom, S&P Global, Argus Media, MIGA, Kenya Railways, TRC, Ivanhoe Mines, FOCAC, AMEA Power, PV Magazine, DFC, DBSA, etc.). Notable updates:
   - Algeria: Béchar-Gara Djebilet ✅ inaugurée 01/02/2026; El Hamdania ❌ abandonné 10/06/2025
   - Ethiopia: GERD ✅ inauguré 09/09/2025
   - Tunisia: Kairouan 120 MWp solaire ✅ mis en service 16/12/2025
   - DRC: Inga III Phase 1 ($250M) ✅ approuvée 03/06/2025; Kamoa-Kakula 388 838 t Cu en 2025
   - Tanzania: SGR fret ✅ depuis 06/2025; ligne Burundi 1ère pierre 08/2025
   - Egypt: El Dabaa cuve Unit 1 installée 11/2025
   - Nigeria: Dangote refinery extension vers 1.4M b/j en 2028

## Files Modified Notable
- `/app/backend/server.py` — seed `api_keys` collection on startup
- `/app/backend/.env` — `FRONTEND_API_KEY`
- `/app/frontend/.env` — `REACT_APP_API_KEY`
- `/app/frontend/src/index.js` — axios + fetch X-API-Key injection
- `/app/backend/search/hs_code_search.py` — JSON fallback + NaN sanitization
- `/app/frontend/src/components/NationalPositionsSelector.jsx` — fallback to authentic-tariffs
- `/app/frontend/src/components/profiles/CountryProfilesTab.jsx` — falsy-zero fix (PR #79)
- `/app/data/csv/ZLECAf_ENRICHI_2024_COMMERCE.csv` — restored real data (54 rows)
- `/app/data/csv/ZLECAF_54_PAYS_DONNEES_COMPLETES.csv` — restored real data
- `/app/data/json/projets_structurants_afrique.json` — 15 → 54 countries with verified projects

## Known Notes
- `EMERGENT_LLM_KEY` not set → Gemini AI analysis routes disabled until configured
- Some endpoints require admin tier API key (separate from frontend public key)
- Notification channels (Email/Slack) disabled until SMTP/Slack envs configured
- DZA nomenclature_map.json (17 115 entries) NOT yet integrated as enriched sub-positions in calculator (would require fusion script)

## Next Action Items / Backlog
- Optional: integrate `DZA_nomenclature_map.json` rich descriptions into DZA tariff sub_positions
- Optional: extend tariff DAPS rates beyond ~150 HS6 currently in `etl/country_taxes_algeria.py`
- Optional: add admin UI for bulk-edit of tariff rates per country (CSV upload)
- Optional: configure Gemini key for AI analysis features
- Optional: add SMTP/Slack settings for notifications

## Test Credentials
See `/app/memory/test_credentials.md` for the public frontend API key and any test accounts.
