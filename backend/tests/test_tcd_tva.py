"""Tchad : TVA à l'importation, taux général de 19,25 % (17,5 %, CGI art. 238, et
centimes additionnels de 10 %, loi de finances 2024, art. 14) et exonérations de
l'art. 230 du CGI (15°, liste de la loi de finances 2026 ; 24°).
Fiche : TCD_tva_2026-10-31.json."""

import json
import os

import pytest

from services.calcul import calculer

SOCLE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "socle", "TCD.json")
pytestmark = pytest.mark.skipif(not os.path.exists(SOCLE), reason="socle absent (gitignoré)")


@pytest.fixture(scope="module")
def positions():
    with open(SOCLE, encoding="utf-8") as f:
        return json.load(f)["positions"]


def _tva(position):
    (ligne,) = [d for d in position["droits"] if d["code"] == "TVA"]
    return ligne["taux"]


@pytest.mark.parametrize("code", ["01011010", "10019000", "17019910", "15119000", "84331100", "87019012",
                                  "94021020", "90049020", "39261000"])
def test_taux_general_de_19_25(positions, code):
    """Hors des exonérations, le taux général : plus les 18 % du CGI 2016."""
    assert _tva(positions[code]) == 19.25


@pytest.mark.parametrize("code", ["02071200", "04021000", "29371200", "30049000", "40141000", "90183100",
                                  "94021010", "94029000", "10051000", "31021000", "05111000", "04070010",
                                  "87019011", "84248110", "84323000", "84335100", "84361000", "39011000",
                                  "39021000", "32041100", "33021000", "76071910", "34070020", "84342000",
                                  "56081100"])
def test_biens_exoneres(positions, code):
    assert _tva(positions[code]) == 0.0


@pytest.mark.parametrize("code", ["29392000", "32041200", "85044000", "85078000", "84146000", "85011000",
                                  "39181000", "04049000", "33029000"])
def test_positions_sans_taux(positions, code):
    assert _tva(positions[code]) is None


def test_la_base_reste_valeur_droits_et_accise(positions):
    r = calculer(positions["01011010"], 1000, devise_position="XAF", devise_cif="XAF")
    tva = next(l for l in r["npf"]["lignes"] if l["code"] == "TVA")
    assert tva["montant"] == pytest.approx(tva["base"] * 0.1925, abs=0.01)
