"""Ghana : ECOWAS Levy, AU Import Levy, EXIM Levy et Special Import Levy sur la
valeur c.a.f. (MoFEP/IFS 2026, tableau 3.9 ; Act 911 s. 29) ; TVA, NHIL et
GETFund sur une même base, valeur en douane + droits et taxes à l'importation
autres que la TVA (VAT Act 2025, Act 1151, s. 45). Fiche : GHA_prelevements_TVA_2026-10-10.json."""

import json
import os

import pytest

from services.calcul import calculer

SOCLE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "socle", "GHA.json")

pytestmark = pytest.mark.skipif(not os.path.exists(SOCLE), reason="socle absent (gitignoré)")


@pytest.fixture(scope="module")
def positions():
    with open(SOCLE, encoding="utf-8") as f:
        return json.load(f)["positions"]


def _calcul(position):
    r = calculer(position, 1000, devise_cif="GHS")["npf"]
    return r["etat"], {l["code"]: l for l in r["lignes"]}


def test_prelevements_et_base_commune_de_la_tva(positions):
    """0101.21 : DD 5 % : 50 ; ECOWAS 5 ; AU 2 ; EXIM 7,5 ; SIL 20 ; base 1 084,5."""
    etat, lignes = _calcul(positions["0101210000"])
    assert etat == "COMPLET"
    assert [lignes[c]["montant"] for c in ("DD", "CEDEAO", "PUA", "EXIM", "SIL")] == [50.0, 5.0, 2.0, 7.5, 20.0]
    for c in ("TVA", "NHIL", "GETFUND"):
        assert lignes[c]["base"] == 1084.5
    assert lignes["TVA"]["montant"] == pytest.approx(162.675)


def test_produits_petroliers_hors_exim_et_sil(positions):
    code = next(k for k in positions if k.startswith("2710"))
    codes = {d["code"] for d in positions[code]["droits"]}
    assert "EXIM" not in codes and "SIL" not in codes and "CEDEAO" in codes


def test_engrais_hors_sil(positions):
    code = next(k for k in positions if k.startswith("31"))
    codes = {d["code"] for d in positions[code]["droits"]}
    assert "SIL" not in codes and "EXIM" in codes


def test_machines_sans_taux_de_sil(positions):
    """Machines et équipements exclus du SIL sans liste : taux non établi, TVA indisponible."""
    code = next(k for k in positions if k.startswith("847130"))
    etat, lignes = _calcul(positions[code])
    assert lignes["SIL"]["taux_pct"] is None
    assert lignes["TVA"]["montant"] is None and etat != "COMPLET"
