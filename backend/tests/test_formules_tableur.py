"""Neutralisation des formules de tableur (audit M5) : la règle seule."""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from formules_tableur import neutraliser_formule  # noqa: E402


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
