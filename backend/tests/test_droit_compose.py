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
