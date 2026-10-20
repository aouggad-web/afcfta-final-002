"""Égypte : TVA et Taxe de Table sur la valeur, les droits de douane et les
autres impôts (loi 67/2016, art. 10 et 39), tabacs à la seule Taxe de Table,
Taxe de Table des alcools au taux du tableau de 2016 et redevances sur la
valeur en douane (décisions avec réserve), droits au kilo et minimums de la
Taxe de Table publiés par la douane. Fiche : EGY_TVA_taxe_de_table_2026-10-14.json."""

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


def _calcul(code, quantite=None):
    r = calculer(_positions()[code], 1000, quantite=quantite)["npf"]
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


def test_alcool_taxe_de_table_reclame_les_litres():
    """Instruction ر7065 : 150 % avec un minimum de 15 EGP/l (tableau de 2016,
    sur décision) ; sans quantité, ni elle ni la TVA qui s'y assied."""
    etat, lignes = _calcul("2208300000")
    assert etat == "PARTIEL"
    assert lignes[TAXE_DE_TABLE]["statut"] == "QUANTITE_REQUISE"
    assert "sous réserve" in lignes[TAXE_DE_TABLE]["note"]
    assert lignes["TVA"]["montant"] is None


def test_alcool_le_plus_eleve_des_deux():
    """Whisky, 10 l : DD 3 000 % ; Taxe de Table max(150 % × 31 000, 15 × 10)."""
    etat, lignes = _calcul("2208300000", quantite=10)
    assert etat == "COMPLET"
    assert lignes[TAXE_DE_TABLE]["montant"] == pytest.approx(46_500.0)
    assert lignes["TVA"]["montant"] == pytest.approx(0.14 * (1000 + 30_000 + 46_500))


def test_biere_a_son_propre_taux():
    """Bière alcoolisée : 250 % avec un minimum de 500 EGP par hectolitre (item 4)."""
    tt = next(d for d in _positions()["2203000000"]["droits"] if d["code"] == TAXE_DE_TABLE)
    assert tt["taux"] == 250.0 and tt["specifique"]["montant"] == 5.0


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


def test_frais_de_chambre_sur_la_valeur():
    """Textile : redevance de la chambre de 1 % sur la valeur en douane (décision
    avec réserve), comprise dans l'assiette de la TVA."""
    etat, lignes = _calcul("5004000090")
    assert etat == "COMPLET"
    assert "sous réserve" in lignes["رسممحصلةلحسابغرفةنسيج"]["note"]
    assert lignes["TVA"]["montant"] == pytest.approx(0.14 * (1000 + 50 + 10))


def test_droit_de_douane_au_kilo_reclame_la_quantite():
    """Cigares : « 150 جنية لكل كيلو جرام صافى »."""
    etat, lignes = _calcul("2402100010")
    assert etat == "PARTIEL"
    assert lignes["DD"]["statut"] == "QUANTITE_REQUISE"


def test_tabac_droit_au_kilo_et_minimum_de_la_taxe_de_table():
    """Cigares, 10 kg : DD 150 × 10 ; assurance santé 10 % ; Taxe de Table
    max(200 % × (1 000 + 1 500 + 100), 50 × 10), le minimum ne s'y ajoute pas."""
    etat, lignes = _calcul("2402100010", quantite=10)
    assert etat == "COMPLET"
    assert lignes["DD"]["montant"] == pytest.approx(1500.0)
    assert lignes[TAXE_DE_TABLE]["montant"] == pytest.approx(5200.0)
    assert "VAT2" not in lignes


def test_le_minimum_au_kilo_l_emporte_sur_un_faible_taux():
    """Tabac brut, 100 kg déclarés pour 1 000 EGP : DD 9 × 100, redevance 0,5 % ;
    75 % × 1 905 < 60 × 100, le minimum est dû."""
    etat, lignes = _calcul("2401100010", quantite=100)
    assert etat == "COMPLET"
    assert lignes["DD"]["montant"] == pytest.approx(900.0)
    assert lignes[TAXE_DE_TABLE]["montant"] == pytest.approx(6000.0)


def test_minimum_au_litre_de_2106_90_20():
    """« بحد ادنى 15 جنية لكل لتر سائل » : 150 % × 31 000 ou 15 EGP par litre."""
    _, lignes = _calcul("2106902000", quantite=10_000)
    assert lignes[TAXE_DE_TABLE]["montant"] == pytest.approx(150_000.0)
    assert lignes["TVA"]["montant"] == pytest.approx(0.14 * (1000 + 30_000 + 150_000))
    assert "ضريبةالجدول2" not in lignes


def test_tabac_chauffe_taxe_de_table_de_l_instruction():
    """2404.11 : instruction ر7058, 1 800 EGP par kilo net ; 2 kg pour 1 000 EGP :
    DD 20 %, assurance santé 10 %, Taxe de Table 3 600, TVA 14 % sur le tout."""
    etat, lignes = _calcul("2404110000", quantite=2)
    assert etat == "COMPLET"
    assert lignes[TAXE_DE_TABLE]["montant"] == pytest.approx(3600.0)
    assert lignes["TVA"]["montant"] == pytest.approx(0.14 * (1000 + 200 + 100 + 3600))


def test_liquide_de_cigarette_electronique_n_est_pas_complet():
    """2404.12.00.10 : quatre instructions de 4 EGP/ml, cumul non tranché — la
    Taxe de Table est déclarée, sans taux, et le total n'est pas complet."""
    etat, lignes = _calcul("2404120010", quantite=1)
    assert etat == "PARTIEL"
    assert lignes[TAXE_DE_TABLE]["montant"] is None
    assert "ر7067" in lignes[TAXE_DE_TABLE]["note"]
