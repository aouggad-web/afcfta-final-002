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

# Env var names Emergent has been observed to expose with this pod's own
# public preview URL. Checked in order; the first one present wins.
_EMERGENT_PREVIEW_ENV_VARS = ("PREVIEW_ENDPOINT", "preview_endpoint")


def resolve_cors_origins(env: dict) -> list[str]:
    """Static origin allowlist from ALLOWED_ORIGINS / FRONTEND_URL / Replit /
    Emergent env vars.

    Deliberately an exact-origin allowlist, not a subdomain-family pattern:
    *.preview.emergentagent.com is a multi-tenant domain — reflecting
    Access-Control-Allow-Origin for the whole family (as an earlier version
    of this function did via a regex) combined with allow_credentials=True
    would let ANY other Emergent-hosted preview read authenticated responses
    from this API using a victim user's browser-held session cookie. Only
    this pod's own resolved origin is safe to add automatically.
    """
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

    # Emergent's preview URL is a random subdomain assigned on every pod
    # restart/redeploy (multiple different ones have been observed within a
    # single afternoon) — a static ALLOWED_ORIGINS/FRONTEND_URL entry
    # inevitably goes stale and silently breaks CORS for credentialed
    # requests until someone notices and updates the .env by hand. Emergent
    # exposes the pod's own current public URL as an env var; add exactly
    # that one origin (never the whole subdomain family — see the docstring)
    # so a redeploy can't break auth without also being able to fix it.
    for var_name in _EMERGENT_PREVIEW_ENV_VARS:
        preview_endpoint = env.get(var_name, "").strip()
        if preview_endpoint and preview_endpoint not in origins:
            origins.append(preview_endpoint)
            break

    return origins


def resolve_cors_origin_regex(env: dict) -> str | None:
    """Regex for the Replit app domain, when configured. Starlette's
    CORSMiddleware applies this with re.fullmatch, so no anchors are needed
    here. Returns None (no regex) when no such domain is configured — origin
    matching then relies entirely on the exact-origin allowlist above."""
    replit_app_domain = env.get("REPLIT_APP_DOMAIN", "")
    if not replit_app_domain:
        return None

    return rf"https://{re.escape(replit_app_domain)}"
