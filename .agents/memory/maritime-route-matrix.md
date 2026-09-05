---
name: Maritime route matrix is the single source of truth for ports/routes
description: Where sea ports and port-to-port routes come from, and why features must derive from it instead of keeping parallel hard-coded port lists.
---

# Maritime ports/routes: derive, never hard-code

`backend/logistics_fees_data.py` is the authoritative maritime module. `PORTS`
holds every African container port (each entry carries `iso` = ISO3 country).
`_build_route_matrix()` precomputes `_ALL_ROUTES`/`_ROUTE_INDEX` over **every
pair** of ports (published benchmark routes + great-circle modeled routes with
`is_modeled=True`). `get_route_between`, `get_routes_from_port`, and
`get_total_cost(o, d, container_type)` work for **any** pair of those ports.

**Rule:** any feature that needs sea ports or routes for a country must derive
them from `PORTS` (group by `p["iso"]`) and call `get_total_cost`. Do NOT
maintain a separate hard-coded country→port list.

**Why:** the multimodal comparator (`services/multimodal_freight_service.py`)
used to keep its own hard-coded `COUNTRY_DEFAULT_PORT` (one port for ~19
countries). That silently dropped ~16 coastal countries (no sea option at all)
and misrouted Libya to an Egyptian port. The maritime data already covered all
of them; only the parallel list was the limiter.

**How to apply:** group `PORTS` by `iso` to get country→[LOCODE]; pick the
representative/default port from that list (order preferred port first if you
keep a small preference map); enumerate origin×destination port pairs for
country-level sea options. Propagate `is_modeled`/`source`/disclaimer so modeled
estimates are not shown as published rates.
