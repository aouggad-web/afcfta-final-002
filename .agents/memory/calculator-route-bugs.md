---
name: Calculator route bugs (fixed)
description: Three critical bugs that blocked the ZLECAf calculator sub-modules — patterns to avoid in future routes.
---

# Calculator route bugs — fixed patterns

## Bug 1 — Hard 404 on ETL coverage gaps
**File:** `backend/routes/tariffs.py` — `GET /tariffs/detailed/{country_code}/{hs_code}`

The route called `get_detailed_tariff(iso3, hs_code)` and raised HTTPException 404 when it returned None. Since the detailed ETL only covers a subset of countries, all others (including DZA) got 404.

**Rule:** Never raise 404 on coverage gaps. Always fall back to chapter-level data and return 200 with `data_source: "chapter_fallback"`.

**Note:** `get_tariff_rate_for_country()` and `get_vat_rate_for_country()` in `etl/country_tariffs_complete.py` both return **tuples** `(rate, source)` — must unpack, never use raw.

## Bug 2 — Dismantlement router imported but not registered
**File:** `backend/routes/__init__.py`

The dismantlement router was imported **twice** (duplicate blocks at lines 73-79 and 95-101), alongside two duplicate Rules-of-Origin data load blocks. Despite the imports, the router was never passed to `include_router()`.

**Rule:** Always verify both import AND `include_router()` registration when adding a new router to `__init__.py`. Watch for duplicate import blocks introduced by copy-paste.

**Fix applied:** Removed two duplicate import+data-load pairs; added `include_router(dismantlement_router)` after `tariffs_calc_router`.

## Bug 3 — DismantlementSchedule npfRate always 0 (authentic path)
**File:** `frontend/src/components/calculator/CalculatorTab.jsx`

`DismantlementSchedule` received `npfRate={result.customs_duty_rate ?? result.dd_rate_pct ?? result.tariff_rate ?? 0}`, but the `transformedResult` built from authentic API data only exposed `normal_tariff_rate` (decimal 0-1), not the percentage fields. Result: component always saw 0 and displayed "Déjà en franchise ZLECAf".

**Rule:** When building `transformedResult` from authentic data, always expose both the decimal form (`normal_tariff_rate`) and the percentage form (`dd_rate_pct`, `customs_duty_rate`) of the DD rate. Child components may expect either.
