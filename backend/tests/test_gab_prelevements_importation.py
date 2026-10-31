"""Gabon : CCI de la CEEAC, prélèvement OHADA, contribution UA et CSS.
Fiche : GAB_prelevements_importation_2026-10-29.json."""

import json
import os

import pytest

from services import exoneration_origine
from services.calcul import COMPLET, PARTIEL, calculer

SOCLE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "socle", "GAB.json")
pytestmark = pytest.mark.skipif(not os.path.exists(SOCLE), reason="socle absent (gitignoré)")


@pytest.fixture(scope="module")
def positions():
    with open(SOCLE, encoding="utf-8") as f:
        return json.load(f)["positions"]


def _lignes(position, origine=None):
    position, _ = exoneration_origine.appliquer(position, origine)
    r = calculer(position, 1000, devise_position="XAF", devise_cif="XAF")
    return r["npf"]["etat"], {l["code"]: l for l in r["npf"]["lignes"]}


def test_un_cheval_paie_cci_ohada_et_css(positions):
    """CIF 1 000 : DD 5 % = 50 ; TCI 10 ; CIA 2 ; CCI 0,4 % = 4 ; OHADA 0,05 % = 0,5 ;
    CSS 1 % et TVA 18 % sur CIF + DD = 1 050."""
    etat, lignes = _lignes(positions["01011010"])
    assert (lignes["CCI"]["montant"], lignes["OHADA"]["montant"]) == (4.0, 0.5)
    assert (lignes["CSS"]["base"], lignes["CSS"]["montant"]) == (1050.0, 10.5)
    assert lignes["TVA"]["base"] == 1050.0 and etat == COMPLET


def test_la_css_s_assied_sur_l_accise_comme_la_tva(positions):
    """Bière : la CSS a l'assiette de la TVA (valeur + DD + DA), qui ne la comprend pas."""
    position, _ = exoneration_origine.appliquer(positions["22030010"], None)
    r = calculer(position, 1000, quantites={"litre": 100}, devise_position="XAF", devise_cif="XAF")
    lignes = {l["code"]: l for l in r["npf"]["lignes"]}
    assert lignes["CSS"]["base"] == lignes["TVA"]["base"] == 1300.0 + lignes["DA"]["montant"]


@pytest.mark.parametrize(
    "origine, retires",
    [("CMR", {"CIA", "CCI", "OHADA", "TCI"}), ("AGO", {"CIA", "CCI", "OHADA"}), ("RWA", {"CIA"}), ("SEN", {"CIA", "OHADA"}),
     ("NGA", {"CIA"}), ("FRA", set())],
)
def test_les_prelevements_communautaires_suivent_l_origine(positions, origine, retires):
    _, exonerations = exoneration_origine.appliquer(positions["01011010"], origine)
    assert {e["code"] for e in exonerations} == retires


def test_les_medicaments_sont_exoneres_de_css(positions):
    etat, lignes = _lignes(positions["30049000"])
    assert lignes["CSS"]["montant"] == 0.0 and etat == COMPLET


def test_les_engrais_restent_sans_css_faute_de_connaitre_l_usage(positions):
    etat, lignes = _lignes(positions["31021000"])
    assert lignes["CSS"]["statut"] == "TAUX_INDISPONIBLE" and etat == PARTIEL


def test_chaque_position_porte_les_quatre_prelevements(positions):
    for code, position in positions.items():
        codes = [d["code"] for d in position["droits"]]
        assert {"CIA", "CCI", "OHADA", "CSS"} <= set(codes), code
        assert codes.index("CSS") > codes.index("DA") if "DA" in codes else True
        assert codes.index("CSS") < codes.index("TVA"), code
