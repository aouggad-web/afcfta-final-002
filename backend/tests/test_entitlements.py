from datetime import datetime, timedelta, timezone

import pytest
from entitlements import TIERS, resolve_entitlements


def test_no_user_grants_free_tier():
    ent = resolve_entitlements(None)

    assert ent.tier == "free"
    assert ent.daily_calculations == 5
    assert ent.export_formats == ()
    assert ent.api_access is False


def test_user_with_no_subscription_field_grants_free_tier():
    ent = resolve_entitlements({"email": "a@example.com"})

    assert ent.tier == "free"


@pytest.mark.parametrize("tier", ["starter", "pro", "business"])
def test_active_subscription_grants_its_tier(tier):
    user = {"subscription_tier": tier, "subscription_status": "active"}

    ent = resolve_entitlements(user)

    assert ent.tier == tier


def test_business_tier_grants_api_access_and_seats():
    user = {"subscription_tier": "business", "subscription_status": "active"}

    ent = resolve_entitlements(user)

    assert ent.api_access is True
    assert ent.api_monthly_quota == 1000
    assert ent.seats_included == 5


def test_pro_tier_unlocks_all_export_formats_and_unlimited_profiles():
    user = {"subscription_tier": "pro", "subscription_status": "active"}

    ent = resolve_entitlements(user)

    assert set(ent.export_formats) == {"csv", "excel", "pdf"}
    assert ent.monthly_country_profiles is None
    assert ent.daily_calculations is None


def test_starter_tier_only_unlocks_csv_export():
    user = {"subscription_tier": "starter", "subscription_status": "active"}

    ent = resolve_entitlements(user)

    assert ent.export_formats == ("csv",)


def test_trialing_status_grants_paid_tier():
    user = {"subscription_tier": "pro", "subscription_status": "trialing"}

    assert resolve_entitlements(user).tier == "pro"


def test_canceling_status_still_grants_paid_tier_before_period_end():
    now = datetime(2026, 8, 15, tzinfo=timezone.utc)
    user = {
        "subscription_tier": "pro",
        "subscription_status": "canceling",
        "subscription_current_end": now + timedelta(days=5),
    }

    assert resolve_entitlements(user, now=now).tier == "pro"


@pytest.mark.parametrize(
    "status",
    ["past_due", "canceled", "incomplete_expired", None, ""],
)
def test_inactive_status_falls_back_to_free_despite_stale_tier_field(status):
    """A stale subscription_tier must never grant paid entitlements once the
    subscription itself is no longer active — this is the actual downgrade
    enforcement, independent of whether/when a webhook updates the field."""
    user = {"subscription_tier": "business", "subscription_status": status}

    assert resolve_entitlements(user).tier == "free"


def test_lapsed_period_end_falls_back_to_free_even_if_status_still_active():
    """Covers a missed or delayed downgrade webhook: the paid window the user
    actually paid for has passed, regardless of what subscription_status
    still says."""
    now = datetime(2026, 8, 15, tzinfo=timezone.utc)
    user = {
        "subscription_tier": "pro",
        "subscription_status": "active",
        "subscription_current_end": now - timedelta(days=1),
    }

    assert resolve_entitlements(user, now=now).tier == "free"


def test_period_end_as_iso_string_is_parsed():
    now = datetime(2026, 8, 15, tzinfo=timezone.utc)
    user = {
        "subscription_tier": "pro",
        "subscription_status": "active",
        "subscription_current_end": (now + timedelta(days=1)).isoformat(),
    }

    assert resolve_entitlements(user, now=now).tier == "pro"


def test_period_end_naive_datetime_is_treated_as_utc():
    """MongoDB/pymongo returns naive datetimes for values written as UTC —
    same caveat handled in user_auth.py's login-lockout check."""
    now = datetime(2026, 8, 15, tzinfo=timezone.utc)
    naive_future = (now + timedelta(days=1)).replace(tzinfo=None)
    user = {
        "subscription_tier": "pro",
        "subscription_status": "active",
        "subscription_current_end": naive_future,
    }

    assert resolve_entitlements(user, now=now).tier == "pro"


def test_missing_period_end_does_not_block_active_subscription():
    """Right after checkout, before the webhook has populated
    subscription_current_end, an active subscription must still grant its
    tier rather than being blocked by an absent end date."""
    user = {"subscription_tier": "pro", "subscription_status": "active"}

    assert resolve_entitlements(user).tier == "pro"


def test_unknown_tier_value_fails_closed_to_free():
    user = {"subscription_tier": "enterprise-legacy", "subscription_status": "active"}

    assert resolve_entitlements(user).tier == "free"


def test_all_declared_tiers_are_resolvable():
    for tier in TIERS:
        user = {"subscription_tier": tier, "subscription_status": "active"}
        assert resolve_entitlements(user).tier == tier


@pytest.mark.parametrize(
    "malformed_end",
    [
        "not-a-date",
        12345,
        {"nested": "dict"},
        ["2026-08-15"],
    ],
)
def test_malformed_period_end_fails_closed_to_free_without_raising(malformed_end):
    """A legacy or corrupted subscription_current_end must never crash the
    resolver (routes gate on this) nor silently grant unlimited paid access
    by being treated as an absent value."""
    user = {
        "subscription_tier": "business",
        "subscription_status": "active",
        "subscription_current_end": malformed_end,
    }

    assert resolve_entitlements(user).tier == "free"
