"""CORS origin resolution — pure functions, no side effects at import time.

Kept separate from server.py (which has heavy import-time side effects: DB
connections, route registration) so the origin/regex-building logic can be
unit-tested in isolation.
"""

from __future__ import annotations

import re

DEFAULT_ORIGINS = [
    "http://localhost:3000",
    "http://localhost:5000",
    "http://localhost:8000",
    "https://afcfta.trade",
    "https://www.afcfta.trade",
]

# Emergent's preview URL is a random subdomain assigned on every pod
# restart/redeploy (multiple different ones have been observed within a
# single afternoon). A static ALLOWED_ORIGINS/FRONTEND_URL entry inevitably
# goes stale and silently breaks CORS for credentialed requests (no
# Access-Control-Allow-Origin at all, since the origin isn't in the static
# list) until someone notices and updates the .env by hand. Always allow the
# whole subdomain family instead, so a redeploy never breaks auth.
EMERGENT_PREVIEW_REGEX = r"https://[a-z0-9-]+\.preview\.emergentagent\.com"


def resolve_cors_origins(env: dict) -> list[str]:
    """Static origin allowlist from ALLOWED_ORIGINS / FRONTEND_URL / Replit env vars."""
    env_origins = env.get("ALLOWED_ORIGINS", "")
    origins = (
        [o.strip() for o in env_origins.split(",") if o.strip()]
        if env_origins
        else list(DEFAULT_ORIGINS)
    )

    frontend_url = env.get("FRONTEND_URL", "")
    if frontend_url and frontend_url not in origins:
        origins.append(frontend_url)

    replit_dev_domain = env.get("REPLIT_DEV_DOMAIN", "")
    if replit_dev_domain:
        replit_origin = f"https://{replit_dev_domain}"
        if replit_origin not in origins:
            origins.append(replit_origin)

    return origins


def resolve_cors_origin_regex(env: dict) -> str:
    """Combined regex: always matches Emergent preview subdomains, plus the
    Replit app domain when configured. Starlette's CORSMiddleware applies
    this with re.fullmatch, so no anchors are needed here."""
    patterns = [EMERGENT_PREVIEW_REGEX]

    replit_app_domain = env.get("REPLIT_APP_DOMAIN", "")
    if replit_app_domain:
        patterns.append(rf"https://{re.escape(replit_app_domain)}")

    return "|".join(patterns)
