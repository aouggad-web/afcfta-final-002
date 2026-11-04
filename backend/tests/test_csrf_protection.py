import importlib

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from backend.middlewares.csrf_protection import (
    CSRF_COOKIE,
    CSRF_HEADER,
    CSRFMiddleware,
)


@pytest.fixture
def client():
    app = FastAPI()
    app.add_middleware(
        CSRFMiddleware,
        exempt_paths=["/api/health", "/api/"],
    )

    @app.get("/api/health")
    async def health():
        return {"status": "ok"}

    @app.post("/api/")
    async def exempt_mutation():
        return {"status": "exempt"}

    @app.api_route(
        "/api/resource",
        methods=["POST", "PUT", "PATCH", "DELETE"],
    )
    async def mutate_resource():
        return {"status": "updated"}

    return TestClient(app)


def test_safe_request_issues_matching_cookie_and_header(client):
    response = client.get("/api/health")

    assert response.status_code == 200
    assert response.headers[CSRF_HEADER] == client.cookies[CSRF_COOKIE]


@pytest.mark.parametrize("method", ["POST", "PUT", "PATCH", "DELETE"])
def test_all_mutating_methods_require_csrf_token(client, method):
    response = client.request(method, "/api/resource")

    assert response.status_code == 403
    assert response.json() == {"detail": "CSRF token missing"}


@pytest.mark.parametrize("method", ["POST", "PUT", "PATCH", "DELETE"])
def test_all_mutating_methods_accept_matching_csrf_token(client, method):
    token = client.get("/api/health").headers[CSRF_HEADER]

    response = client.request(
        method,
        "/api/resource",
        headers={CSRF_HEADER: token},
    )

    assert response.status_code == 200
    assert response.json() == {"status": "updated"}


def test_exempt_path_does_not_exempt_descendants(client):
    response = client.post("/api/resource")

    assert response.status_code == 403


def test_exact_exempt_path_allows_mutation_without_token(client):
    response = client.post("/api/")

    assert response.status_code == 200


@pytest.mark.parametrize(
    "https_enabled, expected_samesite, expects_secure, expects_partitioned",
    [
        # HTTPS deployments (incl. the Emergent preview iframe, a cross-site
        # top-level document): SameSite=None so the cookie still comes back
        # on our own fetches, which requires Secure. Chrome's CHIPS also
        # requires the Partitioned attribute for that cross-site case, or it
        # drops the cookie outright despite SameSite=None; Secure being set.
        ("true", "samesite=none", True, True),
        # Plain HTTP (local dev): SameSite=None without Secure would be
        # rejected by browsers, so fall back to Lax (still same-origin-safe).
        # Partitioned has no meaning without Secure, so it's omitted.
        ("false", "samesite=lax", False, False),
    ],
)
def test_csrf_cookie_samesite_matches_https_flag(
    monkeypatch, https_enabled, expected_samesite, expects_secure, expects_partitioned
):
    monkeypatch.setenv("HTTPS_ENABLED", https_enabled)
    import backend.middlewares.csrf_protection as csrf_protection_module

    importlib.reload(csrf_protection_module)
    try:
        app = FastAPI()
        app.add_middleware(csrf_protection_module.CSRFMiddleware, exempt_paths=["/api/health"])

        @app.get("/api/health")
        async def health():
            return {"status": "ok"}

        response = TestClient(app).get("/api/health")

        set_cookie = response.headers.get("set-cookie")
        assert set_cookie is not None
        assert expected_samesite in set_cookie.lower()
        assert ("secure" in set_cookie.lower()) == expects_secure
        assert ("partitioned" in set_cookie.lower()) == expects_partitioned
    finally:
        # Restore the module to its default (HTTPS_ENABLED unset) state so a
        # leftover reload doesn't leak into tests running after this one —
        # monkeypatch undoes the env var, but not an already-reloaded module.
        monkeypatch.delenv("HTTPS_ENABLED", raising=False)
        importlib.reload(csrf_protection_module)


def _avec_hote(app, hote: bytes):
    """httpx refuse un en-tête Host invalide : on le remplace directement dans
    le scope ASGI, comme le ferait un client HTTP brut."""

    async def asgi(scope, receive, send):
        if scope["type"] == "http":
            entetes = [(k, v) for k, v in scope["headers"] if k != b"host"]
            scope = {**scope, "headers": entetes + [(b"host", hote)]}
        await app(scope, receive, send)

    return asgi


@pytest.mark.parametrize("hote", [b"testserver/api/health?", b"testserver/api/health#"])
def test_host_forge_n_exempte_pas_du_jeton(hote):
    """Audit M3 : Starlette reconstruit request.url à partir de l'en-tête Host,
    alors que le routage suit le vrai chemin. Un Host « testserver/api/health? »
    faisait lire /api/health (exempté) pendant que /api/resource s'exécutait.
    Le middleware lit désormais le chemin routé, scope["path"]."""
    app = FastAPI()
    app.add_middleware(CSRFMiddleware, exempt_paths=["/api/health"])

    @app.post("/api/resource")
    async def mutate_resource():
        return {"status": "updated"}

    response = TestClient(_avec_hote(app, hote)).post("/api/resource")

    assert response.status_code == 403
    assert response.json() == {"detail": "CSRF token missing"}
