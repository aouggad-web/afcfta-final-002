"""CORS origin resolution — pure functions, no side effects at import time.

Kept separate from server.py (which has heavy import-time side effects: DB
connections, route registration) so the origin/regex-building logic can be
unit-tested in isolation.
"""

from __future__ import annotations

#: Origines de développement local, servies seulement hors production quand
#: ALLOWED_ORIGINS n'est pas défini. La liste comptait aussi afcfta.trade et
#: www.afcfta.trade, un domaine qui ne sert pas l'application : toute page
#: publiée sur ce domaine (ou un script tiers qui y serait chargé) pouvait
#: lire les réponses de l'API avec la session du visiteur et son jeton CSRF.
#: Seules les origines qui servent réellement le frontend doivent figurer
#: dans ALLOWED_ORIGINS.
DEFAULT_ORIGINS = [
    "http://localhost:3000",
    "http://localhost:5000",
    "http://localhost:8000",
]

# Env var names Emergent has been observed to expose with this pod's own
# public preview URL. Checked in order; the first one present wins.
_EMERGENT_PREVIEW_ENV_VARS = ("PREVIEW_ENDPOINT", "preview_endpoint")


def resolve_cors_origins(env: dict) -> list[str]:
    """Static origin allowlist from ALLOWED_ORIGINS / FRONTEND_URL / Emergent
    env vars. Without ALLOWED_ORIGINS, production (APP_ENV=production) starts
    from an empty list: the app is served from its own origin and needs CORS
    only for origins declared explicitly.

    Deliberately an exact-origin allowlist, not a subdomain-family pattern:
    *.preview.emergentagent.com is a multi-tenant domain — reflecting
    Access-Control-Allow-Origin for the whole family (as an earlier version
    of this function did via a regex) combined with allow_credentials=True
    would let ANY other Emergent-hosted preview read authenticated responses
    from this API using a victim user's browser-held session cookie. Only
    this pod's own resolved origin is safe to add automatically.
    """
    env_origins = env.get("ALLOWED_ORIGINS", "")
    if env_origins:
        origins = [o.strip() for o in env_origins.split(",") if o.strip()]
    elif env.get("APP_ENV", "development") == "production":
        origins = []
    else:
        origins = list(DEFAULT_ORIGINS)

    frontend_url = env.get("FRONTEND_URL", "")
    if frontend_url and frontend_url not in origins:
        origins.append(frontend_url)

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
