"""Bénin : tarif officiel de la DGDDI (TEC CEDEAO SH 2022) ; PCS 0,8 %, PC 0,5 %,
prélèvement de solidarité de l'UA 0,2 % ; TVA sur la valeur en douane majorée
des droits et taxes perçus à l'entrée (directive UEMOA n° 02/98, art. 27).
Fiche : BEN_prelevements_TVA_2026-10-11.json."""

import json
import os

import pytest

from services.calcul import calculer

SOCLE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "socle", "BEN.json")

pytestmark = pytest.mark.skipif(not os.path.exists(SOCLE), reason="socle absent (gitignoré)")


@pytest.fixture(scope="module")
def positions():
    with open(SOCLE, encoding="utf-8") as f:
        return json.load(f)["positions"]


def _calcul(position):
    r = calculer(position, 1000, devise_cif="XOF")["npf"]
    return r["etat"], {l["code"]: l for l in r["lignes"]}


def test_prelevements_et_tva_sur_les_droits_d_entree(positions):
    """0101.21 : DD 5 % : 50 ; RS 10 ; PCS 8 ; PC 5 ; PUA 2 ; TVA 18 % sur 1 075."""
    etat, lignes = _calcul(positions["0101210000"])
    assert etat == "COMPLET"
    assert [lignes[c]["montant"] for c in ("DD", "RS", "PCS", "PCC", "PUA")] == [50.0, 10.0, 8.0, 5.0, 2.0]
    assert lignes["TVA"]["base"] == 1075.0


def test_droit_de_douane_du_tarif_sh2022(positions):
    """Viandes 0201.10 : 20 % au tarif de la DGDDI (35 % à la collecte de février 2026) ; jus 2009.31.90 : 35 %."""
    dd = {k: next(d["taux"] for d in positions[k]["droits"] if d["code"] == "DD") for k in ("0201100000", "2009319000")}
    assert dd == {"0201100000": 20.0, "2009319000": 35.0}


def test_rs_non_lue_rend_la_tva_indisponible(positions):
    etat, lignes = _calcul(positions["9405910000"])
    assert lignes["RS"]["taux_pct"] is None
    assert lignes["TVA"]["montant"] is None and etat != "COMPLET"
