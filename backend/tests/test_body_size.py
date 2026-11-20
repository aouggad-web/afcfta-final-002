"""Limite de taille du corps de requête (audit DoS, 17/11/2026).

Aucune borne n'existait : un POST anonyme de 20 Mo était bufferisé et parsé,
épuisant la mémoire du worker unique. Le middleware refuse 413 avant la route.
"""

import asyncio

from fastapi.testclient import TestClient
from starlette.applications import Starlette
from starlette.responses import PlainTextResponse
from starlette.routing import Route

from middlewares.body_size import BodySizeLimitMiddleware


async def _echo(request):
    corps = await request.body()
    return PlainTextResponse(str(len(corps)))


def _client(max_bytes):
    app = Starlette(routes=[Route("/", _echo, methods=["GET", "POST"])])
    app.add_middleware(BodySizeLimitMiddleware, max_bytes=max_bytes)
    return TestClient(app)


def test_corps_sous_la_borne_passe():
    reponse = _client(1000).post("/", content=b"x" * 500)
    assert reponse.status_code == 200
    assert reponse.text == "500"


def test_corps_au_dessus_de_la_borne_refuse_413():
    reponse = _client(1000).post("/", content=b"x" * 5000)
    assert reponse.status_code == 413
    assert reponse.json()["detail"] == "Request body too large."


def test_content_length_illisible_refuse():
    reponse = _client(1000).post("/", headers={"Content-Length": "pas-un-nombre"}, content=b"x")
    # Starlette/uvicorn peut rejeter un Content-Length illisible en amont ;
    # dans tous les cas la requête ne doit pas être servie en 200.
    assert reponse.status_code in (400, 413)


def test_get_sans_corps_passe():
    reponse = _client(1000).get("/")
    assert reponse.status_code == 200


# ── Requêtes « chunked » (sans Content-Length), au niveau ASGI ──────────────
# Revue Codex (18/11/2026) : au dépassement, la route ne doit PAS être invoquée
# (sinon un préfixe JSON valide s'exécute avant que le 413 ne remplace la
# réponse — effet de bord malgré le rejet).


def _jouer_middleware(max_bytes, chunks, app):
    """Pilote le middleware au niveau ASGI avec un corps livré en morceaux."""
    mw = BodySizeLimitMiddleware(app, max_bytes=max_bytes)
    scope = {"type": "http", "method": "POST", "headers": []}  # aucun Content-Length
    file = list(chunks)
    i = {"n": 0}

    async def receive():
        m = file[i["n"]]
        i["n"] += 1
        return m

    envois = []

    async def send(message):
        envois.append(message)

    asyncio.run(mw(scope, receive, send))
    return envois


def test_corps_chunked_au_dessus_de_la_borne_n_invoque_pas_la_route():
    appelee = {"v": False}

    async def app(scope, receive, send):
        appelee["v"] = True
        await send({"type": "http.response.start", "status": 200, "headers": []})
        await send({"type": "http.response.body", "body": b"ok"})

    chunks = [
        {"type": "http.request", "body": b'{"message":"x"}', "more_body": True},
        {"type": "http.request", "body": b"A" * 2000, "more_body": False},
    ]
    envois = _jouer_middleware(1000, chunks, app)

    assert appelee["v"] is False  # la route n'a pas tourné : pas d'effet de bord
    assert envois[0]["type"] == "http.response.start"
    assert envois[0]["status"] == 413


def test_corps_chunked_sous_la_borne_invoque_la_route_avec_le_corps_complet():
    recu = {"body": None}

    async def app(scope, receive, send):
        body = b""
        while True:
            m = await receive()
            if m["type"] == "http.request":
                body += m.get("body", b"")
                if not m.get("more_body", False):
                    break
            else:
                break
        recu["body"] = body
        await send({"type": "http.response.start", "status": 200, "headers": []})
        await send({"type": "http.response.body", "body": b""})

    chunks = [
        {"type": "http.request", "body": b'{"a":', "more_body": True},
        {"type": "http.request", "body": b"1}", "more_body": False},
    ]
    envois = _jouer_middleware(1000, chunks, app)

    assert recu["body"] == b'{"a":1}'  # la route reçoit le corps complet
    assert envois[0]["status"] == 200


# Revue Codex (20/11/2026) — deux P1 sur le middleware :


def test_apres_le_tampon_delegue_au_vrai_receive():
    """Un http.disconnect synthétique après le tampon annulerait à tort une
    réponse en flux (téléchargement tronqué). Le middleware doit déléguer au
    vrai receive, qui porte les vraies déconnexions."""
    file = [
        {"type": "http.request", "body": b"hi", "more_body": False},
        {"type": "http.disconnect"},
    ]
    i = {"n": 0}
    apres_corps = {"n": 0}

    async def receive():
        if i["n"] >= 1:  # au-delà du corps déjà tamponné
            apres_corps["n"] += 1
        m = file[i["n"]]
        i["n"] += 1
        return m

    vu = {"msg": None}

    async def app(scope, receive_, send):
        await receive_()  # corps (tamponné)
        vu["msg"] = await receive_()  # doit venir du vrai receive
        await send({"type": "http.response.start", "status": 200, "headers": []})
        await send({"type": "http.response.body", "body": b""})

    mw = BodySizeLimitMiddleware(app, max_bytes=1000)

    async def send(message):
        pass

    asyncio.run(mw({"type": "http", "headers": []}, receive, send))

    assert apres_corps["n"] == 1  # le vrai receive a bien été consulté
    assert vu["msg"]["type"] == "http.disconnect"


def test_content_length_avec_transfer_encoding_chunked_est_borne():
    """Content-Length + Transfer-Encoding: chunked : le serveur décode en
    chunked, donc on ne fait pas confiance au Content-Length — on compte le
    corps réel et on borne (sinon la faille mémoire est rouverte)."""
    appelee = {"v": False}

    async def app(scope, receive, send):
        appelee["v"] = True
        await send({"type": "http.response.start", "status": 200, "headers": []})
        await send({"type": "http.response.body", "body": b""})

    mw = BodySizeLimitMiddleware(app, max_bytes=1000)
    scope = {
        "type": "http",
        "headers": [(b"content-length", b"1"), (b"transfer-encoding", b"chunked")],
    }
    chunks = [{"type": "http.request", "body": b"A" * 2000, "more_body": False}]
    i = {"n": 0}

    async def receive():
        m = chunks[i["n"]]
        i["n"] += 1
        return m

    envois = []

    async def send(message):
        envois.append(message)

    asyncio.run(mw(scope, receive, send))

    assert appelee["v"] is False  # route non invoquée
    assert envois[0]["status"] == 413
