"""Nigéria : IAT de la Customs, Excise Tariff, Etc. (Variation) Order 2026
(S.I. 29, Gazette n° 79 du 1er mai 2026). Fiche : NGA_IAT_SI29_2026-10-08.json."""

import json
import os

import pytest

SOCLE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "socle", "NGA.json")
pytestmark = pytest.mark.skipif(not os.path.exists(SOCLE), reason="socle absent (gitignoré)")


@pytest.fixture(scope="module")
def positions():
    with open(SOCLE, encoding="utf-8") as f:
        return json.load(f)["positions"]


def _taux(position, code):
    return next(d["taux"] for d in position["droits"] if d["code"] == code)


def test_riz_iat_de_la_liste(positions):
    """Ligne 5 : 1006.30.10.00, droit 10 %, IAT 37,5 % (50 % au portail, Order 2023)."""
    assert _taux(positions["1006301000"], "IAT") == 37.5


def test_vin_sorti_de_la_liste_n_a_plus_d_iat(positions):
    """2204.21 portait 50 % en 2023 ; absent de la liste de 2026."""
    assert _taux(positions["2204210000"], "IAT") == 0.0


def test_groupe_electrogene_a_deux_taux_reste_indisponible(positions):
    """8502.11.90.00 : 15 % (basic) ou 35 % (soundproof) — non attribuable."""
    assert _taux(positions["8502119000"], "IAT") is None


def test_ciment_l_accise_egale_a_l_iat_n_est_pas_servie_deux_fois(positions):
    """2523.10 : droit 10 % + IAT 40 % = 50 % selon la liste ; l'« accise » de 40 % est écartée."""
    p = positions["2523100000"]
    assert _taux(p, "IAT") == 40.0 and _taux(p, "EXC") is None


def test_vehicules_d_occasion_selon_la_gazette(positions):
    """Lignes 181-186 : IAT 10 % dans la Gazette (20 % dans la circulaire d'avril)."""
    assert _taux(positions["8703232000"], "IAT") == 10.0


def test_code_corrige_par_la_gazette(positions):
    """Ligne 4 : antipaludéens 3004.60.00.00 (3004.90.10.00 dans la circulaire)."""
    assert _taux(positions["3004600000"], "IAT") == 20.0
