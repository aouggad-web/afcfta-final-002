"""
Tests for the OEC connectivity diagnostic (real_trade_service.ping_oec).

httpx is stubbed so the test is hermetic (no network).
"""

import asyncio

from services import real_trade_data_service as mod


def run(coro):
    return asyncio.run(coro)


class _FakeResp:
    def __init__(self, status, data):
        self.status_code = status
        self._data = data

    def json(self):
        return {"data": self._data}


def _fake_client_factory(resp=None, exc=None):
    class _FakeClient:
        def __init__(self, *a, **k):
            pass

        async def __aenter__(self):
            return self

        async def __aexit__(self, *a):
            return False

        async def get(self, *a, **k):
            if exc:
                raise exc
            return resp

    return lambda *a, **k: _FakeClient()


def test_ping_oec_reachable(monkeypatch):
    monkeypatch.setattr(
        mod.httpx, "AsyncClient", _fake_client_factory(resp=_FakeResp(200, [{"x": 1}]))
    )
    r = run(mod.real_trade_service.ping_oec())
    assert r["reachable"] is True
    assert r["status_code"] == 200
    assert r["records"] == 1
    assert r["error"] is None


def test_ping_oec_http_error(monkeypatch):
    monkeypatch.setattr(mod.httpx, "AsyncClient", _fake_client_factory(resp=_FakeResp(403, [])))
    r = run(mod.real_trade_service.ping_oec())
    assert r["reachable"] is False
    assert r["status_code"] == 403
    assert "403" in r["error"]


def test_ping_oec_connection_exception(monkeypatch):
    monkeypatch.setattr(mod.httpx, "AsyncClient", _fake_client_factory(exc=RuntimeError("boom")))
    r = run(mod.real_trade_service.ping_oec())
    assert r["reachable"] is False
    assert r["status_code"] is None
    assert "boom" in r["error"]
