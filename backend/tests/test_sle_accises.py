"""Sierra Leone : accise à l'importation (Excise Act 1982, First Schedule
modifiée par les Finance Acts 2021, 2024 et 2026). Fiche :
SLE_accises_2026-10-25.json."""

import importlib.util
import json
import os
import sys

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from services import socle

RACINE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

pytestmark = pytest.mark.skipif(
    not os.path.exists(os.path.join(RACINE, "backend", "socle", "SLE.json")), reason="socle absent (gitignoré)"
)


@pytest.fixture(autouse=True)
def _cache_propre():
    socle.vider_cache()
    yield
    socle.vider_cache()


@pytest.fixture(scope="module")
def client():
    chemin = os.path.join(RACINE, "backend", "routes", "calcul.py")
    spec = importlib.util.spec_from_file_location("routes_calcul_sle_accises_test", chemin)
    module = importlib.util.module_from_spec(spec)
    sys.modules["routes_calcul_sle_accises_test"] = module
    spec.loader.exec_module(module)
    app = FastAPI()
    app.include_router(module.router)
    return TestClient(app)


def _calcul(client, code, quantite):
    reponse = client.post("/calcul", json={
        "destination": "SLE", "code_sh": code, "valeur_cif": 11000, "valeur_fob": 10000,
        "devise_cif": "SLE", "origine": "CHN", "quantite": quantite,
    })
    assert reponse.status_code == 200
    npf = reponse.json()["npf"]
    return npf["etat"], {ligne["code"]: ligne for ligne in npf["lignes"]}


@pytest.mark.parametrize("code,quantite,montant", [
    ("2203001000", 1000, 15_000.0),  # bière de malt, Le15 par litre (FA 2024)
    ("2402200000", 500, 1_500.0),    # cigarettes, NLe3 par paquet de 20 (FA 2026)
    ("2401100000", 100, 9_800.0),    # tabac non fabriqué, NLe98 par kg
    ("2523290000", 1000, 200.0),     # ciment Portland, NLe10 par 50 kg
    ("2710192100", 1000, 5_000.0),   # gazole, NLe5,0 par litre
    ("2710191200", 1000, 2_000.0),   # pétrole lampant, NLe2,0 par litre
    ("3923210000", 100, 1_600.0),    # sacs en polyéthylène, Le16 par kg (FA 2024)
])
def test_accise_specifique_liquidee_et_dans_la_gst(client, code, quantite, montant):
    """GST Act 2009, s.26(1)(c) : la valeur de l'importation comprend les autres
    taxes dues à l'importation, l'accise comprise."""
    etat, lignes = _calcul(client, code, quantite)
    assert etat == "COMPLET"
    assert lignes["EXC"]["montant"] == pytest.approx(montant)
    autres = sum(lignes[c]["montant"] for c in lignes if c != "TVA")
    assert lignes["TVA"]["base"] == pytest.approx(11_000 + autres)


@pytest.mark.parametrize("code", [
    "2208300000",  # whiskies : taux selon le titre alcoométrique
    "2204210000",  # vins
    "2202999000",  # boissons sucrées : taux par gramme de sucre
    "2403110000",  # shisha : par kg et par litre
    "3401111000",  # savons : 20 %, valeur imposable non établie
])
def test_accise_declaree_sans_liquidation(client, code):
    etat, lignes = _calcul(client, code, 10)
    assert etat != "COMPLET"
    assert lignes["EXC"]["montant"] is None
    assert lignes["TVA"]["montant"] is None


def test_hors_du_perimetre():
    """Vin de palme absent du tableau de 2024 ; essence d'aviation, graisses
    lubrifiantes et bouteilles plastiques non reprises."""
    with open(os.path.join(RACINE, "backend", "socle", "SLE.json"), encoding="utf-8") as f:
        positions = json.load(f)["positions"]
    for code in ("2206009100", "2710123000", "2710193300", "3923309000"):
        assert not any(d["code"] == "EXC" for d in positions[code]["droits"])
