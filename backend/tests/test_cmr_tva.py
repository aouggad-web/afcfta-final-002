"""Cameroun : TVA à l'importation, biens exonérés par l'art. 128 du CGI (édition
2026) et son annexe I (biens de première nécessité), exclusions de l'art. 128,
6) b) ; ailleurs, taux général de 19,25 %. Fiche : CMR_tva_2026-10-31.json."""

import json
import os

import pytest

from services.calcul import calculer

SOCLE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "socle", "CMR.json")
pytestmark = pytest.mark.skipif(not os.path.exists(SOCLE), reason="socle absent (gitignoré)")


@pytest.fixture(scope="module")
def positions():
    with open(SOCLE, encoding="utf-8") as f:
        return json.load(f)["positions"]


def _tva(position):
    lignes = [d for d in position["droits"] if d["code"] == "TVA"]
    assert len(lignes) == 1
    return lignes[0]["taux"]


def test_chaque_position_porte_une_ligne_de_tva(positions):
    """Le tarif source laissait sans TVA les positions marquées « EXO »."""
    assert all(sum(d["code"] == "TVA" for d in p["droits"]) == 1 for p in positions.values())


@pytest.mark.parametrize("code", ["01051100", "03023200", "03037900", "03055110", "04013000", "04022100",
                                  "04070010", "10011090", "10062000", "10064000", "11010010", "19011011",
                                  "23040000", "23092000", "27101123", "27111300", "29411000", "30049000",
                                  "31021000", "34070020", "38089390", "38089490", "40141000", "48010000",
                                  "84192000", "85023100", "87131000", "90181100", "90221400", "94029000"])
def test_biens_exoneres(positions, code):
    assert _tva(positions[code]) == 0.0


@pytest.mark.parametrize("code", ["03027000", "03031100", "03032200", "03038000", "03052000", "03056210"])
def test_poissons_exclus_par_l_art_128_6_b(positions, code):
    """Saumons et truites, foies, œufs et laitances, morues salées."""
    assert _tva(positions[code]) == 19.25


@pytest.mark.parametrize("code", ["02011000", "02071200", "11022000", "23021000", "19011012", "38089990",
                                  "40113000", "90183100", "90211000", "94021020"])
def test_taux_general(positions, code):
    """Viande bovine importée, farines « produits localement », positions que le tarif
    source marquait « EXO » sans que le CGI les exonère."""
    assert _tva(positions[code]) == 19.25


@pytest.mark.parametrize("code", ["03054991", "04029900", "10063090", "25010090", "29392000", "38089110",
                                  "63049300"])
def test_positions_mixtes_sans_taux(positions, code):
    assert _tva(positions[code]) is None


def test_la_base_reste_valeur_droit_de_douane_et_accise(positions):
    r = calculer(positions["90183100"], 1000, devise_position="XAF", devise_cif="XAF")
    tva = next(l for l in r["npf"]["lignes"] if l["code"] == "TVA")
    assert tva["base"] == 1000.0 + next(l for l in r["npf"]["lignes"] if l["code"] == "DD")["montant"]
    assert tva["montant"] == pytest.approx(tva["base"] * 0.1925, abs=0.01)
