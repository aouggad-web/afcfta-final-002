"""TEC CEMAC : deux taux imprimés hors catégorie (fiche CEMAC_TEC_coquilles).

4407.29.25 « 3% » et 6906.00.00 « .30 % » : aucun n'est une catégorie du TEC,
et les positions voisines sont à 30 %. Le gabarit commun aux six États les
recopiait tels quels.
"""

import json
import os

import pytest

SOCLE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "socle")
CEMAC = ("CMR", "COG", "GAB", "TCD", "CAF", "GNQ")


@pytest.mark.parametrize("iso", CEMAC)
def test_aucun_droit_de_douane_hors_categorie(iso):
    chemin = os.path.join(SOCLE, f"{iso}.json")
    if not os.path.exists(chemin):
        pytest.skip("socle absent (gitignoré)")
    with open(chemin, encoding="utf-8") as f:
        positions = json.load(f)["positions"]
    for code in ("44072925", "69060000"):
        dd = next(d for d in positions[code]["droits"] if d["code"] == "DD")
        assert dd["taux"] == 30.0 and "coquille" in dd["note"]
    hors = {
        d["taux"]
        for p in positions.values()
        for d in p["droits"]
        if d["code"] == "DD" and d.get("taux") is not None
    } - {0.0, 5.0, 10.0, 20.0, 30.0}
    assert hors == set()
