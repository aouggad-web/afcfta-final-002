---
name: GDP platform alignment
description: Where GDP data lives and which source wins for each part of the platform
---

## Rule
Two GDP sources coexist; they use slightly different IMF WEO vintages:

| File | Source | Used by |
|------|--------|---------|
| `backend/country_data.py` | FMI WEO Oct 2025 / BM WDI 2024 | `/country-profile/{iso3}` endpoint |
| `backend/routes/statistics.py` | FMI WEO Oct 2024 (web-confirmed) | `/statistics` dashboard + top-10 ranking |

## Corrected values (both files aligned):
- ZAF: 373B (was 401 in country_data)
- EGY: 347B (was 389 in country_data) — post EGP devaluation March 2024
- NGA: 252B (confirmed in both)
- DZA: 266B (statistics.py) / 269.31B (country_data.py — minor vintage diff, acceptable)

## Known divergence:
- ETH: statistics.py=205B (IMF WEO Oct 2024), country_data.py=142B (reflects Birr devaluation July 2024)
- MAR: statistics.py=150B, country_data.py=160.6B

**Why:** Ethiopian Birr and EGP both devalued in 2024; different IMF WEO snapshots give materially different USD figures.

## Fix applied to countries.py else-branch:
When `get_country_commerce_profile()` returns None (most countries), the else branch now populates:
- population_millions, hdi from real_data
- projections: key_sectors, zlecaf_potential, main_exports, main_imports, risk_ratings, GAI, gold reserves
- profile.risk_ratings from real_data.get('risk_ratings')
