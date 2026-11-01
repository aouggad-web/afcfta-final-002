"""Guinée équatoriale : CCI de la CEEAC et prélèvement OHADA.
Fiche : GNQ_prelevements_importation_2026-10-31.json."""

import json
import os

import pytest

from services import exoneration_origine
from services.calcul import calculer

SOCLE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "socle", "GNQ.json")
pytestmark = pytest.mark.skipif(not os.path.exists(SOCLE), reason="socle absent (gitignoré)")


@pytest.fixture(scope="module")
def positions():
    with open(SOCLE, encoding="utf-8") as f:
        return json.load(f)["positions"]


def test_tci_cci_et_ohada_font_un_virgule_quarante_cinq_pour_cent(positions):
    r = calculer(positions["01011010"], 1000, devise_position="XAF", devise_cif="XAF")
    lignes = {l["code"]: l for l in r["npf"]["lignes"]}
    assert (lignes["TCI"]["montant"], lignes["CCI"]["montant"], lignes["OHADA"]["montant"]) == (10.0, 4.0, 0.5)
    assert lignes["TVA"]["base"] == 1000.0 + lignes["DD"]["montant"]


def test_produits_pharmaceutiques_sans_prelevement_ohada(positions):
    assert next(d for d in positions["30049000"]["droits"] if d["code"] == "OHADA")["taux"] == 0.0


@pytest.mark.parametrize(
    "origine, retires",
    [("CMR", {"TCI", "CCI", "OHADA"}), ("AGO", {"CCI", "OHADA"}), ("SEN", {"OHADA"}), ("FRA", set())],
)
def test_les_prelevements_suivent_l_origine(positions, origine, retires):
    _, exonerations = exoneration_origine.appliquer(positions["01011010"], origine)
    assert {e["code"] for e in exonerations} == retires
