# CHANGELOG - ZLECAf Trade Calculator

## [2026-03-02] - Migration PostgreSQL et Corrections Frontend

### Added
- Migration complète des données vers PostgreSQL
  - 54 pays migrés
  - 894,783 commodités
  - 2,439,140 mesures tarifaires
  - 920,297 formalités administratives
  - 894,783 avantages fiscaux
- Script de migration automatisé (`/app/engine/run_full_migration.py`)
- Configuration DATABASE_URL dans `.env`

### Fixed
- Import manquant `get_sub_positions` dans `/app/backend/routes/hs6_database.py`
- Import manquant `FileCheck` icon dans CalculatorTab.jsx
- Import manquant `Shield` icon dans CalculatorTab.jsx
- Affichage des totaux (total_taxes_npf, total_taxes_zlecaf) dans les résultats du calculateur

### Database Schema
Tables PostgreSQL créées:
- `countries` - Pays et métadonnées
- `commodities` - Positions tarifaires
- `measures` - Taxes et droits de douane
- `requirements` - Formalités administratives
- `fiscal_advantages` - Avantages fiscaux ZLECAf

### Credentials
```
Database: afcfta_regulatory
User: afcfta
Password: afcfta2026
URL: postgresql://afcfta:afcfta2026@localhost:5432/afcfta_regulatory
```
