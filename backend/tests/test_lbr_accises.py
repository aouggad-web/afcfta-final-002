"""Libéria : accise à l'importation (Liberia Revenue Code, ch. 11 et
Schedule 1, modifiés par le Tax Amendment Act de décembre 2025). Fiche :
LBR_accises_2026-10-25.json."""

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
    not os.path.exists(os.path.join(RACINE, "backend", "socle", "LBR.json")), reason="socle absent (gitignoré)"
)


@pytest.fixture(autouse=True)
def _cache_propre():
    socle.vider_cache()
    yield
    socle.vider_cache()


@pytest.fixture(scope="module")
def client():
    chemin = os.path.join(RACINE, "backend", "routes", "calcul.py")
    spec = importlib.util.spec_from_file_location("routes_calcul_lbr_accises_test", chemin)
    module = importlib.util.module_from_spec(spec)
    sys.modules["routes_calcul_lbr_accises_test"] = module
    spec.loader.exec_module(module)
    app = FastAPI()
    app.include_router(module.router)
    return TestClient(app)


def _calcul(client, code, quantite, devise="USD", taux_de_change=None):
    demande = {"destination": "LBR", "code_sh": code, "valeur_cif": 11000, "valeur_fob": 10000,
               "devise_cif": devise, "origine": "CHN", "quantite": quantite}
    if taux_de_change is not None:
        demande["taux_de_change"] = taux_de_change
    reponse = client.post("/calcul", json=demande)
    assert reponse.status_code == 200
    npf = reponse.json()["npf"]
    return npf["etat"], {ligne["code"]: ligne for ligne in npf["lignes"]}


@pytest.mark.parametrize("code,quantite,montant", [
    ("2203001000", 1000, 1_000.0),  # bière, 1,00 $/l
    ("2208300000", 100, 300.0),     # whisky, 3,00 $/l
    ("2201101000", 1000, 150.0),    # eau minérale, 0,15 $/l
    ("2202999000", 1000, 450.0),    # boissons non alcooliques, 0,45 $/l
    ("2402200000", 500, 250.0),     # cigarettes, 0,50 $ le paquet de 20
    ("2402900000", 1000, 250.0),    # autres, 0,25 $ par unité
    ("2401100000", 10, 250.0),      # tabac non fabriqué, 25 $/kg
])
def test_accise_specifique_en_dollars_et_dans_la_gst(client, code, quantite, montant):
    """s.1004(d)(3) : la valeur imposable de la GST comprend l'accise."""
    etat, lignes = _calcul(client, code, quantite)
    assert etat == "COMPLET"
    assert lignes["EXC"]["montant"] == pytest.approx(montant)
    autres = sum(lignes[c]["montant"] for c in lignes if c != "TVA")
    assert lignes["TVA"]["base"] == pytest.approx(11_000 + autres)


def test_valeur_en_dollars_liberiens_avec_taux_de_change(client):
    _, lignes = _calcul(client, "2203001000", 1000, devise="LRD")
    assert lignes["EXC"]["statut"] == "TAUX_DE_CHANGE_REQUIS"
    _, lignes = _calcul(client, "2203001000", 1000, devise="LRD", taux_de_change=190)
    assert lignes["EXC"]["montant"] == pytest.approx(190_000.0)


@pytest.mark.parametrize("code,taux", [
    ("3304990000", 20.0),  # cosmétiques
    ("1701991000", 5.0),   # sucre
    ("7113110000", 10.0),  # bijouterie
    ("9504500000", 30.0),  # consoles de jeux
    ("9614000000", 50.0),  # pipes
])
def test_accise_ad_valorem_sur_cif_et_droits(client, code, taux):
    """s.1110(c) : CIF, droit de douane, redevances et prélèvement CEDEAO."""
    _, lignes = _calcul(client, code, 1)
    base = 11_000 + sum(lignes[c]["montant"] for c in ("DD", "PCC", "CUF") if c in lignes)
    assert lignes["EXC"]["base"] == pytest.approx(base)
    assert lignes["EXC"]["montant"] == pytest.approx(base * taux / 100)


def test_hors_du_perimetre():
    """Dentifrice et huiles essentielles hors des cosmétiques ; véhicules de
    luxe (condition de valeur unitaire) non repris."""
    with open(os.path.join(RACINE, "backend", "socle", "LBR.json"), encoding="utf-8") as f:
        positions = json.load(f)["positions"]
    for code in ("3306100000", "3301120000", "8703230000"):
        position = next((p for c, p in positions.items() if c.startswith(code[:6])), None)
        assert position is not None
        assert not any(d["code"] == "EXC" for d in position["droits"])
