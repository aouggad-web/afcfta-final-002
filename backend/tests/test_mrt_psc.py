"""Mauritanie : taxe de promotion de la culture et du sport (PSC, 1 % c.a.f.,
chapitres 21 à 98) et téléphones de la loi de finances 2026, art. 3.2.5.
Fiche : MRT_psc_2026-11-01.json."""

import json
import os

import pytest

from services.calcul import calculer

SOCLE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "socle", "MRT.json")

pytestmark = pytest.mark.skipif(not os.path.exists(SOCLE), reason="socle absent (gitignoré)")


@pytest.fixture(scope="module")
def positions():
    with open(SOCLE, encoding="utf-8") as f:
        return json.load(f)["positions"]


def _psc(position):
    return next((d for d in position["droits"] if d["code"] == "PSC"), None)


@pytest.mark.parametrize("code", ["8517610000", "8702102200", "8701201000", "2106909100"])
def test_psc_un_pour_cent(positions, code):
    assert _psc(positions[code])["taux"] == 1.0


@pytest.mark.parametrize(
    "code",
    [
        "0101210000",  # chapitre 01 : hors champ
        "1001990000",  # céréales
        "3004100000",  # médicaments
        "8432100000",  # charrues
        "8702102100",  # minibus usagé, 10 à 22 places
        "8702101190",  # minibus neuf, 10 à 22 places
    ],
)
def test_hors_du_champ_de_la_psc(positions, code):
    assert _psc(positions[code]) is None


def test_tracteur_sans_taux(positions):
    assert _psc(positions["8701911900"])["taux"] is None


def test_la_tva_comprend_la_psc(positions):
    """8517.61, 1 000 : DD 5 + RS 10 + PC 5 + PSC 10 entrent dans la base de la TVA."""
    r = calculer(positions["8517610000"], 1000, devise_cif="MRU")["npf"]
    lignes = {l["code"]: l for l in r["lignes"]}
    base = 1000 + sum(lignes[c]["montant"] for c in ("DD", "RS", "PC", "PSC"))
    assert lignes["PSC"]["montant"] == 10.0
    assert lignes["TVA"]["base"] == pytest.approx(base)


def test_telephones_lf2026(positions):
    droits = {d["code"]: d.get("taux") for d in positions["8517120000"]["droits"]}
    assert droits["DD"] == 10.0 and droits["PSC"] == 1.0 and droits["TVA"] is None
