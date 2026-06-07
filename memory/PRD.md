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

### June 7, 2026 — Recherche SH2/SH4/SH6 + Intitulé (Statistiques → Par Pays & SH6)
- Sous-module « Par Pays & SH6 » : recherche en **onglets séparés Chapitre (SH2) / Position (SH4) / Sous-position (SH6)**, chacun avec agrégation correcte (SH2 = tout le chapitre, SH4 = toute la position, SH6 = sous-position exacte).
- Nouvel **onglet « Intitulé »** affichant le libellé officiel OMD du code SH sélectionné (FR/EN, chapitre, position, catégorie).
- Backend : param `level` (hs2/hs4/hs6) sur `/api/oec/country/{iso3}/hs6/{code}/history` (filtrage explicite par niveau via les 6 derniers chiffres de l'ID OEC) ; nouvel endpoint `/api/hs-codes/label/{code}`.
- Le changement d'onglet relance automatiquement la requête au bon niveau. Testé via curl + screenshots (Algérie ch.27 = 205,6 Md$ cumulés).


### June 7, 2026 — Calculateur de fret terrestre (Logistique → Terrestre)
- Calculateur de fret routier/ferroviaire sur les **15 corridors PIDA** africains (longueur réelle, postes-frontières, OSBP, opérateurs).
- Modèle : transport ($/tonne-km × tonnage × distance × coef. marchandise) + franchissement frontières (réduit pour OSBP) + documentation ; choix du mode (route/rail selon corridor) ; délais selon vitesse + attentes frontières.
- Calibré Banque Mondiale SSATP / UNECA / AfDB 2024. Endpoints : `GET /api/logistics/land/fees/{corridors|cargo-types|cost}`.
- Frontend : `LandFreightCalculator.jsx` intégré dans l'onglet « Terrestre (Corridors) ».
- Testé : curl + screenshot (Abidjan-Lagos route 30 t = 4 080 $, 0,1371 $/tonne-km).


### June 7, 2026 — Calculateur de fret aérien (Logistique → Aérien)
- Nouveau calculateur de fret aérien couvrant les **64 aéroports cargo** africains (registre `logistics_air_data`).
- Méthodologie IATA TACT : poids taxable = max(poids réel, poids volumétrique à 167 kg/m³), + FSC (carburant), SSC (sûreté), manutention/LTA, charge minimale ; coefficients par nature de marchandise (général, périssable, pharma, DGR, valeur, animaux vivants).
- Modèle distance-coût calibré (IATA TACT 2024 + tarifs cargo compagnies africaines) ; sélection des compagnies par région ; délais selon connectivité hub.
- Endpoints : `GET /api/logistics/air/fees/airports`, `/air/fees/commodities`, `/air/fees/cost`.
- Frontend : `AirFreightCalculator.jsx` intégré dans l'onglet « Aérien (Fret) », sélecteurs groupés par région, décomposition des coûts + poids taxable.
- Testé via curl + screenshot (Nairobi→Lagos 1000 kg/4 m³ périssable = 4 590 $).


### June 7, 2026 — Expansion du calculateur de fret maritime (Logistique)
- Couverture portuaire passée de **21 → 55 ports** africains à conteneurs (5 façades : Méditerranée, Atlantique, Mer Rouge, Océan Indien, îles).
- Matrice de routes complète : **1 485 paires** (32 routes "benchmark" tarifs armateurs publiés + 1 453 routes modélisées).
- Modèle distance-coût calibré (Drewry 2024 / UNCTAD MRTS 2024) avec distances maritimes réalistes via points de passage (Gibraltar, Suez, Bab-el-Mandeb, Cap de Bonne-Espérance).
- Nouvel endpoint `GET /api/logistics/fees/ports` ; frontend charge les ports dynamiquement, sélecteurs groupés par région, badge provenance "Publié/Estimé", tableau plafonné à 250 lignes.
- Fichiers : `backend/logistics_fees_data.py` (réécrit), `backend/routes/logistics.py`, `frontend/src/components/logistics/ShippingFeesCalculator.jsx`.
- Testé via curl (endpoints) + screenshot (UI Lomé→Mombasa OK).
- ⚠️ Disque `/app` était plein à 100% — caches nettoyés (~1,9 Go libres). Sauvegarde locale pré-pull GitHub dans `/app/.local_backups/`.


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

## Tech Stack Versions
- Python 3.11+
- React 18
- FastAPI 0.100+
- PostgreSQL 15
- Redis 7
