# ZLECAf Trade Calculator - PRD

## Original Problem Statement
Build a comprehensive regulatory data engine for all 54 AfCFTA countries with a full-stack trade calculator application featuring tariff calculations, regulatory compliance, and trade analytics.

## Core Requirements
1. **Regulatory Engine**: Process, validate, and serve detailed tariff and compliance data for all African countries
2. **Trade Calculator**: Calculate import taxes comparing NPF vs ZLECAf regimes with savings display
3. **Multi-Country Support**: Cover all 54 AfCFTA member states
4. **Data Accuracy**: Display authentic national tariff positions with exact descriptions

## Architecture
- **Backend**: FastAPI (Python)
- **Frontend**: React + Vite + Tailwind CSS + Shadcn UI
- **Database**: MongoDB (primary), PostgreSQL (regulatory data - migration done)
- **Caching**: Redis

## What's Been Implemented

### March 15, 2026 - PostgreSQL Migration Complete
- ✅ Migrated all 54 countries to PostgreSQL (894,783 records)
- ✅ Created full-text search index for French descriptions
- ✅ New `/api/postgres-tariffs/*` API endpoints
- ✅ Frontend updated to use PostgreSQL API with fallback
- ✅ Real national tariff descriptions (e.g., Kenya: "Café Arabica AA" instead of "Type 1")
- Note: Some countries (Algeria) use generic labels in their official nomenclature

### March 15, 2026 - Banking System Integration
- ✅ Added Banking tab with full African banking system data
- ✅ Integrated `banking_system` module (banks_registry, foreign_exchange, trade_finance, risk_assessment, compliance)
- ✅ Created `/api/banking/*` endpoints for country banks, regulations, risk assessment
- ✅ BankingInfoPanel component with tabs: Banks, Forex, Risk, Instruments, Payment Systems, Compliance

### March 15, 2026 - GitHub Update
- Added African currencies system (`currencies.py`, `exchange_rates.py`)
- Added AI intelligence routes (`ai_intelligence.py`, `investment_intelligence.py`)
- Added regional analytics dashboard
- Added shipping fees calculator
- Added comprehensive search component

### Previous Sessions
- ✅ Built Regulatory Engine v3
- ✅ PostgreSQL migration (1.5GB regulatory data)
- ✅ Text Search API (French/English support)
- ✅ Redis caching implementation
- ✅ OEC data audit (fixed NaN values)
- ✅ UI flickering fix
- ✅ Calculator UI enhancements

## Pending Issues
1. **P0**: National positions display "Type 1, Type 2" instead of exact descriptions
2. **P1**: Core API still uses flat files (.jsonl) instead of PostgreSQL

## Prioritized Backlog

### P0 (Critical)
- [ ] Fix national position descriptions in calculator

### P1 (High)
- [ ] Refactor `/api/authentic-tariffs/calculate` to use PostgreSQL
- [ ] Refactor `/api/regulatory-engine/details` to use PostgreSQL

### P2 (Medium)
- [ ] Integrate Sankey Diagram (PR pending)
- [ ] Full API v2 migration

### P3 (Low)
- [ ] Add RASD (Sahrawi Arab Democratic Republic) as 55th country
- [ ] Audit economic indicators

### P4 (Enhancement)
- [ ] Enhanced country profile pages
- [ ] Mobile API optimization

## API Endpoints
- `GET /api/health` - Health check
- `POST /api/authentic-tariffs/calculate` - Tariff calculation
- `GET /api/authentic-tariffs/country/{iso3}/sub-positions/{hs6}` - Sub-positions
- `GET /api/commodities/search` - Text search (PostgreSQL)
- `GET /api/statistics` - Dashboard statistics
- `GET /api/currencies` - African currencies (NEW)
- `GET /api/exchange-rates` - Exchange rates (NEW)
- `GET /api/banking` - Banking information (NEW)

## Credentials
- **PostgreSQL**: set `POSTGRES_URL` in `.env` (see `.env.example`)
- **Redis**: set `REDIS_URL` in `.env` (see `.env.example`)
- **Emergent LLM Universal Key**: `EMERGENT_LLM_KEY` in `/app/backend/.env` (powers Claude Sonnet 4.6 / Haiku 4.5 via `emergentintegrations`)
- **Claude Bulk Mode**: `CLAUDE_BULK_MODE="true"` activates Haiku (10× faster + cheaper) for live requests

## Tech Stack Versions
- Python 3.11+
- React 18
- FastAPI 0.100+
- PostgreSQL 15
- Redis 7

## June 14, 2026 — Opportunities module migrated to Anthropic Claude (preview-ready)
- ✅ Imported from `aouggad-web/afcfta-final-002@main` (selective merge, code only, data protected)
- ✅ New `services/claude_trade_service.py` (1098 lines, adapted to use `emergentintegrations` + Emergent LLM Universal Key)
- ✅ Updated `routes/gemini_analysis.py` — `/ai/*` endpoints now powered by Claude:
  - `GET /api/ai/health` — service status
  - `GET /api/ai/compare` — **NEW** bilateral country comparison (complementarité commerciale)
  - `GET /api/ai/summary` — AfCFTA overview
  - `GET /api/ai/value-chains` — value chain analysis
  - `GET /api/ai/opportunities/{country}` — export/import/industrial opportunities
  - `GET /api/ai/profile/{country}` — country economic profile
  - `GET /api/ai/product/{hs_code}` — product analysis
  - `GET /api/ai/balance/{country}` — trade balance
- ✅ Updated `services/redis_cache_service.py` — JSON file fallback under `/app/backend/data/ai_cache/` (survives restarts when Redis unavailable)
- ✅ Frontend opportunities module:
  - 6 sub-tabs: Analyse IA · Substitution · Vue d'ensemble · Chaînes de Valeur · Par Produit · **Comparaison (NEW)**
  - Updated: `OpportunitiesTab.jsx`, `AIAnalysis.jsx`, `OpportunitySummary.jsx`, `ProductAnalysisView.jsx`
  - New: `CountryComparison.jsx` (473 lines)
- ✅ Critical data preserved during selective merge:
  - DZA 7610909910 sous-position (DAPS 60 / DD 5 / PRCT 2 / TCS 3 / TVA 19) — intact
  - DZA 721090 (DD 30 / DAPS 60) — intact
  - CSV 54 pays ZLECAF + 117 projets structurants — intact
  - `frontend/src/index.js` X-API-Key interceptor (6 occurrences) — intact
  - `backend/.env` SECRET_KEY — intact + `EMERGENT_LLM_KEY` ajoutée

### Known constraint (gateway timeout)
- Claude API call duration: 60–90 s for cold pairs (uncached)
- Kubernetes ingress hard timeout: 60 s → first call to a new country pair returns 502 from gateway, but the request completes server-side and populates the file cache; subsequent calls return instantly (< 100 ms).
- Mitigation deployed: `CLAUDE_BULK_MODE=true` uses Haiku model (faster, ~10× cheaper).
- For full smooth demo: pre-warm the cache for common pairs (e.g. Morocco/Algeria already cached).
