"""Seychelles — treize colonnes, un calendrier, et une remise qui se déduit.

Le barème de S.I. 113 of 2022 aligne TREIZE colonnes de taux. Une seule est un
droit dû ; les douze autres sont des préférences, dont DIX sont des MILLÉSIMES —
cinq taux SADC et cinq taux ZLECAf, un par année civile de 2022 à 2026. Aucun des
tarifs intégrés avant celui-ci ne publie de calendrier de démantèlement.

Ces tests tiennent ce qui empêche de servir un chiffre faux :

1. LES ABSCISSES NE SONT PAS ÉCRITES EN DUR. La grille se déplace d'une page à
   l'autre — la colonne NPF tombe à 256 page 35 et à 354 page 132 — et c'est
   l'EN-TÊTE de chaque page qui donne ses treize abscisses.

2. « SCR60/l » N'EST PAS UN POURCENTAGE. Un droit spécifique se liquide à la
   quantité ; le lire comme un taux donnerait un montant absurde.

3. « 7% + SCR5/kg » EST UN DROIT COMPOSÉ, et le « + » n'est pas un « or » : les
   deux composantes sont dues ensemble, il n'y a rien à départager. C'est ce qui
   le sépare du « 40% or 240c/kg » sud-africain, qui reste refusé.

4. LA REMISE COI SE DÉDUIT, PARCE QUE LA SCHEDULE II ÉNONCE LA FORMULE — cinq
   POINTS de moins que le NPF, avec cinq exceptions nommées, et rien du tout
   quand le NPF n'est pas un pourcentage.
"""

import pathlib
import sys

import pytest

RACINE = pathlib.Path(__file__).resolve().parents[1]
if str(RACINE) not in sys.path:
    sys.path.insert(0, str(RACINE))

pytest.importorskip("pymupdf")

from crawlers.countries import seychelles_si113_scraper as syc  # noqa: E402


def _mot(x, texte, y=100.0):
    """Un token au format de pymupdf : (x0, y0, x1, y1, mot, ...)."""
    return (x, y, x + 10.0, y + 8.0, texte, 0, 0, 0)


def _entete(base=256.0):
    """Un en-tête de page complet, à l'abscisse que l'on veut."""
    mots = [_mot(base, "MFN", 116.0), _mot(base + 45, "FTA", 126.0),
            _mot(base + 97, "UK", 126.0)]
    for i, annee in enumerate(syc.MILLESIMES):
        mots.append(_mot(base + 138 + 35 * i, annee, 143.0))
    for i, annee in enumerate(syc.MILLESIMES):
        mots.append(_mot(base + 333 + 40 * i, annee, 143.0))
    return mots


def test_les_treize_abscisses_sont_lues_dans_l_en_tete():
    ancres = syc.ancres_de_la_page(_entete(256.0))
    assert ancres is not None
    assert len(ancres) == 13
    assert ancres[0] == 256.0
    assert ancres == sorted(ancres)


def test_la_grille_suit_l_en_tete_quand_la_page_la_deplace():
    """Page 35 la colonne NPF tombe à 256, page 132 à 354 : presque trois colonnes
    d'écart. Écrire les abscisses en dur ferait lire, sur une page, le taux de la
    colonne voisine."""
    gauche = syc.ancres_de_la_page(_entete(256.0))
    droite = syc.ancres_de_la_page(_entete(354.0))
    assert gauche[0] == 256.0 and droite[0] == 354.0
    assert [b - a for a, b in zip(gauche, gauche[1:])] == [
        b - a for a, b in zip(droite, droite[1:])
    ]


def test_un_en_tete_incomplet_ne_sert_pas_de_carte():
    """Neuf pages du barème sur 591 n'en portent pas : elles sont déclarées, pas
    devinées."""
    partiel = [m for m in _entete() if m[4] != "MFN"]
    assert syc.ancres_de_la_page(partiel) is None
    assert syc.ancres_de_la_page([]) is None


def test_chaque_valeur_est_rattachee_a_sa_colonne():
    ancres = syc.ancres_de_la_page(_entete(256.0))
    toks = [(x, "7%") for x in ancres]
    cellules = syc.cellules_de_la_ligne(toks, ancres)
    assert cellules == {rang: "7%" for rang in range(13)}


def test_une_valeur_coupee_en_deux_est_rassemblee_par_colonne():
    """« SCR60/l » sort parfois en « SCR » sur la bande du code et « 60/l » sur la
    bande suivante. Recoller par adjacence horizontale ne verrait pas la coupure
    verticale : les morceaux sont rassemblés par COLONNE."""
    ancres = syc.ancres_de_la_page(_entete(256.0))
    toks = [(ancres[0], "SCR"), (ancres[0] + 1.0, "60/l")]
    assert syc.cellules_de_la_ligne(toks, ancres)[0] == "SCR60/l"


def test_une_valeur_hors_de_toute_colonne_est_ignoree():
    """Le « 99% » d'une désignation (« containing 99% or more by weight ») tombe à
    gauche de la première colonne : il n'est pas un taux."""
    ancres = syc.ancres_de_la_page(_entete(354.0))
    assert syc.cellules_de_la_ligne([(120.0, "99%")], ancres) == {}


