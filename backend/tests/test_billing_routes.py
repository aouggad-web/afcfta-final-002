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
def trusted_edge(monkeypatch):
    """Simule une origine réellement protégée derrière Cloudflare, pour les
    tests qui portent sur le routage plutôt que sur la preuve de provenance."""
    monkeypatch.delenv("CLOUDFLARE_EDGE_SECRET", raising=False)
    monkeypatch.setenv("TRUST_CLOUDFLARE_HEADERS", "true")


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


def test_chargily_amount_missing_env_falls_back_to_grid_default(monkeypatch):
    # Sans surcharge d'environnement, le montant retombe désormais sur la grille
    # unique pricing.py (source de vérité) au lieu d'échouer en 503.
    monkeypatch.delenv("CHARGILY_PRICE_STARTER_M", raising=False)
    assert chargily_service.resolve_amount_dzd("starter", "monthly") == 1500


def test_chargily_amount_invalid_env_is_503(monkeypatch):
    monkeypatch.setenv("CHARGILY_PRICE_STARTER_M", "pas-un-nombre")
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


def test_cloudflare_header_ignored_when_unproven(monkeypatch):
    """Sans preuve de provenance, l'en-tête CF est ignoré : sinon n'importe qui
    pourrait déclarer son pays en ligne de commande et contourner le verrou."""
    monkeypatch.delenv("CLOUDFLARE_EDGE_SECRET", raising=False)
    monkeypatch.delenv("TRUST_CLOUDFLARE_HEADERS", raising=False)
    req = _request_with({"cf-ipcountry": "dz"})
    assert geo_service.country_from_request(req) is None


def test_country_from_cloudflare_header_when_secret_matches(monkeypatch):
    monkeypatch.setenv("CLOUDFLARE_EDGE_SECRET", "s3cr3t")
    req = _request_with({"cf-ipcountry": "dz", "x-edge-secret": "s3cr3t"})
    assert geo_service.country_from_request(req) == "DZ"


def test_forged_edge_secret_is_rejected(monkeypatch):
    monkeypatch.setenv("CLOUDFLARE_EDGE_SECRET", "s3cr3t")
    req = _request_with({"cf-ipcountry": "FR", "x-edge-secret": "wrong"})
    assert geo_service.country_from_request(req) is None


def test_trust_flag_allows_cloudflare_header(monkeypatch):
    monkeypatch.delenv("CLOUDFLARE_EDGE_SECRET", raising=False)
    monkeypatch.setenv("TRUST_CLOUDFLARE_HEADERS", "true")
    req = _request_with({"cf-ipcountry": "DZ"})
    assert geo_service.country_from_request(req) == "DZ"


def test_connecting_ip_used_when_cloudflare_trusted(monkeypatch):
    monkeypatch.setenv("CLOUDFLARE_EDGE_SECRET", "s3cr3t")
    req = _request_with(
        {
            "x-edge-secret": "s3cr3t",
            "cf-connecting-ip": "41.100.0.9",
            "x-forwarded-for": "1.2.3.4",
        }
    )
    assert geo_service.client_ip(req) == "41.100.0.9"


def test_country_unknown_when_no_source():
    req = _request_with({})
    assert geo_service.country_from_request(req) is None


def test_algerian_ip_forces_chargily_and_locks(trusted_edge):
    req = _request_with({"cf-ipcountry": "DZ"})
    ctx = billing.resolve_provider(req, {}, None)
    assert ctx["provider"] == "chargily"
    assert ctx["locked"] is True


def test_algerian_ip_beats_declared_foreign_country(trusted_edge):
    """Propriété de sécurité : le pays déclaré par le client ne peut pas
    contourner une IP algérienne détectée."""
    req = _request_with({"cf-ipcountry": "DZ"})
    ctx = billing.resolve_provider(req, {}, "FR")
    assert ctx["provider"] == "chargily"
    assert ctx["locked"] is True


def test_exemption_releases_the_lock(trusted_edge):
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


def test_checkout_from_algerian_ip_routes_to_chargily(client, monkeypatch, trusted_edge):
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


# ── Idempotence et sûreté au crash des webhooks ─────────────────────────────


class _FakeCollection:
    """Collection Mongo minimale : dédup par event_id, insert/delete/find/update."""

    def __init__(self):
        self.docs = []
        self._unique = set()

    async def insert_one(self, doc):
        from pymongo.errors import DuplicateKeyError

        eid = doc.get("event_id")
        if eid is not None:
            if eid in self._unique:
                raise DuplicateKeyError("dup")
            self._unique.add(eid)
        self.docs.append(doc)
        return type("R", (), {"inserted_id": "x"})()

    async def delete_one(self, query):
        eid = query.get("event_id")
        self._unique.discard(eid)
        self.docs = [d for d in self.docs if d.get("event_id") != eid]

    async def find_one(self, query, projection=None):
        return None

    async def update_one(self, query, update):
        return None


class _FakeDB2:
    def __init__(self):
        self.payment_events = _FakeCollection()
        self.users = _FakeCollection()
        self.payment_attempts = _FakeCollection()


