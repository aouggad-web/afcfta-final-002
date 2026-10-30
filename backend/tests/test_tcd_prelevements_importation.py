"""Tchad : CCI de la CEEAC et prélèvement OHADA, aux taux du rapport de l'OMC.
Fiche : TCD_prelevements_importation_2026-10-30.json."""

import json
import os

import pytest

from services import exoneration_origine
from services.calcul import calculer

SOCLE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "socle", "TCD.json")
pytestmark = pytest.mark.skipif(not os.path.exists(SOCLE), reason="socle absent (gitignoré)")


@pytest.fixture(scope="module")
def positions():
    with open(SOCLE, encoding="utf-8") as f:
        return json.load(f)["positions"]


def test_tci_cci_et_ohada_font_un_virgule_quarante_cinq_pour_cent(positions):
    """« Cumulées, ces différentes taxes s'élèvent à 1,45% de la valeur c.a.f. » (annexe Tchad, § 3.20)."""
    r = calculer(positions["01011010"], 1000, devise_position="XAF", devise_cif="XAF")
    lignes = {l["code"]: l for l in r["npf"]["lignes"]}
    assert (lignes["CCI"]["montant"], lignes["OHADA"]["montant"]) == (4.0, 0.5)
    assert lignes["TCI"]["montant"] + lignes["CCI"]["montant"] + lignes["OHADA"]["montant"] == 14.5
    assert lignes["TVA"]["base"] == 1000.0 + lignes["DD"]["montant"] + lignes["TCI"]["montant"]


@pytest.mark.parametrize(
    "origine, retires",
    [("CMR", {"TCI", "CCI", "OHADA", "PUA"}), ("AGO", {"CCI", "PUA"}), ("SEN", {"OHADA", "PUA"}),
     ("NGA", {"PUA"}), ("FRA", set())],
)
def test_cci_et_ohada_suivent_l_origine(positions, origine, retires):
    _, exonerations = exoneration_origine.appliquer(positions["01011010"], origine)
    assert {e["code"] for e in exonerations} == retires
