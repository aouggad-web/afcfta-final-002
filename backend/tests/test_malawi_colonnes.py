"""Malawi — rattacher un taux à SA colonne quand la grille se déplace sous lui.

Le décret dit QUELLE colonne porte quoi (paragraphe 4), il ne dit pas OÙ chaque
colonne tombe sur la page. Or la grille bouge : sur les 556 lignes qui portent
les neuf valeurs, 466 tombent à l'abscisse nominale, mais les pages 452 à 454 —
les véhicules automobiles — glissent jusqu'à 24 unités vers la gauche, presque
une colonne entière. Comparer une abscisse à une grille fixe y lisait le taux de
la colonne voisine : un droit COMESA de 13 % se servait comme droit de douane.

Ces tests tiennent les trois choses qui empêchent cela :
  — un décalage d'ensemble ne change pas la lecture, parce que c'est l'ÉCART
    entre colonnes qui identifie la ligne, non sa position ;
  — une ligne dont le placement HÉSITE est refusée, jamais devinée ;
  — « Zero » et « Exempt » viennent des annexes du VAT Act : ils ne peuvent être
    que dans la colonne TVA, et cette attache tranche l'hésitation sans deviner.
"""

import pathlib
import sys

import pytest

RACINE = pathlib.Path(__file__).resolve().parents[1]
if str(RACINE) not in sys.path:
    sys.path.insert(0, str(RACINE))

pymupdf = pytest.importorskip("pymupdf")

from crawlers.countries import malawi_tariffs_order_scraper as mwi  # noqa: E402

GRILLE = mwi.GRILLE


def _ligne(xs, mots=None):
    mots = mots or ["10%"] * len(xs)
    return list(zip(xs, mots))


def test_les_neuf_valeurs_se_placent_dans_l_ordre_sans_rien_arbitrer():
    assert mwi._colonnes_de_la_ligne(_ligne(GRILLE)) == list(range(9))


def test_un_decalage_d_ensemble_ne_change_pas_la_lecture():
    """Page 452, la grille glisse de 24 unités vers la gauche. La ligne doit se
    lire à l'identique : c'est l'écart entre colonnes qui l'identifie."""
    for decalage in (-24.0, -10.0, 8.0):
        décalée = [x + decalage for x in GRILLE]
        assert mwi._colonnes_de_la_ligne(_ligne(décalée)) == list(range(9)), decalage


def test_une_colonne_absente_est_identifiee_et_non_decalee():
    """Il ne suffit pas de lire huit valeurs : il faut savoir LAQUELLE des neuf
    colonnes manque. Ici c'est l'accise (colonne 10) — la décaler ferait servir
    la TVA comme accise et l'Advance Income Tax comme TVA."""
    sans_accise = [x for i, x in enumerate(GRILLE) if i != 6]
    assert mwi._colonnes_de_la_ligne(_ligne(sans_accise)) == [0, 1, 2, 3, 4, 5, 7, 8]


def test_une_ligne_dont_le_placement_hesite_est_refusee():
    """Une valeur isolée pourrait être n'importe laquelle des neuf colonnes. Un
    taux d'accise servi comme droit de douane est un chiffre faux ; une colonne
    déclarée illisible n'est qu'un manque nommé."""
    assert mwi._colonnes_de_la_ligne(_ligne([GRILLE[3]])) is None


def test_une_ligne_deformee_est_refusee_et_non_ajustee():
    """Des écarts qui ne sont pas ceux de la grille : la ligne ne se lit pas."""
    assert mwi._colonnes_de_la_ligne(_ligne([340.0, 355.0, 372.0, 390.0])) is None


