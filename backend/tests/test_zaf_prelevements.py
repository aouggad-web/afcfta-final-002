"""Afrique du Sud : prélèvements à l'importation (Schedule No. 1 Parts 3A, 3C,
3D, 3E, 5A, 5B, 7A) et leur place dans l'assiette de la TVA. Fiche :
ZAF_prelevements_2026-10-14.json."""

import importlib.util
import json
import os
import sys

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from services import socle

RACINE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
PRELEVEMENTS = os.path.join(RACINE, "data", "zaf", "prelevements_sch1_parts3_5_7.json")
LEGISLATION = os.path.join(RACINE, "data", "sources", "ZAF", "legislation")

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
    spec = importlib.util.spec_from_file_location("routes_calcul_zaf_prelevements_test", chemin)
    module = importlib.util.module_from_spec(spec)
    sys.modules["routes_calcul_zaf_prelevements_test"] = module
    spec.loader.exec_module(module)
    app = FastAPI()
    app.include_router(module.router)
    return TestClient(app)


def _extracteur():
    spec = importlib.util.spec_from_file_location(
        "extraire_prelevements_zaf_test", os.path.join(RACINE, "scripts", "extraire_prelevements_zaf.py")
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _calcul(client, code, quantite):
    reponse = client.post("/calcul", json={
        "destination": "ZAF", "code_sh": code, "valeur_cif": 11000, "valeur_fob": 10000,
        "devise_cif": "ZAR", "origine": "CHN", "quantite": quantite,
    })
    assert reponse.status_code == 200
    npf = reponse.json()["npf"]
    return npf["etat"], {ligne["code"]: ligne for ligne in npf["lignes"]}


@pytest.mark.parametrize("brut,attendu", [
    ("32c/bag", {"montant": 0.32, "unite": "bag"}),
    ("R20.00/lamp", {"montant": 20.0, "unite": "lamp"}),
    ("R2.30/kg net", {"montant": 2.3, "unite": "kg"}),
    ("429c/li", {"montant": 4.29, "unite": "li"}),
    ("196,5c/li", {"montant": 1.965, "unite": "li"}),
    ("free", {"taux": 0.0}),
    ("R146.00 per g/km CO2 emissions exceeding 95g/km", {"par_g_km_co2": 146.0, "seuil_g_km": 95}),
    ("2,21c/gram of the sugar content that exceeds 4g/100ml", {"par_gramme_de_sucre": 0.0221, "seuil_g_100ml": 4}),
    ("Petrol, as defined in Additional Note 1(b) to Chapter 27 225c/li", None),
])
def test_lecture_des_taux(brut, attendu):
    lu = _extracteur().taux(brut)
    if attendu is None:
        assert lu is None  # un taux se lit sur sa propre ligne, jamais collé au libellé
    else:
        assert {k: v for k, v in lu.items() if k != "brut"} == attendu


@pytest.mark.skipif(not os.path.exists(os.path.join(LEGISLATION, "ZAF_Sch1_Part5A_2026-07-01.pdf")),
                    reason="documents de la PR #648 absents")
def test_le_parseur_reproduit_le_fichier():
    extracteur = _extracteur()
    articles = []
    for partie, nom in extracteur.PARTIES.items():
        articles += extracteur.lire(os.path.join(LEGISLATION, nom), partie)
    with open(PRELEVEMENTS, encoding="utf-8") as f:
        assert articles == json.load(f)["articles"]


def test_nombre_d_articles():
    with open(PRELEVEMENTS, encoding="utf-8") as f:
        articles = json.load(f)["articles"]
    compte = {}
    for article in articles:
        compte[article["partie"]] = compte.get(article["partie"], 0) + 1
    assert compte == {"3A": 4, "3C": 7, "3D": 17, "3E": 222, "5A": 15, "5B": 15, "7A": 11}


def test_essence(client):
    """2710.12.02, 1 000 litres : accise 3,909 c/l, taxe sur les carburants 429 c/l,
    Road Accident Fund 225 c/l, tous dans l'assiette de la TVA."""
    etat, lignes = _calcul(client, "27101202", 1000)
    assert etat == "COMPLET"
    assert lignes["FLV"]["montant"] == pytest.approx(4_290.0)
    assert lignes["RAF"]["montant"] == pytest.approx(2_250.0)
    taxes = sum(lignes[c]["montant"] for c in ("DD", "EXS", "FLV", "RAF"))
    assert lignes["TVA"]["base"] == pytest.approx(11_000.0 + taxes)


def test_boisson_sucree_teneur_reputee(client):
    """2202.10.10, 100 litres : (20 − 4) g × 2,21 c par 100 ml, soit 3,536 R par litre."""
    etat, lignes = _calcul(client, "22021010", 100)
    assert etat == "COMPLET" and lignes["HPL"]["montant"] == pytest.approx(353.6)


@pytest.mark.parametrize("code,ligne,quantite,montant", [
    ("39232107", "EVB", 1000, 320.0),
    ("85392145", "EVL", 10, 200.0),
    ("40111001", "EVT", 50, 115.0),
])
def test_prelevements_environnementaux(client, code, ligne, quantite, montant):
    etat, lignes = _calcul(client, code, quantite)
    assert etat == "COMPLET" and lignes[ligne]["montant"] == pytest.approx(montant)


def test_vehicule_co2_et_pneus_montes_incomplets(client):
    etat, lignes = _calcul(client, "87032390", 1)
    assert etat != "COMPLET"
    assert lignes["EVC"]["montant"] is None and lignes["EVT"]["montant"] is None
