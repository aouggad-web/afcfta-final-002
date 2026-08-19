"""Tests for the single pricing source of truth (pricing.py)."""

import pytest

import pricing


def test_every_plan_cycle_has_eur_and_dzd():
    for plan in pricing.PLANS:
        for cycle in pricing.CYCLES:
            assert pricing.eur_amount(plan, cycle) > 0
            assert pricing.dzd_amount(plan, cycle) >= pricing.CHARGILY_MIN_DZD


def test_eur_annual_is_eleven_times_monthly():
    # Grille validée : annuel = 11 × mensuel (~1 mois offert).
    for plan in pricing.PLANS:
        assert pricing.eur_amount(plan, "annual") == 11 * pricing.eur_amount(plan, "monthly")


def test_stripe_cents_is_eur_times_100():
    assert pricing.stripe_cents("pro", "monthly") == pricing.eur_amount("pro", "monthly") * 100
    assert pricing.stripe_cents("business", "annual") == 137500


def test_dzd_defaults_match_reviewed_grid():
    assert pricing.dzd_amount("starter", "monthly") == 1500
    assert pricing.dzd_amount("starter", "annual") == 16500
    assert pricing.dzd_amount("business", "annual") == 206250


def test_dzd_env_override_wins(monkeypatch):
    monkeypatch.setenv("CHARGILY_PRICE_PRO_M", "9999")
    assert pricing.dzd_amount("pro", "monthly") == 9999


def test_dzd_blank_override_falls_back_to_default(monkeypatch):
    monkeypatch.setenv("CHARGILY_PRICE_PRO_M", "   ")
    assert pricing.dzd_amount("pro", "monthly") == 3750


def test_dzd_invalid_override_raises_invalid_price(monkeypatch):
    monkeypatch.setenv("CHARGILY_PRICE_PRO_M", "abc")
    with pytest.raises(pricing.InvalidPrice):
        pricing.dzd_amount("pro", "monthly")


def test_dzd_below_minimum_raises_invalid_price(monkeypatch):
    monkeypatch.setenv("CHARGILY_PRICE_STARTER_M", "10")
    with pytest.raises(pricing.InvalidPrice):
        pricing.dzd_amount("starter", "monthly")


def test_unknown_plan_cycle_raises():
    with pytest.raises(pricing.UnknownPlanCycle):
        pricing.eur_amount("enterprise", "monthly")
    with pytest.raises(pricing.UnknownPlanCycle):
        pricing.dzd_amount("pro", "weekly")


def test_grid_shape():
    rows = pricing.grid()
    assert [r["plan"] for r in rows] == list(pricing.PLANS)
    starter = rows[0]
    assert starter["eur"] == {"monthly": 10, "annual": 110}
    assert starter["dzd"] == {"monthly": 1500, "annual": 16500}
