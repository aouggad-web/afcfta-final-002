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
  - `REACT_APP_BACKEND_URL=https://github-import-74.preview.emergentagent.com`
  - `REACT_APP_API_KEY=zlecaf-frontend-public-key`

## How to use the API key with curl
```bash
curl -H "X-API-Key: zlecaf-frontend-public-key" \
     https://github-import-74.preview.emergentagent.com/api/countries
```

## Admin endpoints
Admin-tier endpoints (e.g., `/api/admin/keys`) require an admin API key — none seeded yet. Generate one via the admin keys route once an authenticated admin is present, or directly in MongoDB with `tier: "admin"`.

## Other integrations (not configured)
- `EMERGENT_LLM_KEY` — for Gemini AI analysis routes (not set)
- SMTP — for email notifications (not set)
- Slack webhook — for Slack notifications (not set)
