"""Le tarif libyen mélange deux écritures de taux dans la même colonne.

Relevé sur le XLSX officiel `customs.gov.ly` (التعريفة الجمركية 2022) :

    0.05              4 379 lignes     fraction décimale  →  5 %
    معفاة               988 lignes     exonéré            →  0 %
    5%                  356 lignes     pourcentage écrit  →  5 %
    0.3                  71 lignes                        → 30 %
    ممنوع استيراده       62 lignes     importation INTERDITE
    0.1                  48 lignes                        → 10 %
    30% / 10%             7 lignes

La première version de `parse_rate` rendait `float(s)` pour tout : `0.05`
devenait 0,05 % — cent fois trop bas, sur les trois quarts du tarif — et `5%`
levait une exception, perdant le taux. Sa docstring annonçait pourtant
« 0.05 → 5.0 ». Personne ne l'avait exécutée sur le fichier réel.

L'interdiction d'importation est le second piège : ce n'est pas un taux
absent. La rendre `None` sans la dire ferait lire « droit indisponible » là où
la réponse est « vous ne pouvez pas importer » ; la rendre 0 % ferait liquider
une marchandise prohibée.
"""

from __future__ import annotations

import importlib.util
import os

import pytest

_spec = importlib.util.spec_from_file_location(
    "libya_customs_scraper",
    os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
        "backend",
        "crawlers",
        "countries",
        "libya_customs_scraper.py",
    ),
)
libya = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(libya)


@pytest.mark.parametrize(
    "brut,attendu",
    [
        ("0.05", 5.0),
        ("5%", 5.0),
        ("0.3", 30.0),
        ("30%", 30.0),
        ("0.1", 10.0),
        ("10%", 10.0),
    ],
    ids=["frac_5", "pct_5", "frac_30", "pct_30", "frac_10", "pct_10"],
)
def test_les_deux_ecritures_donnent_le_meme_taux(brut, attendu):
    """`0.05` et `5%` désignent le même droit et doivent le rendre.

    C'est le cœur du défaut : les deux écritures coexistent pour des
    marchandises voisines, et seule leur égalité prouve que la lecture est
    juste.
    """
    assert libya.parse_rate(brut) == attendu


def test_un_taux_exonere_est_un_zero_publie():
    """`معفاة` est un zéro que le tarif ÉNONCE — il n'est pas fabriqué."""
    assert libya.parse_rate("معفاة") == 0.0


@pytest.mark.parametrize(
    "brut", [None, "", "   ", "xyz", "غير محدد"], ids=["none", "vide", "espaces", "texte", "arabe"]
)
def test_une_cellule_sans_taux_ne_devient_jamais_zero(brut):
    """L'absence se dit `None`. Un zéro de substitution ferait liquider à tort."""
    assert libya.parse_rate(brut) is None


def test_l_interdiction_n_est_pas_un_taux():
    """`ممنوع استيراده` rend un drapeau, et surtout aucun taux.

    Les deux moitiés comptent : sans le drapeau l'interdiction disparaît,
    et avec un taux elle deviendrait une importation liquidable.
    """
    taux, interdit = libya.lire_cellule_droit("ممنوع استيراده")

    assert interdit is True
    assert taux is None


def test_une_cellule_ordinaire_ne_leve_aucun_drapeau():
    """La contrepartie : le drapeau ne doit pas se lever pour rien."""
    taux, interdit = libya.lire_cellule_droit("0.05")

    assert interdit is False
    assert taux == 5.0


def test_une_valeur_superieure_a_un_reste_un_pourcentage():
    """Garde-fou de la règle de lecture.

    Une fraction vaut au plus 1. Multiplier par cent une valeur qui la dépasse
    produirait des droits de plusieurs milliers de pour cent — l'erreur
    symétrique de celle qu'on corrige.
    """
    assert libya.parse_rate("15") == 15.0
    assert libya.parse_rate("1") == 100.0
