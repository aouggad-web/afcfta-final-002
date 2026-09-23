"""Le Kenya sert enfin une préférence ZLECAf — et seulement celle qui est publiée.

Avant ce lot, le moteur rendait ZÉRO préférence ZLECAf sur les 2 756 couples
destination × origine que le socle permet de former. Les 148 qu'il servait
relevaient d'unions douanières antérieures. La cause était une intersection
vide : le Kenya était le seul couloir juridiquement établi, et le seul dont
le tarif ne portait aucun taux préférentiel.

Le barème existe pourtant, publié ligne à ligne par la Legal Notice
EAC/321/2022. Ces tests verrouillent ce qu'il dit — et surtout ce qu'il ne
dit pas.
"""

import datetime
import json
import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.preference import taux_preferentiels  # noqa: E402
from services.zlecaf_schedule_ken import (  # noqa: E402
    DERNIERE_ANNEE,
    LIGNES_COMPOSITES,
    OPPOSABLE_A_PARTIR_DU,
    POSITIONS,
    PREMIERE_ANNEE,
    compute_ken_zlecaf_rate,
)

RACINE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SOCLE_KEN = os.path.join(RACINE, "backend", "socle", "KEN.json")

#: Les quatre bandes du tarif extérieur commun de l'EAC. Le barème ZLECAf
#: prend son taux de base dans cette grille, et nulle part ailleurs.
BANDES_TEC = {0.0, 10.0, 25.0, 35.0}

EN_2026 = datetime.date(2026, 9, 23)


def test_le_bareme_sert_un_taux_lu_dans_la_colonne_publiee():
    """2026 est la sixième annuité : une base de 35 % y vaut 14 %."""
    taux, libelle = compute_ken_zlecaf_rate("02011000", "NGA", EN_2026)
    assert taux == 14.0
    assert "EAC/321/2022" in libelle and "2026" in libelle

    assert compute_ken_zlecaf_rate("01012900", "NGA", EN_2026)[0] == 10.0  # base 25 %
    assert compute_ken_zlecaf_rate("85414100", "NGA", EN_2026)[0] == 0.0  # base 0 %


#: Les dix colonnes publiées pour une base de 35 %, telles que le document
#: les imprime.
ANNUITES_BASE_35 = [31.5, 28.0, 24.5, 21.0, 17.5, 14.0, 10.5, 7.0, 3.5, 0.0]


def test_les_dix_colonnes_publiees_vont_de_2021_a_2030():
    """Ce que le DOCUMENT porte, indépendamment de ce qui est servi."""
    assert (PREMIERE_ANNEE, DERNIERE_ANNEE) == (2021, 2030)
    assert POSITIONS["0201.10.00"]["annuites_pct"] == ANNUITES_BASE_35


def test_le_taux_servi_suit_la_colonne_de_l_annee():
    """À partir de l'opposabilité seulement — les deux ne se confondent pas.

    Le barème PUBLIE une colonne 2021 et une colonne 2022 ; le Kenya ne les
    a pas pour autant rendues opposables avant la gazettisation du
    06/09/2022. Tester le taux servi sur toute la décennie reviendrait à
    exiger du moteur qu'il serve une préférence qui n'était pas due — c'est
    exactement ce que ce lot s'interdit, et c'est ce test qui l'a rappelé.
    """
    for decalage, attendu in enumerate(ANNUITES_BASE_35):
        annee = PREMIERE_ANNEE + decalage
        if annee < OPPOSABLE_A_PARTIR_DU.year:
            continue
        jour = max(datetime.date(annee, 6, 1), OPPOSABLE_A_PARTIR_DU)
        taux, libelle = compute_ken_zlecaf_rate("02011000", "NGA", jour)
        assert taux == attendu, f"{annee} devrait valoir {attendu} %"
        assert str(annee) in libelle


def test_apres_2030_le_droit_reste_eteint():
    """Le barème s'arrête à 2030 ; il s'y arrête à zéro, et le zéro tient."""
    taux, libelle = compute_ken_zlecaf_rate("02011000", "NGA", datetime.date(2035, 6, 1))
    assert taux == 0.0
    assert "2030" in libelle


