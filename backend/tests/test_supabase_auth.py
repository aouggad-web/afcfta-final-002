"""
Tests de l'intégration Supabase Auth (étape A : identité seulement).

Hermétiques : une vraie paire de clés ES256 est générée pour signer des jetons
comme le ferait Supabase ; la récupération des clés publiques (JWKS) et l'API
d'administration Supabase sont remplacées ; la base est en mémoire.
"""

import asyncio
import sys
import time
from pathlib import Path

import jwt
import pytest
from bson import ObjectId
from cryptography.hazmat.primitives.asymmetric import ec
from fastapi import FastAPI, Request
from fastapi.testclient import TestClient

backend_path = Path(__file__).parent.parent
if str(backend_path) not in sys.path:
    sys.path.insert(0, str(backend_path))

import entitlement_guard  # noqa: E402
from routes import user_auth  # noqa: E402
from services import stripe_service, supabase_auth  # noqa: E402
from services.user_auth_service import create_access_token  # noqa: E402

SUPABASE_URL = "https://projet-test.supabase.co"
SUB = "7b0c2a52-1b1e-4a8e-9c1d-000000000001"
PRIVATE_KEY = ec.generate_private_key(ec.SECP256R1())


class _Cursor:
    def __init__(self, docs):
        self.docs = docs

    async def to_list(self, length=None):
        return self.docs


class _FullCol:
    """Collection Mongo minimale en mémoire (égalité simple, $set)."""

    def __init__(self):
        self.docs = []

    @staticmethod
    def _match(doc, query):
        return all(doc.get(k) == v for k, v in query.items())

    async def insert_one(self, doc):
        doc = dict(doc)
        doc.setdefault("_id", ObjectId())
        self.docs.append(doc)
        return type("R", (), {"inserted_id": doc["_id"]})()

    async def find_one(self, query, projection=None):
        return next((dict(d) for d in self.docs if self._match(d, query)), None)

    async def update_one(self, query, update):
        for d in self.docs:
            if self._match(d, query):
                d.update(update.get("$set", {}))
                return

    async def delete_one(self, query):
        for d in self.docs:
            if self._match(d, query):
                self.docs.remove(d)
                return

    def find(self, query, projection=None):
        docs = [dict(d) for d in self.docs if self._match(d, query)]
        for d in docs:
            for field, keep in (projection or {}).items():
                if not keep:
                    d.pop(field, None)
        return _Cursor(docs)

    async def update_many(self, query, update):
        for d in self.docs:
            if self._match(d, query):
                d.update(update.get("$set", {}))

    async def delete_many(self, query):
        self.docs = [d for d in self.docs if not self._match(d, query)]


class _DB:
    def __init__(self):
        for name in (
            "users",
            "purchases",
            "api_keys",
            "payment_attempts",
            "usage_counters",
            "login_attempts",
            "contact_messages",
        ):
            setattr(self, name, _FullCol())

    def __getitem__(self, name):
        return getattr(self, name)


def _token(sub=SUB, email="alice@example.com", issuer=None, exp_in=3600):
    now = int(time.time())
    return jwt.encode(
        {
            "sub": sub,
            "email": email,
            "aud": "authenticated",
            "iss": issuer or f"{SUPABASE_URL}/auth/v1",
            "iat": now,
            "exp": now + exp_in,
            "role": "authenticated",
        },
        PRIVATE_KEY,
        algorithm="ES256",
        headers={"kid": "test-kid"},
    )


class _FakeJwks:
    def get_signing_key_from_jwt(self, token):
        return type("K", (), {"key": PRIVATE_KEY.public_key()})()


@pytest.fixture
def supabase(monkeypatch):
    monkeypatch.setenv("SUPABASE_URL", SUPABASE_URL)
    monkeypatch.setenv("JWT_SECRET", "legacy-secret")
    monkeypatch.setattr(supabase_auth, "_jwks", lambda: _FakeJwks())
    admin = {"user": {"email_confirmed_at": "2026-09-25T10:00:00Z", "user_metadata": {}}}
    deleted = []

    async def _get_admin_user(user_id):
        return admin["user"]

    async def _delete_admin_user(user_id):
        deleted.append(user_id)

    monkeypatch.setattr(supabase_auth, "get_admin_user", _get_admin_user)
    monkeypatch.setattr(supabase_auth, "delete_admin_user", _delete_admin_user)
    return {"admin": admin, "deleted": deleted}


@pytest.fixture
def db(monkeypatch):
    fake = _DB()
    user_auth.set_database(fake)
    entitlement_guard.set_database(fake)
    monkeypatch.setattr(user_auth, "send_welcome_email", lambda *a: None)
    yield fake
    entitlement_guard.set_database(None)


@pytest.fixture
def client(db):
    app = FastAPI()
    app.include_router(user_auth.router)
    return TestClient(app)


# ── Vérification des jetons ─────────────────────────────────────────────────


def test_valid_token_is_accepted(supabase):
    assert supabase_auth.decode_token(_token())["sub"] == SUB


def test_token_from_another_project_is_rejected(supabase):
    assert supabase_auth.decode_token(_token(issuer="https://autre.supabase.co/auth/v1")) is None


def test_expired_token_is_rejected(supabase):
    assert supabase_auth.decode_token(_token(exp_in=-10)) is None


def test_legacy_hs256_token_is_not_a_supabase_token(supabase):
    assert supabase_auth.decode_token(create_access_token(str(ObjectId()), "a@b.c")) is None


def test_disabled_without_supabase_url(supabase, monkeypatch):
    monkeypatch.delenv("SUPABASE_URL")
    assert supabase_auth.decode_token(_token()) is None


