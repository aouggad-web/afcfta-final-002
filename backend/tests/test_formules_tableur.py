"""Neutralisation des formules de tableur (audit M5) : la règle seule."""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from formules_tableur import neutraliser_formule, neutraliser_formule_csv  # noqa: E402


@pytest.mark.parametrize(
    "valeur",
    ["=1+1", "+cmd", "-2+3+cmd|' /C calc'!A0", "@SUM(A1)", "\t=1", "\r=1", "-- Other"],
)
def test_les_debuts_de_formule_sont_neutralises(valeur):
    assert neutraliser_formule(valeur) == "'" + valeur


@pytest.mark.parametrize("valeur", [-5, -5.0, 0, None, True, ["=x"]])
def test_les_nombres_et_valeurs_non_textuelles_restent_intacts(valeur):
    assert neutraliser_formule(valeur) is valeur


@pytest.mark.parametrize("valeur", ["Maroc", "general", "0101", "", "a=b"])
def test_le_texte_ordinaire_reste_intact(valeur):
    assert neutraliser_formule(valeur) == valeur


@pytest.mark.parametrize("valeur", ["-", "+", "="])
def test_un_signe_seul_reste_intact(valeur):
    assert neutraliser_formule(valeur) == valeur


# Excel en français coupe un CSV à virgules sur chaque « ; » et chaque saut de
# ligne, même entre guillemets : chaque morceau commence une cellule.
@pytest.mark.parametrize(
    "valeur, attendu",
    [
        ("x;=1+2;y", "x;'=1+2;y"),
        ("x\n=1+2", "x\n'=1+2"),
        ("x\r\n+cmd", "x\r\n'+cmd"),
        ('x;"=1+2"', 'x;\'"=1+2"'),
        ("=1;@SUM(A1)", "'=1;'@SUM(A1)"),
        # En fin de champ, le morceau continue sur le champ suivant.
        ("a,b;=", "a,b;'="),
        ("x;-", "x;'-"),
    ],
)
def test_csv_neutralise_aussi_apres_un_point_virgule_ou_un_saut_de_ligne(valeur, attendu):
    assert neutraliser_formule_csv(valeur) == attendu


# Le module csv écrit le texte d'une liste ou d'un dictionnaire : coupé sur ses
# « ; », ce texte livrerait la formule telle quelle.
@pytest.mark.parametrize(
    "valeur, attendu",
    [
        (["x;=1+1;"], "['x;'=1+1;']"),
        ({"note": "y;@SUM(A1)"}, "{'note': 'y;'@SUM(A1)'}"),
    ],
)
def test_csv_juge_une_liste_ou_un_dictionnaire_sur_son_texte(valeur, attendu):
    assert neutraliser_formule_csv(valeur) == attendu


@pytest.mark.parametrize("valeur", ["Animaux vivants; produits", "x;-;y", "x; =1", -5, None])
def test_csv_laisse_intacts_le_texte_ordinaire_et_un_signe_seul(valeur):
    assert neutraliser_formule_csv(valeur) == valeur


# Premier champ d'une ligne : ouvert avec le séparateur « ; », son morceau
# continue après la virgule sur le champ suivant (`-,1+cmd|' /C calc'!A0`) ;
# un signe seul ou un nombre négatif y est neutralisé lui aussi.
@pytest.mark.parametrize(
    "valeur, attendu",
    [("-", "'-"), ("=", "'="), (-5, "'-5"), (-0.5, "'-0.5"), ("=1;=2", "'=1;'=2")],
)
def test_csv_neutralise_tout_debut_de_formule_en_debut_de_ligne(valeur, attendu):
    assert neutraliser_formule_csv(valeur, debut_de_ligne=True) == attendu


@pytest.mark.parametrize("valeur", ["KE", "010110", 5, 0, True, None, ""])
def test_csv_laisse_intact_un_debut_de_ligne_ordinaire(valeur):
    assert neutraliser_formule_csv(valeur, debut_de_ligne=True) == valeur
