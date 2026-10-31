"""Centrafrique : les neuf prélèvements de la loi de finances 2026 (art. 16),
aux taux du rapport de l'OMC. Fiche : CAF_prelevements_importation_2026-10-30.json."""

import json
import os

import pytest

from services import exoneration_origine
from services.calcul import COMPLET, calculer

SOCLE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "socle", "CAF.json")
pytestmark = pytest.mark.skipif(not os.path.exists(SOCLE), reason="socle absent (gitignoré)")


@pytest.fixture(scope="module")
def positions():
    with open(SOCLE, encoding="utf-8") as f:
        return json.load(f)["positions"]


def _lignes(position, **kw):
    r = calculer(position, 1000, devise_position="XAF", devise_cif="XAF", **kw)
    return r["npf"]["etat"], {l["code"]: l for l in r["npf"]["lignes"]}


def test_un_cheval_paie_les_neuf_prelevements(positions):
    """CIF 1 000 : TCI 10, TUA 2, CCI 4, OHADA 0,5, COMIFAC 1, REIF 5, RDS, RGS et RCCAC 2,5 chacune."""
    etat, lignes = _lignes(positions["01011010"])
    montants = {code: lignes[code]["montant"] for code in
                ("TCI", "TUA", "CCI", "OHADA", "COMIFAC", "REIF", "RDS", "RGS", "RCCAC")}
    assert montants == {"TCI": 10.0, "TUA": 2.0, "CCI": 4.0, "OHADA": 0.5, "COMIFAC": 1.0, "REIF": 5.0,
                        "RDS": 2.5, "RGS": 2.5, "RCCAC": 2.5}
    assert "RS" not in lignes and etat == COMPLET


def test_ni_l_accise_ni_la_tva_ne_s_assoient_sur_ces_prelevements(positions):
    _, lignes = _lignes(positions["33030000"])
    assert lignes["DA"]["base"] == 1000.0 + lignes["DD"]["montant"]
    assert lignes["TVA"]["base"] == lignes["DA"]["base"] + lignes["DA"]["montant"]


@pytest.mark.parametrize(
    "origine, retires",
    [("CMR", {"TCI", "CCI", "OHADA", "TUA"}), ("AGO", {"CCI", "OHADA", "TUA"}), ("SEN", {"OHADA", "TUA"}),
     ("NGA", {"TUA"}), ("FRA", set())],
)
def test_les_prelevements_communautaires_suivent_l_origine(positions, origine, retires):
    _, exonerations = exoneration_origine.appliquer(positions["01011010"], origine)
    assert {e["code"] for e in exonerations} == retires
