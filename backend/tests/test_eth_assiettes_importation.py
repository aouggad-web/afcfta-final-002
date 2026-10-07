"""Éthiopie : accise sur CIF + DD (Proclamation 1186/2020 art. 9) ; TVA sur CIF +
droits et accise (Proclamation 1341/2024 art. 27) ; surtaxe sur CIF + DD +
accise + TVA (Règlement 133/2007) ; WHR 3 % du CIF (Proclamation 979/2016
art. 85). Fiche : ETH_assiettes_importation_2026-10-07.json."""

import json
import os

import pytest

from services.calcul import COMPLET, calculer

SOCLE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "socle", "ETH.json")
pytestmark = pytest.mark.skipif(not os.path.exists(SOCLE), reason="socle absent (gitignoré)")


@pytest.fixture(scope="module")
def positions():
    with open(SOCLE, encoding="utf-8") as f:
        return json.load(f)["positions"]


def _lignes(position):
    r = calculer(position, 1000, devise_position="ETB")
    return r["npf"]["etat"], {l["code"]: l for l in r["npf"]["lignes"]}


def test_biere_accise_sur_cif_et_droit_puis_tva_et_whr(positions):
    """2203 : DD 35 %, accise 40 % sur 1 350, TVA sur 1 890, WHR 3 % de 1 000."""
    etat, lignes = _lignes(positions["22030000000"])
    assert (lignes["EXC"]["base"], lignes["EXC"]["montant"]) == (1350.0, 540.0)
    assert lignes["TVA"]["base"] == 1890.0
    assert (lignes["WHR"]["base"], lignes["WHR"]["montant"]) == (1000.0, 30.0)
    assert etat == COMPLET


def test_la_surtaxe_s_assoit_sur_la_tva(positions):
    etat, lignes = _lignes(positions["40159090000"])
    assert lignes["TVA"]["base"] == 1350.0 and lignes["SUR"]["base"] == 1552.5
