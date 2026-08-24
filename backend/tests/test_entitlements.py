"""
Tests de la couche entitlements (`entitlements.py` + `entitlement_guard.py`) :
résolution du tier effectif, gating par module, compteur de quota atomique,
et application de bout en bout sur de vraies routes FastAPI avec session JWT.

Hermétiques : la "base Mongo" est un double en mémoire qui reproduit juste
assez de la sémantique motor (`find_one`, `find_one_and_update`, `insert_one`)
pour exercer `check_and_increment_usage` sans dépendance réseau.
"""

import asyncio
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest
from bson import ObjectId
from fastapi import Depends, FastAPI, HTTPException
from fastapi.testclient import TestClient
from pymongo.errors import DuplicateKeyError

backend_path = Path(__file__).parent.parent
if str(backend_path) not in sys.path:
    sys.path.insert(0, str(backend_path))

import entitlement_guard  # noqa: E402
from entitlements import MODULES, TIERS, ModuleAccess, resolve_entitlements  # noqa: E402
from services.user_auth_service import create_access_token  # noqa: E402


class _FakeCollection:
    """Assez de sémantique Mongo pour exercer check_and_increment_usage:
    find_one, find_one_and_update (avec $inc et un filtre $lt), insert_one
    (avec DuplicateKeyError sur la clé composite déjà prise)."""

    def __init__(self, *, yield_before_return=False):
        self._docs = {}
        # Force un point de cession (await asyncio.sleep(0)) avant de rendre
        # la main, pour que deux appels concurrents (asyncio.gather) puissent
        # réellement s'entrelacer sur une boucle mono-thread — sans ça,
        # aucune des deux coroutines ne cède le contrôle et la "concurrence"
        # ne serait qu'un enchaînement séquentiel déguisé.
        self._yield_before_return = yield_before_return

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
        if self._yield_before_return:
            await asyncio.sleep(0)
        for doc in self._docs.values():
            if self._match(doc, filt):
                return dict(doc)
        return None

    async def find_one_and_update(self, filt, update, return_document=None):
        if self._yield_before_return:
            await asyncio.sleep(0)
        for key, doc in self._docs.items():
            if self._match(doc, filt):
                if "$inc" in update:
                    for field, amount in update["$inc"].items():
                        doc[field] = doc.get(field, 0) + amount
                return dict(doc)
        return None

    async def insert_one(self, doc):
        if self._yield_before_return:
            await asyncio.sleep(0)
        key = self._key(doc)
        if key in self._docs:
            raise DuplicateKeyError("duplicate key")
        self._docs[key] = dict(doc)


class _UsersCollection:
    """Juste assez pour `get_optional_subscriber`: find_one par `_id`."""

    def __init__(self, users=None):
        self._users = {u["_id"]: u for u in (users or [])}

    async def find_one(self, filt):
        return self._users.get(filt.get("_id"))


class _FakeDB:
    def __init__(self, users=None, *, yield_before_return=False):
        self.usage_counters = _FakeCollection(yield_before_return=yield_before_return)
        self.users = _UsersCollection(users)


@pytest.fixture(autouse=True)
def fake_db():
    db = _FakeDB()
    entitlement_guard.set_database(db)
    yield db
    entitlement_guard.set_database(None)


def _user(tier="starter", status="active", subscription_current_end=None):
    doc = {
        "_id": ObjectId(),
        "subscription_tier": tier,
        "subscription_status": status,
    }
    if subscription_current_end is not None:
        doc["subscription_current_end"] = subscription_current_end
    return doc


# ── resolve_entitlements : résolution du tier effectif ──────────────────────


def test_no_user_grants_free_tier():
    ent = resolve_entitlements(None)

    assert ent.tier == "free"
    assert ent.daily_calculations == 10
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
    assert ent.daily_calculations == 100


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


@pytest.mark.parametrize(
    "days_from_period_end, expected_tier",
    [(-1, "pro"), (1, "free")],
)
def test_naive_now_is_treated_as_utc_without_raising(days_from_period_end, expected_tier):
    """A caller-supplied `now` can be naive (e.g. datetime.now() without a
    tz) while subscription_current_end is always normalized to UTC-aware —
    comparing the two directly would raise TypeError, breaking the "never
    raises" guarantee."""
    period_end = datetime(2026, 8, 15, tzinfo=timezone.utc)
    naive_now = (period_end + timedelta(days=days_from_period_end)).replace(tzinfo=None)
    user = {
        "subscription_tier": "pro",
        "subscription_status": "active",
        "subscription_current_end": period_end,
    }

    assert resolve_entitlements(user, now=naive_now).tier == expected_tier


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


