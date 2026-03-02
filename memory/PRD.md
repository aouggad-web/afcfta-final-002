# ZLECAf Trade Calculator - Product Requirements Document

## Original Problem Statement
Build a comprehensive African Continental Free Trade Area (AfCFTA) trade calculator platform that provides accurate tariff calculations, regulatory information, and trade intelligence for all 54 African countries.

## Implementation Status: MAJOR MILESTONE ACHIEVED ✅

### Regulatory Engine v3 - 54/54 Countries Complete
All 54 AfCFTA member countries now have full regulatory data in the canonical format.

### PostgreSQL Migration - COMPLETE (2026-03-02) ✅
All data migrated from JSONL flat files to PostgreSQL database:
- **54 countries** migrated
- **894,783 commodités** (positions tarifaires)
- **2,439,140 mesures** (taxes et droits)
- **920,297 formalités** administratives
- **894,783 avantages fiscaux** ZLECAf

**Database:** `postgresql://afcfta:afcfta2026@localhost:5432/afcfta_regulatory`

## Architecture

```
/app
├── backend/
│   ├── app/services/
│   ├── routes/
│   └── server.py
├── engine/                      # Regulatory Engine v3 - COMPLETE
│   ├── adapters/
│   │   ├── base_adapter.py
│   │   ├── dza_adapter.py      
│   │   └── generic_adapter.py  # NEW: Universal adapter
│   ├── api/
│   │   └── engine_service.py   # UPDATED: Fixed index format
│   ├── database/               # NEW: PostgreSQL support
│   │   ├── models.py           # SQLAlchemy models
│   │   └── migration.py        # Migration service
│   ├── output/                 # 1.5GB canonical data
│   │   ├── {ISO3}_canonical.jsonl (54 files)
│   │   └── indexes/            # 109 index files
│   ├── schemas/
│   └── pipeline.py             # UPDATED: 54 countries
├── frontend/
│   └── src/components/calculator/
│       └── CalculatorTab.jsx   # UPDATED: 54 country badges
└── memory/PRD.md
```

## Data Statistics

| Metric | Value |
|--------|-------|
| Countries | 54 |
| Total Records | 894,783 |
| Data Size | 1.5 GB |
| Index Files | 109 |
| HS6 Codes per Country | ~5,831 |
| Avg Response Time | <5ms |

## Countries with Full Regulatory Data

### North Africa
DZA (Algeria), EGY (Egypt), LBY (Libya), MAR (Morocco), TUN (Tunisia)

### West Africa  
BEN (Benin), BFA (Burkina Faso), CIV (Côte d'Ivoire), CPV (Cape Verde), 
GHA (Ghana), GIN (Guinea), GMB (Gambia), GNB (Guinea-Bissau), 
LBR (Liberia), MLI (Mali), MRT (Mauritania), NER (Niger), 
NGA (Nigeria), SEN (Senegal), SLE (Sierra Leone), TGO (Togo)

### Central Africa
CAF (Central African Republic), CMR (Cameroon), COD (DR Congo), 
COG (Congo), GAB (Gabon), GNQ (Equatorial Guinea), 
STP (São Tomé and Príncipe), TCD (Chad)

### East Africa
BDI (Burundi), COM (Comoros), DJI (Djibouti), ERI (Eritrea), 
ETH (Ethiopia), KEN (Kenya), MDG (Madagascar), MUS (Mauritius), 
RWA (Rwanda), SOM (Somalia), SSD (South Sudan), SDN (Sudan), 
SYC (Seychelles), TZA (Tanzania), UGA (Uganda)

### Southern Africa
AGO (Angola), BWA (Botswana), LSO (Lesotho), MWI (Malawi), 
MOZ (Mozambique), NAM (Namibia), SWZ (Eswatini), ZAF (South Africa), 
ZMB (Zambia), ZWE (Zimbabwe)

## API Endpoints

### Regulatory Engine v3
```
GET /api/regulatory-engine/details
  ?country={ISO3}     # e.g., SEN, MAR, NGA
  &code={HS_CODE}     # e.g., 090111, 870323
  &search_type=hs6    # or 'national'

Response: {
  success: true,
  country_iso3: "SEN",
  total_npf_pct: 40.0,
  total_zlecaf_pct: 20.0,
  savings_pct: 20.0,
  commodity: { ... },
  measures: [ ... ],
  requirements: [ ... ],
  fiscal_advantages: [ ... ]
}
```

## PostgreSQL Schema (Migration Ready)

```sql
-- 5 tables created
countries (iso3, name_fr, currency, vat_rate, total_positions)
commodities (country_iso3, national_code, hs6, description_fr, total_npf_pct, ...)
measures (commodity_id, measure_type, code, rate_pct, zlecaf_rate_pct)
requirements (commodity_id, code, document_fr, issuing_authority)
fiscal_advantages (commodity_id, tax_code, reduced_rate_pct, condition_fr)

-- To run migration:
python /app/engine/database/migration.py --database-url postgresql://afcfta:afcfta2026@localhost:5432/afcfta_regulatory
```

## Completed Work (March 2026)

- [x] Regulatory Engine v3 for 54 countries
- [x] Generic adapter for enhanced_v2 format
- [x] 894,783 canonical records generated
- [x] Index generation for all countries
- [x] PostgreSQL models and migration service
- [x] Frontend updated with 54-country badges
- [x] API bug fix for new index format

## Backlog

- [ ] Complete PostgreSQL migration
- [ ] Text search API for product descriptions
- [ ] OEC data audit
- [ ] RASD (55th country) addition
- [ ] PDF export functionality
- [ ] Performance optimization for large queries
