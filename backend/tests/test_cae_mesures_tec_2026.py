"""CAE : exceptions au TEC de l'exercice 2026/27 (Legal Notice EAC/160/2026).
Fiche : CAE_mesures_TEC_2026_27_2026-10-14.json."""

import json
import os

import pytest

from services.calcul import calculer

RACINE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SOCLE = os.path.join(RACINE, "backend", "socle")
MESURES = os.path.join(RACINE, "data", "eac", "mesures_tec_cae_2026_27.json")

pytestmark = pytest.mark.skipif(
    not os.path.exists(os.path.join(SOCLE, "KEN.json")), reason="socle absent (gitignoré)"
)


def _dd(iso, code):
    with open(os.path.join(SOCLE, f"{iso}.json"), encoding="utf-8") as f:
        position = json.load(f)["positions"][code]
    return position, next(d for d in position["droits"] if d["code"] == "DD")


def test_toutes_les_lignes_des_tables_lues():
    with open(MESURES, encoding="utf-8") as f:
        mesures = json.load(f)["mesures"]
    par_table = {}
    for m in mesures:
        par_table[m["table"]] = par_table.get(m["table"], 0) + 1
    assert par_table == {"I": 325, "II": 47, "III": 293, "IV": 267, "V": 34, "VI": 233, "VII": 13,
                         "VIII": 3, "IX": 10, "X": 10}


def test_telephones_mobiles_kenya_25():
    """Table I n° 19 (b) : Kenya, 8517.13.00 de 0 % à 25 %."""
    position, dd = _dd("KEN", "85171300")
    assert dd["taux"] == 25.0 and "EAC/160/2026, Table I, n° 19" in dd["source"]
    r = calculer(position, 10_000)["npf"]
    assert next(l for l in r["lignes"] if l["code"] == "DD")["montant"] == 2_500.0


def test_decision_fusionnee_sur_plusieurs_lignes():
    """Sucre, Table I n° 63 à 66 : une seule décision (Rwanda, 25 %) pour quatre lignes."""
    for code in ("17011290", "17011490", "17019100", "17019990"):
        assert _dd("RWA", code)[1]["taux"] == 25.0


def test_mesure_conditionnelle_en_note_seulement():
    """Table I n° 3 (a) : cartes à puce à 0 % pour la seule National Identification Authority."""
    _, dd = _dd("TZA", "85235200")
    assert dd["taux"] == 25.0 and "Mesure conditionnelle" in dd["note"]


def test_droit_compose_de_la_table_iii():
    """Kenya, tissus : 25 % ou 0,75 US$/kg, le plus élevé."""
    _, dd = _dd("KEN", "52081100")
    assert dd["compose"] and dd["regle_composee"] == "LE_PLUS_ELEVE"
    assert dd["taux"] == 25.0 and dd["specifique"]["montant"] == 0.75


def test_amendement_du_tec_pour_tous():
    """Table X n° 1 : levures actives, 25 % ou 0,66 US$/kg, dans les six pays."""
    for iso in ("KEN", "RWA", "TZA", "UGA", "BDI", "SSD"):
        _, dd = _dd(iso, "21021000")
        assert dd["specifique"]["montant"] == 0.66 and dd["taux"] == 25.0


def test_exclusion_lue():
    """Table I n° 121 : Tanzanie, fils de coton à 25 % sauf 5205.23.00."""
    assert "EAC/160/2026" not in str(_dd("TZA", "52052300")[1].get("source"))
