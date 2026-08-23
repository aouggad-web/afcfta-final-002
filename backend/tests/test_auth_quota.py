"""
Tests for backend/auth.py: public-data passthrough and the AI monthly usage
quota enforced by check_ai_quota.

Uses a tiny in-memory fake Mongo collection (no real MongoDB needed) since
auth.py only calls find_one / find_one_and_update on db["api_keys"].
"""

import asyncio
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import auth
import pytest
from fastapi import HTTPException


class _FakeCollection:
    def __init__(self, docs):
        self._docs = {d["_id"]: dict(d) for d in docs}

    async def find_one(self, query):
        for doc in self._docs.values():
            if all(doc.get(k) == v for k, v in query.items()):
                return dict(doc)
        return None

    async def find_one_and_update(self, query, update, return_document=None):
        for _id, doc in self._docs.items():
            if all(doc.get(k) == v for k, v in query.items()):
                if "$inc" in update:
                    for k, v in update["$inc"].items():
                        doc[k] = doc.get(k, 0) + v
                if "$set" in update:
                    doc.update(update["$set"])
                return dict(doc)
        return None


class _FakeDB:
    def __init__(self, docs):
        self._col = _FakeCollection(docs)

    def __getitem__(self, name):
        return self._col


@pytest.fixture(autouse=True)
def _reset_db():
    auth.set_database(None)
    yield
    auth.set_database(None)


def test_require_auth_public_passthrough_when_no_db():
    result = asyncio.run(auth.require_auth(x_api_key=None))
    assert result["tier"] == "public"


def test_require_auth_public_passthrough_when_db_but_no_key():
    auth.set_database(_FakeDB([]))
    result = asyncio.run(auth.require_auth(x_api_key=None))
    assert result["tier"] == "public"
    assert auth.PUBLIC_DATA_ACCESS is True


def test_require_auth_rejects_unknown_key_when_db_configured():
    auth.set_database(_FakeDB([]))
    with pytest.raises(HTTPException) as exc:
        asyncio.run(auth.require_auth(x_api_key="bogus"))
    assert exc.value.status_code == 401


def test_require_auth_rejects_no_key_no_session_when_public_access_disabled(monkeypatch):
    monkeypatch.setattr(auth, "PUBLIC_DATA_ACCESS", False)
    auth.set_database(_FakeDB([]))
    with pytest.raises(HTTPException) as exc:
        asyncio.run(auth.require_auth(x_api_key=None))
    assert exc.value.status_code == 401


def test_require_auth_accepts_valid_jwt_session_when_public_access_disabled(monkeypatch):
    """The entitlement-gated module routers put `_auth` before the entitlement
    dependency in the FastAPI dependency chain — if `_auth` 401s a signed-in
    SaaS subscriber for lacking an X-API-Key, `entitlement_guard.require_module`
    never even runs, and the JWT-based subscription gating this PR adds is
    dead on any deployment with PUBLIC_DATA_ACCESS=false. A valid session
    cookie must let the request through here so entitlement_guard can resolve
    the subscriber's real tier downstream."""
    monkeypatch.setenv("JWT_SECRET", "test-secret")
    monkeypatch.setattr(auth, "PUBLIC_DATA_ACCESS", False)
    auth.set_database(_FakeDB([]))

    from services.user_auth_service import create_access_token

    token = create_access_token("507f1f77bcf86cd799439011", "subscriber@example.com")

    result = asyncio.run(auth.require_auth(x_api_key=None, access_token=token))
    assert result["tier"] == "subscriber"


def test_require_auth_rejects_invalid_jwt_session_when_public_access_disabled(monkeypatch):
    monkeypatch.setattr(auth, "PUBLIC_DATA_ACCESS", False)
    auth.set_database(_FakeDB([]))
    with pytest.raises(HTTPException) as exc:
        asyncio.run(auth.require_auth(x_api_key=None, access_token="not-a-real-jwt"))
    assert exc.value.status_code == 401


def test_check_ai_quota_blocks_when_no_db():
    with pytest.raises(HTTPException) as exc:
        asyncio.run(auth.check_ai_quota(x_api_key="whatever"))
    assert exc.value.status_code == 503


def test_check_ai_quota_requires_key_even_with_public_data_access():
    auth.set_database(_FakeDB([]))
    with pytest.raises(HTTPException) as exc:
        asyncio.run(auth.check_ai_quota(x_api_key=None))
    assert exc.value.status_code == 401


def test_check_ai_quota_allows_within_quota_and_increments():
    key_hash = auth._hash_key("freekey")
    auth.set_database(_FakeDB([{"_id": "1", "key_hash": key_hash, "active": True, "tier": "free"}]))
    result = asyncio.run(auth.check_ai_quota(x_api_key="freekey"))
    assert result["usage_count"] == 1
    result = asyncio.run(auth.check_ai_quota(x_api_key="freekey"))
    assert result["usage_count"] == 2


def test_check_ai_quota_blocks_once_exceeded():
    key_hash = auth._hash_key("freekey")
    period = auth._current_period()
    auth.set_database(
        _FakeDB(
            [
                {
                    "_id": "1",
                    "key_hash": key_hash,
                    "active": True,
                    "tier": "free",
                    "usage_period": period,
                    "usage_count": auth.AI_TIER_QUOTAS["free"],
                }
            ]
        )
    )
    with pytest.raises(HTTPException) as exc:
        asyncio.run(auth.check_ai_quota(x_api_key="freekey"))
    assert exc.value.status_code == 429


def test_check_ai_quota_admin_tier_is_unlimited():
    key_hash = auth._hash_key("adminkey")
    auth.set_database(
        _FakeDB([{"_id": "1", "key_hash": key_hash, "active": True, "tier": "admin"}])
    )
    for _ in range(5):
        result = asyncio.run(auth.check_ai_quota(x_api_key="adminkey"))
    assert result["tier"] == "admin"


def test_check_ai_quota_respects_per_key_monthly_quota_override():
    key_hash = auth._hash_key("customkey")
    auth.set_database(
        _FakeDB(
            [
                {
                    "_id": "1",
                    "key_hash": key_hash,
                    "active": True,
                    "tier": "free",
                    "monthly_quota": 1,
                }
            ]
        )
    )
    asyncio.run(auth.check_ai_quota(x_api_key="customkey"))
    with pytest.raises(HTTPException) as exc:
        asyncio.run(auth.check_ai_quota(x_api_key="customkey"))
    assert exc.value.status_code == 429


def test_check_ai_quota_zero_override_disables_ai():
    # An explicit monthly_quota=0 must disable AI use (not be treated as unset).
    key_hash = auth._hash_key("blockedkey")
    auth.set_database(
        _FakeDB(
            [
                {
                    "_id": "1",
                    "key_hash": key_hash,
                    "active": True,
                    "tier": "pro",
                    "monthly_quota": 0,
                }
            ]
        )
    )
    with pytest.raises(HTTPException) as exc:
        asyncio.run(auth.check_ai_quota(x_api_key="blockedkey"))
    assert exc.value.status_code == 429


def test_resolve_ai_quota():
    assert auth.resolve_ai_quota("admin") is None
    assert auth.resolve_ai_quota("free") == auth.AI_TIER_QUOTAS["free"]
    assert auth.resolve_ai_quota("pro") == auth.AI_TIER_QUOTAS["pro"]
    assert auth.resolve_ai_quota("unknown-tier") == auth.AI_TIER_QUOTAS["free"]
    # Explicit override wins, including a falsy 0.
    assert auth.resolve_ai_quota("free", 5) == 5
    assert auth.resolve_ai_quota("pro", 0) == 0
