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
- **PostgreSQL**: `postgresql://afcfta:afcfta2026@localhost:5432/afcfta_regulatory`
- **Redis**: `redis://localhost:6379`

## Tech Stack Versions
- Python 3.11+
- React 18
- FastAPI 0.100+
- PostgreSQL 15
- Redis 7
