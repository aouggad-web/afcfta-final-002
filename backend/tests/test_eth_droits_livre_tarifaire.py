"""Éthiopie : droit de douane à 0 % perdu à la collecte du portail, rétabli là où
le livre tarifaire 2021 du ministère des Finances le dit « Free ». Fiche :
ETH_droits_livre_tarifaire_2021-10-07.json."""

import json
import os

import pytest

from services.calcul import COMPLET, calculer

SOCLE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "socle", "ETH.json")
pytestmark = pytest.mark.skipif(not os.path.exists(SOCLE), reason="socle absent (gitignoré)")


@pytest.fixture(scope="module")
def positions():
    with open(SOCLE, encoding="utf-8") as f:
        return json.load(f)["positions"]


def _dd(position):
    return next(d for d in position["droits"] if d["code"] == "DD")


def test_reproducteurs_droit_du_livre(positions):
    """0101.2100 : 0 % écarté par la collecte, « Free » au livre (page 1)."""
    dd = _dd(positions["01012100000"])
    assert dd["taux"] == 0.0 and dd["source"].startswith("Livre tarifaire")
    assert "omettait les taux à 0 %" in dd["note"]
    assert calculer(positions["01012100000"], 1000, devise_position="ETB")["npf"]["etat"] == COMPLET


def test_un_taux_non_nul_du_livre_n_est_pas_servi(positions):
    """0404.1000 (lactosérum) : la collecte a perdu le droit, qui était très
    probablement un 0 % du portail ; le livre de 2021 porte 5 %. Le conflit est
    nommé, le droit reste à compléter plutôt que servi à 5 %."""
    dd = _dd(positions["04041000000"])
    assert dd["taux"] is None
    assert "le livre tarifaire 2021 porte 5 %" in dd["note"]
    assert calculer(positions["04041000000"], 1000, devise_position="ETB")["npf"]["etat"] != COMPLET


def test_seuls_les_free_du_livre_sont_repris(positions):
    """Aucun droit repris du livre n'est servi à un autre taux que 0 %."""
    repris = [
        d["taux"]
        for p in positions.values()
        for d in p["droits"]
        if d["code"] == "DD" and str(d.get("source", "")).startswith("Livre tarifaire")
    ]
    assert repris and set(repris) == {0.0}


def test_le_portail_prime_sur_le_livre(positions):
    """07.13 : 15 % au livre de 2021, 5 % au portail — le portail est conservé."""
    dd = _dd(positions[next(k for k in positions if k.startswith("07131000"))])
    assert dd["taux"] == 5.0 and "Livre" not in dd["source"]


def test_sous_position_modifiee_en_sh2022_non_comblee(positions):
    """1211.90 figure à la table I de l'OMD : le code de 2017 peut désigner un
    autre produit, le droit reste indisponible plutôt que repris du livre."""
    assert _dd(positions["12119000000"])["taux"] is None
