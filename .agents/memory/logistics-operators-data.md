---
name: Logistics operators (Intervenants) data convention
description: How the hand-maintained logistics operators dataset and its frontend renderer must be kept in sync.
---

# Logistics "Intervenants" operators dataset

Operators are hand-curated in `backend/logistics_operators_data.py` (a Python dict keyed by 8 category names) and surfaced via `GET /api/logistics/operators`. The frontend renders them in `frontend/src/components/logistics/IntervenantsTab.jsx`.

## Rules to follow when adding/editing operators
- **No fabricated contacts.** Only add phone/email/address that are web-verified from the operator's official site or an authoritative source. If a phone/email cannot be verified, include website + HQ address only — never invent one. **Why:** the user explicitly requires authentic, up-to-date contact data ("ne pas inventer les contacts").
- Each entry needs `id` (unique), `name`, `type`, `type_label`, `contacts`. Keep `type` consistent within a category (note: `customs_agents` intentionally mixes `customs_agency` for authorities vs `customs_agent` for brokers — semantic, not a bug).
- `contacts` values may be **flat strings** (`phone`, `email`, `website`, `address`, or named links like `offices_directory`) **or nested office dicts** (e.g. `headquarters`, `global_hq`, `<region>_office` each with `phone`/`email`/`address`/`website`).

## Renderer contract (must stay in sync)
`ContactsBlock` must handle BOTH flat strings and nested office dicts. **Why:** an earlier version only rendered nested `phone/email/address` and silently dropped flat strings and nested `website`, hiding real contacts. It now type-detects strings (url/email/phone/text) and renders nested `website` too.

## Country badges / filter
The country dropdown + badges come from `COUNTRY_LABELS` in the same file (ISO3 → flag + French name). When introducing operators in a new country, add its ISO3 to `COUNTRY_LABELS` or the badge shows a raw ISO code and the country can't be filtered.

## Freshness labels
`data_source` / `last_updated` are duplicated in both `get_operators_summary()` (in the data file) and `backend/routes/logistics.py` — update both together to avoid drift.