# ─────────────────────────────────────────────────────────────────────────────
# LES CONTRÔLES NÉGATIFS — ils comptent plus que le chemin nominal.
#
# Un barème préférentiel qui sert un taux de trop est un droit non perçu, et
# c'est l'opérateur qui le découvre au bureau de douane.
# ─────────────────────────────────────────────────────────────────────────────


def test_un_pourcentage_de_la_designation_n_est_pas_un_taux():
    """Le piège qui a fabriqué des bases de 0,25 %, 85 % et 99,99 %.

    Un intitulé de position décrit souvent la COMPOSITION du produit —
    « containing 99% or more lactose », « less than 20% by weight of
    fructose ». Ces pourcentages font corps avec la désignation ; ils ne sont
    ni un droit ni une taxe. Une extraction qui prend le premier « % » du
    segment les ramasse et fabrique un barème faux.

    Le garde est structurel : toute base doit appartenir aux quatre bandes du
    TEC. Aucune des cinquante-cinq positions dont la désignation porte un
    pourcentage n'y échappe.
    """
    hors_bandes = {
        code: ligne["base_pct"]
        for code, ligne in POSITIONS.items()
        if ligne["base_pct"] not in BANDES_TEC
    }
    assert not hors_bandes, (
        "des taux de base sortent des bandes du TEC — signe qu'un pourcentage "
        f"de désignation a été lu comme un droit : {dict(list(hors_bandes.items())[:5])}"
    )

    # Et le cas nommément : 1702.30.00 dit « moins de 20 % de fructose » et
    # porte pourtant une base de 10 %, pas de 20 %.
    assert POSITIONS["1702.30.00"]["base_pct"] == 10.0


def test_chaque_annuite_est_celle_du_document():
    """La régularité est un CONTRÔLE, jamais la règle de production.

    Les colonnes valent `base x (1 - n/10)` sur les 53 420 colonnes du
    document. On le vérifie — mais le module lit la colonne, il ne la calcule
    pas : le jour où une ligne s'en écarterait, c'est elle qui ferait foi.
    """
    ecarts = []
    for code, ligne in POSITIONS.items():
        annuites = ligne["annuites_pct"]
        assert len(annuites) == 10, f"{code} porte {len(annuites)} annuités"
        for n, valeur in enumerate(annuites, start=1):
            if abs(valeur - ligne["base_pct"] * (1 - n / 10.0)) > 0.051:
                ecarts.append((code, n, valeur))
    assert not ecarts, f"annuités non conformes au document : {ecarts[:5]}"


def test_les_taux_composites_sont_hors_bareme():
    """Onze lignes d'aciers publient « 25% or $200/MT whichever is higher ».

    Les ramener à leur volet ad valorem servirait un droit INFÉRIEUR à celui
    qui est dû — le plancher au tonnage disparaîtrait. Elles restent hors
    barème, et la position retombe au NPF.
    """
    assert len(LIGNES_COMPOSITES) == 11
    for code in LIGNES_COMPOSITES:
        assert code not in POSITIONS, f"{code} porte un taux composite et ne doit pas être servi"
        assert compute_ken_zlecaf_rate(code.replace(".", ""), "NGA", EN_2026) == (None, None)


def test_une_position_hors_bareme_ne_se_deduit_pas():
    """611 positions kényannes n'y figurent pas : sensibles, catégories B et C.

    Aucun barème n'est publié pour elles. Le moteur rend None — l'appelant
    reste au NPF — au lieu de dériver un taux du plein droit.
    """
    with open(SOCLE_KEN, encoding="utf-8") as f:
        positions_socle = set(json.load(f)["positions"])
    codes_bareme = {c.replace(".", "") for c in POSITIONS}
    hors_bareme = positions_socle - codes_bareme
    assert len(hors_bareme) > 500, "le barème ne couvre pas tout le tarif, et c'est attendu"
    for code in sorted(hors_bareme)[:20]:
        assert compute_ken_zlecaf_rate(code, "NGA", EN_2026) == (None, None)


