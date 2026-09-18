"""Un régime que le tarif publie doit être montré, sans être appliqué.

Le socle porte, pour six pays, jusqu'à cinq colonnes préférentielles par
position — ``EU_UK``, ``EFTA``, ``SADC``, ``MERCOSUR``, ``AFCFTA`` pour la
SACU, ``COMESA`` pour l'Éthiopie. Une seule était lue : ``AFCFTA``. Les autres
étaient collectées, stockées, jamais montrées.

Le coût, mesuré avant ce lot : la position sud-africaine 020110 publie 40 % en
NPF, 40 % sous ZLECAf et **0 % sous SADC**. Un exportateur mozambicain — membre
SADC selon le roster sourcé du dépôt — se voyait servir 140 000 sur un CIF de
100 000, sans qu'aucun champ ne signale la colonne à 0 %. Sur les six pays,
20 599 positions étaient dans ce cas.

La frontière que ces tests gardent est celle entre MONTRER et APPLIQUER. Le
module refusait de toucher aux zones de libre-échange au motif que « les rendre
à 0 % serait fabriquer une exonération » : vrai d'un taux servi, faux d'un taux
montré avec sa réserve.
"""

from __future__ import annotations

import pytest
from services.preference import SIMULABLES, simulations_regionales
from services.regional_blocs import COMESA, SADC

#: La position qui a révélé le défaut : bœuf en carcasses, tarif sud-africain.
ZAF_BOEUF = {
    "hs6": "020110",
    "droits": [{"code": "DD", "famille": "droit", "taux": 40.0, "assiette": "CIF"}],
    "preferentiels": {
        "EU_UK": {"taux": 40.0},
        "EFTA": {"taux": 40.0},
        "SADC": {"taux": 0.0},
        "MERCOSUR": {"taux": 40.0},
        "AFCFTA": {"taux": 40.0},
    },
}


def test_la_colonne_sadc_est_montree_a_une_origine_membre():
    """Le cas mesuré : 0 % publié sous SADC quand ZLECAf reste à 40 %."""
    simulations = simulations_regionales(ZAF_BOEUF, "ZAF", "MOZ")

    assert [s["regime"] for s in simulations] == ["SADC"]
    assert simulations[0]["taux_publie_pct"] == 0.0
    assert simulations[0]["prelevement"] == "DD"


def test_une_simulation_n_est_jamais_appliquee():
    """La borne qui sépare ce lot d'une fabrication d'exonération.

    Le total servi doit rester celui du régime retenu par
    ``taux_preferentiels``. Si ``applique`` pouvait devenir vrai, une franchise
    dont les règles d'origine ne sont pas vérifiées entrerait dans un montant
    opposable.
    """
    for simulation in simulations_regionales(ZAF_BOEUF, "ZAF", "MOZ"):
        assert simulation["applique"] is False


def test_une_simulation_porte_sa_reserve_d_origine():
    """Un taux montré sans sa condition serait lu comme un droit acquis."""
    simulation = simulations_regionales(ZAF_BOEUF, "ZAF", "MOZ")[0]

    assert "règles d'origine" in simulation["reserve"]
    assert simulation["eligibilite"] == "ORIGINE_ET_DESTINATION_MEMBRES"


@pytest.mark.parametrize("origine", ["MAR", "DZA", "NGA"], ids=["maroc", "algerie", "nigeria"])
def test_aucune_simulation_pour_une_origine_hors_du_bloc(origine):
    """L'éligibilité vient du roster sourcé, pas de la présence d'une colonne.

    La position publie bien un taux SADC ; le montrer à une origine qui n'est
    pas membre suggérerait une franchise à laquelle elle n'a aucun droit.
    """
    assert origine not in SADC
    assert simulations_regionales(ZAF_BOEUF, "ZAF", origine) == []


def test_l_ordre_est_neutre_et_non_classe_par_avantage():
    """Décision de produit, tenue par un test.

    Classer par avantage mettrait en tête le taux le plus bas — c'est-à-dire
    celui dont les règles d'origine sont précisément ce que le moteur ne
    vérifie pas. L'ordre est donc alphabétique, et ne dépend pas des taux.
    """
    position = {
        "hs6": "020110",
        "droits": [{"code": "DD", "famille": "droit", "taux": 40.0, "assiette": "CIF"}],
        # SADC est ici le PLUS avantageux : un tri par montant le mettrait en
        # tête, devant COMESA. L'ordre alphabétique doit tenir malgré ça.
        "preferentiels": {"COMESA": {"taux": 25.0}, "SADC": {"taux": 0.0}},
    }
    # Couloir NOMMÉ, et non calculé. Une première version dérivait le couloir
    # en parcourant deux `frozenset` : l'ordre d'itération variant d'une
    # exécution à l'autre, elle tombait parfois sur un couloir incluant la RD
    # Congo — hors des deux zones — et le test échouait une fois sur deux. Un
    # test intermittent est pire qu'un test absent.
    origine, destination = "ZMB", "ZWE"
    assert {origine, destination} <= set(COMESA) & set(
        SADC
    ), "le test suppose un couloir membre des DEUX zones"

    regimes = [s["regime"] for s in simulations_regionales(position, destination, origine)]

    assert regimes == sorted(regimes), f"ordre non neutre : {regimes}"
    assert regimes == ["COMESA", "SADC"]