# ── Module entitlements ──────────────────────────────────────────────────────


def test_every_tier_declares_every_module():
    for tier in TIERS:
        ent = resolve_entitlements({"subscription_tier": tier, "subscription_status": "active"})
        assert set(ent.modules) == set(MODULES)


def test_free_tier_module_caps_and_denials():
    ent = resolve_entitlements(None)

    stats = ent.module("stats")
    assert stats.enabled is True
    assert stats.quota == 20
    assert stats.quota_period == "month"

    assert ent.module("tools").enabled is False
    assert ent.module("roo").quota == 60
    assert ent.module("roo").quota_period == "day"


def test_pro_tier_mixes_unlimited_and_capped_modules():
    ent = resolve_entitlements({"subscription_tier": "pro", "subscription_status": "active"})

    production = ent.module("production")
    assert production.enabled is True
    assert production.quota is None  # unlimited
    assert production.quota_period is None

    logistics = ent.module("logistics")
    assert logistics.quota == 300
    assert logistics.quota_period == "day"


def test_business_tier_unlimited_modules_and_capped_reports():
    ent = resolve_entitlements({"subscription_tier": "business", "subscription_status": "active"})

    for module_id in ("production", "logistics", "roo", "tools"):
        assert ent.module(module_id).enabled is True
        assert ent.module(module_id).quota is None

    assert ent.module("reports").quota == 200
    assert ent.module("stats").quota == 300


def test_unknown_module_fails_closed_to_denied():
    ent = resolve_entitlements(None)

    denied = ent.module("nonexistent-module")
    assert denied.enabled is False
    assert denied.quota is None


def test_inactive_subscription_falls_back_to_free_module_set():
    """A lapsed business subscriber must lose the business module grants and
    get the free tier's caps (e.g. tools denied) rather than keep them."""
    user = {"subscription_tier": "business", "subscription_status": "canceled"}

    ent = resolve_entitlements(user)
    assert ent.tier == "free"
    assert ent.module("tools").enabled is False


def test_entitlements_modules_mapping_is_immutable():
    """`Entitlements.__post_init__` freezes `modules` into a MappingProxyType
    specifically so mutating one caller's view can't corrupt the shared
    singleton returned to every other caller of the same tier."""
    ent = resolve_entitlements({"subscription_tier": "pro", "subscription_status": "active"})

    with pytest.raises(TypeError):
        ent.modules["tools"] = ModuleAccess(enabled=False)

    # Same singleton instance is handed out to every caller of that tier —
    # confirms there is exactly one shared object to corrupt in the first
    # place, not a defensive copy per call.
    ent_again = resolve_entitlements({"subscription_tier": "pro", "subscription_status": "active"})
    assert ent.modules is ent_again.modules


def test_entitlements_dataclass_itself_is_frozen():
    ent = resolve_entitlements(None)
    with pytest.raises(Exception):
        ent.tier = "business"


# ── require_module dependency (in-process, no HTTP) ─────────────────────────


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
async def test_require_module_allows_anonymous_without_metering():
    # No identity to meter usage against — an anonymous caller keeps the
    # module's prior (unmetered) public access rather than being newly
    # blocked, as long as the module is enabled for the free tier.
    dep = entitlement_guard.require_module("stats")
    for _ in range(10):
        await _call_dep(dep, None)


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


# ── require_module_enabled : on/off switch only, never metered ───────────────


@pytest.mark.asyncio
async def test_require_module_enabled_denies_disabled_module():
    # The tier on/off switch is still enforced: a module a tier doesn't grant
    # (tools on free) is refused with the same 403 as the metered variant.
    dep = entitlement_guard.require_module_enabled("tools")
    with pytest.raises(HTTPException) as exc:
        await _call_dep(dep, None)
    assert exc.value.status_code == 403
    assert exc.value.detail["error"] == "upgrade_required"