# ── POST /auth/session ──────────────────────────────────────────────────────


def _open_session(client, token=None):
    return client.post("/auth/session", headers={"Authorization": f"Bearer {token or _token()}"})


def test_first_session_creates_linked_account_with_consent(client, db, supabase):
    supabase["admin"]["user"]["user_metadata"] = {
        "name": "  Alice   Test ",
        "terms_version": "2026-09",
        "terms_accepted_at": "2026-09-25T10:00:00Z",
    }
    resp = _open_session(client)
    assert resp.status_code == 200
    user = db.users.docs[0]
    assert user["supabase_id"] == SUB and user["name"] == "Alice Test"
    assert user["consents"][0]["version"] == "2026-09"
    assert "signup_ip" not in user  # le pays seul est conservé, jamais l'IP
    assert "access_token" in resp.cookies


def test_existing_account_is_linked_not_duplicated(client, db, supabase):
    db.users.docs.append(
        {"_id": ObjectId(), "email": "alice@example.com", "name": "Alice", "password_hash": "x"}
    )
    assert _open_session(client).status_code == 200
    assert len(db.users.docs) == 1
    assert db.users.docs[0]["supabase_id"] == SUB


def test_unconfirmed_email_cannot_claim_an_account(client, db, supabase):
    supabase["admin"]["user"]["email_confirmed_at"] = None
    db.users.docs.append({"_id": ObjectId(), "email": "alice@example.com", "name": "Alice"})
    assert _open_session(client).status_code == 403
    assert "supabase_id" not in db.users.docs[0]


def test_invalid_token_is_refused(client, db, supabase):
    assert _open_session(client, token="pas-un-jeton").status_code == 401


def test_session_route_absent_without_supabase(client, db, supabase, monkeypatch):
    monkeypatch.delenv("SUPABASE_URL")
    assert _open_session(client).status_code == 404


def test_me_and_entitlements_recognise_supabase_session(client, db, supabase):
    _open_session(client)
    me = client.get("/auth/me")
    assert me.status_code == 200 and me.json()["email"] == "alice@example.com"

    app = FastAPI()

    @app.get("/who")
    async def who(request: Request):
        user = await entitlement_guard.get_optional_subscriber(request)
        return {"email": user and user["email"]}

    resp = TestClient(app).get("/who", headers={"Authorization": f"Bearer {_token()}"})
    assert resp.json() == {"email": "alice@example.com"}


def test_legacy_session_still_works(client, db, supabase):
    uid = ObjectId()
    db.users.docs.append({"_id": uid, "email": "old@example.com", "name": "Old"})
    client.cookies.set("access_token", create_access_token(str(uid), "old@example.com"))
    assert client.get("/auth/me").json()["email"] == "old@example.com"


# ── Export et suppression (RGPD) ────────────────────────────────────────────


def _seed_account(db):
    uid = ObjectId()
    db.users.docs.append(
        {
            "_id": uid,
            "email": "alice@example.com",
            "name": "Alice",
            "password_hash": "secret-hash",
            "supabase_id": SUB,
            "subscription_id": "sub_plan",
        }
    )
    db.purchases.docs.append(
        {
            "_id": ObjectId(),
            "user_id": uid,
            "product": "api_starter",
            "status": "active",
            "stripe_subscription_id": "sub_api",
        }
    )
    db.api_keys.docs.append({"_id": ObjectId(), "user_id": str(uid), "key_hash": "h", "name": "k"})
    db.payment_attempts.docs.append({"_id": ObjectId(), "user_id": uid, "ip": "41.100.0.9"})
    db.contact_messages.docs.append({"_id": ObjectId(), "email": "alice@example.com"})
    return uid


def test_export_contains_data_without_secrets(client, db, supabase):
    _seed_account(db)
    client.cookies.set("access_token", _token())
    resp = client.get("/auth/account/export")
    assert resp.status_code == 200
    body = resp.json()
    assert "password_hash" not in body["compte"]
    assert "key_hash" not in body["cles_api"][0]
    assert body["achats"][0]["product"] == "api_starter"
    assert "attachment" in resp.headers["content-disposition"]


def test_delete_account_cancels_billing_and_erases_data(client, db, supabase, monkeypatch):
    uid = _seed_account(db)
    canceled = []
    monkeypatch.setattr(stripe_service, "cancel_subscription", canceled.append)
    client.cookies.set("access_token", _token())
    resp = client.delete("/auth/account")
    assert resp.status_code == 200
    assert set(canceled) == {"sub_plan", "sub_api"}
    assert supabase["deleted"] == [SUB]
    assert not db.users.docs and not db.api_keys.docs and not db.payment_attempts.docs
    assert not db.contact_messages.docs
    assert db.purchases.docs[0]["user_id"] is None  # conservé anonymisé
    assert uid not in [d.get("user_id") for d in db.purchases.docs]


def test_delete_account_keeps_everything_if_billing_cancel_fails(client, db, supabase, monkeypatch):
    _seed_account(db)

    def _fail(subscription_id):
        raise RuntimeError("Stripe injoignable")

    monkeypatch.setattr(stripe_service, "cancel_subscription", _fail)
    client.cookies.set("access_token", _token())
    assert client.delete("/auth/account").status_code == 502
    assert db.users.docs and not supabase["deleted"]


def test_decode_never_raises_on_garbage(supabase):
    for junk in ("", "a.b.c", "x" * 50):
        assert asyncio.run(asyncio.to_thread(supabase_auth.decode_token, junk)) is None
