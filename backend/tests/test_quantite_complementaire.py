"""Quantité complémentaire (`xQTC`) : une seconde quantité, jamais la première.

Le droit de consommation tunisien DC/ALC s'assied sur les litres d'alcool que
contient la marchandise — 570 D/hl et 16 D/hl du tableau annexé à la loi
n° 88-62 (loi n° 2017-66, art. 45), servis à 5,7 et 0,16 dinars sur « QCI ».
Un chocolat se déclare pourtant en kilos et un vin muté en bouteilles : liquider
ce droit sur la quantité tarifaire multiplierait 5,7 D par des kilos.
"""

import importlib.util
import json
import os
import sys

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from services.calcul import (
    MANQUE_QUANTITE_COMPLEMENTAIRE,
    MANQUE_UNITES,
    calculer,
)

SOCLE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "socle")

DCALC = {
    "code": "DCALC",
    "famille": "accise",
    "taux": None,
    "specifique": {"montant": 5.7, "unite_quantite": "litre d'alcool contenu", "brut": "5.7 dinars"},
    "assiette": "xQTC",
}
VIN_MUTE = {
    "droits": [
        {"code": "DD", "famille": "douane", "taux": 50.0, "assiette": "CIF"},
        {
            "code": "DCVBBA",
            "famille": "accise",
            "taux": None,
            "specifique": {"montant": 7.5, "unite_quantite": "bouteille", "brut": "7.5 dinars"},
            "assiette": "xQTE",
        },
        DCALC,
        {"code": "TVA", "famille": "tva", "taux": 19.0, "assiette": "CIF+TOUS_SAUF_TVA"},
    ]
}


def _ligne(r, code):
    return next(l for l in r["npf"]["lignes"] if l["code"] == code)


def test_sans_quantite_complementaire_le_droit_la_reclame():
    r = calculer(VIN_MUTE, 1000, quantite=10)
    dcalc = _ligne(r, "DCALC")
    assert dcalc["statut"] == MANQUE_QUANTITE_COMPLEMENTAIRE and dcalc["montant"] is None
    assert dcalc["unite_quantite"] == "litre d'alcool contenu"
    assert r["npf"]["etat"] == "PARTIEL"


def test_la_quantite_tarifaire_ne_sert_jamais_la_complementaire():
    """Dix bouteilles ne sont pas dix litres d'alcool."""
    r = calculer({"droits": [DCALC]}, 1000, quantite=10)
    assert _ligne(r, "DCALC")["montant"] is None


def test_le_droit_se_liquide_sur_la_quantite_complementaire():
    r = calculer(VIN_MUTE, 1000, quantite=10, quantite_complementaire=1.5)
    assert _ligne(r, "DCALC")["montant"] == pytest.approx(8.55)
    assert _ligne(r, "DCVBBA")["montant"] == pytest.approx(75.0)
    # La TVA s'assied sur tous les droits, DC/ALC compris.
    assert _ligne(r, "TVA")["montant"] == pytest.approx((1000 + 500 + 75 + 8.55) * 0.19)
    assert r["npf"]["etat"] == "COMPLET"


def test_les_deux_unites_ne_se_disputent_pas():
    """Bouteille (quantité tarifaire) et litre d'alcool (complémentaire) sont
    saisis à part : la position n'est pas « à unités multiples »."""
    r = calculer(VIN_MUTE, 1000, quantite=10, quantite_complementaire=1.5)
    assert all(l.get("statut") != MANQUE_UNITES for l in r["npf"]["lignes"])


@pytest.fixture
def client():
    chemin = os.path.join(os.path.dirname(SOCLE), "routes", "calcul.py")
    spec = importlib.util.spec_from_file_location("routes_calcul_qtc_test", chemin)
    module = importlib.util.module_from_spec(spec)
    sys.modules["routes_calcul_qtc_test"] = module
    spec.loader.exec_module(module)
    app = FastAPI()
    app.include_router(module.router)
    return TestClient(app)


@pytest.mark.parametrize("valeur", [0, -1])
def test_l_api_refuse_une_quantite_complementaire_nulle(client, valeur):
    corps = {
        "destination": "TUN",
        "code_sh": "1806201001",
        "valeur_cif": 1000,
        "quantite_complementaire": valeur,
    }
    assert client.post("/calcul", json=corps).status_code == 422


besoin_socle_tun = pytest.mark.skipif(
    not os.path.exists(os.path.join(SOCLE, "TUN.json")), reason="socle absent (gitignoré)"
)


@pytest.fixture(scope="module")
def positions():
    with open(os.path.join(SOCLE, "TUN.json"), encoding="utf-8") as f:
        return json.load(f)["positions"]


@besoin_socle_tun
def test_seuls_les_dc_alc_etablis_passent_en_quantite_complementaire(positions):
    xqtc, qci = set(), set()
    for p in positions.values():
        for d in p["droits"]:
            cle = (d["code_source"], (d.get("specifique") or {}).get("montant"))
            if d.get("assiette") == "xQTC":
                assert d["specifique"]["unite_quantite"] == "litre d'alcool contenu"
                xqtc.add(cle)
            elif str(d.get("assiette_non_traduite", "")).startswith("quantité complémentaire"):
                qci.add(cle)
    assert xqtc == {("DC/ALC", 5.7), ("DC/ALC", 0.16)}
    # Sans texte établi : DC/ALC 0,06, surtaxe 0,8, DCVBBA 48 restent non traduits.
    assert {("DC/ALC", 0.06), ("DCS/ALC", 0.8), ("DCVBBA", 48.0)} <= qci


@besoin_socle_tun
def test_l_alcool_ethylique_reste_a_l_hectolitre(positions):
    """22.07 : 570 D sur « QCS » HECTOLITRE, quantité tarifaire."""
    dcalc = next(d for d in positions["2207100011"]["droits"] if d["code_source"] == "DC/ALC")
    assert dcalc["assiette"] == "xQTE" and dcalc["specifique"]["unite_quantite"] == "hectolitre"
