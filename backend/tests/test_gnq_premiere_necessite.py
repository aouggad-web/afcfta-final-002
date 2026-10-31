"""Guinée équatoriale : droit de douane de 5 % et TVA de 0 % ou 5 % sur les biens de
première nécessité (loi n° 9/2025, budget 2026, art. 13).
Fiche : GNQ_premiere_necessite_2026-10-31.json."""

import json
import os

import pytest

SOCLE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "socle", "GNQ.json")
pytestmark = pytest.mark.skipif(not os.path.exists(SOCLE), reason="socle absent (gitignoré)")


@pytest.fixture(scope="module")
def positions():
    with open(SOCLE, encoding="utf-8") as f:
        return json.load(f)["positions"]


def _taux(position, code):
    (ligne,) = [d for d in position["droits"] if d["code"] == code]
    return ligne["taux"]


@pytest.mark.parametrize("code", ["03037100", "10063090", "11010010", "17019910", "04021000", "02071400",
                                  "15119000", "34022000", "48184000", "73170010", "72104100", "94055010"])
def test_premier_tableau_dd_5_et_tva_0(positions, code):
    assert _taux(positions[code], "DD") == 5.0
    assert _taux(positions[code], "TVA") == 0.0


@pytest.mark.parametrize("code", ["07019000", "08051000", "04061000", "16010000", "18050000", "25232900",
                                  "84678100", "31021000", "94042100", "72142000", "56081100"])
def test_second_tableau_dd_5_et_tva_5(positions, code):
    assert _taux(positions[code], "DD") == 5.0
    assert _taux(positions[code], "TVA") == 5.0


@pytest.mark.parametrize("code", ["82014000", "82013000", "22011000", "25010011", "38089110", "21022000"])
def test_positions_mixtes_sans_taux(positions, code):
    assert _taux(positions[code], "DD") is None
    assert _taux(positions[code], "TVA") is None


@pytest.mark.parametrize("code", ["19024000", "02061000", "25232100", "01011010"])
def test_hors_liste(positions, code):
    """Couscous, abats, ciment blanc, chevaux : hors de l'art. 13."""
    assert _taux(positions[code], "TVA") == 15.0


@pytest.mark.parametrize("code", ["30049000", "90183100", "37011000"])
def test_positions_exo_du_tarif_camerounais_sans_taux(positions, code):
    """Une ligne de TVA, sans taux : la loi générale fiscale n° 1/2024 n'a pas été lue."""
    assert _taux(positions[code], "TVA") is None


def test_chaque_position_porte_une_ligne_de_tva(positions):
    assert all(sum(d["code"] == "TVA" for d in p["droits"]) == 1 for p in positions.values())