_STRIPE_EVENT = {
    "id": "evt_1",
    "type": "checkout.session.completed",
    "data": {
        "object": {
            "metadata": {"user_id": "000000000000000000000001", "plan": "pro", "cycle": "monthly"},
            "subscription": "sub_1",
            "customer": "cus_1",
        }
    },
}


@pytest.fixture
def webhook_client(monkeypatch):
    fake = _FakeDB2()
    billing.set_database(fake)
    monkeypatch.setattr(stripe_service, "construct_event", lambda payload, sig: _STRIPE_EVENT)
    app = FastAPI()
    app.include_router(billing.router)
    return TestClient(app, raise_server_exceptions=False), fake


def test_webhook_releases_reservation_when_handler_fails(webhook_client, monkeypatch):
    """Propriété critique : si le traitement échoue, la réservation est libérée
    pour que le rejeu Stripe refasse le travail — un paiement n'est jamais perdu."""
    client, fake = webhook_client

    async def _boom(*a, **k):
        raise RuntimeError("db indisponible")

    monkeypatch.setattr(billing, "_update_user_by_id", _boom)
    resp = client.post("/billing/webhook", content=b"{}", headers={"stripe-signature": "x"})
    assert resp.status_code == 500
    assert "evt_1" not in fake.payment_events._unique  # réservation libérée

    # Rejeu : le handler réussit désormais → l'événement est bien traité.
    async def _ok(*a, **k):
        return None

    monkeypatch.setattr(billing, "_update_user_by_id", _ok)
    replay = client.post("/billing/webhook", content=b"{}", headers={"stripe-signature": "x"})
    assert replay.status_code == 200
    assert replay.json()["status"] == "ok"


def test_geo_diagnostic_reports_what_backend_sees(client, monkeypatch):
    """Le diagnostic reflète fidèlement la requête : en-têtes vus, IP, pays."""
    monkeypatch.delenv("CLOUDFLARE_EDGE_SECRET", raising=False)
    monkeypatch.delenv("TRUST_CLOUDFLARE_HEADERS", raising=False)
    monkeypatch.delenv("GEOIP_DB_PATH", raising=False)
    resp = client.get(
        "/billing/geo-diagnostic",
        headers={"CF-IPCountry": "DZ", "X-Forwarded-For": "1.2.3.4, 41.100.0.9"},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["client_ip"] == "41.100.0.9"
    assert body["detected_country"] is None  # en-tête CF non prouvé → ignoré
    assert body["cloudflare_trusted"] is False
    assert body["geoip_db_configured"] is False
    assert body["headers_seen"]["cf_ipcountry"] is True
    assert body["headers_seen"]["x_forwarded_for_hops"] == 2


def test_webhook_is_idempotent_on_replay(webhook_client, monkeypatch):
    """Deux livraisons du même événement → traité une seule fois."""
    client, fake = webhook_client

    async def _ok(*a, **k):
        return None

    monkeypatch.setattr(billing, "_update_user_by_id", _ok)
    first = client.post("/billing/webhook", content=b"{}", headers={"stripe-signature": "x"})
    second = client.post("/billing/webhook", content=b"{}", headers={"stripe-signature": "x"})
    assert first.json()["status"] == "ok"
    assert second.json()["status"] == "already_processed"


# ── Résolution de l'IP derrière plusieurs relais ────────────────────────────


def test_client_ip_honours_trusted_hop_count(monkeypatch):
    """Avec 3 relais en frontal, l'IP du visiteur est à 3 positions de la fin."""
    monkeypatch.setenv("TRUSTED_PROXY_HOPS", "3")
    req = _request_with({"x-forwarded-for": "41.100.0.9, 10.0.0.1, 10.0.0.2"})
    assert geo_service.client_ip(req) == "41.100.0.9"


def test_client_ip_default_single_hop_takes_rightmost(monkeypatch):
    monkeypatch.delenv("TRUSTED_PROXY_HOPS", raising=False)
    req = _request_with({"x-forwarded-for": "1.2.3.4, 81.200.5.4"})
    assert geo_service.client_ip(req) == "81.200.5.4"


def test_client_cannot_promote_itself_by_lengthening_the_chain(monkeypatch):
    """Un client qui préfixe la chaîne pour se désigner échoue : l'index est
    borné, donc sa valeur forgée reste à gauche de la position retenue."""
    monkeypatch.setenv("TRUSTED_PROXY_HOPS", "3")
    req = _request_with({"x-forwarded-for": "6.6.6.6, 41.100.0.9, 10.0.0.1, 10.0.0.2"})
    assert geo_service.client_ip(req) == "41.100.0.9"


def test_hop_count_larger_than_chain_is_clamped(monkeypatch):
    monkeypatch.setenv("TRUSTED_PROXY_HOPS", "9")
    req = _request_with({"x-forwarded-for": "41.100.0.9"})
    assert geo_service.client_ip(req) == "41.100.0.9"


def test_invalid_hop_count_falls_back_to_one(monkeypatch):
    monkeypatch.setenv("TRUSTED_PROXY_HOPS", "beaucoup")
    assert geo_service.trusted_proxy_hops() == 1
