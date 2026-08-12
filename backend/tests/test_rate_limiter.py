"""
Tests du middleware de limitation de débit.

Le défaut historique : la liste d'exemptions contenait "/api/" et la
comparaison se faisait par préfixe, si bien que **toutes** les routes (toutes
montées sous /api) étaient exemptées et le middleware ne limitait rien. Les
tests ci-dessous verrouillent le comportement corrigé, en particulier :
  - une route ordinaire est bien limitée ;
  - les webhooks de paiement ne le sont jamais (perdre un événement = perdre
    un paiement) ;
  - la connexion a un quota nettement plus serré que le reste.
"""

import sys
from pathlib import Path

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

backend_path = Path(__file__).parent.parent
if str(backend_path) not in sys.path:
    sys.path.insert(0, str(backend_path))

from middlewares.rate_limiter import RateLimitMiddleware  # noqa: E402


def _make_app(**kwargs) -> TestClient:
    app = FastAPI()
    app.add_middleware(RateLimitMiddleware, **kwargs)

    @app.get("/api/countries")
    async def countries():
        return {"ok": True}

    @app.get("/api/health")
    async def health():
        return {"ok": True}

    @app.post("/api/billing/webhook")
    async def webhook():
        return {"ok": True}

    @app.post("/api/auth/login")
    async def login():
        return {"ok": True}

    @app.get("/api/auth/me")
    async def me():
        return {"ok": True}

    return TestClient(app)


def test_ordinary_route_is_actually_limited():
    """Non-régression du défaut : une route sous /api DOIT être limitée."""
    client = _make_app(requests_per_minute=3, burst_limit=100)
    codes = [client.get("/api/countries").status_code for _ in range(5)]
    assert codes[:3] == [200, 200, 200]
    assert 429 in codes, "le middleware n'a rien limité — l'exemption /api/ est revenue"


def test_health_endpoint_stays_exempt():
    client = _make_app(requests_per_minute=2, burst_limit=100)
    codes = [client.get("/api/health").status_code for _ in range(6)]
    assert set(codes) == {200}


def test_payment_webhook_is_never_limited():
    """Un 429 sur un webhook ferait perdre un événement de paiement."""
    client = _make_app(requests_per_minute=2, burst_limit=100)
    codes = [client.post("/api/billing/webhook").status_code for _ in range(10)]
    assert set(codes) == {200}


def test_login_has_tighter_quota_than_regular_routes():
    client = _make_app(requests_per_minute=50, auth_requests_per_minute=3, burst_limit=100)
    login_codes = [client.post("/api/auth/login").status_code for _ in range(5)]
    assert 429 in login_codes, "la connexion doit être plafonnée plus tôt"
    # Une route ordinaire garde son quota généreux malgré les 429 sur /login.
    assert client.get("/api/countries").status_code == 200


def test_session_check_keeps_the_general_quota():
    """/auth/me est appelé à chaque chargement de page : il ne doit pas tomber
    sous le quota serré de la connexion."""
    client = _make_app(requests_per_minute=50, auth_requests_per_minute=2, burst_limit=100)
    codes = [client.get("/api/auth/me").status_code for _ in range(6)]
    assert set(codes) == {200}


def test_burst_limit_triggers():
    client = _make_app(requests_per_minute=1000, burst_limit=3)
    codes = [client.get("/api/countries").status_code for _ in range(6)]
    assert 429 in codes


def test_kill_switch_disables_everything(monkeypatch):
    monkeypatch.setenv("RATE_LIMIT_ENABLED", "false")
    client = _make_app(requests_per_minute=1, burst_limit=1)
    codes = [client.get("/api/countries").status_code for _ in range(5)]
    assert set(codes) == {200}


def test_limits_read_from_environment(monkeypatch):
    monkeypatch.setenv("RATE_LIMIT_ENABLED", "true")
    monkeypatch.setenv("RATE_LIMIT_PER_MINUTE", "2")
    monkeypatch.setenv("RATE_LIMIT_BURST", "99")
    client = _make_app()
    codes = [client.get("/api/countries").status_code for _ in range(4)]
    assert 429 in codes


def test_invalid_env_falls_back_to_default(monkeypatch):
    monkeypatch.setenv("RATE_LIMIT_PER_MINUTE", "beaucoup")
    app = FastAPI()
    middleware = RateLimitMiddleware(app)
    assert middleware.requests_per_minute == 120


@pytest.mark.parametrize("path", ["/api/", "/api/docs", "/api/openapi.json"])
def test_exempt_paths_match_exactly_not_by_prefix(path):
    """`/api/` reste exempt en tant que chemin exact, sans exempter ses enfants."""
    middleware = RateLimitMiddleware(FastAPI())
    assert path in middleware.exempt_paths
    assert "/api/countries" not in middleware.exempt_paths
