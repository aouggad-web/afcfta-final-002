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
    # Le texte de l'exception reste au journal du serveur (constat M9).
    assert r["error"] == "Upstream service error"


# ── Audit D3 (17/11/2026) : diagnostic public mis en cache ──────────────────


def test_diagnostic_oec_public_ne_rappelle_pas_l_oec_dans_la_minute(monkeypatch):
    from fastapi import FastAPI
    from fastapi.testclient import TestClient
    from routes import reports
    from services import oec_trade_service

    appels = []

    async def ping(year):
        appels.append(year)
        return {"reachable": True, "token_configured": False}

    async def importateurs(hs, year):
        appels.append(hs)
        return {"data": [{"x": 1}]}

    monkeypatch.setattr(mod.real_trade_service, "ping_oec", ping)
    monkeypatch.setattr(oec_trade_service.oec_service, "get_top_african_importers", importateurs)
    monkeypatch.setattr(reports, "_diagnostic_oec", {})
    app = FastAPI()
    app.include_router(reports.router_diagnostics, prefix="/api")
    client = TestClient(app)

    premiere = client.get("/api/reports/oec-health").json()
    assert [client.get("/api/reports/oec-health").json() for _ in range(5)] == [premiere] * 5
    assert appels == ["180100", 2022]
    # Une autre année est un autre diagnostic ; une année hors du cube est refusée.
    client.get("/api/reports/oec-health", params={"year": 2023})
    assert len(appels) == 4
    assert client.get("/api/reports/oec-health", params={"year": 1900}).status_code == 422
    assert len(appels) == 4
