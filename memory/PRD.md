# ZLECAf Trade Calculator - Product Requirements Document

## Original Problem Statement
Build a comprehensive African Continental Free Trade Area (AfCFTA) trade calculator platform that provides accurate tariff calculations, regulatory information, and trade intelligence for all 54 African countries.

## Core Requirements

### P0 - Critical ✅ DONE
1. **Regulatory Engine v3**: Process, validate, and serve detailed tariff and compliance data
2. **Calculator UI**: Modern, functional calculator interface
3. **Environment Stability**: Reliable backend/frontend services

### P1 - High Priority ✅ DONE  
1. **HS Code Search**: Smart search functionality for harmonized system codes
2. **Extend Regulatory Engine**: Support for 8 major African countries
3. **Backend Modular Architecture**: Route-based structure

### P2 - Medium Priority 🔄 IN PROGRESS
1. **PostgreSQL Migration**: Database setup complete, migration ready to execute
2. **Sankey Diagram Integration**: Trade flow visualization
3. **Full 54-country coverage**: Tariff data available for remaining countries

### P3-P5 - Lower Priority
- OEC Data Audit
- RASD (55th country) Addition
- AfCFTA Stats Clarification
- Economic Indicators Enhancement
- Country Profile Enhancements
- PDF Export functionality

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
│   ├── adapters/           
│   │   ├── base_adapter.py
│   │   ├── dza_adapter.py      # Algeria specific
│   │   └── generic_adapter.py  # NEW: Universal adapter for all countries
│   ├── api/                
│   │   └── engine_service.py
│   ├── database/           # NEW: PostgreSQL migration
│   │   ├── models.py       # SQLAlchemy models
│   │   └── migration.py    # Migration service
│   ├── output/             # Generated canonical data (232MB total)
│   │   ├── DZA_canonical.jsonl (37MB, 16,569 records)
│   │   ├── MAR_canonical.jsonl (27MB, 16,575 records)
│   │   ├── EGY_canonical.jsonl (24MB, 16,570 records)
│   │   ├── NGA_canonical.jsonl (31MB, 16,577 records)
│   │   ├── ZAF_canonical.jsonl (24MB, 16,568 records)
│   │   ├── KEN_canonical.jsonl (27MB, 16,572 records)
│   │   ├── CIV_canonical.jsonl (31MB, 16,567 records)
│   │   └── GHA_canonical.jsonl (34MB, 16,572 records)
│   ├── schemas/            
│   └── pipeline.py         # Data processing pipeline (8 countries)
├── frontend/
│   ├── src/components/calculator/
│   │   ├── CalculatorTab.jsx       # Updated with 8-country badges
│   │   ├── RegulatoryDetailsPanel.jsx
│   │   └── EnhancedRegulatoryPanel.jsx
│   └── package.json
└── memory/
    └── PRD.md
```

## Key API Endpoints
- `POST /api/calculate-tariff`: Core calculator endpoint
- `GET /api/hs6/smart-search`: HS code smart search
- `GET /api/regulatory-engine/details`: Regulatory Engine v3 data (8 countries)
- `GET /api/authentic-tariffs/calculate/{country}/{hs_code}`: Authentic tariff calculations

## Countries with Full Regulatory Data (Moteur Réglementaire v3)

| ISO3 | Country | Currency | VAT | Records |
|------|---------|----------|-----|---------|
| DZA | Algérie | DZD | 19% | 16,569 |
| MAR | Maroc | MAD | 20% | 16,575 |
| EGY | Égypte | EGP | 14% | 16,570 |
| NGA | Nigeria | NGN | 7.5% | 16,577 |
| ZAF | Afrique du Sud | ZAR | 15% | 16,568 |
| KEN | Kenya | KES | 16% | 16,572 |
| CIV | Côte d'Ivoire | XOF | 18% | 16,567 |
| GHA | Ghana | GHS | 15% | 16,572 |

**Total: 132,570 tariff line records**

## PostgreSQL Schema (Ready for Migration)

```sql
-- Countries table
CREATE TABLE countries (
    iso3 VARCHAR(3) PRIMARY KEY,
    name_fr VARCHAR(100),
    currency VARCHAR(3),
    vat_rate FLOAT,
    total_positions INTEGER
);

-- Commodities table (main tariff lines)
CREATE TABLE commodities (
    id SERIAL PRIMARY KEY,
    country_iso3 VARCHAR(3) REFERENCES countries(iso3),
    national_code VARCHAR(15),
    hs6 VARCHAR(6),
    description_fr TEXT,
    total_npf_pct FLOAT,
    total_zlecaf_pct FLOAT,
    savings_pct FLOAT
);

-- Measures table (taxes/duties)
CREATE TABLE measures (
    id SERIAL PRIMARY KEY,
    commodity_id INTEGER REFERENCES commodities(id),
    measure_type VARCHAR(20),
    code VARCHAR(20),
    rate_pct FLOAT,
    zlecaf_rate_pct FLOAT
);

-- Requirements table (documents)
CREATE TABLE requirements (
    id SERIAL PRIMARY KEY,
    commodity_id INTEGER REFERENCES commodities(id),
    code VARCHAR(20),
    document_fr VARCHAR(300),
    issuing_authority VARCHAR(200)
);
```

## Implementation Status

### Completed (March 2026)
- [x] Regulatory Engine v3 extended to 8 major countries
- [x] Generic adapter for enhanced_v2 format
- [x] 132,570 canonical records generated
- [x] PostgreSQL models and migration service created
- [x] UI updated with "Disponible" badges for all 8 countries
- [x] Pipeline updated to process multiple countries

### In Progress
- [ ] Execute PostgreSQL migration (infrastructure ready)

### Backlog
- [ ] Add remaining 46 countries to regulatory engine
- [ ] OEC data audit
- [ ] RASD country addition
- [ ] Text search API for products
- [ ] PDF export functionality

## Technical Notes
- User language preference: French
- API response time: <2ms for regulatory queries
- Data format: enhanced_v2 JSON with sub-positions
