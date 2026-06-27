"""
AfCFTA API-key authentication
==============================
Three FastAPI dependencies are exported:
  require_auth   — any valid active key of any tier (free/basic/pro/admin);
                    also allows public passthrough when MongoDB is not
                    configured, or — if PUBLIC_DATA_ACCESS is true — when no
                    key is supplied (tariff/trade data is public information).
  require_admin  — admin-tier keys only
  check_ai_quota — valid key + monthly usage quota for AI/Claude-backed
                    endpoints, which have real per-request API cost. No public
                    passthrough: AI endpoints require both a database and a key.

Wire the database before first request:
    from auth import set_database
    set_database(db)
"""

import hashlib
import os
from datetime import datetime, timezone
from typing import Annotated, Optional

from fastapi import Depends, Header, HTTPException, status
from pymongo import ReturnDocument

# Tariff/trade data is public information — keep data endpoints accessible
# without a key by default, even once MongoDB (and therefore key validation)
# is configured. A caller that does send a key is still validated/tiered
# normally. Set PUBLIC_DATA_ACCESS=false to require a key for every request.
PUBLIC_DATA_ACCESS = os.getenv("PUBLIC_DATA_ACCESS", "true").lower() == "true"

# ---------------------------------------------------------------------------
# Database handle (injected at startup via set_database)
# ---------------------------------------------------------------------------

_db = None


def set_database(database) -> None:
    global _db
    _db = database


def get_db():
    return _db


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _hash_key(raw_key: str) -> str:
    return hashlib.sha256(raw_key.encode()).hexdigest()


# ---------------------------------------------------------------------------
# Dependencies
# ---------------------------------------------------------------------------


async def require_auth(
    x_api_key: Annotated[Optional[str], Header()] = None,
) -> dict:
    """Validate X-API-Key header; return the key document on success.

    When MongoDB is not configured (optional), all requests are allowed through
    with a public-tier context — tariff data is public information.
    """
    if _db is None:
        return {"tier": "public", "no_db": True}
    if not x_api_key:
        if PUBLIC_DATA_ACCESS:
            return {"tier": "public", "no_key": True}
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing X-API-Key header",
            headers={"WWW-Authenticate": "ApiKey"},
        )
    doc = await _db["api_keys"].find_one({"key_hash": _hash_key(x_api_key), "active": True})
    if not doc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or inactive API key",
            headers={"WWW-Authenticate": "ApiKey"},
        )
    return doc


async def require_admin(
    key_doc: Annotated[dict, Depends(require_auth)],
) -> dict:
    """Require admin-tier API key."""
    if key_doc.get("tier") != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin tier required",
        )
    return key_doc


# ---------------------------------------------------------------------------
# AI usage quotas (subscription tiers)
# ---------------------------------------------------------------------------
# Anthropic Claude calls have real per-request cost (~$0.02-$0.08 each), so
# AI endpoints are metered per calendar month per key. Admin keys are
# unlimited. A key's quota defaults to its tier's value below, but can be
# overridden per-key via the "monthly_quota" field set at creation time.

AI_TIER_QUOTAS = {
    "free": 20,
    "standard": 200,  # legacy tier name, kept as an alias of "basic"
    "basic": 200,
    "pro": 1000,
}


def _current_period() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m")


def resolve_ai_quota(tier: Optional[str], monthly_quota: Optional[int] = None) -> Optional[int]:
    """Effective monthly AI quota for a key.

    Returns None for admin (unlimited). A per-key ``monthly_quota`` override
    takes precedence when set — including an explicit 0, which disables AI use
    for that key — so the check is ``is not None``, not a truthiness test.
    """
    if tier == "admin":
        return None
    if monthly_quota is not None:
        return monthly_quota
    return AI_TIER_QUOTAS.get(tier, AI_TIER_QUOTAS["free"])


async def check_ai_quota(
    x_api_key: Annotated[Optional[str], Header()] = None,
) -> dict:
    """Require a valid API key with available monthly AI-usage quota.

    Unlike require_auth, there is no public/no-DB passthrough here: AI calls
    cost real money per request, so they stay unusable until a database and
    API keys are configured, regardless of MongoDB availability.
    """
    if _db is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="AI endpoints require API key authentication to be configured",
        )
    if not x_api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing X-API-Key header — AI endpoints require an API key",
            headers={"WWW-Authenticate": "ApiKey"},
        )

    doc = await _db["api_keys"].find_one({"key_hash": _hash_key(x_api_key), "active": True})
    if not doc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or inactive API key",
            headers={"WWW-Authenticate": "ApiKey"},
        )

    if doc.get("tier") == "admin":
        return doc

    quota = resolve_ai_quota(doc.get("tier"), doc.get("monthly_quota"))
    period = _current_period()

    updated = await _db["api_keys"].find_one_and_update(
        {"_id": doc["_id"], "usage_period": period},
        {"$inc": {"usage_count": 1}},
        return_document=ReturnDocument.AFTER,
    )
    if updated is None:
        # First call of a new (or first-ever) billing period for this key.
        updated = await _db["api_keys"].find_one_and_update(
            {"_id": doc["_id"]},
            {"$set": {"usage_period": period, "usage_count": 1}},
            return_document=ReturnDocument.AFTER,
        )

    if updated.get("usage_count", 0) > quota:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=(
                f"Monthly AI usage quota exceeded ({quota} requests/month for "
                f"the '{doc.get('tier')}' tier). Upgrade your subscription or "
                "wait for the next billing period."
            ),
        )
    return updated
