"""Afrique du Sud : accises à l'importation (Schedule No. 1 Part 2A et 2B) et
accises dans l'assiette de la TVA. Fiche : ZAF_accises_2026-10-14.json."""

import importlib.util
import json
import os
import sys

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from services import socle

RACINE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
ACCISES = os.path.join(RACINE, "data", "zaf", "accises_sch1_part2.json")

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
    spec = importlib.util.spec_from_file_location("routes_calcul_zaf_accises_test", chemin)
    module = importlib.util.module_from_spec(spec)
    sys.modules["routes_calcul_zaf_accises_test"] = module
    spec.loader.exec_module(module)
    app = FastAPI()
    app.include_router(module.router)
    return TestClient(app)


def _calcul(client, code, quantite=None, origine="CHN", expedition=None):
    demande = {"destination": "ZAF", "code_sh": code, "valeur_cif": 11000, "valeur_fob": 10000,
               "devise_cif": "ZAR", "origine": origine}
    if quantite is not None:
        demande["quantite"] = quantite
    if expedition:
        demande["pays_expedition"] = expedition
    reponse = client.post("/calcul", json=demande)
    assert reponse.status_code == 200
    npf = reponse.json()["npf"]
    return npf["etat"], {ligne["code"]: ligne for ligne in npf["lignes"]}


def _extracteur():
    spec = importlib.util.spec_from_file_location(
        "extraire_accises_zaf_test", os.path.join(RACINE, "scripts", "extraire_accises_zaf.py")
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.mark.parametrize("brut,attendu", [
    ("34,7c/kg", {"montant": 0.347, "unite": "kg"}),
    ("3,909c/li", {"montant": 0.03909, "unite": "li"}),
    ("R6 041.72/kg net", {"montant": 6041.72, "unite": "kg"}),
    ("R11.79/10cigarettes", {"montant": 11.79, "unite": "10cigarettes"}),
    ("R149.98/li aa", {"montant": 149.98, "unite": "li aa"}),
    ("R3.29/ml", {"montant": 3.29, "unite": "ml"}),
    ("free", {"taux": 0.0}),
    ("9%", {"taux": 9.0}),
    ("(See Note 2 to this Part)", {"renvoi": "(See Note 2 to this Part)"}),
])
def test_lecture_des_taux(brut, attendu):
    assert _extracteur().taux(brut) == attendu


def test_le_parseur_reproduit_le_fichier():
    """Les tableaux relus dans les PDF déposés redonnent data/zaf/accises_sch1_part2.json."""
    extracteur = _extracteur()
    legislation = os.path.join(RACINE, "data", "sources", "ZAF", "legislation")
    articles = (extracteur.lire(os.path.join(legislation, "Sch1P2A-Schedule-No-1-Part-2A.pdf"), "2A")
                + extracteur.lire(os.path.join(legislation, "Sch1P2B-Schedule-No-1-Part-2B.pdf"), "2B"))
    with open(ACCISES, encoding="utf-8") as f:
        assert articles == json.load(f)["articles"]
    assert sum(a["partie"] == "2A" for a in articles) == 140
    assert sum(a["partie"] == "2B" for a in articles) == 147


def test_accise_ad_valorem_et_tva(client):
    """3303.00.90 : DD 20 %, accise 9 % sur FOB × 1,15 + DD (s.65(8)(a)), TVA sur
    FOB × 1,10 + DD + accise."""
    etat, lignes = _calcul(client, "33030090")
    assert etat == "COMPLET"
    assert lignes["EXA"]["base"] == pytest.approx(13_500.0) and lignes["EXA"]["montant"] == pytest.approx(1_215.0)
    assert lignes["TVA"]["base"] == pytest.approx(11_000.0 + 2_000.0 + 1_215.0)


def test_origine_sacu_sans_majoration(client):
    """Origine et expédition Botswana : TVA sans les 10 %, accise comprise."""
    _, lignes = _calcul(client, "33030090", origine="BWA", expedition="BWA")
    assert lignes["TVA"]["base"] == pytest.approx(10_000.0 + 2_000.0 + 1_215.0)


def test_accise_specifique_des_cigarettes(client):
    """2402.20.90 : R11,79 par 10 cigarettes ; 500 × 10 cigarettes."""
    etat, _ = _calcul(client, "24022090")
    assert etat != "COMPLET"
    etat, lignes = _calcul(client, "24022090", quantite=500)
    assert etat == "COMPLET" and lignes["EXS"]["montant"] == pytest.approx(5_895.0)
    assert lignes["TVA"]["base"] == pytest.approx(11_000.0 + 4_500.0 + 5_895.0)


def test_vin_au_litre(client):
    etat, lignes = _calcul(client, "22042141", quantite=100)
    assert etat == "COMPLET" and lignes["EXS"]["montant"] == pytest.approx(615.0)


@pytest.mark.parametrize("code", ["22030090", "87032390"])
def test_alcool_absolu_et_vehicules_incomplets(client, code):
    """Bière à l'alcool absolu, voiture au taux fonction de la valeur : total incomplet."""
    etat, lignes = _calcul(client, code, quantite=100)
    assert etat != "COMPLET"
    assert lignes["TVA"]["montant"] is None
