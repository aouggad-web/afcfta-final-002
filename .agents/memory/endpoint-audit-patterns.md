---
name: Endpoint audit patterns
description: Recurring bugs found during full 39-endpoint audit with fixes applied
---

## Pattern 1: Missing module-level cache variables
**Rule:** Python module-level cache variables (`_cache = None`) must be declared before the `load_*()` function that uses `global _cache`. Also applies to helper functions called inside loaders.
**Why:** `load_airports_data()` called `_airports_cache` and `_load_enhanced_airport_index()` without them being defined at module scope → NameError → 500.
**How to apply:** When a 500 says `name '_xxx_cache' is not defined`, add `_xxx_cache = None` at the top of the module before any function that uses it.

## Pattern 2: Hard 404 instead of chapter fallback
**Rule:** Routes like `/{country}/{hs6}` should fall back to chapter-level data when exact HS6 not found, never raise 404.
**Why:** `get_country_hs6_tariff(iso3, hs6_code)` returns None when ETL has no data for that HS6; same for `get_detailed_tariff()`. Frontend breaks silently.
**How to apply:** When `tariff = get_xxx(iso3, hs6)` returns None, build a fallback dict using `get_tariff_rate_for_country()` + `get_vat_rate_for_country()` (both return tuples `(rate, source)`).

## Pattern 3: ISO2 vs ISO3 mismatch
**Rule:** `banking_system.banks_registry.CENTRAL_BANKS` uses ISO2 keys (DZ, MA, NG). Frontend always sends ISO3 (DZA, MAR, NGA). Add ISO3→ISO2 conversion at route entry.
**Why:** No normalization layer between frontend and banking registry.
**How to apply:** Check `len(code) == 3` and look up in `_ISO3_TO_ISO2` dict (defined inline in banking.py get_banks_by_country).

## Pattern 4: Route shadowing with catch-all params
**Rule:** When a route `/ports/{port_id}` already exists and you need `/ports/{country_iso}`, do NOT add a second route — it will never be reached. Merge the logic into the existing handler.
**Why:** FastAPI resolves routes in registration order; second catch-all is dead code.
**How to apply:** In the existing handler, detect format (ISO code = `re.fullmatch(r"[A-Za-z]{2,3}", val)`) and branch accordingly.

## Pattern 5: PostgreSQL fallback for commodities/search
**Rule:** `/commodities/search` must fall back to `search.hs_code_search.get_search_engine()` when `POSTGRES_AVAILABLE=False`.
**Why:** PostgreSQL is not configured in this Replit environment; hard 503 breaks the UI.
**Import path:** `from search.hs_code_search import get_search_engine` (NOT `tariff_search_engine`).

## Import paths verified
- `from search.hs_code_search import get_search_engine` ← TariffSearchEngine (JSON)
- `from search.enhanced_search import get_search_engine` ← EnhancedSearchEngine (full)