@pytest.mark.parametrize(
    "cellule,taux,specifique,motif",
    [
        ("25%", 25.0, None, None),
        # « 0% » et « Free » sont des ZEROS PUBLIES — une franchise, pas une absence.
        ("0%", 0.0, None, None),
        ("Free", 0.0, None, None),
        # Un droit specifique se liquide a la QUANTITE, jamais sur la valeur.
        ("SCR60/l", None, "SCR60/l", None),
        ("SCR0/l", None, "SCR0/l", None),
        ("SCR5.13/kg", None, "SCR5.13/kg", None),
        ("", None, None, "CELLULE_VIDE"),
        ("n.a.", None, None, "EXPRESSION_NON_LUE"),
        # Deux valeurs sous une meme colonne : deux lignes du bareme s'y sont fondues.
        ("0%0%", None, None, "DEUX_VALEURS_DANS_LA_COLONNE"),
    ],
)
def test_une_cellule_rend_son_taux_ou_son_motif(cellule, taux, specifique, motif):
    lu_taux, lu_spec, lu_motif = syc.lire_valeur(cellule)
    assert lu_taux == taux
    assert (lu_spec["brut"] if lu_spec else None) == specifique
    assert lu_motif == motif


def test_un_droit_compose_se_liquide_entierement():
    """« 7% + SCR5/kg » : le « + » n'est pas un « or ». Les deux composantes sont
    dues ENSEMBLE, il n'y a rien à départager, et la ligne se liquide donc tout
    entière — à la différence du « 40% or 240c/kg » sud-africain, qui reste refusé
    parce qu'aucun texte n'y dit laquelle des deux s'applique."""
    taux, specifique, motif = syc.lire_valeur("7%+SCR5/kg")
    assert motif is None
    assert taux == 7.0
    assert specifique["montant"] == 5.0
    assert specifique["unite"] == "kg"
    # `brut` ne porte QUE la composante spécifique : le socle relit cette chaîne
    # pour en tirer le montant unitaire, et lui donner l'expression entière lui
    # faisait lire 7 — le taux ad valorem servi comme un montant en roupies au kilo.
    assert specifique["brut"] == "SCR5/kg"
    assert specifique["compose_avec_taux_pct"] == 7.0


def test_un_droit_specifique_au_paquet_est_lu_avec_son_unite():
    _taux, specifique, motif = syc.lire_valeur("SCR96perpackof200")
    assert motif is None
    assert specifique["montant"] == 96.0
    assert specifique["devise"] == "SCR"


@pytest.mark.parametrize(
    "npf,code,attendu,exception",
    [
        # La formule : cinq POINTS de moins, non cinq pour cent du taux.
        (25.0, "84071000", 20.0, False),
        (7.5, "61091000", 2.5, False),
        # Exception 1 : le taux NPF est deja a 5 % ou moins.
        (5.0, "84071000", 5.0, True),
        (0.0, "84071000", 0.0, True),
        # Exceptions 2 et 3 : chapitres 22 et 24, en entier.
        (25.0, "22030000", 25.0, True),
        (200.0, "24022000", 200.0, True),
        # Exceptions 4 et 5 : positions 27.10 et 27.11, et elles seules.
        (25.0, "27101210", 25.0, True),
        (25.0, "27111100", 25.0, True),
        (25.0, "27129000", 20.0, False),
    ],
)
def test_la_remise_coi_suit_la_formule_de_la_schedule_ii(npf, code, attendu, exception):
    taux, motif = syc.taux_coi(npf, code)
    assert taux == attendu
    assert bool(motif) is exception


def test_la_remise_coi_n_a_pas_de_sens_sur_un_droit_specifique():
    """« 5 % de moins » qu'un droit en roupies au litre ne veut rien dire, et aucun
    texte ne dit comment le calculer. Rien n'est supposé."""
    taux, motif = syc.taux_coi(None, "22030000")
    assert taux is None
    assert "INDEFINIE" in motif


def test_le_calendrier_ne_se_reconduit_pas_de_lui_meme():
    """Le règlement publie cinq années et s'arrête. Passé la dernière, il ne dit
    plus rien : le dernier taux n'est pas reconduit en silence."""
    assert syc.MILLESIMES == ["2022", "2023", "2024", "2025", "2026"]
    annee = syc._annee_en_vigueur()
    assert annee in syc.MILLESIMES or annee == ""


def test_les_trente_huit_etats_parties_sont_ceux_de_la_schedule_vi():
    assert len(syc.ETATS_ZLECAF) == 38
    assert "Republic of South Africa" in syc.ETATS_ZLECAF
    # L'Afrique du Sud EST partie ici, à la différence du Malawi qui l'exclut
    # nommément de sa colonne ZLECAf : chaque pays a sa règle, aucune ne se déduit
    # de celle du voisin.
    assert "Republic of Seychelles" not in syc.ETATS_ZLECAF
