"""La clé de contrôle tunisienne n'est pas une subdivision tarifaire.

Le portail `douane.gov.tn` publie `01012100015`. Ce n'est pas une position à
onze chiffres : c'est la sous-position `0101210001` suivie de la clé `5`, que
le déclarant saisit avec elle sur la déclaration en douane.

Le socle s'indexait sur le code COLLÉ à sa clé. Trois conséquences, toutes
mesurées avant correction :

  - le code qu'un déclarant tape — dix chiffres — se voyait répondre
    « Position nationale introuvable » ;
  - le sélecteur affichait « HS11 digits », c'est-à-dire que le produit
    AFFIRMAIT une nomenclature tunisienne à onze chiffres, qui n'existe pas ;
  - seule la forme à onze caractères calculait, et elle ne s'obtenait qu'en
    recopiant une suggestion.

La preuve que le onzième chiffre est une clé et non un niveau tient dans la
donnée : tronquer les 17 541 codes au dixième caractère donne 17 541
préfixes DISTINCTS. Si c'était une subdivision, plusieurs codes partageraient
leur parent.
"""

import json
import os
import sys
from collections import Counter

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services import authentic_tariff_service  # noqa: E402
from services import socle  # noqa: E402

RACINE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SOCLE = os.path.join(RACINE, "backend", "socle")

besoin_socle = pytest.mark.skipif(
    not os.path.exists(os.path.join(SOCLE, "TUN.json")),
    reason="socle absent (gitignoré) : reconstruire avec scripts/build_socle.py",
)


def _pays(iso3):
    with open(os.path.join(SOCLE, f"{iso3}.json"), encoding="utf-8") as f:
        return json.load(f)


@besoin_socle
def test_le_socle_tunisien_s_indexe_sur_la_position_pas_sur_la_cle():
    """Dix chiffres, pour les 17 542 positions."""
    positions = _pays("TUN")["positions"]
    longueurs = Counter(len(code) for code in positions)
    assert set(longueurs) == {10}, f"des clés hors format : {dict(longueurs)}"


@besoin_socle
def test_la_cle_de_controle_est_conservee_a_cote_du_code():
    """Elle sert à la saisie : on la détache, on ne la jette pas."""
    positions = _pays("TUN")["positions"]
    assert positions["0101210001"]["cle_controle"] == "5"
    portent_une_cle = sum(1 for p in positions.values() if p.get("cle_controle"))
    assert portent_une_cle == 17541, (
        "une seule position est publiée sans clé par la source ; les autres "
        "doivent toutes conserver la leur"
    )


@besoin_socle
def test_la_nomenclature_est_declaree_par_le_pays_lui_meme():
    """Rien n'est déduit d'une longueur : le fichier pays le dit."""
    nomenclature = _pays("TUN")["nomenclature"]
    assert nomenclature["longueur_position"] == 10
    assert "déclaration" in nomenclature["cle_controle"]


@besoin_socle
@pytest.mark.parametrize("saisi", ["0101210001", "01012100015"])
def test_les_deux_formes_saisies_resolvent_la_meme_position(saisi):
    """Celle que le déclarant tape, et celle qu'il recopie de sa déclaration.

    La seconde n'est pas un code tarifaire, mais elle figure sur le document
    qu'il a sous les yeux. La refuser le laisserait sans réponse alors que la
    position est parfaitement connue.
    """
    position, provenance = socle.position("TUN", saisi)
    assert provenance["niveau"] == "national"
    assert position["cle_controle"] == "5"
    assert position["designation"].startswith("Chevaux de course")


@besoin_socle
def test_le_selecteur_affiche_la_position_et_non_la_position_plus_sa_cle():
    """« HS11 digits » était une affirmation fausse sur l'écran."""
    proposees = authentic_tariff_service.get_sub_positions("TUN", "010121", language="fr")
    assert proposees, "la position sentinelle doit se résoudre"
    for entree in proposees:
        assert len(entree["code"]) == 10, f"code affiché hors format : {entree['code']}"
        assert entree["digits"] == 10
        assert entree["cle_controle"]


# ─────────────────────────────────────────────────────────────────────────────
# LES CONTRÔLES NÉGATIFS — c'est ici que se joue la règle du dépôt.
#
# « NE CHERCHE PAS À GÉNÉRALISER » : une nomenclature peut légitimement
# compter onze chiffres. Le détachement ne vaut que pour les pays qui le
# DÉCLARENT.
# ─────────────────────────────────────────────────────────────────────────────


@besoin_socle
def test_l_ethiopie_garde_ses_onze_caracteres():
    """Même longueur, cause différente : son onzième chiffre est un REMPLISSAGE.

    Les 6 296 codes éthiopiens se terminent TOUS par « 0 » — une clé de
    contrôle ne l'est jamais, elle se répartit sur les dix chiffres. L'Éthiopie
    ne déclare donc rien, et rien ne lui est retiré. Appliquer le raisonnement
    tunisien sur la seule foi de la longueur aurait amputé 6 296 positions.
    """
    ethiopie = _pays("ETH")
    assert "nomenclature" not in ethiopie, "l'Éthiopie ne déclare aucune clé de contrôle"
    longueurs = Counter(len(code) for code in ethiopie["positions"])
    assert set(longueurs) == {11}, f"ses codes ont été touchés : {dict(longueurs)}"
    derniers = {code[-1] for code in ethiopie["positions"]}
    assert derniers == {"0"}, (
        "le onzième caractère éthiopien n'est plus uniformément « 0 » : "
        "la justification de ce contrôle est à revérifier"
    )


@besoin_socle
def test_aucun_autre_pays_n_est_touche():
    """Un seul pays déclare, un seul pays change."""
    for iso3 in ("KEN", "DZA", "MAR", "EGY", "MUS"):
        assert "nomenclature" not in _pays(iso3), f"{iso3} ne devrait rien déclarer"


@besoin_socle
def test_un_code_trop_court_ne_gagne_pas_une_position_par_troncature():
    """Le détachement ne doit pas devenir une remontée silencieuse.

    `010121000` (neuf chiffres) n'est ni une position ni une position avec sa
    clé. Il doit échouer, et non se voir servir un voisin.
    """
    with pytest.raises(KeyError):
        socle.position("TUN", "010121000")
