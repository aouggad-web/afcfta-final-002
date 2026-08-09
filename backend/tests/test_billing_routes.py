"""
Tests de la couche facturation (Stripe) — Phase 1.

Hermétiques : aucun appel réseau à Stripe ni base Mongo réelle. On vérifie la
résolution des prix (autorité serveur), la vérification de signature du webhook,
et le comportement des routes (auth requise, routage Algérie → 501, webhook non
signé → 400) via un mini-app FastAPI montant uniquement le routeur billing.
"""

import sys
from pathlib import Path

import pytest
from fastapi import FastAPI, HTTPException
from fastapi.testclient import TestClient

backend_path = Path(__file__).parent.parent
if str(backend_path) not in sys.path:
    sys.path.insert(0, str(backend_path))

from routes import billing, user_auth  # noqa: E402
from services import chargily_service, geo_service, stripe_service  # noqa: E402


class _FakeDB:
    """Base non-None suffisante pour franchir les gardes _require_db()."""


@pytest.fixture
def client(monkeypatch):
    # Câble une base factice pour billing et user_auth (get_current_user).
    billing.set_database(_FakeDB())
    user_auth.set_database(_FakeDB())
    app = FastAPI()
    app.include_router(billing.router)
    return TestClient(app)


# ── Autorité serveur sur les prix ───────────────────────────────────────────


def test_resolve_price_id_reads_env(monkeypatch):
    monkeypatch.setenv("STRIPE_PRICE_PRO_M", "price_pro_monthly_123")
    assert stripe_service.resolve_price_id("pro", "monthly") == "price_pro_monthly_123"


def test_resolve_price_id_unknown_plan_is_400():
    with pytest.raises(HTTPException) as exc:
        stripe_service.resolve_price_id("enterprise", "monthly")
    assert exc.value.status_code == 400


def test_resolve_price_id_missing_env_is_503(monkeypatch):
    monkeypatch.delenv("STRIPE_PRICE_BUSINESS_Y", raising=False)
    with pytest.raises(HTTPException) as exc:
        stripe_service.resolve_price_id("business", "annual")
    assert exc.value.status_code == 503


# ── Vérification de signature du webhook ────────────────────────────────────


def test_construct_event_without_secret_raises(monkeypatch):
    monkeypatch.delenv("STRIPE_WEBHOOK_SECRET", raising=False)
    with pytest.raises(ValueError):
        stripe_service.construct_event(b"{}", "sig")


def test_construct_event_without_signature_raises(monkeypatch):
    monkeypatch.setenv("STRIPE_WEBHOOK_SECRET", "whsec_test")
    with pytest.raises(ValueError):
        stripe_service.construct_event(b"{}", None)


# ── Routes ──────────────────────────────────────────────────────────────────


def test_checkout_requires_authentication(client):
    # Aucun cookie de session → get_current_user lève 401.
    resp = client.post("/billing/checkout", json={"plan": "pro", "cycle": "monthly"})
    assert resp.status_code == 401


def test_checkout_algeria_disabled_returns_501(client, monkeypatch):
    """Chargily non activé : la branche algérienne annonce clairement 501."""

    async def _fake_user(_request):
        return {"_id": "000000000000000000000001", "email": "u@example.com", "name": "U"}

    monkeypatch.setattr(billing, "get_current_user", _fake_user)
    monkeypatch.setenv("CHARGILY_ENABLED", "false")
    resp = client.post(
        "/billing/checkout",
        json={"plan": "pro", "cycle": "monthly", "billing_country": "DZ"},
    )
    assert resp.status_code == 501


def test_checkout_missing_price_config_is_503(client, monkeypatch):
    async def _fake_user(_request):
        return {"_id": "000000000000000000000001", "email": "u@example.com", "name": "U"}

    monkeypatch.setattr(billing, "get_current_user", _fake_user)
    monkeypatch.delenv("STRIPE_PRICE_PRO_M", raising=False)
    resp = client.post("/billing/checkout", json={"plan": "pro", "cycle": "monthly"})
    assert resp.status_code == 503


def test_webhook_unsigned_returns_400(client, monkeypatch):
    monkeypatch.setenv("STRIPE_WEBHOOK_SECRET", "whsec_test")
    resp = client.post("/billing/webhook", content=b"{}")
    assert resp.status_code == 400


# ── Chargily (Algérie) ──────────────────────────────────────────────────────


def test_chargily_amount_reads_env(monkeypatch):
    monkeypatch.setenv("CHARGILY_PRICE_PRO_M", "2500")
    assert chargily_service.resolve_amount_dzd("pro", "monthly") == 2500


def test_chargily_amount_unknown_plan_is_400():
    with pytest.raises(HTTPException) as exc:
        chargily_service.resolve_amount_dzd("enterprise", "monthly")
    assert exc.value.status_code == 400


