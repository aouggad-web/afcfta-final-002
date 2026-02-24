# AfCFTA Project — Integration Pack (Security + Queue + Data QA)

Generated: 2026-02-06

## What you get
- Rate limiting (Upstash Redis) for tRPC endpoints
- CSRF protection for tRPC mutations (double-submit)
- CSP + security headers (Next.js middleware)
- Crawl queue schema + Node worker (Drizzle/MySQL/TiDB)
- Data QA + Delta + Cost Engine Python stubs

## Install deps
```bash
pnpm add @upstash/redis
```

## Env vars
Add:
- UPSTASH_REDIS_REST_URL
- UPSTASH_REDIS_REST_TOKEN

## Wire into tRPC
1) Add middleware requireCsrf() to protectedProcedure in your `server/api/trpc.ts` (or equivalent)
2) Use withRateLimit() on endpoints like crawl.create, crawl.stop, tariff.search

## Client CSRF header
Call GET /api/csrf once and attach header `x-csrf-token` on tRPC mutations.

## Worker
Run:
```bash
node --loader ts-node/esm server/worker/crawlWorker.ts
```
(Adjust to your runtime: tsx/pm2/docker.)

## Notes
- Update python script path in `crawlWorker.ts` to match your repo.
- Add Drizzle migration for crawl_queue table (schema included).
