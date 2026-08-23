"""
Tests de la couche entitlements (`entitlements.py` + `entitlement_guard.py`) :
résolution du tier effectif, gating par module, et compteur de quota atomique.

Hermétiques : la "base Mongo" est un double en mémoire qui reproduit juste
assez de la sémantique motor (`find_one`, `find_one_and_update`, `update_one`)
pour exercer `check_and_increment_usage` sans dépendance réseau.
"""

import sys
from pathlib import Path

import pytest
from bson import ObjectId
from fastapi import HTTPException
from pymongo.errors import DuplicateKeyError

backend_path = Path(__file__).parent.parent
if str(backend_path) not in sys.path:
    sys.path.insert(0, str(backend_path))

import entitlement_guard  # noqa: E402
from entitlements import ModuleAccess, resolve_entitlements  # noqa: E402


class _FakeCollection:
    """Assez de sémantique Mongo pour exercer check_and_increment_usage:
    find_one, find_one_and_update (avec $inc et un filtre $lt), update_one
    avec $setOnInsert + upsert."""

    def __init__(self):
        self._docs = {}

    @staticmethod
    def _key(doc):
        return tuple(str(doc[k]) for k in ("user_id", "counter_id", "period_key"))

    def _match(self, doc, filt):
        for k, v in filt.items():
            if isinstance(v, dict) and "$lt" in v:
                if not (doc.get(k, 0) < v["$lt"]):
                    return False
            elif doc.get(k) != v:
                return False
        return True

    async def find_one(self, filt):
        for doc in self._docs.values():
            if self._match(doc, filt):
                return dict(doc)
        return None

    async def find_one_and_update(self, filt, update, return_document=None):
        for key, doc in self._docs.items():
            if self._match(doc, filt):
                if "$inc" in update:
                    for field, amount in update["$inc"].items():
                        doc[field] = doc.get(field, 0) + amount
                return dict(doc)
        return None

    async def insert_one(self, doc):
        key = self._key(doc)
        if key in self._docs:
            raise DuplicateKeyError("duplicate key")
        self._docs[key] = dict(doc)


class _FakeDB:
    def __init__(self):
        self.usage_counters = _FakeCollection()


@pytest.fixture(autouse=True)
def fake_db():
    db = _FakeDB()
    entitlement_guard.set_database(db)
    yield db
    entitlement_guard.set_database(None)


def _user(tier="starter", status="active"):
    return {
        "_id": ObjectId(),
        "subscription_tier": tier,
        "subscription_status": status,
    }


# ── resolve_entitlements / module() ─────────────────────────────────────────


def test_free_tier_denies_tools():
    ent = resolve_entitlements(None)
    assert ent.tier == "free"
    assert ent.module("tools").enabled is False


def test_pro_tier_unlocks_tools_unlimited():
    ent = resolve_entitlements(_user("pro"))
    access = ent.module("tools")
    assert access.enabled is True
    assert access.quota is None


# ── require_module dependency ───────────────────────────────────────────────


async def _call_dep(dep, user):
    return await dep(request=None, user=user)


@pytest.mark.asyncio
async def test_require_module_denies_disabled_module():
    dep = entitlement_guard.require_module("tools")
    with pytest.raises(HTTPException) as exc:
        await _call_dep(dep, None)
    assert exc.value.status_code == 403
    assert exc.value.detail["error"] == "upgrade_required"


@pytest.mark.asyncio
async def test_require_module_requires_login_for_quota_capped_module():
    dep = entitlement_guard.require_module("stats")
    with pytest.raises(HTTPException) as exc:
        await _call_dep(dep, None)
    assert exc.value.status_code == 401
    assert exc.value.detail["error"] == "login_required"


@pytest.mark.asyncio
async def test_require_module_allows_within_quota_then_blocks():
    dep = entitlement_guard.require_module("stats")
    user = _user("starter")  # stats capped at 5/day for starter
    for _ in range(5):
        await _call_dep(dep, user)
    with pytest.raises(HTTPException) as exc:
        await _call_dep(dep, user)
    assert exc.value.status_code == 429
    assert exc.value.detail["error"] == "quota_exceeded"


@pytest.mark.asyncio
async def test_require_module_unlimited_module_never_blocks():
    dep = entitlement_guard.require_module("production")
    user = _user("pro")  # production unlimited for pro
    for _ in range(50):
        await _call_dep(dep, user)


# ── check_and_increment_usage atomicity ─────────────────────────────────────


@pytest.mark.asyncio
async def test_check_and_increment_usage_respects_quota():
    user = _user("free")
    access = ModuleAccess(enabled=True, quota=2, quota_period="day")
    assert await entitlement_guard.check_and_increment_usage(user, "roo", access) is True
    assert await entitlement_guard.check_and_increment_usage(user, "roo", access) is True
    assert await entitlement_guard.check_and_increment_usage(user, "roo", access) is False


@pytest.mark.asyncio
async def test_check_and_increment_usage_unlimited_skips_db():
    user = _user("business")
    access = ModuleAccess(enabled=True, quota=None, quota_period=None)
    assert await entitlement_guard.check_and_increment_usage(user, "production", access) is True
