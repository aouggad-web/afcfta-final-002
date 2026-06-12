---
name: New tariff JSON format
description: Field name differences between legacy and new authentic national-position files
---

# New vs Legacy Tariff File Format

## Summary field names
| Field | Legacy (data/*.json) | New (crawled/*.json) |
|-------|---------------------|----------------------|
| total sub-positions | `total_positions` or `total_sub_positions` | `total_national_positions` |
| chapters | `chapters_covered` | `chapters_covered` (same) |
| lines count | `total_lines` | `total_tariff_lines` |

## Per-line sub-position field names
| Field | Legacy | New |
|-------|--------|-----|
| duty rate | `dd` | `dd_rate` |

**Why:** The generator scripts (`generate_ecowas_*`, `generate_eac_*`, `generate_cemac_*`) used clearer field names. The service must handle both via `sp.get('dd_rate', sp.get('dd', parent))`.

## Countries list performance
`get_available_countries()` uses `_load_country_header()` which reads only the first 8KB of each file (up to `"tariff_lines"` key). This keeps the endpoint under 1 second for all 54 countries combined instead of loading 54 × 15-20 MB files.

## data_source values
- `tec_cedeao_authentic` — 15 ECOWAS countries, 6130 positions each
- `eac_cet_2022_authentic` — 7 EAC countries, 5891 positions each  
- `tec_cemac_authentic` — 6 CEMAC countries, 6130 positions each
- `conformepro_dz` — DZA only, 17115 positions (DO NOT regenerate)
- `legacy` — remaining 25 countries (old stubs)
