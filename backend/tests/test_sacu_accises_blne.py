"""Botswana, Lesotho, Namibie, Eswatini : accises aux taux communs de la SACU
(tarif sud-africain), valeur de l'accise ad valorem selon chaque loi
nationale. Fiche : SACU_accises_BLNE_2026-10-20.json."""

import importlib.util
import json
import os
import sys

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from services import socle

RACINE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
#: Devise de la valeur déclarée : celle du tarif servi (backend/socle/devises_pays.json).
DEVISE = {"BWA": "ZAR", "LSO": "LSL", "NAM": "NAD", "SWZ": "SZL"}

pytestmark = pytest.mark.skipif(
    not os.path.exists(os.path.join(RACINE, "backend", "socle", "BWA.json")), reason="socle absent (gitignoré)"
)


@pytest.fixture(autouse=True)
def _cache_propre():
    socle.vider_cache()
    yield
    socle.vider_cache()


@pytest.fixture(scope="module")
def client():
    chemin = os.path.join(RACINE, "backend", "routes", "calcul.py")
    spec = importlib.util.spec_from_file_location("routes_calcul_sacu_accises_test", chemin)
    module = importlib.util.module_from_spec(spec)
    sys.modules["routes_calcul_sacu_accises_test"] = module
    spec.loader.exec_module(module)
    app = FastAPI()
    app.include_router(module.router)
    return TestClient(app)


def _calcul(client, destination, code, quantite=None, devise=None):
    demande = {"destination": destination, "code_sh": code, "valeur_cif": 11000, "valeur_fob": 10000,
               "devise_cif": devise or DEVISE[destination], "origine": "CHN"}
    if quantite is not None:
        demande["quantite"] = quantite
    reponse = client.post("/calcul", json=demande)
    assert reponse.status_code == 200
    npf = reponse.json()["npf"]
    return npf["etat"], {ligne["code"]: ligne for ligne in npf["lignes"]}


def _ligne_du_socle(iso, code, code_ligne):
    with open(os.path.join(RACINE, "backend", "socle", f"{iso}.json"), encoding="utf-8") as f:
        droits = json.load(f)["positions"][code]["droits"]
    return next(d for d in droits if d["code"] == code_ligne)


@pytest.mark.parametrize("pays", ["BWA", "LSO", "NAM", "SWZ"])
def test_cigarettes_au_taux_sud_africain(client, pays):
    """2402.20.90 : R11,79 par 10 cigarettes, comme en Afrique du Sud ; 500 × 10 cigarettes."""
    etat, lignes = _calcul(client, pays, "24022090", quantite=500)
    assert etat == "COMPLET"
    assert lignes["EXS"]["montant"] == pytest.approx(5_895.0)
    assert "Taux commun SACU" in _ligne_du_socle(pays, "24022090", "EXS")["source"]


def test_tva_du_botswana_avec_l_accise(client):
    """VAT Act 2001 s.13(1)(a)(iii) : CIF + droits de douane et d'accise."""
    _, lignes = _calcul(client, "BWA", "24022090", quantite=500)
    assert lignes["TVA"]["base"] == pytest.approx(11_000.0 + 4_500.0 + 5_895.0)


@pytest.mark.parametrize("pays,tva", [
    ("NAM", 11_000.0),                       # FOB × 1,10, sans les droits
    ("SWZ", 10_000.0 + 2_000.0 + 1_215.0),   # FOB + droits et accises
])
def test_accise_ad_valorem_namibie_eswatini(client, pays, tva):
    """3303.00.90 : 9 % sur FOB × 1,15 + DD (s.75(9)(a) NAM, s.65(7)(a) SWZ)."""
    etat, lignes = _calcul(client, pays, "33030090")
    assert etat == "COMPLET"
    assert lignes["EXA"]["base"] == pytest.approx(13_500.0) and lignes["EXA"]["montant"] == pytest.approx(1_215.0)
    assert lignes["TVA"]["base"] == pytest.approx(tva)


def test_accise_ad_valorem_lesotho_sans_l_accise_specifique():
    """s.67(6)(a) de 1982 : seuls les droits de la Part 1 s'ajoutent."""
    assert _ligne_du_socle("LSO", "33030090", "EXA")["assiette"] == "FOBx1.15+DD"


def test_accise_ad_valorem_du_botswana_non_liquidee(client):
    """s.69(1) : prix de gros sur le marché botswanais ; ni l'accise ni la TVA ne sont liquidées."""
    etat, lignes = _calcul(client, "BWA", "33030090")
    assert etat != "COMPLET"
    assert lignes["EXA"]["montant"] is None
    assert lignes["TVA"]["montant"] is None


def test_valeur_en_pula_exige_un_taux_de_change(client):
    """Unités de compte du Botswana = rand : une valeur en pula ne s'y additionne pas sans taux."""
    _, lignes = _calcul(client, "BWA", "24022090", quantite=500, devise="BWP")
    assert lignes["EXS"]["statut"] == "TAUX_DE_CHANGE_REQUIS"
