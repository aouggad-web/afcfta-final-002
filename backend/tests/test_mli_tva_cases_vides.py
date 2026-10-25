"""Mali : TVA de droit commun (CGI art. 229, 18 %) sur les positions dont la case
TVA du tarif de la DGD est vide. Fiche : MLI_tva_cases_vides_2026-10-25.json."""

import json
import os

import pytest

RACINE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SOCLE = os.path.join(RACINE, "backend", "socle", "MLI.json")

pytestmark = pytest.mark.skipif(not os.path.exists(SOCLE), reason="socle absent (gitignoré)")


@pytest.mark.parametrize("code", ["8708220000", "9508210000", "9508400000", "9701290000"])
def test_case_vide_au_taux_de_droit_commun(code):
    with open(SOCLE, encoding="utf-8") as f:
        droits = json.load(f)["positions"][code]["droits"]
    tva = next(d for d in droits if d["code"] == "TVA")
    assert tva["taux"] == 18.0
    assert "Art. 229" in tva["note"]


def test_plus_aucune_tva_sans_taux():
    with open(SOCLE, encoding="utf-8") as f:
        positions = json.load(f)["positions"]
    assert not [c for c, p in positions.items() for d in p["droits"] if d["code"] == "TVA" and d.get("taux") is None]
