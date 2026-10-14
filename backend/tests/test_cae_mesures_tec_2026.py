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


@pytest.mark.parametrize("iso,code,source", [
    ("UGA", "85287290", "Table II, n° 45 (p. 42)"),
    ("UGA", "11081100", "Table II, n° 47 (p. 42)"),
    ("UGA", "63039200", "Table VII, n° 10 (p. 65)"),
    ("KEN", "96121090", "Table I, n° 324 (p. 39)"),
])
def test_colonnes_decalees_lues(iso, code, source):
    """Pages 39, 42 et 65 : des colonnes vides décalent la position, qui reste lue."""
    assert source in _dd(iso, code)[1]["source"]


def test_aucune_mesure_appliquee_sans_position():
    with open(MESURES, encoding="utf-8") as f:
        mesures = json.load(f)["mesures"]
    assert not [(m["table"], m["sn"]) for m in mesures if not m["positions"]
                and any(d.get("lu") and not d.get("restriction") for d in m["decisions"])]


@pytest.mark.parametrize("iso,code,attendu", [
    ("UGA", "85076000", "n° 50"),   # n° 100 : « 85.07 excluding 8507.60.00 »
    ("KEN", "62114210", None),      # n° 134 : « Chapter 61 and 62 (Excluding … 6211.42.10 …) »
    ("UGA", "85442000", None),      # n° 254 : « 85.44 Excluding 8544.20.00 8544.70.00 »
])
def test_exclusions_de_la_cellule_des_positions(iso, code, attendu):
    source = _dd(iso, code)[1].get("source") or ""
    assert ("n° 100" not in source and "n° 134" not in source and "n° 254" not in source)
    assert attendu is None or attendu in source


def test_chapitres_de_la_cellule_des_positions():
    """Table I n° 134 : Kenya, chapitres 61 et 62 à 35 %."""
    assert "n° 134" in _dd("KEN", "61091000")[1]["source"]


def test_usage_de_la_description_restreint_la_mesure():
    """Table I n° 77 : « Penstock pipes for use in Hydro Electric Power Projects »."""
    _, dd = _dd("UGA", "73043100")
    assert "EAC/160/2026" not in dd["source"] and "n° 77" in dd["note"]


def test_taux_par_defaut_et_exception_en_note():
    """Table I n° 253 : compteurs électriques à 35 %, sauf ceux importés par l'État."""
    _, dd = _dd("UGA", "90283000")
    assert dd["taux"] == 35.0 and "exception non appliquée" in dd["note"]
