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
    "https_enabled, expected_samesite, expects_secure",
    [
        # HTTPS deployments (incl. the Emergent preview iframe, a cross-site
        # top-level document): SameSite=None so the cookie still comes back
        # on our own fetches, which requires Secure.
        ("true", "samesite=none", True),
        # Plain HTTP (local dev): SameSite=None without Secure would be
        # rejected by browsers, so fall back to Lax (still same-origin-safe).
        ("false", "samesite=lax", False),
    ],
)
def test_csrf_cookie_samesite_matches_https_flag(
    monkeypatch, https_enabled, expected_samesite, expects_secure
):
    monkeypatch.setenv("HTTPS_ENABLED", https_enabled)
    import backend.middlewares.csrf_protection as csrf_protection_module

    importlib.reload(csrf_protection_module)
    try:
        app = FastAPI()
        app.add_middleware(
            csrf_protection_module.CSRFMiddleware, exempt_paths=["/api/health"]
        )

        @app.get("/api/health")
        async def health():
            return {"status": "ok"}

        response = TestClient(app).get("/api/health")

        set_cookie = response.headers.get("set-cookie")
        assert set_cookie is not None
        assert expected_samesite in set_cookie.lower()
        assert ("secure" in set_cookie.lower()) == expects_secure
    finally:
        # Restore the module to its default (HTTPS_ENABLED unset) state so a
        # leftover reload doesn't leak into tests running after this one —
        # monkeypatch undoes the env var, but not an already-reloaded module.
        monkeypatch.delenv("HTTPS_ENABLED", raising=False)
        importlib.reload(csrf_protection_module)
