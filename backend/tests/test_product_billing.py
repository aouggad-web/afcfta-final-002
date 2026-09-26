"""
Tests des produits hors formule (API, options, rapports, formation).

Hermétiques : Stripe, Chargily et l'envoi d'emails sont remplacés ; la base est
une petite collection Mongo en mémoire (égalité simple, $set / $inc).
"""

import asyncio
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest
from bson import ObjectId
from fastapi import FastAPI, HTTPException
from fastapi.testclient import TestClient
from pymongo.errors import DuplicateKeyError

backend_path = Path(__file__).parent.parent
if str(backend_path) not in sys.path:
    sys.path.insert(0, str(backend_path))

import auth  # noqa: E402
import pricing  # noqa: E402
from routes import billing  # noqa: E402
from services import chargily_service, product_fulfillment, stripe_service  # noqa: E402

USER_ID = ObjectId("000000000000000000000001")


class _Col:
    def __init__(self, unique=None):
        self.docs = []
        self.unique = unique

    @staticmethod
    def _match(doc, query):
        return all(doc.get(k) == v for k, v in query.items())

    async def insert_one(self, doc):
        if self.unique and any(d.get(self.unique) == doc.get(self.unique) for d in self.docs):
            raise DuplicateKeyError("dup")
        doc = dict(doc)
        doc.setdefault("_id", ObjectId())
        self.docs.append(doc)
        return type("R", (), {"inserted_id": doc["_id"]})()

    async def find_one(self, query, projection=None):
        for d in self.docs:
            if self._match(d, query):
                return dict(d)
        return None

    async def update_one(self, query, update):
        for d in self.docs:
            if self._match(d, query):
                d.update(update.get("$set", {}))
                return

    async def delete_one(self, query):
        self.docs = [d for d in self.docs if not self._match(d, query)]

    async def find_one_and_update(self, query, update, return_document=None):
        for d in self.docs:
            if self._match(d, query):
                d.update(update.get("$set", {}))
                for k, v in update.get("$inc", {}).items():
                    d[k] = d.get(k, 0) + v
                return dict(d)
        return None


class _DB:
    def __init__(self):
        self.users = _Col()
        self.purchases = _Col()
        self.api_keys = _Col()
        self.payment_events = _Col(unique="event_id")
        self.payment_attempts = _Col()

    def __getitem__(self, name):
        return getattr(self, name)


@pytest.fixture
def db(monkeypatch):
    fake = _DB()
    fake.users.docs.append(
        {"_id": USER_ID, "email": "u@example.com", "name": "U", "signup_country": "FR"}
    )
    billing.set_database(fake)
    auth.set_database(fake)
    sent = []

    def _capture(to, subject, body):
        sent.append((to, subject, body))

    monkeypatch.setattr(product_fulfillment, "send_email", _capture)
    monkeypatch.setattr(billing, "send_email", _capture)
    monkeypatch.setenv("SAAS_SMTP_USER", "equipe@example.com")
    fake.sent = sent
    yield fake
    auth.set_database(None)


@pytest.fixture
def client(db, monkeypatch):
    async def _user(_request):
        return dict(db.users.docs[0])

    monkeypatch.setattr(billing, "get_current_user", _user)
    app = FastAPI()
    app.include_router(billing.router)
    return TestClient(app, raise_server_exceptions=False)


def _activate(db, product_id, provider="stripe", subscription_id=None):
    asyncio.run(
        product_fulfillment.activate(
            db,
            user_id=str(USER_ID),
            product_id=product_id,
            provider=provider,
            subscription_id=subscription_id,
        )
    )


# ── Grille ──────────────────────────────────────────────────────────────────


def test_product_dzd_follows_plan_rule():
    assert pricing.product_dzd_amount("api_starter") == 29 * 150


def test_product_dzd_env_override(monkeypatch):
    monkeypatch.setenv("CHARGILY_PRICE_REPORT_PHARMA", "12000")
    assert pricing.product_dzd_amount("report_pharma") == 12000


def test_pricing_endpoint_lists_products(client):
    data = client.get("/billing/pricing").json()
    ids = {p["product"] for p in data["products"]}
    assert ids == set(pricing.PRODUCTS)


# ── Checkout ────────────────────────────────────────────────────────────────


def test_unknown_product_is_rejected(client):
    resp = client.post("/billing/product-checkout", json={"product": "nope"})
    assert resp.status_code == 422


def test_stripe_product_checkout_uses_server_price(client, monkeypatch):
    captured = {}
    monkeypatch.setattr(stripe_service, "get_or_create_customer", lambda *a: "cus_1")

    def _session(**kwargs):
        captured.update(kwargs)
        return "https://stripe.test/s"

    monkeypatch.setattr(stripe_service, "create_product_checkout_session", _session)
    resp = client.post("/billing/product-checkout", json={"product": "api_business"})
    assert resp.status_code == 200
    assert captured["amount_eur"] == 99
    assert captured["recurring"] is True
    assert captured["metadata"] == {
        "user_id": str(USER_ID),
        "kind": "product",
        "product": "api_business",
    }


def test_algerian_account_pays_product_with_chargily(client, db, monkeypatch):
    db.users.docs[0]["signup_country"] = "DZ"
    monkeypatch.setenv("CHARGILY_ENABLED", "true")
    captured = {}

    def _checkout(**kwargs):
        captured.update(kwargs)
        return "https://chargily.test/c"

    monkeypatch.setattr(chargily_service, "create_checkout", _checkout)
    resp = client.post("/billing/product-checkout", json={"product": "certification"})
    assert resp.status_code == 200
    assert captured["amount_dzd"] == 129 * 150


