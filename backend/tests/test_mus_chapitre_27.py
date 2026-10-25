"""Maurice : chapitre 27 du tarif intégré (colonne « Levy ») et MID levy (Excise
Act s.3A, First Schedule Part II). Fiche : MUS_mid_levy_2026-10-25.json."""

import importlib.util
import json
import os
import sys

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from services import socle

RACINE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
CRAWL = os.path.join(RACINE, "backend", "data", "crawled", "MUS_tariffs.json")

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
    spec = importlib.util.spec_from_file_location("routes_calcul_mus_ch27_test", chemin)
    module = importlib.util.module_from_spec(spec)
    sys.modules["routes_calcul_mus_ch27_test"] = module
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


def test_la_colonne_levy_ne_decale_plus_la_tva_ni_les_preferences():
    """Page 156 : « 0 | 0 | 30 cents per kg | 15 | 0 … » sur 2701.11.00."""
    with open(CRAWL, encoding="utf-8") as f:
        positions = {p["national_code"]: p for p in json.load(f)["sub_positions"]}
    anthracite = positions["27011100"]
    taxes = {t["code"]: t["raw_value"] for t in anthracite["taxes"]}
    assert taxes == {"DD": "0", "EXC": "0", "MID": "30 cents per kg", "TVA": "15"}
    assert {r["regime"]: r["rate_pct"] for r in anthracite["preferential_rates"]}["COMESA_I"] == 0.0
    white_spirit = {t["code"]: t["rate_pct"] for t in positions["27101210"]["taxes"]}
    assert white_spirit["TVA"] == 15.0


def test_mid_levy_dans_l_assiette_de_la_tva(client):
    """Charbon : 30 cents le kilo, TVA à 15 % sur CIF + droit + accise + MID levy."""
    etat, lignes = _calcul(client, "27011100", quantite=1000)
    assert etat == "COMPLET"
    assert lignes["MID"]["montant"] == pytest.approx(300.0)
    assert lignes["TVA"]["montant"] == pytest.approx((10_000 + 300) * 0.15)


def test_chapitre_27_porte_sa_tva(client):
    etat, lignes = _calcul(client, "27101210")
    assert etat == "COMPLET"
    assert lignes["TVA"]["montant"] == pytest.approx(1_500.0)
