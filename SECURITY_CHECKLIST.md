# Security Checklist — ZLECAf Trade Calculator

## Phase 1 — Git Security
- [x] .gitignore cleaned and consolidated (removed 600+ duplicate lines)
- [x] .env.example documented with placeholder values only
- [x] .env excluded from version control
- [ ] Purge .env from Git history with git-filter-repo (run manually if secrets were ever committed)

## Phase 2 — Root Cleanup
- [x] ~80 parasitic files deleted (shell fragments: `}`, `for`, `if`, `except`, `EOF`, etc.)
- [x] JSON data files moved to `data/json/`
- [x] CSV data files moved to `data/csv/`
- [x] XLSX data files moved to `data/xlsx/`
- [x] TypeScript crawlers moved to `engine/crawlers/`
- [x] Python utility scripts moved to `scripts/`
- [x] Backend import paths updated to reference new `data/json/` and `data/csv/` locations

## Phase 3 — Structure & Duplicates
- [x] `backup_before_github_merge/` removed
- [x] `src/components/trade/` removed (duplicate of `frontend/src/components/opportunities/`)
- [x] Clean folder structure:
  ```
  backend/          ← FastAPI application
  data/
  ├── json/         ← African trade/logistics JSON datasets
  ├── csv/          ← ZLECAf CSV datasets
  └── xlsx/         ← ZLECAf Excel files
  engine/
  └── crawlers/     ← TypeScript crawler utilities
  scripts/          ← Utility & maintenance Python scripts
  frontend/         ← React application
  ```

## Phase 4 — Backend Security Hardening
- [x] CORS `allow_origins` now controlled via `ALLOWED_ORIGINS` environment variable
- [x] CORS `allow_headers` restricted to required headers only (no wildcard)
- [x] SecurityHeadersMiddleware in place (CSP, X-Frame-Options, HSTS, X-Content-Type-Options)
- [x] CSRFMiddleware active on mutation endpoints
- [x] CSRF cookie `secure` flag controlled via `HTTPS_ENABLED` env variable (true in production)
- [x] RateLimitMiddleware active (120 req/min, burst 20)
- [x] ALLOWED_ORIGINS and HTTPS_ENABLED documented in .env.example

## Manual Actions Required After Deployment
These cannot be automated — must be done manually:

1. **Gmail** → Revoke current App Password → Create a new one → Update `EMAIL_SMTP_PASSWORD` in production `.env`
2. **Slack** → Regenerate webhook URL in Settings > Incoming Webhooks → Update `SLACK_WEBHOOK_URL`
3. **MongoDB Atlas** → Change DB user password → Update `MONGO_URL` in production `.env`
4. **Redeploy** the service after updating credentials

## Verification Commands
```bash
# Health check
curl http://localhost:8000/api/health

# Test tariff calculation
curl -X POST http://localhost:8000/api/calculate-tariff \
  -H "Content-Type: application/json" \
  -d '{"origin_country":"KE","destination_country":"GH","hs_code":"080300","value":10000}'

# Test countries endpoint
curl http://localhost:8000/api/countries
```