def test_rien_n_est_servi_avant_la_gazettisation():
    """Le calendrier commence en 2021, l'instrument n'est opposable qu'en 2022.

    La Directive ministérielle 1/2021 répute le démantèlement commencé au
    1er janvier 2021 (§11), mais dispense expressément de tout remboursement
    des droits perçus avant la mise en œuvre effective (§15). Servir une
    préférence à une date antérieure à la gazettisation ferait dire au
    produit qu'un droit était dû alors qu'il ne l'était pas.
    """
    assert OPPOSABLE_A_PARTIR_DU == datetime.date(2022, 9, 6)
    assert compute_ken_zlecaf_rate("02011000", "NGA", datetime.date(2022, 9, 5)) == (None, None)
    assert compute_ken_zlecaf_rate("02011000", "NGA", datetime.date(2022, 9, 6))[0] is not None


@pytest.mark.parametrize("origine", ["NGA", "GHA", "SEN", "EGY"])
def test_le_bareme_ne_depend_pas_de_l_origine(origine):
    """Le barème ne nomme aucun pays — vérifié sur ses 347 pages.

    L'admission de l'origine est tranchée en amont par le registre
    d'application, qui la tient de l'Annexe 1 de la Directive. Confondre les
    deux ferait porter au barème une condition qu'il n'énonce pas.
    """
    assert compute_ken_zlecaf_rate("02011000", origine, EN_2026)[0] == 14.0


# ─────────────────────────────────────────────────────────────────────────────
# LE PÉRIMÈTRE — la question que le cas algérien a appris à poser.
# ─────────────────────────────────────────────────────────────────────────────


def _position(code):
    with open(SOCLE_KEN, encoding="utf-8") as f:
        return json.load(f)["positions"][code]


def test_la_preference_ne_reduit_que_le_droit_de_douane():
    """L'IDF et le RDL restent dus au taux plein.

    Le tarif kényan porte l'Import Declaration Fee (3,5 %) et le Railway
    Development Levy (2 %), que le socle classe en `redevance` et non en
    `droit`. L'article 7(3) du Protocole définit pourtant le droit
    d'importation largement, avec une exclusion pour les redevances de
    l'article VIII du GATT — mais AUCUNE détermination publiée ne qualifie
    ces deux-là, et les exonérations du Miscellaneous Fees and Levies Act ne
    visent que l'origine EAC.

    Le moteur sert donc ce que le Kenya perçoit, pas ce qu'on croit qu'il
    devrait percevoir. Étendre le périmètre sans texte ferait perdre une
    recette qui est due ; c'est l'erreur inverse du cas algérien, où le DAPS
    était expressément adjoint.
    """
    resultat = taux_preferentiels(_position("02011000"), "KEN", "NGA", "02011000")
    assert resultat["applique"] is True
    assert resultat["regime"] == "ZLECAF"
    assert set(resultat["taux"]) == {"DD"}, (
        "seul le droit de douane est réduit : l'IDF et le RDL n'ont pas de "
        "détermination publiée qui les rattache à la concession"
    )
    assert resultat["taux"]["DD"]["taux"] == 14.0


def test_la_preference_est_refusee_a_une_origine_non_admise():
    """Le barème ne suffit pas : encore faut-il que le couloir soit ouvert.

    Le Maroc n'est pas à l'Annexe 1 de la Directive. Le registre refuse donc
    avant même que le barème soit consulté.
    """
    resultat = taux_preferentiels(_position("02011000"), "KEN", "MAR", "02011000")
    assert resultat["applique"] is False
    assert resultat["taux"] == {}


def test_une_position_hors_bareme_rend_preference_non_tracee():
    """Couloir ouvert, mais rien de publié pour cette position : on le dit."""
    with open(SOCLE_KEN, encoding="utf-8") as f:
        positions_socle = json.load(f)["positions"]
    codes_bareme = {c.replace(".", "") for c in POSITIONS}
    hors = next(c for c in sorted(positions_socle) if c not in codes_bareme)
    resultat = taux_preferentiels(positions_socle[hors], "KEN", "NGA", hors)
    assert resultat["applique"] is False
    assert resultat["statut"] == "PREFERENCE_NON_TRACEE"
