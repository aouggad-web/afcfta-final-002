"""Côte d'Ivoire : RS, PCS, PCC et PUA (circulaire DGD n° 2258), TVA sur la
valeur en douane majorée des droits et taxes d'entrée (directive UEMOA
n° 02/98, art. 27). Fiche : CIV_prelevements_TVA_2026-10-10.json."""

import json
import os

import pytest

from services.calcul import calculer

SOCLE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "socle", "CIV.json")

pytestmark = pytest.mark.skipif(not os.path.exists(SOCLE), reason="socle absent (gitignoré)")


@pytest.fixture(scope="module")
def positions():
    with open(SOCLE, encoding="utf-8") as f:
        return json.load(f)["positions"]


def _calcul(position):
    r = calculer(position, 1000, devise_cif="XOF")["npf"]
    return r["etat"], {l["code"]: l for l in r["lignes"]}


def test_tissu_porte_les_prelevements_et_la_tva_sur_les_droits_d_entree(positions):
    """DD 10 % : 100 ; RS 10 ; PCS 8 ; PCC 5 ; PUA 2 ; TVA 18 % sur 1 125."""
    etat, lignes = _calcul(positions["5208110000"])
    assert [lignes[c]["montant"] for c in ("DD", "RS", "PCS", "PCC", "PUA")] == [100.0, 10.0, 8.0, 5.0, 2.0]
    assert lignes["TVA"]["base"] == 1125.0 and etat == "COMPLET"


def test_spiritueux_taxe_speciale_sur_valeur_et_droits_d_entree(positions):
    """CGI art. 418 : taxe sur valeur + droits hors TVA ; TVA sur le tout."""
    etat, lignes = _calcul(positions["2208201000"])
    assert lignes["TSBPT"]["base"] == 1225.0
    assert lignes["TVA"]["base"] == 1225.0 + lignes["TSBPT"]["montant"] and etat == "COMPLET"


def test_toutes_les_positions_taxees_portent_les_quatre_prelevements(positions):
    for p in positions.values():
        codes = {d["code"] for d in p["droits"]}
        if codes:
            assert {"RS", "PCS", "PCC", "PUA"} <= codes
