# Application Audit — May 21, 2026

## Scope

- Backend API bootstrap and security middleware wiring (`backend/server.py`).
- V2 API endpoints for search/bulk analytics (`backend/api/v2/endpoints.py`).
- Mobile API endpoints and caching/ETag behavior (`backend/api/mobile/lightweight_endpoints.py`).

## Executive Summary

The platform has solid baseline controls (CORS allow-list, optional CSRF/rate-limit/security headers middleware, and production docs disabling). Main risks are around **silent failure patterns**, **unbounded bulk processing**, and **cache consistency/security hygiene** in mobile routes.

## Findings

### 1) Optional security middleware can fail open (Medium)

- Security middleware import/registration is wrapped in `try/except ImportError`; on failure, app continues and only logs warning.
- This creates a fail-open path where security controls may be absent in misconfigured deployments.

**Evidence:** `backend/server.py` security middleware initialization block.

**Recommendation:**
- In production (`APP_ENV=production`), fail startup if middleware imports fail.
- Keep fail-open only for explicit local dev mode.

---

### 2) CSRF exemptions include state-changing crawler/tariff endpoints (Medium)

- Exemptions include `/api/tariff-data/collect`, `/api/crawl`, and `/api/crawl/start`.
- If these routes are cookie-authenticated or accessible from browser contexts, exemptions increase CSRF risk.

**Evidence:** `backend/server.py` `CSRFMiddleware` `exempt_paths` list.

**Recommendation:**
- Restrict exemptions to read-only/public endpoints.
- Require non-cookie auth (e.g., signed API key/bearer) for automation endpoints.

---

### 3) Bulk endpoints have no payload size caps on item arrays (Medium)

- `BulkTariffRequest`/`BulkInvestmentRequest` accept arrays without explicit max length.
- Nested loops in tariff calculation (`products x routes`) can create large in-memory workloads.

**Evidence:** `backend/api/v2/endpoints.py` models and `bulk_tariff_calculations` processing loop.

**Recommendation:**
- Add validation caps (e.g., `max_items`) and server-side hard limits.
- Add async job queue for large batch requests.

---

### 4) Mobile ETag uses MD5 (Low)

- `_etag` uses `hashlib.md5` on JSON payload.
- For non-cryptographic cache tags this is common, but modern hygiene favors SHA-256 to avoid weak-hash optics and collisions.

**Evidence:** `backend/api/mobile/lightweight_endpoints.py` `_etag` function.

**Recommendation:**
- Replace MD5 with SHA-256.

---

### 5) Broad exception swallowing in mobile endpoints degrades observability (Low/Medium)

- Multiple `except Exception` blocks default to empty/placeholder response content and continue.
- This protects availability but can hide regressions.

**Evidence:** `backend/api/mobile/lightweight_endpoints.py` around cache access and intelligence/regional data loading.

**Recommendation:**
- Log exceptions with context and warning severity.
- Track fallback rate via metrics.

## Positive Controls Observed

- API docs/openapi disabled in production by env-driven URL config.
- CORS origins are environment-controlled and not wildcarded by default.
- Input constraints exist for several query params (e.g., min/max for `limit`, search `q` length).

## Prioritized Remediation Plan

1. **P1:** Enforce security middleware hard-fail in production.
2. **P1:** Revisit CSRF exemptions for write/automation endpoints.
3. **P2:** Add bounded list validation and request size limits for bulk endpoints.
4. **P3:** Upgrade ETag hash to SHA-256.
5. **P3:** Add structured warning logs + fallback metrics where exceptions are swallowed.
