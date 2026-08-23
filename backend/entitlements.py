"""Subscription entitlements — single source of truth for what each plan tier
unlocks (calculator limits, exports, API access, seats), decoupled from the
billing/payment flow itself.

Pure functions, no DB access: callers pass in the already-fetched user
document; testable in isolation, same pattern as cors_config.py.

This does NOT yet gate any route — see the SaaS monetization plan for the
follow-up phases (usage counters, route-level enforcement, team seats).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from types import MappingProxyType
from typing import Mapping, Optional

TIERS = ("free", "starter", "pro", "business")

# Feature modules gated per tier (mirrors the app's sidebar). Each tier grants
# or denies each module and, when granted, may cap its usage over a period.
MODULES = ("stats", "production", "logistics", "roo", "tools", "reports")

# Reset window a module quota is counted over.
#   "day"   — rolling/calendar day, reset nightly
#   "month" — calendar month
#   "cycle" — the paid subscription period (30d monthly / 365d annual), reset
#             at renewal rather than on a calendar boundary
QUOTA_PERIODS = ("day", "month", "cycle")

# Subscription statuses that still grant the paid tier's entitlements.
# "canceling" = cancel_at_period_end was requested but the paid period the
# user already paid for hasn't ended yet — access continues until it does
# (checked separately via subscription_current_end below).
_ACTIVE_STATUSES = frozenset({"active", "trialing", "canceling"})


@dataclass(frozen=True)
class ModuleAccess:
    """Whether a tier can open a module, and (if capped) how much per period."""

    enabled: bool
    quota: Optional[int] = None  # None = unlimited when enabled
    quota_period: Optional[str] = None  # one of QUOTA_PERIODS; None when unlimited/disabled


# A module a tier grants without any usage cap.
_UNLIMITED = ModuleAccess(enabled=True)
# A module a tier does not grant at all.
_DENIED = ModuleAccess(enabled=False)


def _capped(quota: int, period: str) -> ModuleAccess:
    return ModuleAccess(enabled=True, quota=quota, quota_period=period)


@dataclass(frozen=True)
class Entitlements:
    tier: str
    daily_calculations: Optional[int]  # None = unlimited
    monthly_country_profiles: Optional[int]  # None = unlimited (all 54)
    export_formats: tuple[str, ...]
    api_access: bool
    api_monthly_quota: Optional[int]
    seats_included: int
    modules: Mapping[str, ModuleAccess] = field(default_factory=dict)

    def __post_init__(self) -> None:
        # These instances are shared singletons (resolve_entitlements returns
        # the same object for every caller of a tier). A plain dict here would
        # let any caller mutate `ent.modules` and permanently alter access for
        # all subsequent users — breaking fail-closed. Freeze the mapping so
        # module access is read-only after construction. (frozen=True only
        # blocks reassigning the attribute, not mutating the dict it points to.)
        object.__setattr__(self, "modules", MappingProxyType(dict(self.modules)))

    def module(self, module_id: str) -> ModuleAccess:
        """Access for a module id; unknown/ungranted modules fail closed to
        denied so callers can gate without a separate membership check."""
        return self.modules.get(module_id, _DENIED)


_TIER_ENTITLEMENTS: dict[str, Entitlements] = {
    "free": Entitlements(
        tier="free",
        daily_calculations=10,
        monthly_country_profiles=None,
        export_formats=(),
        api_access=False,
        api_monthly_quota=None,
        seats_included=1,
        modules={
            "stats": _capped(20, "month"),
            "production": _capped(10, "day"),
            "logistics": _capped(5, "day"),
            "roo": _capped(60, "day"),
            "tools": _DENIED,
            "reports": _capped(2, "day"),
        },
    ),
    "starter": Entitlements(
        tier="starter",
        daily_calculations=40,
        monthly_country_profiles=None,
        export_formats=("csv",),
        api_access=False,
        api_monthly_quota=None,
        seats_included=1,
        modules={
            "stats": _capped(5, "day"),
            "production": _capped(50, "day"),
            "logistics": _capped(50, "day"),
            "roo": _capped(200, "day"),
            "tools": _capped(10, "day"),
            "reports": _capped(10, "day"),
        },
    ),
    "pro": Entitlements(
        tier="pro",
        daily_calculations=100,
        monthly_country_profiles=None,
        export_formats=("csv", "excel", "pdf"),
        api_access=False,
        api_monthly_quota=None,
        seats_included=1,
        modules={
            "stats": _capped(50, "day"),
            "production": _UNLIMITED,
            "logistics": _capped(300, "day"),
            "roo": _UNLIMITED,
            "tools": _UNLIMITED,
            "reports": _capped(30, "day"),
        },
    ),
    "business": Entitlements(
        tier="business",
        daily_calculations=None,
        monthly_country_profiles=None,
        export_formats=("csv", "excel", "pdf"),
        api_access=True,
        api_monthly_quota=1000,
        seats_included=5,
        modules={
            "stats": _capped(300, "day"),
            "production": _UNLIMITED,
            "logistics": _UNLIMITED,
            "roo": _UNLIMITED,
            "tools": _UNLIMITED,
            "reports": _capped(200, "day"),
        },
    ),
}


# Distinguishes "no period end recorded" (None — subscription still
# ongoing, e.g. Stripe hasn't sent its first invoice yet) from "the stored
# value is malformed" (_INVALID — a legacy/corrupted document must fail
# closed to free, not raise and not grant unlimited access).
_INVALID = object()


def _parse_period_end(value):
    """Returns a datetime, None (no value recorded), or the _INVALID
    sentinel for a value that couldn't be parsed as one."""
    if value is None:
        return None
    try:
        if isinstance(value, str):
            value = datetime.fromisoformat(value)
        if not isinstance(value, datetime):
            return _INVALID
        if value.tzinfo is None:
            # MongoDB/BSON stores datetimes without timezone info, so pymongo
            # returns a naive datetime here even though it was written as
            # UTC-aware (same caveat as the login-lockout check in
            # user_auth.py).
            value = value.replace(tzinfo=timezone.utc)
        return value
    except (ValueError, TypeError):
        return _INVALID


