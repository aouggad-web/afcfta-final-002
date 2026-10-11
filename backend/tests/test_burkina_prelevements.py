"""Burkina Faso : PCS 0,8 % ; taxes spécifiques du CGI (version consolidée de la
DGI) et de la LFI 2026 sur la valeur en douane majorée des droits et taxes de
douane ; TVA sur la valeur en douane et tous les droits et taxes de porte
(CGI art. 310, 4°). Fiche : BFA_prelevements_TVA_2026-10-11.json."""

import json
import os

import pytest

from services.calcul import calculer

SOCLE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "socle", "BFA.json")

pytestmark = pytest.mark.skipif(not os.path.exists(SOCLE), reason="socle absent (gitignoré)")


@pytest.fixture(scope="module")
def positions():
    with open(SOCLE, encoding="utf-8") as f:
        return json.load(f)["positions"]


def _calcul(position):
    r = calculer(position, 1000, devise_cif="XOF")["npf"]
    return r["etat"], {l["code"]: l for l in r["lignes"]}


def test_pcs_et_tva_sur_tous_les_droits_de_porte(positions):
    """0101.21 : DD 50 ; RS 10 ; PCS 0,8 % : 8 ; PC-AES 5 ; TVA sur 1 073."""
    etat, lignes = _calcul(positions["0101210000"])
    assert etat == "COMPLET"
    assert lignes["PCS"]["montant"] == 8.0
    assert lignes["TVA"]["base"] == 1073.0


def test_vin_taxe_sur_les_boissons(positions):
    """Art. 359 I.3 : vins 70 % sur 1 000 + 200 + 10 + 8 + 5 ; TVA sur cette base + la taxe."""
    etat, lignes = _calcul(positions["2204210000"])
    assert lignes["DA"]["taux_pct"] == 70.0 and lignes["DA"]["base"] == 1223.0
    assert lignes["TVA"]["base"] == pytest.approx(1223.0 + 856.1)


def test_taux_des_taxes_specifiques(positions):
    taux = {
        code: next(d["taux"] for d in positions[code]["droits"] if d["code"] == "DA")
        for code in ("2202991000", "2202999000", "2402200000", "0902300000", "0802700000")
    }
    assert taux == {"2202991000": 50.0, "2202999000": 15.0, "2402200000": 55.0, "0902300000": 12.0, "0802700000": 10.0}


def test_biere_selon_le_degre_sans_taux(positions):
    etat, lignes = _calcul(positions["2203001000"])
    assert lignes["DA"]["montant"] is None
    assert lignes["TVA"]["montant"] is None and etat != "COMPLET"
