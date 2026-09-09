---
name: Multimodal carrier/operator sourcing
description: Where the "transport companies that can perform a freight option" come from for each mode in the multimodal comparator.
---

# Carrier/operator sourcing per transport mode

The multimodal comparator surfaces, per option/segment, the transport companies that can perform the prestation. Each mode has a **different authoritative source** — do not unify them naively:

- **Sea** & **air** segments already carry a `carriers` list straight from the maritime route matrix (`logistics_fees_data`) and the air data module (`logistics_air_fees_data._carriers_air`). Aggregate those to option level; never re-derive.
- **Land / rail / multimodal** corridors: the **exact** operators are embedded in the corridor data and exposed via `get_land_freight_cost(...)["operators"]` (e.g. Transrail = Dakar-Bamako, Sitarail = Abidjan-Ouaga, TAZARA, ASKY Logistics = Lomé-Ouaga). This is the source of truth.

**Rule:** for land legs use `land.get("operators")` as the PRIMARY source; only fall back to broad matching against `LOGISTICS_OPERATORS` (trucking by `africa_presence`, rail by `country_iso`/`countries`) when the corridor lists no operators.

**Why:** a company merely operating *in a country* is not evidence it can run a *specific corridor*. Using country-presence as the primary source fabricated plausible-but-wrong carriers and dropped the real corridor operator — a data-integrity error for a fiscal/regulatory-accuracy product.

**How to apply:** any future change touching multimodal option building must keep corridor operators primary and the `LOGISTICS_OPERATORS` match strictly as fallback. Note `rail_operators` entries are keyed by either `country_iso` (national) OR a `countries` list (transnational: TAZARA, SITARAIL, Ethiopia-Djibouti) — match both.