# ── Livraison ───────────────────────────────────────────────────────────────


def test_api_plan_creates_metered_key_and_emails_it(db):
    _activate(db, "api_starter", subscription_id="sub_api")
    key = db.api_keys.docs[0]
    assert key["request_quota"] == 5000 and key["active"] is True
    purchase = db.purchases.docs[0]
    assert purchase["api_key_id"] == key["_id"]
    to, _subject, body = db.sent[0]
    assert to == "u@example.com" and "afcfta_" in body
    assert len(db.sent) == 1  # livraison automatique : pas de notification équipe


def test_manual_product_notifies_team(db):
    _activate(db, "report_pharma")
    assert not db.api_keys.docs
    assert [to for to, _, _ in db.sent] == ["u@example.com", "equipe@example.com"]


def test_chargily_renewal_extends_from_current_end(db):
    _activate(db, "api_business", provider="chargily")
    first_end = db.purchases.docs[0]["period_end"]
    _activate(db, "api_business", provider="chargily")
    assert len(db.purchases.docs) == 1 and len(db.api_keys.docs) == 1
    assert db.purchases.docs[0]["period_end"] == first_end + timedelta(days=30)
    assert db.api_keys.docs[0]["expires_at"] == first_end + timedelta(days=30)


def test_ended_stripe_subscription_disables_key(db):
    _activate(db, "api_starter", subscription_id="sub_api")
    asyncio.run(product_fulfillment.update_stripe_subscription(db, "sub_api", "canceled"))
    assert db.api_keys.docs[0]["active"] is False
    assert db.purchases.docs[0]["status"] == "canceled"


# ── Webhooks : un produit ne touche jamais à la formule ─────────────────────


def _stripe_event(monkeypatch, event):
    monkeypatch.setattr(stripe_service, "construct_event", lambda payload, sig: event)


def test_product_subscription_deleted_keeps_plan(client, db, monkeypatch):
    db.users.docs[0].update({"subscription_tier": "pro", "subscription_status": "active"})
    db.users.docs[0]["stripe_customer_id"] = "cus_1"
    _activate(db, "newsletter", subscription_id="sub_news")
    _stripe_event(
        monkeypatch,
        {
            "id": "evt_del",
            "type": "customer.subscription.deleted",
            "data": {
                "object": {
                    "id": "sub_news",
                    "customer": "cus_1",
                    "metadata": {"kind": "product", "product": "newsletter"},
                }
            },
        },
    )
    resp = client.post("/billing/webhook", content=b"{}", headers={"stripe-signature": "x"})
    assert resp.status_code == 200
    assert db.users.docs[0]["subscription_tier"] == "pro"
    assert db.purchases.docs[0]["status"] == "canceled"


def test_product_invoice_failure_keeps_plan_status(client, db, monkeypatch):
    db.users.docs[0].update({"subscription_status": "active", "stripe_customer_id": "cus_1"})
    _activate(db, "api_starter", subscription_id="sub_api")
    _stripe_event(
        monkeypatch,
        {
            "id": "evt_inv",
            "type": "invoice.payment_failed",
            "data": {
                "object": {
                    "customer": "cus_1",
                    "parent": {"subscription_details": {"subscription": "sub_api"}},
                }
            },
        },
    )
    resp = client.post("/billing/webhook", content=b"{}", headers={"stripe-signature": "x"})
    assert resp.status_code == 200
    assert db.users.docs[0]["subscription_status"] == "active"
    assert db.purchases.docs[0]["status"] == "past_due"


def test_stripe_product_checkout_completed_delivers(client, db, monkeypatch):
    _stripe_event(
        monkeypatch,
        {
            "id": "evt_ok",
            "type": "checkout.session.completed",
            "data": {
                "object": {
                    "subscription": None,
                    "customer": "cus_1",
                    "metadata": {
                        "user_id": str(USER_ID),
                        "kind": "product",
                        "product": "report_agri",
                    },
                }
            },
        },
    )
    resp = client.post("/billing/webhook", content=b"{}", headers={"stripe-signature": "x"})
    assert resp.status_code == 200
    assert db.purchases.docs[0]["product"] == "report_agri"
    assert "subscription_tier" not in db.users.docs[0]


# ── Clés vendues : quota mensuel et expiration ──────────────────────────────


def _key(db, **fields):
    raw = "afcfta_test"
    db.api_keys.docs.append(
        {"_id": ObjectId(), "key_hash": auth._hash_key(raw), "active": True, **fields}
    )
    return raw


def test_sold_key_is_metered(db):
    raw = _key(db, tier="free", request_quota=2)
    asyncio.run(auth.require_auth(x_api_key=raw))
    asyncio.run(auth.require_auth(x_api_key=raw))
    with pytest.raises(HTTPException) as exc:
        asyncio.run(auth.require_auth(x_api_key=raw))
    assert exc.value.status_code == 429


def test_admin_created_key_is_not_metered(db):
    raw = _key(db, tier="pro")
    for _ in range(3):
        asyncio.run(auth.require_auth(x_api_key=raw))
    assert "request_count" not in db.api_keys.docs[0]


def test_expired_key_is_rejected(db):
    raw = _key(
        db,
        tier="free",
        request_quota=10,
        expires_at=datetime.now(timezone.utc) - timedelta(days=1),
    )
    with pytest.raises(HTTPException) as exc:
        asyncio.run(auth.require_auth(x_api_key=raw))
    assert exc.value.status_code == 401
