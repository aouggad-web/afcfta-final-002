# ZLECAf Trade Calculator - Product Requirements Document

## Original Problem Statement
Build a comprehensive African Continental Free Trade Area (AfCFTA) trade calculator platform that provides accurate tariff calculations, regulatory information, and trade intelligence for all 54 African countries.

## Core Requirements

### P0 - Critical
1. **Regulatory Engine v3**: Process, validate, and serve detailed tariff and compliance data (duties, taxes, requirements, formalities)
2. **Calculator UI**: Modern, functional calculator interface with country selection, HS code search, and results display
3. **Environment Stability**: Reliable backend/frontend services

### P1 - High Priority
1. **HS Code Search**: Smart search functionality for harmonized system codes
2. **Backend Modular Architecture**: Route-based structure for maintainability

### P2 - Medium Priority
1. **Sankey Diagram Integration**: Trade flow visualization
2. **Tariff Data for All Countries**: Expand coverage beyond Algeria

### P3-P5 - Lower Priority
3. **OEC Data Audit**: Correct trade statistics
4. **RASD Addition**: Add 55th country (Sahrawi Arab Democratic Republic)
5. **AfCFTA Stats Clarification**: Header statistics accuracy
6. **Economic Indicators Enhancement**: Verify and augment indicators
7. **Country Profile Enhancements**: New data sections and layout

## Architecture

```
/app
├── backend/
│   ├── app/
│   │   ├── services/
│   │   ├── models/
│   │   └── data/           # Source data (CSVs, JSONs)
│   ├── routes/             # Modular FastAPI routers
│   └── server.py           # FastAPI entry point
├── engine/                 # Regulatory Engine v3
│   ├── adapters/           # Country-specific adapters (dza_adapter.py)
│   ├── api/                # engine_service.py
│   ├── output/             # Generated canonical data (.jsonl)
│   ├── schemas/            # Pydantic schemas
│   └── pipeline.py         # Data processing pipeline
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   └── calculator/
│   │   │       ├── CalculatorTab.jsx
│   │   │       ├── RegulatoryDetailsPanel.jsx
│   │   │       └── EnhancedRegulatoryPanel.jsx
│   │   └── ...
│   └── package.json
└── memory/
    └── PRD.md
```

## Key API Endpoints
- `POST /api/calculate-tariff`: Core calculator endpoint
- `GET /api/hs6/smart-search`: HS code smart search
- `GET /api/regulatory-engine/details`: Regulatory Engine v3 data
- `GET /api/authentic-tariffs/calculate/{country}/{hs_code}`: Authentic tariff calculations

## Canonical Data Schema
- `commodity_codes.jsonl`: {country_code, commodity_code, description, hs6_code, chapter}
- `measures.jsonl`: {country_code, commodity_code, measure_code, name_fr, rate, base, notes}
- `requirements.jsonl`: {country_code, commodity_code, doc_code, name_fr, issuing_authority}

## Implementation Status

### Completed (December 2025)
- [x] Regulatory Engine v3 backend for Algeria (DZA)
- [x] Frontend integration with EnhancedRegulatoryPanel
- [x] Algerian data correction (tax names, authorities, calculations)
- [x] HS Code search bar fix
- [x] Calculator UI refactoring
- [x] 3-tab interface (Calculator, Réglementation, Comparaison Multi-Pays)

### In Progress
- [ ] Expand Regulatory Engine to Morocco (MAR)

### Backlog
- [ ] PostgreSQL migration for engine data
- [ ] OEC data audit
- [ ] RASD country addition
- [ ] AfCFTA stats clarification
- [ ] PDF export functionality

## Technical Notes
- User language preference: French
- Algeria canonical data: 37MB, 21,970 positions, 98 chapters
- API response time: <1ms for regulatory queries
