---
name: Tariff data routing
description: authentic_tariff_service.py file lookup order — crawled/ overrides data/ root
---

# Tariff Data Routing Rule

`load_country_tariffs(iso3)` must check `backend/data/crawled/{ISO3}_tariffs.json` FIRST, then fall back to `backend/data/{ISO3}_tariffs.json`.

**Why:** The new authentic national-position files (ECOWAS/EAC/CEMAC) are written to `crawled/`; the root `data/` files are old legacy stubs. Before this fix, the API served legacy stubs even when a better crawled file existed.

**How to apply:** Any new function that reads a country tariff file must mirror this two-path lookup. `_load_country_header()` already implements it correctly — copy that pattern.

Also: `get_available_countries()` scans BOTH directories to build the ISO3 list, deduplicating with a `seen` set (CRAWLED_DIR wins because it's checked second via `setdefault`).
