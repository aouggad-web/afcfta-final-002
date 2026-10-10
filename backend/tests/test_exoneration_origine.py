"""Prélèvements communautaires retirés selon l'origine déclarée : PCS (UEMOA,
acte additionnel 04/96, art. 17), PCC/ECOWAS Levy (protocole CEDEAO A/P1/7/96,
art. 4), PUA/AU Import Levy (décision Assembly/AU/Dec.605(XXVII)).
Fiche : ORIGINE_prelevements_communautaires_2026-10-10.json."""

import os
import sys

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from services import exoneration_origine, socle

SOCLE_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "socle")
besoin_socle = pytest.mark.skipif(
    not os.path.exists(os.path.join(SOCLE_DIR, "GHA.json")), reason="socle absent (gitignoré)"
)

POSITION = {
    "droits": [
        {"code": "DD", "taux": 10.0},
        {"code": "PCS", "taux": 0.8, "exoneration_origine": "UEMOA"},
        {"code": "PCC", "taux": 0.5, "exoneration_origine": "CEDEAO"},
        {"code": "PUA", "taux": 0.2, "exoneration_origine": "UA"},
    ]
}


def _codes(origine):
    position, retires = exoneration_origine.appliquer(POSITION, origine)
    return [d["code"] for d in position["droits"]], [r["code"] for r in retires]


def test_origine_uemoa_exoneree_des_trois():
    assert _codes("sen") == (["DD"], ["PCS", "PCC", "PUA"])


def test_origine_cedeao_hors_uemoa_paie_le_pcs():
    assert _codes("GHA") == (["DD", "PCS"], ["PCC", "PUA"])


def test_origine_africaine_hors_cedeao_paie_pcs_et_pcc():
    assert _codes("KEN") == (["DD", "PCS", "PCC"], ["PUA"])


def test_pays_tiers_ou_origine_absente_paient_tout():
    assert _codes("CHN") == (["DD", "PCS", "PCC", "PUA"], [])
    assert _codes(None) == (["DD", "PCS", "PCC", "PUA"], [])


@pytest.fixture
def client():
    import importlib.util

    chemin = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "routes", "calcul.py")
    spec = importlib.util.spec_from_file_location("routes_calcul_exo", chemin)
    module = importlib.util.module_from_spec(spec)
    sys.modules["routes_calcul_exo"] = module
    spec.loader.exec_module(module)
    app = FastAPI()
    app.include_router(module.router)
    socle.vider_cache()
    yield TestClient(app)
    socle.vider_cache()


@besoin_socle
def test_route_ghana_origine_cedeao(client):
    """0101.21 vers le Ghana, origine Nigeria : ECOWAS et AU retirés, base de la TVA 1 077,5."""
    corps = client.post(
        "/calcul", json={"destination": "GHA", "code_sh": "0101210000", "valeur_cif": 1000, "origine": "NGA"}
    ).json()
    assert {e["code"] for e in corps["exonerations_origine"]} == {"CEDEAO", "PUA"}
    lignes = {l["code"]: l for l in corps["npf"]["lignes"]}
    assert "CEDEAO" not in lignes and "PUA" not in lignes
    assert lignes["TVA"]["base"] == 1077.5
