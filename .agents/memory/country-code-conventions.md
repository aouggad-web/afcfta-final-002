---
name: Country code conventions (ISO2 vs ISO3)
description: The codebase mixes ISO2 and ISO3 country codes; cross-module lookups must normalize or they silently fall back to wrong data.
---

# Country code conventions (ISO2 vs ISO3)

The codebase uses **two** country-code conventions and they cross at runtime:

- `AFRICAN_COUNTRIES` (and the calculator request models) speak **ISO3** (`DZA`, `NGA`, `SYC`).
- The currency dataset (`data/json/currencies_african_complete.json`) and the
  banking module (`banking_system/foreign_exchange.py` `_CURRENCY_META`,
  `FOREX_PROFILES`, `banks_registry.CENTRAL_BANKS`) are keyed by **ISO2**
  (`DZ`, `NG`, `SC`).

**Why this matters:** lookups that take a country code and `.get()` against an
ISO2-keyed dict **fail silently** when handed ISO3 — they return `None` or a
USD/default fallback rather than raising. The calculator's bi-currency block came
back empty, and `/banking/forex/convert` returned `1 USD = 1 USD` because the
ISO3 code missed the ISO2 dict.

**How to apply:** any new code that resolves a country code against currency or
banking data must normalize first. Use `currencies.service.to_iso2(code)` — it is
the single source of truth for the ISO3→ISO2 map and covers all 54 AfCFTA states.
`get_by_country` already routes through it. The banking forex helpers normalize
via a local `_normalize_iso2` that delegates to `to_iso2`.

**Gotchas:**
- The "all 54 countries" map is easy to get wrong by one — Seychelles (`SYC`→`SC`)
  was missed on the first pass. Verify coverage by diffing mapped ISO2 values
  against the keys of the currency dataset, not by eyeballing the list.
- Several `routes/banking.py` endpoints (banks, risk-assessment, compliance,
  register, payment-systems, transaction/validate) still `.upper()` the code
  without normalizing. They work in practice only because the frontend banking
  panel always sends ISO2 (from `/banking/countries`). If anything ever passes
  ISO3 to them they will 404 / fall back.

**Test the wrong path, not the happy path:** the calculator API expects fields
`destination_country`, `origin_country`, `hs_code`, `value` (not `dest_country`/
`value_usd`). A wrong-field request returns a 422 with only a `detail` key, which
looks like an empty result — confirm field names before concluding a feature is
broken.
