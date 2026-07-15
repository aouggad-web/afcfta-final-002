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
