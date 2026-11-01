"""São Tomé-et-Príncipe : droits de douane de la Lei n.º 04/2023 (eau minérale,
plastiques, lampes). Fiche : STP_direitos_lei4_2023_2026-11-01.json."""

import json
import os

import pytest

from services.calcul import calculer

SOCLE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "socle", "STP.json")

pytestmark = pytest.mark.skipif(not os.path.exists(SOCLE), reason="socle absent (gitignoré)")


@pytest.fixture(scope="module")
def positions():
    with open(SOCLE, encoding="utf-8") as f:
        return json.load(f)["positions"]


def _dd(position):
    return next(d["taux"] for d in position["droits"] if d["code"] == "DD")


@pytest.mark.parametrize(
    "code, taux",
    [
        ("220110", 10.0),  # eau minérale
        ("392321", 25.0),  # sacs en plastique
        ("392329", 25.0),
        ("390110", 15.0),  # autres positions du chapitre 39
        ("392690", 15.0),
        ("853910", 55.0),  # lampes
        ("853950", 0.0),  # lampes LED, exonérées
    ],
)
def test_droit_de_la_loi(positions, code, taux):
    assert _dd(positions[code]) == taux


@pytest.mark.parametrize("code", ["220190", "853990"])
def test_hors_du_champ_de_la_loi(positions, code):
    """Eau ordinaire et glace, parties de lampes : la loi ne les vise pas."""
    dd = next(d for d in positions[code]["droits"] if d["code"] == "DD")
    assert "Lei n.º 04/2023" not in dd.get("source", "")


def test_la_tva_suit_le_droit(positions):
    """8539.10, 1 000 : DD 55 % = 550 ; TVA 15 % sur 1 550 = 232,5."""
    r = calculer(positions["853910"], 1000, devise_cif="STN")["npf"]
    lignes = {l["code"]: l["montant"] for l in r["lignes"]}
    assert lignes["DD"] == 550.0 and lignes["TVA"] == 232.5