def test_une_mention_du_vat_act_est_rattachee_a_la_colonne_tva():
    """La ligne réelle de 0104.10.10, page 26 : huit valeurs, l'accise absente, et
    « Exempt » posé dix unités à gauche de son abscisse habituelle. Sans l'attache
    documentaire, le placement hésitait entre servir « Exempt » comme accise et le
    servir comme TVA — et la ligne était refusée."""
    xs = [342.2, 369.9, 396.2, 427.8, 453.0, 477.9, 518.3, 556.8]
    mots = ["Free"] * 6 + ["Exempt", "10%"]
    assert mwi._colonnes_de_la_ligne(list(zip(xs, mots))) == [0, 1, 2, 3, 4, 5, 7, 8]


def test_deux_mentions_de_tva_sur_une_ligne_la_font_refuser():
    """Deux « Exempt » sur une ligne : deux lignes du barème se sont fondues, et
    rien ne dit laquelle porte quoi."""
    xs = [GRILLE[0], GRILLE[7], GRILLE[8]]
    assert mwi._colonnes_de_la_ligne(list(zip(xs, ["Exempt", "Exempt", "10%"]))) is None


def test_plus_de_neuf_valeurs_fait_refuser_la_ligne():
    xs = [x - 2 for x in GRILLE] + [GRILLE[-1] + 20]
    assert mwi._colonnes_de_la_ligne(_ligne(xs)) is None


def test_une_valeur_coupee_en_deux_est_recousue():
    """« 30% » sort parfois en deux tokens collés, « 3 » puis « 0% ». Le second
    tombait dans la bande de sa colonne et s'y lisait comme un droit de 0 % :
    0302.49.00 se voyait servir une franchise au lieu de son plein droit de 30 %.
    Coordonnées relevées sur la page 32 du décret."""
    toks = [(340.63, 345.61, "3"), (348.17, 361.50, "0%"), (369.67, 388.05, "25%")]
    assert mwi._recoller(toks) == [(340.63, "30%"), (369.67, "25%")]


def test_deux_colonnes_voisines_ne_sont_jamais_recousues():
    """L'écart entre deux colonnes n'est jamais inférieur à huit unités."""
    toks = [(342.0, 360.0, "3"), (370.0, 388.0, "0%")]
    assert mwi._recoller(toks) == [(342.0, "3"), (370.0, "0%")]


@pytest.mark.parametrize(
    "cellule,attendu",
    [
        ("15%", (15.0, None)),
        ("16.5%", (16.5, None)),
        # « Free » est un ZERO PUBLIE — une franchise, pas une absence.
        ("Free", (0.0, None)),
        # « Zero » : detaxation, VAT Act seconde annexe. Taxee a 0 %.
        ("Zero", (0.0, None)),
        # « Exempt » : premiere annexe. HORS DU CHAMP de la taxe, donc pas un taux.
        ("Exempt", (None, "HORS_CHAMP_DE_LA_TVA")),
        ("", (None, "CELLULE_VIDE")),
        ("n.a.", (None, "EXPRESSION_NON_LUE")),
    ],
)
def test_une_cellule_rend_son_taux_ou_son_motif(cellule, attendu):
    assert mwi.lire_valeur(cellule) == attendu


def test_exonere_et_detaxe_ne_se_confondent_pas():
    """Le VAT Act les traite dans deux annexes differentes : les confondre
    effacerait la distinction que la loi etablit."""
    assert mwi.lire_valeur("Zero")[0] == 0.0
    assert mwi.lire_valeur("Exempt")[0] is None


def test_l_unite_de_quantite_est_lue_sur_un_vocabulaire_ferme():
    """Le dernier mot avant les taux, et seulement s'il est une unite : sinon le
    dernier mot d'une designation qui deborde passerait pour une unite."""
    assert mwi._unite([(200.0, "Carcasses"), (310.0, "."), (317.0, "kg")]) == "kg"
    assert mwi._unite([(200.0, "Vehicles"), (318.0, "U")]) == "U"
    # « 4 » est l'en-tete de la colonne 4, pas une unite.
    assert mwi._unite([(318.0, "4")]) == ""
    assert mwi._unite([(318.0, "heading")]) == ""
    assert mwi._unite([(200.0, "Other")]) == ""
