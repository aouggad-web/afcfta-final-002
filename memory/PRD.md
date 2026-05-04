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

## Imported Capabilities (already present in repo)
- 54 African countries tariff data (`backend/data/*_tariffs.json`)
- HS6 / HS4 catalog and rules of origin
- Calculator (basic + enhanced v2/v3)
- Country profiles, statistics, regional analytics (CEDEAO, CEMAC, EAC, SADC, North Africa, UMA)
- Trade data (WTO, OEC, World Bank, UNCTAD, FAOSTAT, Comtrade)
- Logistics: ports / airports / land transport, fees, operators
- Banking system (registry, FX, payments, trade finance, regulatory)
- Notifications (Email + Slack)
- Data export (CSV/Excel)
- Auth via API keys (`X-API-Key` header), admin keys management
- Crawlers for tariff updates
- Scheduler for exchange rates (every 4h)
- PWA: service worker, offline page, manifest

## Setup Done
- Cloned repo into `/app` (preserving `.git`, `.emergent`, and pre-existing `backend/.env`, `frontend/.env`)
- `pip install -r backend/requirements.txt` in supervisor venv
- `yarn install` in frontend (added `craco` and other deps)
- Restarted supervisor — backend, frontend, mongodb all RUNNING
- Verified: `GET /api/health` returns healthy, `GET /api/` returns API banner
- Verified: Frontend dashboard ("ZLECAf Intelligence") loads with country/stats data

## Known Notes / Observations
- `EMERGENT_LLM_KEY` not set → Gemini AI analysis routes will be disabled until set
- `sqlalchemy` not installed → Postgres-backed search route disabled (graceful fallback)
- Some endpoints require `X-API-Key` header (admin-protected)
- Notification channels disabled until SMTP/Slack envs configured

## Next Action Items (waiting on user)
- User has not yet specified which features to add or which bugs to fix
- When user provides specifics, continue implementation iteratively

## Backlog / Future
- Configure EMERGENT_LLM_KEY / Gemini key if AI analysis features are needed
- Configure SMTP and Slack webhook for notifications
- Add postgres dependency if Postgres-backed tariff search is desired
