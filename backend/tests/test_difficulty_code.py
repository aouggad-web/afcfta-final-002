"""
La difficulté de substitution est un CODE, pas un mot.

Le service rendait le libellé français directement — « Facile », « Modéré ».
Le front devait alors comparer ce texte d'affichage pour choisir une couleur
et une traduction, et il s'est trompé : ses tables étaient clés en anglais,
rien ne correspondait, et toutes les cartes sortaient « Difficile » en ambre
quel que soit le niveau réel. Le défaut a vécu jusqu'à ce qu'un test de
régression le nomme.

La leçon n'est pas « le front avait tort » : c'est qu'un texte d'affichage
est un mauvais identifiant. Il change avec la langue, avec la typographie,
avec l'humeur d'une relecture — et rien ne prévient les consommateurs.
"""

import os
import sys

_backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _backend_dir not in sys.path:
    sys.path.insert(0, _backend_dir)

import pytest  # noqa: E402
from services.real_substitution_service import real_substitution_service as svc  # noqa: E402

CODES = {"easy", "moderate", "difficult", "very_difficult"}


@pytest.mark.parametrize(
    "capacity_ratio,expected",
    [(0.60, "easy"), (0.30, "moderate"), (0.15, "difficult"), (0.02, "very_difficult")],
)
def test_assess_returns_a_stable_code(capacity_ratio, expected):
    assert svc._assess_difficulty(1000.0, 1000.0 * capacity_ratio) == expected


def test_the_code_is_never_a_display_label():
    """Un accent ou une majuscule ici signalerait un retour en arrière."""
    for ratio in (0.9, 0.4, 0.2, 0.01):
        code = svc._assess_difficulty(1000.0, 1000.0 * ratio)
        assert code in CODES
        assert code.islower() and code.isascii(), code


def test_both_fields_are_emitted_and_agree():
    """`difficulty` reste servi en français — déprécié, mais tenu.

    Le retirer casserait tout client externe qui le lit encore ; le garder
    sans le tester en ferait une promesse vide.
    """
    fields = svc._difficulty_fields(1000.0, 600.0)
    assert fields["difficulty_code"] == "easy"
    assert fields["difficulty"] == "Facile"
    assert set(fields) == {"difficulty_code", "difficulty"}


def test_every_code_has_a_french_label():
    assert set(svc._DIFFICULTY_FR) == CODES
    assert all(label for label in svc._DIFFICULTY_FR.values())


def test_distribution_is_keyed_by_code():
    """Une clé de répartition est un identifiant, pas une étiquette.

    Clée sur le français, elle changerait de forme avec la langue et l'écran
    devrait re-traduire des clés — le défaut d'origine, déplacé d'un cran.
    """
    opportunities = [
        {"difficulty_code": "easy", "difficulty": "Facile"},
        {"difficulty_code": "easy", "difficulty": "Facile"},
        {"difficulty_code": "difficult", "difficulty": "Difficile"},
    ]
    block = svc._build_analysis_block(opportunities)
    distribution = block["difficulty_distribution"]
    assert set(distribution) <= CODES, distribution
    assert distribution["easy"] == 2 and distribution["difficult"] == 1
