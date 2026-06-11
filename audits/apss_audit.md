# APSS/API Audit Notes (2026-05-21)

## Scope
- `tariff_engine/api.py`
- `tariff_engine/api_multi.py`

## Findings

1. **Input validation gap (medium)**
   - `hs` accepted arbitrary strings and only removed dots/spaces.
   - Risk: malformed values cause unpredictable lookups and inconsistent error behavior.
   - Fix: enforce basic FastAPI query constraints and numeric-only sanitized HS values.

2. **Shared cache mutation on response (medium)**
   - Multi-bloc endpoint appended `_bloc` and `_dataset` directly onto cached `row`.
   - Risk: state leakage across requests and hard-to-debug response drift.
   - Fix: return a shallow copy (`dict(row)`) before adding response metadata.

3. **Error semantics clarity (low)**
   - Prior behavior returned 404 for many bad inputs that are syntactically invalid.
   - Fix: return 400 for invalid HS syntax; keep 404 for well-formed but missing entries.

## Residual recommendations
- Add unit tests for:
  - invalid HS (`abc123`, symbols, empty-after-normalization)
  - valid-but-missing HS (404)
  - repeated calls confirming no cache mutation side effects
- Consider rate limiting and request logging if exposed publicly.
