"""Angola : droit de douane de 2026 (Lei n.º 14/25, art. 31.º n.º 3 et n.º 6,
Anexo III). Fiche : AGO_droits_2026-10-25.json."""

import json
import os

import pytest

RACINE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SOCLE = os.path.join(RACINE, "backend", "socle", "AGO.json")

pytestmark = pytest.mark.skipif(not os.path.exists(SOCLE), reason="socle absent (gitignoré)")


@pytest.fixture(scope="module")
def positions():
    with open(SOCLE, encoding="utf-8") as f:
        return json.load(f)["positions"]


def _dd(positions, code):
    return next(d for d in positions[code]["droits"] if d["code"] == "DD")


@pytest.mark.parametrize("code,taux", [
    ("02062990", 30.0),  # abats « outras », 50 % en 2024
    ("17019919", 40.0),  # sucres, 30 % en 2024
    ("60061000", 25.0),  # tissus de bonneterie
    ("64022000", 30.0),  # chaussures
    ("72011000", 5.0),   # fonte brute, 2 % en 2024
    ("89039300", 5.0),   # bateaux de 7,5 m au plus, 2 % en 2024
])
def test_taux_de_l_anexo_iii(positions, code, taux):
    dd = _dd(positions, code)
    assert dd["taux"] == taux
    assert "Anexo III" in dd["source"]


def test_minimum_de_5_pour_cent_hors_livre(positions):
    """Art. 31.º n.º 3 : plus aucun taux entre 0 et 5 % ; les « Livre » restent à 0."""
    taux = [_dd(positions, c)["taux"] for c in positions]
    assert not [t for t in taux if t is not None and 0 < t < 5]
    assert _dd(positions, "72115000")["taux"] == 5.0
    assert _dd(positions, "84851000")["taux"] == 0.0


@pytest.mark.parametrize("code", ["05040000", "10063000", "89039900"])
def test_position_subdivisee_sans_taux_propre(positions, code):
    dd = _dd(positions, code)
    assert dd["taux"] is None
    assert "subdivise" in dd["note"]
