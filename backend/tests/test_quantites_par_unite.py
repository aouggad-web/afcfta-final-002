"""Une quantité par unité : chaque droit spécifique sur la quantité de SON unité.

Une position peut porter deux droits spécifiques dans deux unités — Tunisie
0102.29 : D.S.V. par tête, prélèvement viande au kilo ; chocolat tunisien :
poids net et litres d'alcool contenu. Une quantité unique ne peut servir les
deux ; une quantité par unité (`quantites`) le peut, et la position se
liquide alors entière.
"""

import importlib.util
import json
import os
import sys

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from services.calcul import MANQUE_QUANTITE, MANQUE_UNITES, calculer

SOCLE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "socle")


def _specifique(code, montant, unite, assiette="xQTE"):
    return {
        "code": code,
        "famille": "accise",
        "taux": None,
        "specifique": {"montant": montant, "unite_quantite": unite, "brut": f"{montant} dinars"},
        "assiette": assiette,
    }


BOVINS = {
    "droits": [
        {"code": "DD", "famille": "douane", "taux": 10.0, "assiette": "CIF"},
        _specifique("DSV", 0.1, "nombre"),
        _specifique("PV", 0.2, "kg"),
        {"code": "TVA", "famille": "tva", "taux": 19.0, "assiette": "CIF+TOUS_SAUF_TVA"},
    ]
}


def _ligne(r, code):
    return next(l for l in r["npf"]["lignes"] if l["code"] == code)


def test_chaque_droit_prend_la_quantite_de_son_unite():
    r = calculer(BOVINS, 1000, quantites={"nombre": 3, "kg": 1500})
    assert _ligne(r, "DSV")["montant"] == pytest.approx(0.3)
    assert _ligne(r, "PV")["montant"] == pytest.approx(300.0)
    assert _ligne(r, "TVA")["montant"] == pytest.approx((1000 + 100 + 0.3 + 300) * 0.19)
    assert r["npf"]["etat"] == "COMPLET"


def test_une_unite_absente_reste_reclamee():
    r = calculer(BOVINS, 1000, quantites={"kg": 1500})
    assert _ligne(r, "PV")["montant"] == pytest.approx(300.0)
    assert _ligne(r, "DSV")["statut"] == MANQUE_QUANTITE
    assert r["npf"]["etat"] == "PARTIEL"


def test_la_quantite_unique_ne_sert_toujours_pas_deux_unites():
    r = calculer(BOVINS, 1000, quantite=3)
    assert {_ligne(r, c)["statut"] for c in ("DSV", "PV")} == {MANQUE_UNITES}


def test_la_quantite_complementaire_se_saisit_aussi_par_unite():
    chocolat = {
        "droits": [
            _specifique("PN", 0.05, "kg"),
            _specifique("DCALC", 5.7, "litre d'alcool contenu", assiette="xQTC"),
        ]
    }
    r = calculer(chocolat, 1000, quantites={"kg": 50, "litre d'alcool contenu": 2})
    assert _ligne(r, "PN")["montant"] == pytest.approx(2.5)
    assert _ligne(r, "DCALC")["montant"] == pytest.approx(11.4)


def test_un_droit_compose_prend_la_quantite_de_son_unite():
    """« 40% or 240c/kg » : la composante spécifique au kilo saisi."""
    compose = {
        "droits": [
            {
                "code": "DD",
                "famille": "douane",
                "taux": 40.0,
                "specifique": {"montant": 2.4, "unite_quantite": "kg", "brut": "240c/kg"},
                "compose": True,
                "regle_composee": "LE_PLUS_ELEVE",
                "assiette": "CIF",
            }
        ]
    }
    r = calculer(compose, 1000, quantites={"kg": 500})
    dd = _ligne(r, "DD")
    assert dd["montant"] == pytest.approx(1200.0) and dd["composante_retenue"] == "specifique"
    assert dd["unite_quantite"] == "kg"


@pytest.fixture
def client():
    chemin = os.path.join(os.path.dirname(SOCLE), "routes", "calcul.py")
    spec = importlib.util.spec_from_file_location("routes_calcul_qpu_test", chemin)
    module = importlib.util.module_from_spec(spec)
    sys.modules["routes_calcul_qpu_test"] = module
    spec.loader.exec_module(module)
    app = FastAPI()
    app.include_router(module.router)
    return TestClient(app)


@pytest.mark.parametrize("valeur", [0, -1])
def test_l_api_refuse_une_quantite_nulle_par_unite(client, valeur):
    corps = {"destination": "TUN", "code_sh": "0102290001", "valeur_cif": 1000, "quantites": {"kg": valeur}}
    assert client.post("/calcul", json=corps).status_code == 422


@pytest.mark.skipif(not os.path.exists(os.path.join(SOCLE, "TUN.json")), reason="socle absent (gitignoré)")
def test_la_position_tunisienne_a_deux_unites_se_liquide_entiere():
    with open(os.path.join(SOCLE, "TUN.json"), encoding="utf-8") as f:
        positions = json.load(f)["positions"]
    code = next(
        c
        for c, p in positions.items()
        if c.startswith("010229")
        and len(
            {
                d["specifique"]["unite_quantite"]
                for d in p["droits"]
                if isinstance(d.get("specifique"), dict) and d["specifique"].get("unite_quantite")
            }
        )
        > 1
    )
    unites = {
        d["specifique"]["unite_quantite"]
        for d in positions[code]["droits"]
        if isinstance(d.get("specifique"), dict) and d["specifique"].get("unite_quantite")
    }
    r = calculer(positions[code], 1000, devise_cif="TND", quantites={u: 2 for u in unites})
    assert all(l.get("statut") != MANQUE_UNITES for l in r["npf"]["lignes"])
    assert all(
        l.get("statut") == "CALCULE"
        for l in r["npf"]["lignes"]
        if l.get("assiette") in ("xQTE", "xQTC")
    )
