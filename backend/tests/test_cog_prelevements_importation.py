"""Congo : redevance informatique, CCI de la CEEAC et prélèvement OHADA selon
l'arrêté n° 5808. Fiche : COG_prelevements_importation_2026-10-30.json."""

import json
import os

import pytest

from services import exoneration_origine
from services.calcul import COMPLET, calculer

SOCLE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "socle", "COG.json")
pytestmark = pytest.mark.skipif(not os.path.exists(SOCLE), reason="socle absent (gitignoré)")


@pytest.fixture(scope="module")
def positions():
    with open(SOCLE, encoding="utf-8") as f:
        return json.load(f)["positions"]


def _lignes(position, **kw):
    r = calculer(position, 1000, devise_position="XAF", devise_cif="XAF", **kw)
    return r["npf"]["etat"], {l["code"]: l for l in r["npf"]["lignes"]}


def test_un_cheval_paie_la_redevance_informatique_et_la_cci(positions):
    """CIF 1 000 : RI 2 % = 20 ; CCI 0,4 % = 4 ; OHADA 0,05 % = 0,5 ; TVA sur CIF + DD."""
    etat, lignes = _lignes(positions["01011010"])
    assert (lignes["RI"]["montant"], lignes["CCI"]["montant"], lignes["OHADA"]["montant"]) == (20.0, 4.0, 0.5)
    assert lignes["TVA"]["base"] == 1050.0 and etat == COMPLET


def test_ni_l_accise_ni_la_tva_ne_s_assoient_sur_ces_prelevements(positions):
    _, lignes = _lignes(positions["22030010"], quantites={"litre": 100})
    assert lignes["DA"]["base"] == 1300.0
    assert lignes["TVA"]["base"] == 1300.0 + lignes["DA"]["montant"]


@pytest.mark.parametrize(
    "origine, retires",
    [("GAB", {"CCI", "OHADA", "TCI", "CIA"}), ("AGO", {"CCI", "OHADA", "CIA"}), ("SEN", {"OHADA", "CIA"}),
     ("RWA", {"CIA"}), ("NGA", {"CIA"}), ("FRA", set())],
)
def test_cci_et_ohada_suivent_l_origine(positions, origine, retires):
    _, exonerations = exoneration_origine.appliquer(positions["01011010"], origine)
    assert {e["code"] for e in exonerations} == retires


@pytest.mark.parametrize("code", ["30049000", "90189000", "90211000", "90221400"])
def test_produits_pharmaceutiques_et_materiel_medical_sans_prelevement_ohada(positions, code):
    _, lignes = _lignes(positions[code])
    assert lignes["OHADA"]["montant"] == 0.0 and lignes["RI"]["montant"] == 20.0


def test_les_biens_de_la_circulaire_0138_restent_soumis_a_la_redevance(positions):
    """« à l'exception de la redevance informatique et des taxes communautaires »."""
    _, lignes = _lignes(positions["02071400"])
    assert lignes["DD"]["montant"] == 50.0 and lignes["RI"]["montant"] == 20.0 and lignes["CCI"]["montant"] == 4.0


def test_chaque_position_porte_ri_et_cci_avant_l_accise(positions):
    for code, position in positions.items():
        codes = [d["code"] for d in position["droits"]]
        assert {"RI", "CCI", "OHADA"} <= set(codes), code
        if "DA" in codes:
            assert codes.index("RI") < codes.index("DA"), code
