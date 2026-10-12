"""Togo : tarif de l'OTR (TEC CEDEAO actualisé au 10/11/2025) ; DD, RS, PCS
0,8 %, PC, PUA et PNS sur la valeur en douane ; accises du CGI (art. 243) sur
la valeur et les droits d'entrée (art. 245) ; TVA sur la valeur et tous les
droits perçus par la douane (art. 186, 7-) ; PNS dû hors CEDEAO seulement (LF
2025, art. 6-3). Fiche : TGO_prelevements_TVA_2026-10-12.json."""

import json
import os

import pytest

from services import exoneration_origine
from services.calcul import calculer

SOCLE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "socle", "TGO.json")

pytestmark = pytest.mark.skipif(not os.path.exists(SOCLE), reason="socle absent (gitignoré)")


@pytest.fixture(scope="module")
def positions():
    with open(SOCLE, encoding="utf-8") as f:
        return json.load(f)["positions"]


def _calcul(position):
    r = calculer(position, 1_000_000, devise_cif="XOF")["npf"]
    return r["etat"], {l["code"]: l for l in r["lignes"]}


def test_droits_d_entree_et_tva(positions):
    """0201.10 (viande bovine fraîche, 20 % au tarif de l'OTR) : TVA sur 1 000 000 + 230 000."""
    etat, lignes = _calcul(positions["0201100000"])
    assert etat == "COMPLET"
    assert [lignes[c]["montant"] for c in ("DD", "RS", "PCS", "PCC", "PUA", "PNS")] == [
        200_000.0, 10_000.0, 8_000.0, 5_000.0, 2_000.0, 5_000.0,
    ]
    assert lignes["TVA"]["base"] == 1_230_000.0


def test_accise_sur_la_valeur_et_les_droits_d_entree(positions):
    """Bière 2203.00.10 : accise 20 % sur 1 230 000 ; TVA sur cette base + l'accise."""
    etat, lignes = _calcul(positions["2203001000"])
    assert lignes["DA"]["taux_pct"] == 20.0 and lignes["DA"]["base"] == 1_230_000.0
    assert lignes["TVA"]["base"] == pytest.approx(1_230_000.0 + 246_000.0)


def test_accise_sans_taux_quand_la_position_ne_tranche_pas(positions):
    """Voitures de tourisme : 5 % à partir de 13 CV, puissance absente de la position."""
    etat, lignes = _calcul(positions["8703231900"])
    assert lignes["DA"]["taux_pct"] is None and etat != "COMPLET"


def test_pns_retire_pour_une_origine_cedeao(positions):
    position, retires = exoneration_origine.appliquer(positions["0201100000"], "GHA")
    assert {r["code"] for r in retires} == {"PCC", "PNS", "PUA"}
    assert "PNS" not in {d["code"] for d in position["droits"]}
    _, retires_hors = exoneration_origine.appliquer(positions["0201100000"], "MAR")
    assert {r["code"] for r in retires_hors} == {"PUA"}
