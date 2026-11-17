"""Limite de taille du corps de requête (audit DoS, 17/11/2026).

Aucune borne n'existait : un POST anonyme de 20 Mo était bufferisé et parsé,
épuisant la mémoire du worker unique. Le middleware refuse 413 avant la route.
"""

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