@pytest.mark.asyncio
async def test_require_module_enabled_never_meters_capped_module():
    # A single logistics screen fans out to many GETs; enablement-only gating
    # must let a signed-in free user (logistics capped at 5/day for the metered
    # variant) load it any number of times without being blocked.
    dep = entitlement_guard.require_module_enabled("logistics")
    user = _user("free")
    for _ in range(50):
        await _call_dep(dep, user)


@pytest.mark.asyncio
async def test_require_module_enabled_allows_anonymous():
    dep = entitlement_guard.require_module_enabled("stats")
    for _ in range(50):
        await _call_dep(dep, None)


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


@pytest.mark.asyncio
async def test_check_and_increment_usage_raises_503_when_db_unset():
    """A missing database is an operational outage, not a subscriber hitting
    their cap — must surface as 503, never get silently folded into a 429
    "quota_exceeded" that would mislead debugging."""
    entitlement_guard.set_database(None)
    user = _user("free")
    access = ModuleAccess(enabled=True, quota=2, quota_period="day")

    with pytest.raises(HTTPException) as exc:
        await entitlement_guard.check_and_increment_usage(user, "roo", access)
    assert exc.value.status_code == 503
    assert exc.value.detail["error"] == "entitlements_unavailable"


@pytest.mark.asyncio
async def test_check_and_increment_usage_concurrent_first_call_only_one_wins():
    """Two requests racing to create the SAME period's counter for the first
    time (quota=1) must not both succeed: the unique index on
    (user_id, counter_id, period_key) is what makes `insert_one` the atomic
    tie-breaker. A yield point is forced into the fake collection so the two
    coroutines actually interleave on asyncio.gather instead of just running
    sequentially — otherwise this test would pass even with a non-atomic
    check-then-insert implementation and prove nothing."""
    db = _FakeDB(yield_before_return=True)
    entitlement_guard.set_database(db)
    try:
        user = _user("free")
        access = ModuleAccess(enabled=True, quota=1, quota_period="day")

        results = await asyncio.gather(
            entitlement_guard.check_and_increment_usage(user, "roo", access),
            entitlement_guard.check_and_increment_usage(user, "roo", access),
        )

        assert sorted(results) == [False, True]
    finally:
        entitlement_guard.set_database(None)


@pytest.mark.asyncio
async def test_check_and_increment_usage_first_call_race_retries_when_quota_allows_it():
    """Same first-of-the-period race as above, but with quota=5: the losing
    request has plenty of allowance left and must NOT be denied just because
    its own find_one_and_update ran before the counter document existed —
    it should retry the conditional increment against the now-real
    document and succeed, landing both requests within quota."""
    db = _FakeDB(yield_before_return=True)
    entitlement_guard.set_database(db)
    try:
        user = _user("free")
        access = ModuleAccess(enabled=True, quota=5, quota_period="day")

        results = await asyncio.gather(
            entitlement_guard.check_and_increment_usage(user, "roo", access),
            entitlement_guard.check_and_increment_usage(user, "roo", access),
        )

        assert results == [True, True]
        doc = await db.usage_counters.find_one({"user_id": user["_id"], "counter_id": "roo"})
        assert doc["count"] == 2
    finally:
        entitlement_guard.set_database(None)


# ── Bout en bout : vraie route FastAPI + session JWT ─────────────────────────


def _build_app(module_id: str):
    app = FastAPI()

    @app.get("/probe")
    async def probe(ent=Depends(entitlement_guard.require_module(module_id))):
        return {"tier": ent.tier}

    return app


def _client_with_session(app: FastAPI, user_id: str) -> TestClient:
    token = create_access_token(user_id, "subscriber@example.com")
    client = TestClient(app)
    client.cookies.set("access_token", token)
    return client


@pytest.mark.asyncio
async def test_route_grants_access_for_paying_subscriber_jwt(fake_db, monkeypatch):
    monkeypatch.setenv("JWT_SECRET", "test-secret")
    user = _user("pro")
    fake_db.users = _UsersCollection([user])

    app = _build_app("tools")  # denied on free, unlimited on pro
    client = _client_with_session(app, str(user["_id"]))

    resp = client.get("/probe")
    assert resp.status_code == 200
    assert resp.json()["tier"] == "pro"


