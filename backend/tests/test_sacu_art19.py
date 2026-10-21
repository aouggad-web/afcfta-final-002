"""SACU, accord de 2002, art. 19 : une marchandise d'origine tierce déjà
dédouanée dans un autre État membre n'acquitte ni droit de douane ni accise à
destination ; la TVA reste due. Fiche : SACU_art19_2026-10-14.json."""

import importlib.util
import os
import sys

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from services import socle

RACINE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

pytestmark = pytest.mark.skipif(
    not os.path.exists(os.path.join(RACINE, "backend", "socle", "ZAF.json")), reason="socle absent (gitignoré)"
)


@pytest.fixture(autouse=True)
def _cache_propre():
    socle.vider_cache()
    yield
    socle.vider_cache()


@pytest.fixture(scope="module")
def client():
    chemin = os.path.join(RACINE, "backend", "routes", "calcul.py")
    spec = importlib.util.spec_from_file_location("routes_calcul_sacu_art19_test", chemin)
    module = importlib.util.module_from_spec(spec)
    sys.modules["routes_calcul_sacu_art19_test"] = module
    spec.loader.exec_module(module)
    app = FastAPI()
    app.include_router(module.router)
    return TestClient(app)


def _calcul(client, destination, code, origine="CHN", quantite=None, deja_dedouane=True):
    demande = {"destination": destination, "code_sh": code, "valeur_cif": 11000, "valeur_fob": 10000,
               "devise_cif": "ZAR", "origine": origine, "deja_dedouane_sacu": deja_dedouane}
    if quantite is not None:
        demande["quantite"] = quantite
    return client.post("/calcul", json=demande)


def _lignes(bloc):
    return {ligne["code"]: ligne for ligne in bloc["lignes"]}


def test_botswana_sans_second_droit_de_douane(client):
    """Parfum chinois dédouané à Durban puis acheminé au Botswana : DD 0, TVA due."""
    reponse = _calcul(client, "BWA", "33030090")
    assert reponse.status_code == 200
    resultat = reponse.json()
    assert resultat["regime_commercial"]["statut"] == "DEJA_DEDOUANEE_SACU"
    assert "art. 19" in resultat["regime_commercial"]["note"]
    assert "31.4" in resultat["regime_commercial"]["note"]
    assert _lignes(resultat["npf"])["DD"]["montant"] == pytest.approx(2_000.0)
    lignes = _lignes(resultat["preference"])
    assert lignes["DD"]["montant"] == 0.0
    assert lignes["TVA"]["montant"] > 0


def test_afrique_du_sud_ni_droit_ni_accise_mais_prelevements(client):
    """Essence arrivée par un autre État membre : DD et accise à 0, taxe sur les
    carburants et Road Accident Fund maintenus, dans l'assiette de la TVA."""
    lignes = _lignes(_calcul(client, "ZAF", "27101202", quantite=1000).json()["preference"])
    assert lignes["DD"]["montant"] == 0.0 and lignes["EXS"]["montant"] == 0.0
    assert lignes["FLV"]["montant"] == pytest.approx(4_290.0)
    assert lignes["RAF"]["montant"] == pytest.approx(2_250.0)
    assert lignes["TVA"]["base"] == pytest.approx(11_000.0 + 4_290.0 + 2_250.0)


def test_origine_sacu_reste_en_libre_circulation(client):
    resultat = _calcul(client, "BWA", "33030090", origine="ZAF").json()
    assert resultat["regime_commercial"]["statut"] == "LIBRE_CIRCULATION"


def test_sans_le_champ_le_droit_est_du(client):
    resultat = _calcul(client, "BWA", "33030090", deja_dedouane=False).json()
    assert resultat["regime_commercial"]["statut"] != "DEJA_DEDOUANEE_SACU"


def test_champ_refuse_hors_sacu(client):
    reponse = _calcul(client, "KEN", "33030090")
    assert reponse.status_code == 422
    assert "SACU" in reponse.json()["detail"]