def _effective_tier(user: Optional[dict], *, now: Optional[datetime] = None) -> str:
    if not user:
        return "free"

    tier = user.get("subscription_tier") or "free"
    if tier not in _TIER_ENTITLEMENTS:
        # Unknown/legacy value — fail closed to free rather than crash or
        # silently over-grant on a value we don't recognize.
        return "free"
    if tier == "free":
        return "free"

    if user.get("subscription_status") not in _ACTIVE_STATUSES:
        # No active paid subscription (never subscribed, payment failed,
        # fully canceled) — a stale subscription_tier field must not grant
        # paid entitlements on its own; the webhook may not have run yet or
        # a provider (e.g. Chargily one-off payments) never sends one at all.
        return "free"

    period_end = _parse_period_end(user.get("subscription_current_end"))
    if period_end is _INVALID:
        # Malformed value on a legacy or corrupted document — fail closed to
        # free rather than raise (this resolver must never crash a route
        # that gates on it) or silently treat it as "no end date" (which
        # would grant unlimited paid access).
        return "free"
    if period_end is not None:
        effective_now = now or datetime.now(timezone.utc)
        if effective_now.tzinfo is None:
            # A caller-supplied `now` can be naive (e.g. a test using
            # datetime.now() without a tz) while period_end is always
            # normalized to UTC-aware above — comparing the two directly
            # would raise TypeError, breaking the "never raises" guarantee.
            # Same normalization as user_auth._is_locked_out().
            effective_now = effective_now.replace(tzinfo=timezone.utc)
        if effective_now > period_end:
            # The paid period has lapsed — don't grant paid entitlements
            # past what was actually paid for, even if subscription_status
            # hasn't been updated yet (e.g. a missed/delayed downgrade
            # webhook).
            return "free"

    return tier


_ALL_TIER_ENTITLEMENTS_VIEW = MappingProxyType(_TIER_ENTITLEMENTS)


def all_tier_entitlements() -> Mapping[str, Entitlements]:
    """Every tier's `Entitlements`, for callers that need the whole grid (the
    public `/api/billing/entitlements` endpoint) rather than one resolved
    user's effective tier. Read-only view — same rationale as freezing
    `Entitlements.modules`: this is the shared singleton grid every caller
    reads, not a defensive copy, so a caller mutating the returned mapping
    (e.g. `del all_tier_entitlements()["business"]`) would corrupt it for
    every subsequent resolve_entitlements() call."""
    return _ALL_TIER_ENTITLEMENTS_VIEW


def resolve_entitlements(user: Optional[dict], *, now: Optional[datetime] = None) -> Entitlements:
    """Resolve the effective entitlements for a user document. `user=None`
    (an unauthenticated visitor) resolves to the free tier, same as any
    other user without an active paid subscription — this always returns an
    Entitlements instance, never None. Never raises — always returns at
    least the free tier, so callers can gate features without a separate
    "no subscription" branch."""
    return _TIER_ENTITLEMENTS[_effective_tier(user, now=now)]
