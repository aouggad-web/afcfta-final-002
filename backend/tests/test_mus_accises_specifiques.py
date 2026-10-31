"""Maurice : droits d'accise spécifiques de la First Schedule de l'Excise Act
(version consolidée MRA du 01.10.2026). Fiche : MUS_accises_specifiques_2026-10-25.json."""

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
    not os.path.exists(os.path.join(RACINE, "backend", "socle", "MUS.json")), reason="socle absent (gitignoré)"
)


@pytest.fixture(autouse=True)
def _cache_propre():
    socle.vider_cache()
    yield
    socle.vider_cache()


@pytest.fixture(scope="module")
def client():
    chemin = os.path.join(RACINE, "backend", "routes", "calcul.py")
    spec = importlib.util.spec_from_file_location("routes_calcul_mus_accises_test", chemin)
    module = importlib.util.module_from_spec(spec)
    sys.modules["routes_calcul_mus_accises_test"] = module
    spec.loader.exec_module(module)
    app = FastAPI()
    app.include_router(module.router)
    return TestClient(app)


def _calcul(client, code, quantite=None):
    demande = {"destination": "MUS", "code_sh": code, "valeur_cif": 10000, "devise_cif": "MUR", "origine": "CHN"}
    if quantite is not None:
        demande["quantite"] = quantite
    reponse = client.post("/calcul", json=demande)
    assert reponse.status_code == 200
    npf = reponse.json()["npf"]
    return npf["etat"], {ligne["code"]: ligne for ligne in npf["lignes"]}


@pytest.mark.parametrize("code,quantite,montant", [
    ("22030019", 100, 5_810.0),    # bière : Rs 58.10 le litre
    ("27101950", 1000, 4_220.0),   # gasoil : Rs 4.22 le litre
    ("24022000", 10, 82_370.0),    # cigarettes : Rs 8,237 le millier
    ("24021090", 2, 56_894.0),     # cigares : Rs 28,447 le kg
    ("39233010", 500, 1_000.0),    # bouteilles plastiques contenant des marchandises : Rs 2 l'unité (FA 2026)
])
def test_accise_specifique_et_tva(client, code, quantite, montant):
    etat, lignes = _calcul(client, code, quantite)
    assert etat == "COMPLET"
    assert lignes["EXC"]["montant"] == pytest.approx(montant)
    autres = sum(lignes[c]["montant"] for c in lignes if c != "TVA")
    assert lignes["TVA"]["base"] == pytest.approx(10_000 + autres)


@pytest.mark.parametrize("code,motif", [
    ("22030011", "canette"),          # bière en canette : + Rs 2 par canette
    ("22083010", "alcool pur"),       # whisky : par litre d'alcool pur
    ("22029910", "teneur en sucre"),  # boissons sucrées : 15 cents le gramme de sucre
])
def test_accise_non_liquidable_motivee(code, motif):
    with open(os.path.join(RACINE, "backend", "socle", "MUS.json"), encoding="utf-8") as f:
        droits = json.load(f)["positions"][code]["droits"]
    exc = next(d for d in droits if d["code"] == "EXC")
    assert exc.get("taux") is None and not exc.get("specifique")
    assert motif in exc["note"]
