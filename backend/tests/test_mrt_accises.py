"""Mauritanie : droits d'accises à l'importation (CGI, art. 262, 263 et 266 bis,
rédaction de la loi de finances rectificative 2025 ; produits pétroliers de la loi
de finances rectificative 2026). Fiche : MRT_accises_2026-10-25.json."""

import importlib.util
import os
import sys

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from services import socle

RACINE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

pytestmark = pytest.mark.skipif(
    not os.path.exists(os.path.join(RACINE, "backend", "socle", "MRT.json")), reason="socle absent (gitignoré)"
)


@pytest.fixture(autouse=True)
def _cache_propre():
    socle.vider_cache()
    yield
    socle.vider_cache()


@pytest.fixture(scope="module")
def client():
    chemin = os.path.join(RACINE, "backend", "routes", "calcul.py")
    spec = importlib.util.spec_from_file_location("routes_calcul_mrt_accises_test", chemin)
    module = importlib.util.module_from_spec(spec)
    sys.modules["routes_calcul_mrt_accises_test"] = module
    spec.loader.exec_module(module)
    app = FastAPI()
    app.include_router(module.router)
    return TestClient(app)


def _calcul(client, code, quantite=None):
    demande = {"destination": "MRT", "code_sh": code, "valeur_cif": 10000, "valeur_fob": 9000,
               "devise_cif": "MRU", "origine": "CHN"}
    if quantite is not None:
        demande["quantite"] = quantite
    reponse = client.post("/calcul", json=demande)
    assert reponse.status_code == 200
    npf = reponse.json()["npf"]
    return npf["etat"], {ligne["code"]: ligne for ligne in npf["lignes"]}


@pytest.mark.parametrize("code,taux", [
    ("2203001000", 225.0),  # bière
    ("2204100000", 259.0),  # vins mousseux
    ("2208300000", 324.0),  # whiskies
    ("3923210000", 35.0),   # emballages plastiques
    ("2009111000", 30.0),   # jus de fruit
    ("1704900000", 20.0),   # confiseries
])
def test_accise_ad_valorem_sur_la_valeur_en_douane_et_les_droits(client, code, taux):
    """Art. 262 : valeur en douane majorée des droits et taxes d'entrée, PSC comprise
    (chapitres 21 à 98) ; la TVA comprend l'accise."""
    etat, lignes = _calcul(client, code)
    assert etat == "COMPLET"
    base = 10_000 + sum(lignes[c]["montant"] for c in ("DD", "RS", "PC", "PSC") if c in lignes)
    assert lignes["EXC"]["base"] == pytest.approx(base)
    assert lignes["EXC"]["montant"] == pytest.approx(base * taux / 100)
    autres = sum(lignes[c]["montant"] for c in lignes if c != "TVA")
    assert lignes["TVA"]["base"] == pytest.approx(10_000 + autres)


def test_cigarettes_cumul_et_taxe_cancer(client):
    """47 % + 1,6 MRU le paquet de 20 ; taxe de lutte contre le cancer à 10 % (art. 266 bis)."""
    etat, lignes = _calcul(client, "2402200000", quantite=500)
    assert etat == "COMPLET"
    assert lignes["TLC"]["montant"] == pytest.approx(1_000.0)
    base = 10_000 + sum(lignes[c]["montant"] for c in ("DD", "RS", "PC", "PSC", "TLC"))
    assert lignes["EXC"]["montant"] == pytest.approx(base * 0.47 + 500 * 1.6)


def test_produits_petroliers_loi_de_finances_rectificative_2026(client):
    """Super carburant : 9,98 MRU/l, DD 10 %, exempté de la RS."""
    etat, lignes = _calcul(client, "2710124000", quantite=1000)
    assert etat == "COMPLET"
    assert lignes["EXC"]["montant"] == pytest.approx(9_980.0)
    assert lignes["DD"]["montant"] == pytest.approx(1_000.0)
    assert lignes["RS"]["montant"] == pytest.approx(0.0)
