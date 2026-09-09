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
    # Pas de Redis → on exerce le fallback mémoire. Disque désactivé ici : ces
    # tests couvrent le tier mémoire ; le tier disque a sa propre suite plus
    # bas (écriture sur disque réel interdite pendant les tests unitaires).
    monkeypatch.setattr(cache_service, "get_redis_client", lambda: None)
    monkeypatch.setattr(cache_service, "CACHE_ENABLED", True)
    monkeypatch.setattr(cache_service, "_DISK_CACHE_ENABLED", False)
    cache_service._MEMORY_STORE.clear()
    # Horloge contrôlable.
    clock = {"t": 1000.0}
    monkeypatch.setattr(cache_service, "_now", lambda: clock["t"])
    yield clock
    cache_service._MEMORY_STORE.clear()


class TestDiskCacheTier:
    """
    Tier disque persistant : sert de repli quand Redis est absent, pour que
    les redémarrages de conteneur (fréquents en dev/sandbox, ou lors d'une
    panne Redis en production) n'obligent pas à tout réinterroger l'OEC.
    Écrit dans un répertoire temporaire isolé (jamais le vrai cache du dépôt).
    """

    @pytest.fixture(autouse=True)
    def isolated_disk_dir(self, tmp_path, monkeypatch):
        monkeypatch.setattr(cache_service, "_DISK_CACHE_DIR", tmp_path)
        monkeypatch.setattr(cache_service, "_DISK_CACHE_ENABLED", True)
        yield tmp_path

    def test_disk_set_then_get(self):
        assert cache_service._disk_set("k1", {"v": 1}, ttl_seconds=600) is True
        assert cache_service._disk_get("k1") == {"v": 1}

    def test_disk_survives_empty_memory_store(self, no_redis_and_fake_clock):
        # Simulates a process restart: value written, then the in-memory
        # store (the only thing wiped on restart) is cleared — disk must
        # still serve it via the public cache_get() cold-start path.
        cache_service.cache_set("k2", {"trade": 99}, "oec_data")
        cache_service._MEMORY_STORE.clear()
        assert cache_service.cache_get("k2") == {"trade": 99}

    def test_disk_expires_after_ttl(self, no_redis_and_fake_clock):
        clock = no_redis_and_fake_clock
        cache_service._disk_set("k3", "data", ttl_seconds=600)
        clock["t"] += 601
        assert cache_service._disk_get("k3") is None
        assert cache_service._disk_get("k3", allow_stale=True) == "data"

    def test_disk_get_missing_key_returns_none(self):
        assert cache_service._disk_get("never-written") is None

    def test_disk_write_failure_degrades_gracefully(self, tmp_path, monkeypatch):
        # Point the cache dir at a path that is a FILE, not a directory:
        # mkdir() raises OSError, exactly like a permissions error or a full
        # disk would — must degrade silently, never raise.
        blocked = tmp_path / "not_a_directory"
        blocked.write_text("occupied")
        monkeypatch.setattr(cache_service, "_DISK_CACHE_DIR", blocked)
        assert cache_service._disk_set("k4", "x", ttl_seconds=600) is False
        # The public cache_set() must still succeed overall via the memory tier.
        assert cache_service.cache_set("k5", "y", "default") is True

    def test_cache_stats_reports_fallback_not_unavailable(self):
        stats = cache_service.cache_stats()
        assert stats["status"] == "fallback (memory + disk)"
        assert "disk_keys_count" in stats


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


def test_delete_works_in_memory():
    cache_service.cache_set("delme", 1, "default")
    assert cache_service.cache_get("delme") == 1
    assert cache_service.cache_delete("delme") is True
    assert cache_service.cache_get("delme") is None
    # Suppression d'une clé absente → False.
    assert cache_service.cache_delete("delme") is False


def test_delete_pattern_in_memory():
    cache_service.cache_set("zlecaf:oec_request:a", 1, "default")
    cache_service.cache_set("zlecaf:oec_request:b", 2, "default")
    cache_service.cache_set("zlecaf:other:c", 3, "default")
    removed = cache_service.cache_delete_pattern("oec_request:*")
    assert removed == 2
    assert cache_service.cache_get("zlecaf:other:c") == 3


def test_oec_data_ttl_is_long():
    # Le TTL oec_data doit exister et être long (réduit le trafic OEC).
    assert cache_service.CACHE_TTL.get("oec_data", 0) >= 3600