@pytest.mark.asyncio
async def test_route_denies_free_tier_subscriber_jwt(fake_db, monkeypatch):
    monkeypatch.setenv("JWT_SECRET", "test-secret")
    user = _user("free")
    fake_db.users = _UsersCollection([user])

    app = _build_app("tools")
    client = _client_with_session(app, str(user["_id"]))

    resp = client.get("/probe")
    assert resp.status_code == 403
    assert resp.json()["detail"]["error"] == "upgrade_required"


@pytest.mark.asyncio
async def test_route_meters_quota_for_logged_in_user_then_429(fake_db, monkeypatch):
    monkeypatch.setenv("JWT_SECRET", "test-secret")
    user = _user("starter")  # stats capped at 5/day for starter
    fake_db.users = _UsersCollection([user])

    app = _build_app("stats")
    client = _client_with_session(app, str(user["_id"]))

    for _ in range(5):
        assert client.get("/probe").status_code == 200
    resp = client.get("/probe")
    assert resp.status_code == 429
    assert resp.json()["detail"]["error"] == "quota_exceeded"


@pytest.mark.asyncio
async def test_route_expired_subscription_falls_back_to_free_and_is_denied(fake_db, monkeypatch):
    """A Business subscriber whose paid period has lapsed (webhook missed or
    delayed) must be denied a module Business unlocks but Free doesn't, when
    hitting a real route through the JWT session — not just at the
    resolve_entitlements() unit level."""
    monkeypatch.setenv("JWT_SECRET", "test-secret")
    now = datetime.now(timezone.utc)
    user = _user(
        "business",
        status="active",
        subscription_current_end=now - timedelta(days=1),
    )
    fake_db.users = _UsersCollection([user])

    app = _build_app("tools")  # business unlocks it unlimited; free denies it
    client = _client_with_session(app, str(user["_id"]))

    resp = client.get("/probe")
    assert resp.status_code == 403
    assert resp.json()["detail"]["tier"] == "free"


@pytest.mark.asyncio
async def test_route_business_tier_tools_access_is_unmetered(fake_db, monkeypatch):
    """Business unlocks "tools" (the module tariff_data_router/API downloads
    are gated on) with no quota — proves the enforcement holds over many
    real requests, not just a single resolve_entitlements() call."""
    monkeypatch.setenv("JWT_SECRET", "test-secret")
    user = _user("business")
    fake_db.users = _UsersCollection([user])

    app = _build_app("tools")
    client = _client_with_session(app, str(user["_id"]))

    for _ in range(25):
        assert client.get("/probe").status_code == 200


# ── require_api_access : Entitlements.api_access / api_monthly_quota ────────


def _build_api_app():
    app = FastAPI()

    @app.get("/api-probe")
    async def api_probe(ent=Depends(entitlement_guard.require_api_access())):
        return {"tier": ent.tier}

    return app


@pytest.mark.asyncio
async def test_api_access_denied_below_business(fake_db, monkeypatch):
    monkeypatch.setenv("JWT_SECRET", "test-secret")
    user = _user("pro")  # api_access is False below business
    fake_db.users = _UsersCollection([user])

    app = _build_api_app()
    client = _client_with_session(app, str(user["_id"]))

    resp = client.get("/api-probe")
    assert resp.status_code == 403
    assert resp.json()["detail"]["module"] == "api"


@pytest.mark.asyncio
async def test_api_access_anonymous_keeps_prior_unmetered_access(fake_db):
    # No JWT session at all — same "keep prior behavior" fallback as
    # require_module, so an existing API-key-only integration isn't newly
    # locked out of api_v2 by this provisional wiring.
    dep = entitlement_guard.require_api_access()
    for _ in range(5):
        await dep(request=None, user=None)


@pytest.mark.asyncio
async def test_api_access_business_meters_monthly_quota_then_429(fake_db, monkeypatch):
    monkeypatch.setenv("JWT_SECRET", "test-secret")
    user = _user("business")  # api_monthly_quota == 1000
    fake_db.users = _UsersCollection([user])
    entitlement_guard.set_database(_FakeDB(users=[user]))

    dep = entitlement_guard.require_api_access()
    ent = resolve_entitlements(user)
    assert ent.api_monthly_quota == 1000

    for _ in range(1000):
        await dep(request=None, user=user)
    with pytest.raises(HTTPException) as exc:
        await dep(request=None, user=user)
    assert exc.value.status_code == 429
    assert exc.value.detail["error"] == "quota_exceeded"
