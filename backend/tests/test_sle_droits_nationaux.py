"""Sierra Leone : taux nationaux de la Part II du Customs Tariff Act 1978,
remplacée par le Finance Act 2026, s.2. Fiche :
SLE_droits_nationaux_2026-10-25.json."""

import json
import os

import pytest

RACINE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SOCLE = os.path.join(RACINE, "backend", "socle", "SLE.json")

pytestmark = pytest.mark.skipif(not os.path.exists(SOCLE), reason="socle absent (gitignoré)")


@pytest.fixture(scope="module")
def positions():
    with open(SOCLE, encoding="utf-8") as f:
        return json.load(f)["positions"]


def _dd(positions, code):
    return next(d for d in positions[code]["droits"] if d["code"] == "DD")


@pytest.mark.parametrize("code,taux", [
    ("0407110000", 35.0),  # œufs fertilisés, 5 % au TEC
    ("2104109000", 35.0),  # bouillons
    ("2202100000", 35.0),  # eaux additionnées de sucre (2202.10 listée)
    ("2711120000", 0.0),   # propane
    ("4404200000", 35.0),  # échalas et perches
    ("4412310000", 35.0),  # contreplaqués
    ("7317009000", 30.0),  # clous
    ("7321111100", 0.0),   # réchauds à gaz
    ("7321900000", 0.0),   # parties
])
def test_taux_de_la_part_ii(positions, code, taux):
    dd = _dd(positions, code)
    assert dd["taux"] == taux
    assert "Finance Act 2026" in dd["source"]


@pytest.mark.parametrize("code", ["7311000000", "7321190000", "2103909900", "8413700000", "8541401000"])
def test_items_sans_position_exacte_au_taux_du_tec(positions, code):
    assert "Finance Act 2026" not in (_dd(positions, code).get("source") or "")
