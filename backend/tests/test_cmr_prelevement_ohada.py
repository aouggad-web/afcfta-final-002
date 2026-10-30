"""Cameroun : prélèvement OHADA, au taux du rapport de l'OMC ; la CCI n'est pas
servie. Fiche : CMR_prelevement_ohada_2026-10-30.json."""

import json
import os

import pytest

from services import exoneration_origine
from services.calcul import calculer

SOCLE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "socle", "CMR.json")
pytestmark = pytest.mark.skipif(not os.path.exists(SOCLE), reason="socle absent (gitignoré)")


@pytest.fixture(scope="module")
def positions():
    with open(SOCLE, encoding="utf-8") as f:
        return json.load(f)["positions"]


def test_le_prelevement_ohada_est_hors_de_la_base_de_la_tva(positions):
    r = calculer(positions["01011010"], 1000, devise_position="XAF", devise_cif="XAF")
    lignes = {l["code"]: l for l in r["npf"]["lignes"]}
    assert lignes["OHADA"]["montant"] == 0.5 and "CCI" not in lignes
    assert lignes["TVA"]["base"] == 1000.0 + lignes["DD"]["montant"]


@pytest.mark.parametrize("origine, retires", [("GAB", {"TCI", "OHADA"}), ("SEN", {"OHADA"}), ("AGO", set()),
                                              ("FRA", set())])
def test_le_prelevement_ohada_suit_l_origine(positions, origine, retires):
    _, exonerations = exoneration_origine.appliquer(positions["01011010"], origine)
    assert {e["code"] for e in exonerations} == retires