def test_les_regimes_hors_afrique_ne_sont_pas_simules():
    """`EU_UK`, `EFTA` et `MERCOSUR` sont au socle mais hors périmètre.

    Leurs colonnes existent pour l'Afrique du Sud, mais ce calculateur sert
    des échanges intra-africains et aucun roster de ces accords n'est établi
    dans le dépôt. Les simuler demanderait d'inventer leurs membres.
    """
    assert "EU_UK" not in SIMULABLES
    assert "EFTA" not in SIMULABLES
    assert "MERCOSUR" not in SIMULABLES


def test_une_colonne_absente_ne_produit_aucune_simulation():
    """Pas de colonne, pas de simulation — aucun taux dérivé du NPF."""
    position = {"hs6": "020110", "droits": [{"code": "DD", "taux": 40.0}], "preferentiels": {}}

    assert simulations_regionales(position, "ZAF", "MOZ") == []


def test_un_droit_specifique_n_est_pas_simule():
    """« 3,2c/kg » sans quantité ne dirait rien, et le convertir demanderait un
    poids que la demande ne porte pas toujours."""
    position = {
        "hs6": "020110",
        "droits": [{"code": "DD", "taux": 40.0}],
        "preferentiels": {"SADC": {"specifique": {"montant": 3.2, "unite": "kg"}}},
    }

    assert simulations_regionales(position, "ZAF", "MOZ") == []


# ── Participation à la ZONE, et non appartenance au BLOC ────────────────────
#
# Défaut de la première version de ce lot, trouvé en vérifiant les rosters
# plutôt qu'en les supposant : `regional_blocs` porte les membres des BLOCS.
# Les lire comme des participants aux ZONES DE LIBRE-ÉCHANGE montrait une
# simulation COMESA à l'Éthiopie et à la RD Congo, qui n'y participent pas.


ETH_BOEUF = {
    "hs6": "020110",
    "droits": [{"code": "DD", "famille": "droit", "taux": 35.0, "assiette": "CIF"}],
    "preferentiels": {"COMESA": {"taux": 10.0}},
}


def test_l_ethiopie_ne_recoit_aucune_simulation_comesa():
    """L'Éthiopie est membre du bloc COMESA, pas de sa zone de libre-échange.

    tralac, page régionale COMESA, « as of 2026 » : la liste des participants
    à la ZLE ne la comprend pas. Son tarif publie pourtant une colonne COMESA
    à 10 % contre 35 % en NPF — c'est précisément ce qui rendait l'erreur
    crédible.
    """
    from services.regional_blocs import COMESA

    assert "ETH" in COMESA, "le test perd son sens si l'Éthiopie quitte le bloc"
    assert simulations_regionales(ETH_BOEUF, "ETH", "EGY") == []


@pytest.mark.parametrize(
    "regime,exclu,partenaire,membre_du_bloc",
    [
        ("COMESA", "COD", "EGY", "COD"),
        ("SADC", "AGO", "ZAF", "AGO"),
        ("SADC", "COD", "ZAF", "COD"),
    ],
    ids=["comesa_rdc", "sadc_angola", "sadc_rdc"],
)
def test_un_membre_du_bloc_hors_zone_ne_recoit_rien(regime, exclu, partenaire, membre_du_bloc):
    """L'Angola et la RD Congo sont dans la SADC sans être dans sa zone.

    sadc.int, « Integration Milestones / Free Trade Area » : « Thirteen out of
    fifteen SADC Member States are part of the Free Trade Area, while Angola
    and Democratic Republic of Congo remain outside. »
    """
    from services.regional_blocs import COMESA, SADC

    roster = COMESA if regime == "COMESA" else SADC
    assert membre_du_bloc in roster, "le test suppose l'appartenance au bloc"

    position = {
        "hs6": "020110",
        "droits": [{"code": "DD", "famille": "droit", "taux": 35.0, "assiette": "CIF"}],
        "preferentiels": {regime: {"taux": 0.0}},
    }

    assert simulations_regionales(position, partenaire, exclu) == []
    assert simulations_regionales(position, exclu, partenaire) == []


def test_l_exclusion_joue_dans_les_deux_sens():
    """Que le pays hors zone soit l'origine ou la destination, rien n'est
    simulé : une zone de libre-échange lie deux participants, pas un seul."""
    position = {
        "hs6": "020110",
        "droits": [{"code": "DD", "famille": "droit", "taux": 40.0, "assiette": "CIF"}],
        "preferentiels": {"SADC": {"taux": 0.0}},
    }

    assert simulations_regionales(position, "AGO", "MOZ") == []
    assert simulations_regionales(position, "MOZ", "AGO") == []
    # Le couloir de contrôle, lui, produit bien sa simulation.
    assert [s["regime"] for s in simulations_regionales(position, "ZAF", "MOZ")] == ["SADC"]


def test_la_table_ne_porte_que_des_exclusions():
    """Borne de conception, et pas seulement de données.

    Retirer un pays ne peut que faire disparaître une simulation ; en ajouter
    un accorderait une franchise indue. Les deux sources disponibles étant
    imparfaites — page SADC non datée, dénombrement tralac incohérent — la
    table ne doit jamais servir à élargir.
    """
    from services.preference import HORS_ZONE_DE_LIBRE_ECHANGE
    from services.regional_blocs import FREE_TRADE_AREAS

    for regime, exclus in HORS_ZONE_DE_LIBRE_ECHANGE.items():
        assert regime in FREE_TRADE_AREAS
        assert exclus <= FREE_TRADE_AREAS[regime], (
            f"{regime} : la table exclut un pays qui n'est pas dans le bloc — "
            "elle servirait donc à autre chose qu'à restreindre"
        )
