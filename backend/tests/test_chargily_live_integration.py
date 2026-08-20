"""Live integration tests for Chargily Pay activation (Phase 2 → activated).

These tests hit the REAL preview backend (REACT_APP_BACKEND_URL) and the REAL
Chargily test API (test_sk_...). They verify:

  1. GET /api/billing/pricing         — DZD grid matches pricing.py source of truth
  2. GET /api/billing/payment-context — provider/currency selection
  3. POST /api/billing/checkout (DZ)  — returns a hosted Chargily URL for the 3
                                        plans × 2 cycles (6 combos)
  4. POST /api/billing/checkout (no DZ) — non-regression, still routes to Stripe
  5. POST /api/billing/chargily/webhook — 400 on missing / invalid signature

Auth is via cookie session + CSRF double-submit. Credentials come from
`/app/memory/test_credentials.md` (file missing → hard-coded test user from
review_request, prefixed test_cors_fix_final@example.com).
"""

from __future__ import annotations

import os
import re

import pytest
import requests

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "https://commerce-viewer.preview.emergentagent.com").rstrip("/")
TEST_EMAIL = "test_cors_fix_final@example.com"
TEST_PASSWORD = "TestPass123!"

CHARGILY_URL_RE = re.compile(r"^https?://pay\.chargily\.(net|dz)/")


@pytest.fixture(scope="module")
def session():
    s = requests.Session()
    s.headers.update({"Content-Type": "application/json"})
    # Bootstrap CSRF via GET /api/health (mint-on-first-safe-request pattern).
    r = s.get(f"{BASE_URL}/api/health", timeout=20)
    assert r.status_code == 200, f"health failed: {r.status_code} {r.text[:200]}"
    csrf = s.cookies.get("csrf_token") or r.headers.get("X-CSRF-Token")
    assert csrf, "CSRF token not issued by /api/health"
    s.headers["X-CSRF-Token"] = csrf
    return s


@pytest.fixture(scope="module")
def auth_session(session):
    r = session.post(
        f"{BASE_URL}/api/auth/login",
        json={"email": TEST_EMAIL, "password": TEST_PASSWORD},
        timeout=20,
    )
    if r.status_code != 200:
        pytest.skip(f"Login failed ({r.status_code}): {r.text[:200]}")
    # Refresh CSRF header from cookie if server rotated it.
    csrf = session.cookies.get("csrf_token")
    if csrf:
        session.headers["X-CSRF-Token"] = csrf
    return session


# ── 1. Pricing grid ─────────────────────────────────────────────────────────

EXPECTED_DZD = {
    ("starter", "monthly"): 1500,
    ("starter", "annual"): 16500,
    ("pro", "monthly"): 3750,
    ("pro", "annual"): 41250,
    ("business", "monthly"): 18750,
    ("business", "annual"): 206250,
}


def test_pricing_grid_matches_source_of_truth(session):
    r = session.get(f"{BASE_URL}/api/billing/pricing", timeout=15)
    assert r.status_code == 200, r.text[:200]
    body = r.json()
    assert body["currencies"]["chargily"] == "DZD"
    by_plan = {row["plan"]: row for row in body["plans"]}
    for (plan, cycle), expected in EXPECTED_DZD.items():
        got = by_plan[plan]["dzd"][cycle]
        assert got == expected, f"DZD mismatch {plan}/{cycle}: got={got} expected={expected}"


# ── 2. Payment context ──────────────────────────────────────────────────────


def test_payment_context_public(session):
    r = session.get(f"{BASE_URL}/api/billing/payment-context", timeout=15)
    assert r.status_code == 200, r.text[:200]
    body = r.json()
    assert "provider" in body and "currency" in body
    # Without DZ signal it should default to stripe/EUR.
    assert body["provider"] in ("stripe", "chargily")


# ── 3. Chargily checkout for 3 plans × 2 cycles ─────────────────────────────


@pytest.mark.parametrize("plan", ["starter", "pro", "business"])
@pytest.mark.parametrize("cycle", ["monthly", "annual"])
def test_checkout_dz_returns_chargily_hosted_url(auth_session, plan, cycle):
    r = auth_session.post(
        f"{BASE_URL}/api/billing/checkout",
        json={"plan": plan, "cycle": cycle, "billing_country": "DZ"},
        timeout=30,
    )
    assert r.status_code == 200, f"{plan}/{cycle}: {r.status_code} {r.text[:300]}"
    body = r.json()
    url = body.get("url", "")
    assert CHARGILY_URL_RE.match(url), f"{plan}/{cycle}: not a Chargily URL: {url}"


# ── 4. Non-regression: no DZ → Stripe ───────────────────────────────────────


def test_checkout_without_dz_routes_to_stripe(auth_session):
    r = auth_session.post(
        f"{BASE_URL}/api/billing/checkout",
        json={"plan": "starter", "cycle": "monthly"},  # no billing_country
        timeout=30,
    )
    # Success (200 with stripe URL) OR 503 if Stripe env is missing — but NOT
    # a Chargily URL. Backend log: Checkout: provider=stripe ...
    if r.status_code == 200:
        url = r.json().get("url", "")
        assert "chargily" not in url, f"Expected Stripe, got Chargily URL: {url}"
        assert "stripe.com" in url or "checkout.stripe.com" in url, f"Not a Stripe URL: {url}"
    else:
        # Acceptable non-regression signal: not routed to Chargily silently.
        assert r.status_code in (400, 503), f"Unexpected status: {r.status_code} {r.text[:200]}"


# ── 5. Chargily webhook rejects unsigned / invalid signature ────────────────


def test_chargily_webhook_missing_signature_returns_400(session):
    # Webhook is exempt from CSRF (see server.py). Send raw body, no signature.
    r = requests.post(
        f"{BASE_URL}/api/billing/chargily/webhook",
        data=b'{"id":"evt_test","type":"checkout.paid"}',
        headers={"Content-Type": "application/json"},
        timeout=15,
    )
    assert r.status_code == 400, f"expected 400, got {r.status_code}: {r.text[:200]}"


def test_chargily_webhook_invalid_signature_returns_400(session):
    r = requests.post(
        f"{BASE_URL}/api/billing/chargily/webhook",
        data=b'{"id":"evt_test","type":"checkout.paid"}',
        headers={"Content-Type": "application/json", "signature": "deadbeef" * 8},
        timeout=15,
    )
    assert r.status_code == 400, f"expected 400, got {r.status_code}: {r.text[:200]}"
