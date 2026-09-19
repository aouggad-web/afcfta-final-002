"""Un droit qui publie deux composantes sans dire laquelle s'applique.

Le tarif SARS publie « 40% or 240c/kg » sur 140 positions : les deux
composantes sont là, la règle qui les départage ne l'est pas. Le crawl a
délibérément gardé `raw_value` verbatim sans trancher — sa propre métadonnée
l'écrit : « 321 lignes composées — raw_value verbatim ».

Le socle, lui, lisait `specific_value` et seulement en l'ABSENCE de taux ad
valorem. Un droit composé perdait donc sa part spécifique ET son verbatim, et
le moteur servait 40 % comme s'il était le droit entier. Sur la position
020110, la part spécifique l'emporte dès que la valeur unitaire passe sous
6,00 ZAR/kg (240c/kg contre 40 % de la valeur) : l'écart n'est pas théorique.

Ces tests gardent la règle du dépôt appliquée à ce cas qui y échappait : un
inconnu se dit, il ne s'approxime pas.
"""

from __future__ import annotations

from services.calcul import COMPLET, INDISPONIBLE, MANQUE_REGLE_COMPOSEE, calculer

COMPOSE = {
    "designation": "Carcasses and half-carcasses",
    "hs6": "020110",
    "unite": "kg",
    "droits": [
        {
            "code": "DD",
            "famille": "droit",
            "taux": 40.0,
            "specifique": "240c/kg",
            "assiette": "CIF",
            "compose": True,
            "expression_brute": "40% or 240c/kg",
            "source": "sars.gov.za",
        }
    ],
}


def test_un_droit_compose_n_est_pas_liquide_a_sa_seule_part_ad_valorem():
    """Le défaut mesuré : 40 % servi comme s'il était le droit entier."""
    resultat = calculer(COMPOSE, 100000.0)["npf"]
    ligne = resultat["lignes"][0]

    assert ligne["statut"] == MANQUE_REGLE_COMPOSEE
    assert ligne["montant"] is None
    assert resultat["etat"] == INDISPONIBLE


def test_les_deux_composantes_et_le_verbatim_restent_lisibles():
    """Refuser de liquider n'autorise pas à cacher ce que la source publie.

    L'opérateur doit pouvoir constater lui-même les deux composantes, et son
    douanier vérifier le verbatim contre le tarif.
    """
    ligne = calculer(COMPOSE, 100000.0)["npf"]["lignes"][0]

    assert ligne["expression_brute"] == "40% or 240c/kg"
    assert ligne["composantes"] == {"ad_valorem_pct": 40.0, "specifique": "240c/kg"}


def test_le_manque_est_nomme_dans_la_reponse():
    """Un refus silencieux serait indiscernable d'une absence de donnée."""
    manques = calculer(COMPOSE, 100000.0)["npf"]["manques"]

    assert {"code": "DD", "motif": MANQUE_REGLE_COMPOSEE} in manques


def test_un_droit_ad_valorem_simple_reste_liquide():
    """La contrepartie : le garde-fou ne doit mordre que sur le cas composé."""
    simple = dict(COMPOSE, droits=[dict(COMPOSE["droits"][0])])
    simple["droits"][0].pop("compose")
    simple["droits"][0].pop("specifique")
    simple["droits"][0].pop("expression_brute")

    resultat = calculer(simple, 100000.0)["npf"]

    assert resultat["etat"] == COMPLET
    assert resultat["lignes"][0]["montant"] == 40000.0


def test_un_droit_purement_specifique_reste_liquide():
    """Un « 8c/kg » sans part ad valorem n'est pas composé : il se liquide à la
    quantité, comme avant."""
    specifique = dict(
        COMPOSE,
        droits=[
            {
                "code": "DD",
                "famille": "droit",
                "taux": None,
                "specifique": "8c/kg",
                "assiette": "CIF",
                "source": "sars.gov.za",
            }
        ],
    )

    resultat = calculer(specifique, 100000.0, quantite=1000.0)["npf"]

    assert resultat["lignes"][0]["statut"] != MANQUE_REGLE_COMPOSEE


# ── L'autre forme composée : « 450c/kg with a maximum of 96% » ───────────────
#
# Celle-ci n'est PAS une inconnue : elle énonce sa propre règle. Le droit est
# le spécifique, borné à un pourcentage de la valeur en douane. 46 positions
# sud-africaines la portent (lait, crème).
#
# Le crawl avait rangé 96,0 dans `rate_pct` — le PLAFOND pris pour le TAUX. Le
# moteur liquidait donc 96 % ad valorem. Sur 10 000 kg de lait à 50 ZAR/kg :
# 480 000 servis contre 45 000 réellement dus. Un facteur dix.

PLAFONNE = {
    "designation": "Milk, not concentrated",
    "hs6": "040210",
    "unite": "kg",
    "droits": [
        {
            "code": "DD",
            "famille": "droit",
            "taux": None,
            "specifique": {
                "montant": 4.5,
                "unite_quantite": "kg",
                "brut": "450c/kg",
            },
            "assiette": "xQTE",
            "plafond_ad_valorem_pct": 96.0,
            "expression_brute": "450c/kg with a maximum of 96%",
            "source": "sars.gov.za",
        }
    ],
}


def test_le_droit_specifique_s_applique_quand_le_plafond_ne_mord_pas():
    """Marchandise de valeur normale : 450c/kg, pas 96 %."""
    ligne = calculer(PLAFONNE, 500000.0, quantite=10000.0)["npf"]["lignes"][0]

    assert ligne["montant"] == 45000.0
    assert ligne.get("plafond_applique") is not True
    # La borne est annoncée même sans mordre : l'opérateur doit pouvoir la lire.
    assert ligne["plafond_ad_valorem_montant"] == 480000.0


def test_le_plafond_borne_le_droit_sur_une_marchandise_de_faible_valeur():
    """C'est tout l'objet de la borne : 450c/kg deviendrait confiscatoire."""
    ligne = calculer(PLAFONNE, 20000.0, quantite=10000.0)["npf"]["lignes"][0]

    assert ligne["montant"] == 19200.0  # 96 % de 20 000
    assert ligne["plafond_applique"] is True
    assert ligne["montant_avant_plafond"] == 45000.0


def test_le_plafond_n_est_jamais_liquide_comme_un_taux():
    """Le défaut mesuré, dans les deux sens.

    Servir 96 % sur une valeur de 500 000 donnerait 480 000 — plus de dix fois
    le droit dû. Le test borne l'erreur par le haut.
    """
    ligne = calculer(PLAFONNE, 500000.0, quantite=10000.0)["npf"]["lignes"][0]

    assert ligne["montant"] != 480000.0
    assert ligne["montant"] < 500000.0 * 96.0 / 100.0


def test_cette_forme_n_est_pas_traitee_comme_non_tranchee():
    """La distinction entre les deux formes composées.

    « with a maximum of » dit sa règle ; « or » ne la dit pas. Les confondre
    ferait refuser 46 positions parfaitement calculables — ou, pire, liquider
    les 94 autres sur une composante choisie au hasard.
    """
    ligne = calculer(PLAFONNE, 500000.0, quantite=10000.0)["npf"]["lignes"][0]

    assert ligne["statut"] != MANQUE_REGLE_COMPOSEE
