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


@pytest.fixture
def csrf_https(monkeypatch):
    """Le module rechargé avec HTTPS_ENABLED=true, puis remis en mode http."""
    monkeypatch.setenv("HTTPS_ENABLED", "true")
    import backend.middlewares.csrf_protection as module

    importlib.reload(module)
    try:
        app = FastAPI()
        app.add_middleware(module.CSRFMiddleware, exempt_paths=["/api/health"])

        @app.get("/api/health")
        async def health():
            return {"status": "ok"}

        @app.post("/api/resource")
        async def mutate_resource():
            return {"status": "updated"}

        yield module, app
    finally:
        monkeypatch.delenv("HTTPS_ENABLED", raising=False)
        importlib.reload(module)


def test_en_https_le_cookie_porte_le_prefixe_host(csrf_https):
    """Audit INFO-4 : __Host- interdit qu'un sous-domaine ou une réponse http
    impose le jeton ; le navigateur exige alors Secure, Path=/ et pas de Domain."""
    module, app = csrf_https
    assert module.CSRF_COOKIE == "__Host-csrf_token"

    set_cookie = TestClient(app, base_url="https://testserver").get("/api/health").headers[
        "set-cookie"
    ]
    attributs = [a.strip().lower() for a in set_cookie.split(";")]
    assert set_cookie.startswith("__Host-csrf_token=")
    assert {"path=/", "secure", "samesite=none", "partitioned"} <= set(attributs)
    assert not any(a.startswith("domain=") for a in attributs)


def test_en_https_le_double_envoi_fonctionne_avec_le_nouveau_nom(csrf_https):
    _, app = csrf_https
    client = TestClient(app, base_url="https://testserver")
    jeton = client.get("/api/health").headers[CSRF_HEADER]

    reponse = client.post("/api/resource", headers={CSRF_HEADER: jeton})

    assert reponse.status_code == 200


@pytest.mark.parametrize("nom", ["csrf_token", "__host-csrf_token"])
def test_en_https_un_cookie_sans_le_prefixe_exact_est_ignore(csrf_https, nom):
    """Un cookie planté sous l'ancien nom, ou sous une casse voisine, ne compte pas."""
    _, app = csrf_https

    reponse = TestClient(app, base_url="https://testserver").post(
        "/api/resource", headers={"Cookie": f"{nom}=connu", CSRF_HEADER: "connu"}
    )

    assert reponse.status_code == 403
    assert reponse.json() == {"detail": "CSRF token missing"}


def test_en_https_un_jeton_present_est_repris_sans_nouveau_cookie(csrf_https):
    _, app = csrf_https
    client = TestClient(app, base_url="https://testserver")
    entetes = {"Cookie": "__Host-csrf_token=present"}

    reponse = client.get("/api/health", headers=entetes)
    assert reponse.headers[CSRF_HEADER] == "present"
    assert "set-cookie" not in reponse.headers

    refus = client.post("/api/resource", headers={**entetes, CSRF_HEADER: "autre"})
    assert refus.status_code == 403
    assert refus.json() == {"detail": "CSRF token invalid"}


@pytest.mark.parametrize(
    "cookie, entete",
    [("jeton", "jet\xe9n"), ("jet\xe9n", "jeton")],
)
def test_un_jeton_non_ascii_est_refuse_sans_erreur_500(client, cookie, entete):
    """compare_digest sur deux chaînes levait TypeError (500) hors ASCII.
    Starlette décode les en-têtes en latin-1 : on les envoie en octets."""
    reponse = client.post(
        "/api/resource",
        headers={
            "Cookie": f"{CSRF_COOKIE}={cookie}".encode("latin-1"),
            CSRF_HEADER: entete.encode("latin-1"),
        },
    )

    assert reponse.status_code == 403
    assert reponse.json() == {"detail": "CSRF token invalid"}