def test_chargily_amount_missing_env_is_503(monkeypatch):
    monkeypatch.delenv("CHARGILY_PRICE_STARTER_M", raising=False)
    with pytest.raises(HTTPException) as exc:
        chargily_service.resolve_amount_dzd("starter", "monthly")
    assert exc.value.status_code == 503


def test_chargily_amount_below_minimum_is_503(monkeypatch):
    monkeypatch.setenv("CHARGILY_PRICE_STARTER_M", "10")  # < 75 DZD
    with pytest.raises(HTTPException) as exc:
        chargily_service.resolve_amount_dzd("starter", "monthly")
    assert exc.value.status_code == 503


def test_chargily_signature_valid_parses_event(monkeypatch):
    import hashlib
    import hmac

    monkeypatch.setenv("CHARGILY_WEBHOOK_SECRET", "sec_test")
    body = b'{"id":"evt_1","type":"checkout.paid"}'
    sig = hmac.new(b"sec_test", body, hashlib.sha256).hexdigest()
    event = chargily_service.verify_and_parse(body, sig)
    assert event["type"] == "checkout.paid"


def test_chargily_signature_invalid_raises(monkeypatch):
    monkeypatch.setenv("CHARGILY_WEBHOOK_SECRET", "sec_test")
    with pytest.raises(ValueError):
        chargily_service.verify_and_parse(b'{"id":"evt_1"}', "deadbeef")


def test_chargily_webhook_unsigned_returns_400(client, monkeypatch):
    monkeypatch.setenv("CHARGILY_WEBHOOK_SECRET", "sec_test")
    resp = client.post("/billing/chargily/webhook", content=b"{}")
    assert resp.status_code == 400


# ── Détection de pays et routage ────────────────────────────────────────────


def _request_with(headers: dict):
    """Fabrique une Request Starlette minimale portant les en-têtes donnés."""
    from starlette.requests import Request as StarletteRequest

    raw = [(k.lower().encode(), v.encode()) for k, v in headers.items()]
    return StarletteRequest({"type": "http", "headers": raw, "client": ("10.0.0.1", 1234)})


def test_client_ip_trusts_rightmost_forwarded_entry():
    # La valeur de gauche est fournie par le client : elle ne doit pas gagner.
    req = _request_with({"x-forwarded-for": "1.2.3.4, 41.100.0.9"})
    assert geo_service.client_ip(req) == "41.100.0.9"


def test_client_ip_ignores_private_addresses():
    req = _request_with({"x-forwarded-for": "192.168.1.10"})
    assert geo_service.client_ip(req) is None


def test_country_from_cloudflare_header():
    req = _request_with({"cf-ipcountry": "dz"})
    assert geo_service.country_from_request(req) == "DZ"


def test_country_unknown_when_no_source():
    req = _request_with({})
    assert geo_service.country_from_request(req) is None


def test_algerian_ip_forces_chargily_and_locks():
    req = _request_with({"cf-ipcountry": "DZ"})
    ctx = billing.resolve_provider(req, {}, None)
    assert ctx["provider"] == "chargily"
    assert ctx["locked"] is True


def test_algerian_ip_beats_declared_foreign_country():
    """Propriété de sécurité : le pays déclaré par le client ne peut pas
    contourner une IP algérienne détectée."""
    req = _request_with({"cf-ipcountry": "DZ"})
    ctx = billing.resolve_provider(req, {}, "FR")
    assert ctx["provider"] == "chargily"
    assert ctx["locked"] is True


def test_exemption_releases_the_lock():
    req = _request_with({"cf-ipcountry": "DZ"})
    ctx = billing.resolve_provider(req, {"billing_stripe_exemption": True}, None)
    assert ctx["provider"] == "stripe"
    assert ctx["locked"] is False


def test_declared_algeria_without_geo_uses_chargily_unlocked():
    req = _request_with({})
    ctx = billing.resolve_provider(req, {}, "DZ")
    assert ctx["provider"] == "chargily"
    assert ctx["locked"] is False


def test_unknown_country_falls_back_to_stripe():
    req = _request_with({})
    ctx = billing.resolve_provider(req, {}, None)
    assert ctx["provider"] == "stripe"
    assert ctx["locked"] is False


def test_checkout_from_algerian_ip_routes_to_chargily(client, monkeypatch):
    """Bout en bout : IP algérienne + pays déclaré vide → branche Chargily
    (ici désactivée, donc 501) au lieu de partir vers Stripe."""

    async def _fake_user(_request):
        return {"_id": "000000000000000000000001", "email": "u@example.com", "name": "U"}

    monkeypatch.setattr(billing, "get_current_user", _fake_user)
    monkeypatch.setenv("CHARGILY_ENABLED", "false")
    resp = client.post(
        "/billing/checkout",
        json={"plan": "pro", "cycle": "monthly"},
        headers={"CF-IPCountry": "DZ"},
    )
    assert resp.status_code == 501
