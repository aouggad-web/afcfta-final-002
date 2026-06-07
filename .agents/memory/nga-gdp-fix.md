---
name: Nigeria GDP devaluation fix
description: NGA GDP 2023/2024 values and ranking corrections in statistics.py
---

## Rule
Nigeria's GDP in USD dropped sharply after the naira devaluation of June 2023 (NGN went from ~460 to ~1500 per USD). Any data using pre-devaluation exchange rates overestimates Nigeria's GDP.

## Correct values (IMF WEO Oct 2024 / World Bank WDI)
- 2021: $440.8B
- 2022: $477.4B
- 2023: $362.8B (post-devaluation)
- 2024: $363.0B (estimate)

## Ranking impact
Nigeria dropped from rank 1 to rank 3 in African economies:
1. Egypt ~$387B
2. South Africa ~$373B
3. Nigeria ~$363B

## Files affected
- `backend/routes/statistics.py`: GDP_HISTORY_TOP10, build_top_10_gdp_2024(), top_5_gdp_trade_comparison

**Why:** The original data used GDP projections based on old exchange rate (~460 NGN/USD) and did not account for the June 2023 CBN devaluation unification reform.
