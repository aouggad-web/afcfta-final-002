"""Égypte : TVA et Taxe de Table sur la valeur, les droits de douane et les
autres impôts (loi 67/2016, art. 10 et 39), tabacs à la seule Taxe de Table,
Taxe de Table des alcools sans taux. Fiche : EGY_TVA_taxe_de_table_2026-10-14.json."""

import json
import os

import pytest

from services.calcul import calculer

SOCLE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "socle")
TAXE_DE_TABLE = "ضريبةالجدول"

pytestmark = pytest.mark.skipif(
    not os.path.exists(os.path.join(SOCLE, "EGY.json")), reason="socle absent (gitignoré)"
)


def _positions():
    with open(os.path.join(SOCLE, "EGY.json"), encoding="utf-8") as f:
        return json.load(f)["positions"]


def _calcul(code):
    r = calculer(_positions()[code], 1000)["npf"]
    return r["etat"], {l["code"]: l for l in r["lignes"]}


def test_tva_sur_la_valeur_et_les_droits():
    """Chaussures, DD 60 % : TVA 14 % sur 1 000 + 600 (art. 10 (7))."""
    etat, lignes = _calcul("6403190000")
    assert etat == "COMPLET"
    assert lignes["TVA"]["montant"] == pytest.approx(224.0)


def test_taxe_de_table_puis_tva():
    """Parfums : DD 45 %, Taxe de Table 8 % sur valeur + DD (art. 39 (b)), TVA
    14 % sur valeur + DD + Taxe de Table (art. 10 (10))."""
    etat, lignes = _calcul("3303000010")
    assert etat == "COMPLET"
    assert lignes[TAXE_DE_TABLE]["montant"] == pytest.approx(116.0)
    assert lignes["TVA"]["montant"] == pytest.approx(0.14 * (1000 + 450 + 116))
    codes = [d["code"] for d in _positions()["3303000010"]["droits"]]
    assert codes.index(TAXE_DE_TABLE) < codes.index("TVA")


def test_tabac_a_la_seule_taxe_de_table():
    """Cigares : le « TVA 200 % » de la douane est la Taxe de Table (tableau, partie I)."""
    droits = _positions()["2402100010"]["droits"]
    assert not any(d["famille"] == "tva" for d in droits)
    tt = next(d for d in droits if d["code"] == TAXE_DE_TABLE)
    assert tt["taux"] == 200.0 and "partie I" in tt["note"]


@pytest.mark.parametrize("code", ["2203000000", "2208300000"])
def test_alcool_taxe_de_table_a_completer(code):
    """Instruction ر7065 : Taxe de Table due, taux non publié ; la TVA, qui s'y
    assied, ne se liquide pas non plus."""
    etat, lignes = _calcul(code)
    assert etat == "PARTIEL"
    assert lignes[TAXE_DE_TABLE]["statut"] == "TAUX_INDISPONIBLE"
    assert "À compléter" in lignes[TAXE_DE_TABLE]["note"]
    assert lignes["TVA"]["montant"] is None


def test_cigarettes_taxe_de_table_sur_le_prix_de_vente():
    tt = next(d for d in _positions()["2402200000"]["droits"] if d["code"] == TAXE_DE_TABLE)
    assert tt.get("taux") is None and tt["assiette"] is None
    assert "prix de vente" in tt["note"]


def test_ligne_publiee_deux_fois_comptee_une_fois():
    """8481.80.90.90 : « ID 60 % » et « TVA 14 % » publiés deux fois."""
    etat, lignes = _calcul("8481809090")
    assert etat == "COMPLET"
    assert set(lignes) == {"DD", "TVA"}
    assert lignes["TVA"]["montant"] == pytest.approx(224.0)


def test_frais_de_chambre_sans_assiette():
    """Textile : la redevance de la chambre n'a pas d'assiette établie ; la TVA,
    qui s'assied sur elle, n'est pas servie sans elle."""
    etat, lignes = _calcul("5004000090")
    assert etat == "PARTIEL"
    assert lignes["TVA"]["montant"] is None
