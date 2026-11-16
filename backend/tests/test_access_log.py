"""Ligne de journal par requête, sans donnée personnelle (point 17 de l'audit)."""

import io
import logging

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from log_redaction import RedactingFormatter
from middlewares.access_log import AccessLogMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse


@pytest.fixture
def journal():
    """Sortie formatée des lignes d'accès et d'une route, rid compris."""
    flux = io.StringIO()
    gestionnaire = logging.StreamHandler(flux)
    gestionnaire.setFormatter(RedactingFormatter("%(name)s rid=%(rid)s: %(message)s"))
    noms = ("middlewares.access_log", "test.route")
    etats = []
    for nom in noms:
        lg = logging.getLogger(nom)
        etats.append((lg, lg.level))
        lg.addHandler(gestionnaire)
        lg.setLevel(logging.INFO)
    yield flux
    for lg, niveau in etats:
        lg.removeHandler(gestionnaire)
        lg.setLevel(niveau)


def _lignes(flux):
    return [ligne for ligne in flux.getvalue().splitlines() if ligne]


def _appli():
    app = FastAPI()

    @app.get("/api/consultation/{iso3}/recherche")
    async def recherche(iso3: str):
        logging.getLogger("test.route").info("recherche servie")
        return {"iso3": iso3}

    @app.get("/api/health")
    async def sante():
        return {"status": "ok"}

    @app.get("/api/boum")
    async def boum():
        raise RuntimeError("panne")

    @app.get("/{full_path:path}")
    async def repli(full_path: str):
        return {"page": "index"}

    return app


def test_une_ligne_par_requete_sans_ip_ni_query_ni_identifiant(journal):
    app = _appli()
    app.add_middleware(AccessLogMiddleware)

    TestClient(app).get(
        "/api/consultation/DZA/recherche?q=secret-de-requete",
        headers={"Authorization": "Bearer jeton-tres-secret-de-test"},
    )

    acces = [ligne for ligne in _lignes(journal) if "access_log" in ligne]
    assert len(acces) == 1
    ligne = acces[0]
    assert "m=GET p=/api/consultation/{iso3}/recherche s=200" in ligne
    for interdit in ("DZA", "secret-de-requete", "testclient", "Bearer", "jeton-tres"):
        assert interdit not in ligne


def test_gabarit_complet_pour_une_route_d_un_routeur_inclus(journal):
    from fastapi import APIRouter

    sous = APIRouter()

    @sous.get("/consultation/{iso3}/sous-positions/{hs6}")
    async def sous_positions(iso3: str, hs6: str):
        return {}

    api = APIRouter(prefix="/api")
    api.include_router(sous)
    app = FastAPI()
    app.include_router(api)
    app.add_middleware(AccessLogMiddleware)

    TestClient(app).get("/api/consultation/DZA/sous-positions/020110")

    assert any(
        "p=/api/consultation/{iso3}/sous-positions/{hs6} s=200" in ligne
        for ligne in _lignes(journal)
    )


def test_toutes_les_lignes_d_une_requete_portent_le_meme_rid(journal):
    app = _appli()
    app.add_middleware(AccessLogMiddleware)

    TestClient(app).get("/api/consultation/MAR/recherche")

    rids = {ligne.split("rid=")[1].split(":")[0] for ligne in _lignes(journal)}
    assert len(rids) == 1 and rids != {"-"}


def test_les_refus_des_autres_middlewares_sont_journalises(journal):
    class Limiteur(BaseHTTPMiddleware):
        async def dispatch(self, request, call_next):
            return JSONResponse({"detail": "Too many requests"}, status_code=429)

    app = _appli()
    app.add_middleware(Limiteur)
    app.add_middleware(AccessLogMiddleware)

    TestClient(app).get("/api/consultation/DZA/recherche")

    assert any("s=429" in ligne for ligne in _lignes(journal))


def test_une_exception_donne_500_et_sa_classe(journal):
    app = _appli()
    app.add_middleware(AccessLogMiddleware)

    reponse = TestClient(app, raise_server_exceptions=False).get("/api/boum")

    assert reponse.status_code == 500
    ligne = next(ligne for ligne in _lignes(journal) if "p=/api/boum" in ligne)
    assert "s=500" in ligne and "err=RuntimeError" in ligne
    assert "panne" not in ligne  # le message reste dans la trace, au journal d'erreurs


def test_sante_ecrite_seulement_en_erreur(journal):
    app = _appli()
    app.add_middleware(AccessLogMiddleware)
    client = TestClient(app)

    client.get("/api/health")
    assert not _lignes(journal)

    client.post("/api/health")
    assert any("p=/api/health s=405" in ligne for ligne in _lignes(journal))


def test_le_repli_attrape_tout_journalise_le_chemin_demande(journal):
    app = _appli()
    app.add_middleware(AccessLogMiddleware)

    TestClient(app).get("/api/wp-login.php")

    assert any("p=/api/wp-login.php s=200" in ligne for ligne in _lignes(journal))


def test_un_chemin_avec_retour_a_la_ligne_reste_sur_une_ligne(journal):
    app = _appli()
    app.add_middleware(AccessLogMiddleware)

    TestClient(app).get("/x%0A2026-01-01T00:00:00.000Z [INFO] faux: m=GET")

    lignes = _lignes(journal)
    assert len(lignes) == 1
    assert "p=/x%0A2026" in lignes[0]


def test_le_serveur_place_le_journal_d_acces_le_plus_a_l_exterieur():
    from server import app

    assert app.user_middleware[0].cls is AccessLogMiddleware


def test_une_tache_de_fond_n_allonge_pas_la_duree_et_son_erreur_est_signalee(journal):
    import time

    from fastapi import BackgroundTasks

    app = FastAPI()

    def lente():
        time.sleep(0.3)

    def cassee():
        raise ValueError("smtp")

    @app.post("/api/contact")
    async def contact(taches: BackgroundTasks):
        taches.add_task(lente)
        return {"ok": True}

    @app.post("/api/contact-casse")
    async def contact_casse(taches: BackgroundTasks):
        taches.add_task(cassee)
        return {"ok": True}

    app.add_middleware(AccessLogMiddleware)
    client = TestClient(app, raise_server_exceptions=False)

    client.post("/api/contact")
    ligne = next(ligne for ligne in _lignes(journal) if "p=/api/contact " in ligne)
    assert int(ligne.split("ms=")[1].split()[0]) < 250

    client.post("/api/contact-casse")
    ligne = next(ligne for ligne in _lignes(journal) if "p=/api/contact-casse" in ligne)
    assert "s=200" in ligne and "err=ValueError" in ligne


def test_une_requete_annulee_est_nommee_et_signalee():
    import asyncio

    enregistrements = []

    class Capture(logging.Handler):
        def emit(self, record):
            enregistrements.append(record)

    async def appli(scope, receive, send):
        raise asyncio.CancelledError()

    capture = Capture()
    logger = logging.getLogger("middlewares.access_log")
    logger.addHandler(capture)
    try:
        with pytest.raises(asyncio.CancelledError):
            asyncio.run(
                AccessLogMiddleware(appli)(
                    {"type": "http", "method": "GET", "path": "/api/lent"}, None, None
                )
            )
    finally:
        logger.removeHandler(capture)

    (record,) = enregistrements
    assert record.levelno == logging.WARNING
    assert "err=CancelledError" in record.getMessage()
