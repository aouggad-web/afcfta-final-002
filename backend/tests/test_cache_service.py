"""
Tests du cache en mémoire (fallback sans Redis) et du stale-on-error.

Ces tests forcent l'absence de Redis (get_redis_client → None) et pilotent
l'horloge via cache_service._now pour valider l'expiration TTL et le
service de valeurs périmées (stale) en cas de panne upstream.
"""

import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from services import cache_service


@pytest.fixture(autouse=True)
def no_redis_and_fake_clock(monkeypatch):
    # Pas de Redis → on exerce le fallback mémoire.
    monkeypatch.setattr(cache_service, "get_redis_client", lambda: None)
    monkeypatch.setattr(cache_service, "CACHE_ENABLED", True)
    cache_service._MEMORY_STORE.clear()
    # Horloge contrôlable.
    clock = {"t": 1000.0}
    monkeypatch.setattr(cache_service, "_now", lambda: clock["t"])
    yield clock
    cache_service._MEMORY_STORE.clear()


def test_set_then_get_in_memory():
    assert cache_service.cache_set("k1", {"v": 1}, "statistics") is True
    assert cache_service.cache_get("k1") == {"v": 1}


def test_value_expires_after_ttl(no_redis_and_fake_clock):
    clock = no_redis_and_fake_clock
    cache_service.cache_set("k2", "data", "default")  # default TTL = 600s
    clock["t"] += 599
    assert cache_service.cache_get("k2") == "data"  # encore valide
    clock["t"] += 2  # 601s écoulées → expiré
    assert cache_service.cache_get("k2") is None


def test_stale_on_error_returns_expired_value(no_redis_and_fake_clock):
    clock = no_redis_and_fake_clock
    cache_service.cache_set("k3", {"trade": 42}, "default")
    clock["t"] += 10_000  # bien au-delà du TTL
    # Lecture normale : rien (expiré).
    assert cache_service.cache_get("k3") is None
    # Lecture stale : la dernière valeur connue est servie.
    assert cache_service.cache_get_stale("k3") == {"trade": 42}


def test_stale_returns_none_when_never_cached():
    assert cache_service.cache_get_stale("never") is None


def test_disabled_cache_is_noop(monkeypatch):
    monkeypatch.setattr(cache_service, "CACHE_ENABLED", False)
    assert cache_service.cache_set("k4", 1, "default") is False
    assert cache_service.cache_get("k4") is None


def test_capacity_guard_evicts(monkeypatch):
    # Réduit la capacité pour vérifier l'éviction.
    monkeypatch.setattr(cache_service, "_MEMORY_MAX_ENTRIES", 5)
    for i in range(10):
        cache_service.cache_set(f"key{i}", i, "default")
    assert len(cache_service._MEMORY_STORE) <= 5
