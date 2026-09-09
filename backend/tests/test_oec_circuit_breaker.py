"""
Tests du disjoncteur (circuit breaker) de OECTradeService._make_request.

Objectif : après plusieurs échecs consécutifs, arrêter de retenter le réseau
pendant une fenêtre de cooldown et servir directement le repli (cache périmé
ou message d'erreur) — réduit le trafic OEC et l'exposition à ses pannes/
limitations de débit (observées en pratique : blocages 403 côté egress).

httpx est mocké : aucun appel réseau réel.
"""

import asyncio

import httpx
import pytest
from services import cache_service
from services.oec_trade_service import (
    _CIRCUIT_COOLDOWN_SECONDS,
    _CIRCUIT_FAILURE_THRESHOLD,
    OECTradeService,
)


def run(coro):
    return asyncio.run(coro)


@pytest.fixture(autouse=True)
def isolated_cache(monkeypatch):
    monkeypatch.setattr(cache_service, "get_redis_client", lambda: None)
    monkeypatch.setattr(cache_service, "_DISK_CACHE_ENABLED", False)
    cache_service._MEMORY_STORE.clear()
    yield
    cache_service._MEMORY_STORE.clear()


class _FakeResponse:
    def __init__(self, payload):
        self._payload = payload

    def raise_for_status(self):
        pass

    def json(self):
        return self._payload


def _patch_client(monkeypatch, behaviors):
    """``behaviors``: list of callables, each returning a response or raising.
    Consumed in order; the last one repeats once exhausted."""
    calls = {"n": 0}

    class _FakeAsyncClient:
        def __init__(self, *a, **k):
            pass

        async def __aenter__(self):
            return self

        async def __aexit__(self, *a):
            return False

        async def get(self, *a, **k):
            idx = min(calls["n"], len(behaviors) - 1)
            calls["n"] += 1
            behavior = behaviors[idx]
            return behavior()

    monkeypatch.setattr(httpx, "AsyncClient", _FakeAsyncClient)
    return calls


def _ok(payload):
    return lambda: _FakeResponse(payload)


def _fail():
    def _raise():
        raise httpx.ConnectError("network down")

    return _raise


def test_circuit_opens_after_consecutive_failures_and_skips_network(monkeypatch):
    svc = OECTradeService()
    calls = _patch_client(monkeypatch, [_fail() for _ in range(10)])

    for _ in range(_CIRCUIT_FAILURE_THRESHOLD):
        result = run(svc._make_request({"cube": "hs17"}))
        assert "error" in result

    assert svc._circuit_consecutive_failures >= _CIRCUIT_FAILURE_THRESHOLD
    calls_before = calls["n"]

    # Circuit now open: the next call must NOT touch the network.
    result = run(svc._make_request({"cube": "hs17"}))
    assert calls["n"] == calls_before  # no new network attempt
    assert "circuit ouvert" in result["error"]


def test_circuit_serves_stale_cache_when_open(monkeypatch):
    svc = OECTradeService()
    # First call succeeds and populates the cache.
    _patch_client(monkeypatch, [_ok({"data": [{"v": 1}]})])
    good = run(svc._make_request({"cube": "hs17", "cut": "A"}))
    assert good == {"data": [{"v": 1}]}

    # Force the TTL to have elapsed so the normal cache read misses, then
    # drive the circuit open with failures on a DIFFERENT param set.
    monkeypatch.setattr(cache_service, "_now", lambda: cache_service.time.time() + 999_999)
    _patch_client(monkeypatch, [_fail() for _ in range(10)])
    for _ in range(_CIRCUIT_FAILURE_THRESHOLD):
        run(svc._make_request({"cube": "hs17", "cut": "A"}))

    # Circuit open now: stale cache (same params) must still be served.
    result = run(svc._make_request({"cube": "hs17", "cut": "A"}))
    assert result == {"data": [{"v": 1}]}


def test_circuit_resets_on_success(monkeypatch):
    svc = OECTradeService()
    _patch_client(monkeypatch, [_fail(), _fail(), _ok({"data": []})])

    run(svc._make_request({"cube": "hs17", "cut": "B"}))
    run(svc._make_request({"cube": "hs17", "cut": "C"}))
    run(svc._make_request({"cube": "hs17", "cut": "D"}))  # succeeds -> resets

    assert svc._circuit_consecutive_failures == 0
    assert (
        svc._circuit_open_until == 0.0 or svc._circuit_open_until < __import__("time").monotonic()
    )


def test_circuit_cooldown_constant_is_reasonable():
    # Sanity: the cooldown must be short enough not to make a healthy API
    # look "down" for too long once it recovers.
    assert 5 <= _CIRCUIT_COOLDOWN_SECONDS <= 300
    assert _CIRCUIT_FAILURE_THRESHOLD >= 2
