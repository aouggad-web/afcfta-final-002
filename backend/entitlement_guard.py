"""FastAPI dependencies that enforce `entitlements.py` on real routes.

Bridges two systems that were previously disconnected:
  - the SaaS JWT session (`routes/user_auth.py`), which knows the caller's
    subscription tier
  - the X-API-Key system (`auth.py`), which currently gates the module
    routers (production, logistics, ...) but has no notion of a plan/tier

A caller with a valid JWT session is gated on their actual subscription tier.
A caller without one (API-key-only access, or no auth at all) is treated as
the "free" tier — `resolve_entitlements(None)` already resolves to free, so
there is no separate branch for that case.

Wire the database before first request, same pattern as `auth.py`/`billing.py`:
    from entitlement_guard import set_database
    set_database(db)
"""

from __future__ import annotations

from typing import Optional

from bson import ObjectId
from bson.errors import InvalidId
from entitlements import Entitlements, ModuleAccess, resolve_entitlements
from fastapi import Depends, HTTPException, Request, status
from pymongo import ReturnDocument
from pymongo.errors import DuplicateKeyError
from services.user_auth_service import decode_access_token

_db = None


def set_database(database) -> None:
    global _db
    _db = database


async def get_optional_subscriber(request: Request) -> Optional[dict]:
    """Best-effort resolution of the calling user from the JWT session cookie
    or bearer header. Never raises — an absent/invalid/expired token, a
    missing database, or an unknown user id all resolve to `None`, which
    `resolve_entitlements` treats as the free tier."""
    if _db is None:
        return None

    token = request.cookies.get("access_token")
    if not token:
        auth_header = request.headers.get("Authorization", "")
        if auth_header.startswith("Bearer "):
            token = auth_header[7:]
    if not token:
        return None

    payload = decode_access_token(token)
    if not payload:
        return None

    try:
        user_id = ObjectId(payload["sub"])
    except (InvalidId, TypeError, KeyError):
        return None

    return await _db.users.find_one({"_id": user_id})


def _period_key(quota_period: str, user: dict) -> str:
    from datetime import datetime, timezone

    now = datetime.now(timezone.utc)
    if quota_period == "day":
        return now.strftime("%Y-%m-%d")
    if quota_period == "month":
        return now.strftime("%Y-%m")
    # "cycle": the paid subscription period, keyed by its recorded end so a
    # renewal (new `subscription_current_end`) naturally starts a fresh
    # counter without any explicit reset job.
    end = user.get("subscription_current_end")
    return f"cycle:{end}"


async def check_and_increment_usage(user: dict, counter_id: str, access: ModuleAccess) -> bool:
    """Atomically increments the usage counter for (user, counter_id, current
    period) and returns whether the call is within quota. `access.quota is
    None` (unlimited) always returns True without touching the database.
    """
    if access.quota is None:
        return True
    if _db is None:
        # No database to count against — fail closed rather than silently
        # grant unmetered access.
        return False

    period_key = _period_key(access.quota_period, user)
    key = {"user_id": user["_id"], "counter_id": counter_id, "period_key": period_key}

    # Atomic "increment only if still under quota": the filter re-checks
    # `count < quota` as part of the same update, so concurrent requests
    # can't both read a stale count and both succeed past the limit.
    updated = await _db.usage_counters.find_one_and_update(
        {**key, "count": {"$lt": access.quota}},
        {"$inc": {"count": 1}},
        return_document=ReturnDocument.AFTER,
    )
    if updated is not None:
        return True

    # No document matched the filter above — either this is the first call
    # of the period (no document yet, allow it and seed count=1) or the
    # quota is already exhausted (document exists with count >= quota, deny
    # it). These two cases must NOT be conflated: unconditionally upserting
    # here would let every call past the quota re-create/no-op the same
    # maxed-out document and always return True, defeating the cap entirely.
    # The unique index on (user_id, counter_id, period_key) makes the
    # insert itself the atomic "does it already exist" check — a concurrent
    # first call racing this one loses the insert and is correctly denied.
    try:
        await _db.usage_counters.insert_one({**key, "count": 1})
        return True
    except DuplicateKeyError:
        return False


def _forbidden(tier: str, module_id: str) -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail={
            "error": "upgrade_required",
            "tier": tier,
            "module": module_id,
            "message": (
                f"Ce module n'est pas inclus dans la formule '{tier}'. "
                "Passez à une formule supérieure pour y accéder."
            ),
        },
    )


def _quota_exceeded(tier: str, module_id: str, access: ModuleAccess) -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_429_TOO_MANY_REQUESTS,
        detail={
            "error": "quota_exceeded",
            "tier": tier,
            "module": module_id,
            "quota": access.quota,
            "quota_period": access.quota_period,
            "message": (
                f"Quota de la formule '{tier}' atteint ({access.quota}/"
                f"{access.quota_period}) pour ce module. Passez à une formule "
                "supérieure pour continuer."
            ),
        },
    )


def require_module(module_id: str):
    """FastAPI dependency factory: gates a route on a subscriber's access to
    `module_id` per `entitlements.MODULES`, enforcing both the on/off switch
    and any usage quota for the resolved tier."""

    async def _dependency(
        request: Request,
        user: Optional[dict] = Depends(get_optional_subscriber),
    ) -> Entitlements:
        ent = resolve_entitlements(user)
        access = ent.module(module_id)
        if not access.enabled:
            raise _forbidden(ent.tier, module_id)
        if access.quota is not None and user is not None:
            # Metering needs a stable identity to count against. An
            # unauthenticated caller (anonymous visitor, or an API-key-only
            # integration predating the SaaS accounts) has none — these
            # module routers were public/API-key-gated before entitlements
            # existed, so anonymous traffic keeps that prior behavior
            # (module on/off still enforced above, just not metered) rather
            # than being newly locked behind a login wall.
            ok = await check_and_increment_usage(user, module_id, access)
            if not ok:
                raise _quota_exceeded(ent.tier, module_id, access)
        return ent

    return _dependency


def require_calculations_quota():
    """FastAPI dependency for the tariff calculator's `daily_calculations`
    limit — a per-tier field on `Entitlements`, not a `MODULES` entry."""

    async def _dependency(
        request: Request,
        user: Optional[dict] = Depends(get_optional_subscriber),
    ) -> Entitlements:
        ent = resolve_entitlements(user)
        if ent.daily_calculations is None or user is None:
            # Same rationale as require_module: no identity to meter an
            # anonymous caller against, so it keeps its prior (unmetered)
            # access rather than being newly blocked.
            return ent
        access = ModuleAccess(enabled=True, quota=ent.daily_calculations, quota_period="day")
        ok = await check_and_increment_usage(user, "calculator", access)
        if not ok:
            raise _quota_exceeded(ent.tier, "calculator", access)
        return ent

    return _dependency
