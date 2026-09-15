"""
Le code d'une instruction douanière égyptienne se lit dans son propre texte.

L'API officielle (`Services/TrfDetails`) renvoie deux tableaux, `Instructions`
et `InstructionCodes`, qui n'ont ni la même longueur ni le même ordre : sur la
position 0101210000 elle rend onze instructions pour douze codes, et le tableau
des codes porte un doublon. Le constructeur les appariait par position, ce qui
produisait deux défaillances distinctes :

* tailles égales — chaque texte recevait le code d'une autre instruction.
  Mesuré sur l'API en direct : un appariement exact sur quinze ;
* tailles inégales — un garde-fou vidait les deux listes, faisant disparaître
  des préférences réellement publiées. 2 029 positions du fichier livré étaient
  dans ce cas.

Au total, 46 094 appariements sur 56 623 étaient faux — 81,4 %. Ces tests
verrouillent la règle qui corrige les deux : le code officiel est le préfixe du
texte, et rien d'autre.
"""

from __future__ import annotations

import importlib.util
import pathlib

import pytest

REPO_ROOT = pathlib.Path(__file__).resolve().parents[2]
BUILDER = REPO_ROOT / "backend" / "scripts" / "build_egy_tariffs_official.py"


@pytest.fixture(scope="module")
def builder():
    """Import direct : le paquet scripts tire des dépendances inutiles ici."""
    spec = importlib.util.spec_from_file_location("egy_builder", BUILDER)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.mark.parametrize(
    "texte,attendu",
    [
        ("ر6790-اتفاقية التجارة الحرة الافريقية القارية مجموعة [أ]تخفض 100%", "ر6790"),
        ("ر6791-اتفاقية التجارة الحرة الافريقية القارية مجموعة [ب] تخفض 60%", "ر6791"),
        ("غ4046-يشتــرط لاستيراد الصنف الحصول على موافقة مسبقة", "غ4046"),
        ("ق3034- لايصرح بتصدير اصناف منصوص عليها فى إتفاقية سايتس", "ق3034"),
        ("  ر6517-ستثنى من الأعفاء", "ر6517"),
    ],
)
def test_le_code_est_lu_dans_le_prefixe_du_texte(builder, texte, attendu):
    assert builder._instruction_code(texte) == attendu


@pytest.mark.parametrize("texte", ["", None, "texte sans code", "6790-sans lettre"])
def test_absence_de_code_rend_none(builder, texte):
    """Sans préfixe reconnaissable, aucun code n'est inventé."""
    assert builder._instruction_code(texte) is None


def test_le_tableau_des_codes_de_l_api_n_est_plus_une_cle_d_appariement(builder):
    """
    Reproduit la réponse réelle de l'API pour 0101210000 : onze instructions,
    douze codes, ordres différents, un doublon. La règle du préfixe doit rendre
    le bon code pour chaque texte, quel que soit ce tableau.
    """
    instructions = [
        "ر6517-ستثنى من الأعفاء",
        "ر6639-تخفض رسوم جمركية",
        "ر6658-يعفى من الرسوم الجمركيه",
        "ر6700-فى ظل اتفاق التجارة الحرة",
        "ر6715-يعفى اعفاء كامل",
        "ر6723-تخفيض منتجات زراعية",
        "ر6790-اتفاقية التجارة الحرة الافريقية القارية مجموعة [أ]تخفض 100%",
        "ر6791-اتفاقية التجارة الحرة الافريقية القارية مجموعة [ب] تخفض 60%",
        "ر7075-تحصل ضريبةقيمة مضافة",
        "غ4046-يشتــرط لاستيراد الصنف",
        "ق3034- لايصرح بتصدير اصناف",
    ]
    # Ordre et longueur réels du tableau InstructionCodes de l'API.
    codes_api = [
        "غ4046",
        "ر6517",
        "ر6639",
        "ر6658",
        "ق3034",
        "ر6700",
        "ر6700",
        "ر6715",
        "ر7075",
        "ر6790",
        "ر6723",
        "ر6791",
    ]
    assert len(codes_api) != len(instructions), "le cas d'espèce doit rester déséquilibré"

    # L'appariement par position ne tombe juste qu'une fois sur onze.
    exacts_par_position = sum(
        1
        for code, texte in zip(codes_api, instructions)
        if code == builder._instruction_code(texte)
    )
    assert exacts_par_position <= 1

    # La règle du préfixe tombe juste à chaque fois.
    for texte in instructions:
        code = builder._instruction_code(texte)
        assert code is not None
        assert texte.lstrip().startswith(code)


def test_les_trois_familles_d_instructions_sont_distinguees(builder):
    """Préférences, formalités et restrictions ont chacune leur préfixe."""
    familles = {
        builder._instruction_code("ر6790-préférence")[0]: "préférence",
        builder._instruction_code("غ4046-formalité")[0]: "formalité",
        builder._instruction_code("ق3034-restriction")[0]: "restriction",
    }
    assert set(familles) == {"ر", "غ", "ق"}
