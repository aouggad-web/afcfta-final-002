"""Subscription entitlements — single source of truth for what each plan tier
unlocks (calculator limits, exports, API access, seats), decoupled from the
billing/payment flow itself.

Pure functions, no DB access: callers pass in the already-fetched user
document; testable in isolation, same pattern as cors_config.py.

This does NOT yet gate any route — see the SaaS monetization plan for the
follow-up phases (usage counters, route-level enforcement, team seats).
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Optional

TIERS = ("free", "starter", "pro", "business")

# Subscription statuses that still grant the paid tier's entitlements.
# "canceling" = cancel_at_period_end was requested but the paid period the
# user already paid for hasn't ended yet — access continues until it does
# (checked separately via subscription_current_end below).
_ACTIVE_STATUSES = frozenset({"active", "trialing", "canceling"})


@dataclass(frozen=True)
class Entitlements:
    tier: str
    daily_calculations: Optional[int]  # None = unlimited
    monthly_country_profiles: Optional[int]  # None = unlimited (all 54)
    export_formats: tuple[str, ...]
    api_access: bool
    api_monthly_quota: Optional[int]
    seats_included: int


_TIER_ENTITLEMENTS: dict[str, Entitlements] = {
    "free": Entitlements(
        tier="free",
        daily_calculations=5,
        monthly_country_profiles=3,
        export_formats=(),
        api_access=False,
        api_monthly_quota=None,
        seats_included=1,
    ),
    "starter": Entitlements(
        tier="starter",
        daily_calculations=None,
        monthly_country_profiles=10,
        export_formats=("csv",),
        api_access=False,
        api_monthly_quota=None,
        seats_included=1,
    ),
    "pro": Entitlements(
        tier="pro",
        daily_calculations=None,
        monthly_country_profiles=None,
        export_formats=("csv", "excel", "pdf"),
        api_access=False,
        api_monthly_quota=None,
        seats_included=1,
    ),
    "business": Entitlements(
        tier="business",
        daily_calculations=None,
        monthly_country_profiles=None,
        export_formats=("csv", "excel", "pdf"),
        api_access=True,
        api_monthly_quota=1000,
        seats_included=5,
    ),
}


def _parse_period_end(value) -> Optional[datetime]:
    if value is None:
        return None
    if isinstance(value, str):
        value = datetime.fromisoformat(value)
    if value.tzinfo is None:
        # MongoDB/BSON stores datetimes without timezone info, so pymongo
        # returns a naive datetime here even though it was written as
        # UTC-aware (same caveat as the login-lockout check in user_auth.py).
        value = value.replace(tzinfo=timezone.utc)
    return value


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
    if period_end is not None and (now or datetime.now(timezone.utc)) > period_end:
        # The paid period has lapsed — don't grant paid entitlements past
        # what was actually paid for, even if subscription_status hasn't
        # been updated yet (e.g. a missed or delayed downgrade webhook).
        return "free"

    return tier


def resolve_entitlements(user: Optional[dict], *, now: Optional[datetime] = None) -> Entitlements:
    """Resolve the effective entitlements for a user document, or None for an
    unauthenticated visitor. Never raises — always returns at least the free
    tier, so callers can gate features without a separate "no subscription"
    branch."""
    return _TIER_ENTITLEMENTS[_effective_tier(user, now=now)]
