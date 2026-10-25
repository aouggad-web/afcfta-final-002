"""Nigéria : TVA 7,5 % sur CIF + droits, IAT et accise, hors TVA (Nigeria Tax Act
2025, s.150). Fiche : NGA_assiette_TVA_2026-10-07.json."""

import json
import os

import pytest

from services.calcul import COMPLET, calculer

SOCLE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "socle", "NGA.json")
pytestmark = pytest.mark.skipif(not os.path.exists(SOCLE), reason="socle absent (gitignoré)")


@pytest.fixture(scope="module")
def positions():
    with open(SOCLE, encoding="utf-8") as f:
        return json.load(f)["positions"]


def test_vin_tva_sur_cif_droit_et_accise(positions):
    """2204.21 : DD 20 %, accise 20 % sur 1 000, sans IAT en 2026 ; TVA sur 1 400."""
    r = calculer(positions["2204210000"], 1000, devise_position="NGN")
    lignes = {l["code"]: l for l in r["npf"]["lignes"]}
    assert (lignes["TVA"]["base"], lignes["TVA"]["montant"]) == (1400.0, 105.0)
    assert r["npf"]["etat"] == COMPLET


def test_margarine_tva_sur_cif_droit_et_iat(positions):
    """1517.10 : DD 20 %, IAT 20 % sur 1 000 ; TVA sur 1 400."""
    r = calculer(positions["1517100000"], 1000, devise_position="NGN")
    lignes = {l["code"]: l for l in r["npf"]["lignes"]}
    assert (lignes["TVA"]["base"], lignes["TVA"]["montant"]) == (1400.0, 105.0)


def test_tva_non_servie_si_une_taxe_de_son_assiette_est_vide(positions):
    """Une accise sans taux : la TVA ne se calcule pas sur une assiette amputée."""
    for code, position in positions.items():
        taux = {l["code"]: l.get("taux") for l in position["droits"]}
        if taux.get("TVA") is not None and taux.get("EXC") is None:
            break
    r = calculer(position, 1000, devise_position="NGN")
    assert r["npf"]["etat"] != COMPLET, code
