# Test Credentials — afcfta-final-002

## Backend API
- **Public Frontend API Key** (used by the SPA via `X-API-Key` header):
  - `zlecaf-frontend-public-key`
  - Tier: `public`
  - Stored in `api_keys` collection (MongoDB) + env `FRONTEND_API_KEY`

## Environment files (do not check in)
- `/app/backend/.env`
  - `MONGO_URL=mongodb://localhost:27017`
  - `DB_NAME=test_database`
  - `CORS_ORIGINS=*`
  - `FRONTEND_API_KEY=zlecaf-frontend-public-key`
- `/app/frontend/.env`
  - `REACT_APP_BACKEND_URL=https://zlecaf-trade-ops.preview.emergentagent.com`
  - `REACT_APP_API_KEY=zlecaf-frontend-public-key`

## How to use the API key with curl
```bash
curl -H "X-API-Key: zlecaf-frontend-public-key" \
     https://zlecaf-trade-ops.preview.emergentagent.com/api/countries
```

## Admin endpoints
Admin-tier endpoints (e.g., `/api/admin/keys`) require an admin API key — none seeded yet. Generate one via the admin keys route once an authenticated admin is present, or directly in MongoDB with `tier: "admin"`.

## SaaS user accounts (email/password + JWT cookie session) — NEW
- Endpoints: `POST /api/auth/register`, `POST /api/auth/login`, `POST /api/auth/logout`, `GET /api/auth/me`
- Session: JWT in httpOnly cookie `access_token` (7-day TTL, `SameSite=Lax`)
- CSRF: all mutating requests (POST) require header `X-CSRF-Token` matching the `csrf_token` cookie — obtained by first calling `GET /api/health` (sets the cookie + returns the token in the `X-CSRF-Token` response header). The frontend handles this automatically via `frontend/src/services/csrf.js` (already wired into the global axios instance).
- Brute-force protection: 5 failed login attempts per email → 429 lockout for 15 minutes (`login_attempts` collection, keyed by email).
- Seeded admin account (from `/app/backend/.env` — `ADMIN_EMAIL` / `ADMIN_PASSWORD`):
  - Email: `admin@afcfta-zlecaf.com`
  - Password: `ZlecafAdmin2026!`
  - Role: `admin`
- Test user account created during manual testing:
  - Email: `aminata.test@example.com`
  - Password: `SecurePass123`
  - Role: `user`

## Contact form — NEW
- `POST /api/contact` — `{name, email, message}` — stores in `contact_messages` collection and emails the admin mailbox (`SAAS_SMTP_USER`) via background task.

## SaaS transactional email (SMTP — Zoho Mail)
- Configured in `/app/backend/.env`: `SAAS_EMAIL_ENABLED=true`, `SAAS_SMTP_HOST=smtp.zoho.com`, `SAAS_SMTP_PORT=587`, `SAAS_SMTP_USER=noreply@afcfta-zlecaf.com`, `SAAS_SMTP_PASSWORD` (Zoho app password), `SAAS_SMTP_USE_TLS=true`.
- Verified working: welcome email on signup + admin notification on contact form (see backend logs `services.email_service: Email sent to ...`).
- Manual test script: `cd /app/backend && python scripts/test_saas_email.py <recipient_email>`

## Other integrations (not configured)
- Slack webhook — for Slack notifications (not set)
