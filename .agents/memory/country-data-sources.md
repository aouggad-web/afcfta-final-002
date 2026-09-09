---
name: Reliable country-level data sources
description: Where trustworthy per-country macro/trade/development data actually lives, and which metrics genuinely do not exist anywhere.
---

# Reliable country-level data for the 54 AfCFTA states

When you need per-country economic / development data (e.g. for comparisons,
profiles, dashboards), use the in-code Python sources, NOT the AI profile or the
country-profile CSVs:

- `backend/country_data.py` `REAL_COUNTRY_DATA` — all 54 countries:
  `gdp_usd_2024` (in **billions**), `gdp_per_capita_2024`, `population_2024`,
  `development_index` (= HDI score), `africa_rank`, `growth`.
- `backend/gold_reserves_data.py` `GOLD_RESERVES_GAI_DATA["global_attractiveness_index_2025"]`
  — all 54 countries: GAI `score` + `rank_global`.
- Trade performance: hardcoded lists in `backend/routes/statistics.py`
  (`TRADE_PERFORMANCE_GLOBAL_2024`, `TRADE_PERFORMANCE_INTRA_AFRICAN_2024`),
  in **billions**, keyed by **ISO2** — only ~13 major economies. Everyone else
  has no trade data; return null, never fabricate.

## Traps (not obvious from reading code)
- **The country-profile CSVs are stubs.** `data/csv/ZLECAf_ENRICHI_2024_COMMERCE.csv`
  and `ZLECAF_54_PAYS_DONNEES_COMPLETES.csv` are tiny placeholders, so
  `data_loader.get_country_commerce_profile()` returns None for ALL countries
  and `/api/country-profile/{iso}` falls into a sparse else-branch.
- **The AI profile path fails by default.** `/api/ai/profile/{name}` 500s whenever
  `ANTHROPIC_API_KEY` is unset (the common case). Don't build features that depend
  on it as the primary data path.
- **Some metrics exist NOWHERE** in the datasets: inflation, unemployment, and the
  HDI *world* rank. `worldbank_data_latest.json` only has GDP / per-capita /
  population / growth. Surface these as null — do not invent them.

**Why:** data accuracy is the project's #1 priority (never fabricate). The
comparison feature previously showed ~$0 GDP / all "-" because it chained the
failing AI path → stub-CSV profile → 404, instead of reading these reliable
sources.

**How to apply:** for any new per-country data surface, assemble from
`REAL_COUNTRY_DATA` + `GOLD_RESERVES_GAI_DATA` + the trade constants directly;
convert GDP/trade billions→other units explicitly; leave unavailable metrics null.
