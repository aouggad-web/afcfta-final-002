"""
Estimation d'expédition : de la valeur FOB au nombre et au type de conteneurs,
et indice valeur/poids réutilisable comme repère de négociation d'achat.

PROBLÈME RÉSOLU (1) : le coût rendu (landed cost) des scénarios Opportunités
n'ajoutait que le fret d'UN SEUL conteneur 20′ (TEU), quelle que soit la
valeur FOB saisie — une opération de 2 M$ était facturée comme un unique
conteneur. Ce module estime le POIDS de la marchandise à partir de sa valeur
FOB (ratio valeur/poids), en déduit le NOMBRE et le TYPE de conteneurs
nécessaires, pour que le coût de fret soit multiplié en conséquence.

AMÉLIORATION (2) : l'indice valeur/poids sert à DEUX usages — (a) le
dimensionnement logistique ci-dessus, et (b) un repère grossier pour la
négociation du prix d'achat, quand le produit correspond à une matière
première cotée sur un marché mondial (café, cacao, coton, métaux LME, or,
pétrole...). Deux niveaux de qualité, distingués par `classification_source` :

  - "cours_mondial"       : cours RÉEL d'une bourse/organisme de référence
                            (ICE, LME, CBOT, LBMA...), recherché et daté
                            (voir _WORLD_MARKET_BENCHMARKS). C'est un prix
                            RÉEL et SOURCÉ, mais reste un cours de RÉFÉRENCE
                            pour une qualité/grade standard — jamais un devis
                            garanti pour une opération précise (qualité,
                            origine, incoterm et contrat font varier le prix
                            réel négocié). Champ `negotiation` explicite ce
                            garde-fou à chaque sortie.
  - "estimation_chapitre" : à défaut de cours mondial identifié pour ce
                            produit, ordre de grandeur par chapitre SH
                            (UN Comtrade / BACI) — dimensionnement logistique
                            uniquement, PAS une base de négociation fiable
                            (c'est explicitement signalé dans la sortie).

DISCIPLINE « zéro fabrication » : le poids reste une ESTIMATION dérivée d'un
ratio, jamais une donnée réelle en soi. Chaque cours mondial porte sa date,
sa source exacte et sa valeur brute avant conversion — à rafraîchir
périodiquement (cours de marché, pas figés). Si l'appelant fournit un poids
réel (`weight_kg_override`), toute estimation est ignorée.
"""

from __future__ import annotations

import json
import math
import os
from typing import Dict, Optional

# Capacités utiles (charge maximale) des conteneurs — identiques à celles du
# comparateur multimodal (multimodal_freight_service : TEU 21 600 kg, FEU
# 26 400 kg). Redéclarées ici pour éviter une dépendance circulaire.
TEU_CAPACITY_KG = 21_600  # conteneur 20 pieds
FEU_CAPACITY_KG = 26_400  # conteneur 40 pieds

# ---------------------------------------------------------------------------
# Conversions d'unités boursières -> kg (constantes physiques, pas des cours)
# ---------------------------------------------------------------------------
_LB_TO_KG = 0.45359237
_TROY_OZ_TO_KG = 0.0311034768
_TONNE_TO_KG = 1000.0
# Poids conventionnel du boisseau ("bushel") — varie par céréale (masse
# volumique du grain), valeurs standard USDA.
_BUSHEL_TO_KG = {"wheat": 27.2155, "soybeans": 27.2155, "corn": 25.40117}
# 1 baril = 158.987 L ; masse volumique moyenne d'un brut de référence
# (Brent/WTI, ~38-40° API) ~0.85 kg/L — donne ~135 kg/baril.
_BARREL_TO_KG = 158.987 * 0.85

# ---------------------------------------------------------------------------
# Classification logistique par code SH : vrac vs conteneurisable, éligibilité
# à l'aérien, classe de navire vraquier.
#
# PROBLÈME RÉSOLU : le comparateur multimodal proposait un fret aérien pour
# n'importe quelle marchandise (ex. ciment) sans limite de poids, et
# conteneurisait par défaut des matières premières qui ne voyagent jamais en
# conteneur dans la réalité (blé, minerai de fer, charbon, ciment en vrac...).
#
# Table de référence unique (docs/PLAN_FRET_VRAQUIER.md, Annexe A) couvrant
# tous les produits susceptibles d'utiliser le mode vraquier, en quatre
# catégories :
#   - "bulk_major"  : vrac sec majeur (minerai de fer, bauxite, charbon,
#                     grandes céréales, soja, phosphates) — panamax/capesize
#                     possibles ;
#   - "bulk_minor"  : vrac sec mineur (ciment, sucre, engrais, concentrés de
#                     minerais, tourteaux, ferraille...) — handysize/supramax ;
#   - "neobulk"     : conventionnel/neo-bulk (grumes, bois sciés, pâtes,
#                     aciers semi-finis) — cales vraquiers ou navires
#                     conventionnels ;
#   - "liquid_bulk" : vrac liquide (brut, raffinés, GPL/GNL, huiles végétales
#                     en vrac, mélasses...) — marché tanker, hors périmètre du
#                     comparateur vraquier sec.
#
# Chaque entrée peut porter un seuil de bascule propre (`threshold_t`) : en
# dessous, le mode réel reste le conteneur ensaché/conditionné (bi-modes :
# riz, farines, arachides, cacao méga-lot...). Défaut :
# BULK_CONTAINER_THRESHOLD_TONNES.
#
# Effets : jamais d'aérien quel que soit le poids ; type de cargaison
# terrestre par défaut = "bulk" (CARGO_FACTORS, logistics_land_fees_data) ;
# classe(s) de navire admissible(s) exposée(s) pour le fret vraquier
# (logistics_bulk_fees_data). Les marchandises générales absentes de la table
# (café, thé, coton, cajou, manufacturés...) restent au régime général :
# conteneur, aérien sous plafond de poids (AIR_FREIGHT_MAX_KG_GENERAL).
#
# Recherche par spécificité décroissante (6, 4 puis 2 chiffres) — le 6 permet
# de séparer le coke de pétrole (271311/12, vrac sec) des résidus bitumineux
# (2713, liquide).
BULK_CONTAINER_THRESHOLD_TONNES = 2000.0

# Champs par entrée : label, category, vessels (classes admissibles, ordre
# croissant de taille) ; optionnels : threshold_t (seuil bi-mode), note.
_BULK_COMMODITY_TABLE: Dict[str, Dict] = {
    # --- Vrac sec majeur (A.1) ---
    "1001": {
        "label": "Blé",
        "category": "bulk_major",
        "vessels": ["handysize", "supramax", "panamax"],
    },
    "1003": {
        "label": "Orge",
        "category": "bulk_major",
        "vessels": ["handysize", "supramax", "panamax"],
    },
    "1005": {
        "label": "Maïs",
        "category": "bulk_major",
        "vessels": ["handysize", "supramax", "panamax"],
    },
    "1007": {"label": "Sorgho", "category": "bulk_major", "vessels": ["handysize", "supramax"]},
    "1201": {"label": "Soja (fèves)", "category": "bulk_major", "vessels": ["supramax", "panamax"]},
    "2510": {
        "label": "Phosphates naturels",
        "category": "bulk_major",
        "vessels": ["handysize", "supramax", "panamax"],
    },
    "2601": {
        "label": "Minerai de fer",
        "category": "bulk_major",
        "vessels": ["panamax", "capesize"],
    },
    "2606": {"label": "Bauxite", "category": "bulk_major", "vessels": ["panamax", "capesize"]},
    "2818": {"label": "Alumine", "category": "bulk_major", "vessels": ["supramax", "panamax"]},
    "2701": {
        "label": "Houille (charbon)",
        "category": "bulk_major",
        "vessels": ["supramax", "panamax", "capesize"],
    },
    "2702": {"label": "Lignite", "category": "bulk_major", "vessels": ["supramax", "panamax"]},
    "2704": {
        "label": "Coke de houille",
        "category": "bulk_major",
        "vessels": ["supramax", "panamax"],
    },
    # --- Vrac sec mineur (A.2) ---
    "1002": {"label": "Seigle", "category": "bulk_minor", "vessels": ["handysize"]},
    "1004": {"label": "Avoine", "category": "bulk_minor", "vessels": ["handysize"]},
    "1006": {
        "label": "Riz",
        "category": "bulk_minor",
        "vessels": ["handysize", "supramax"],
        "threshold_t": 5000.0,
        "note": "massivement ensaché en conteneur sous le seuil",
    },
    "1008": {"label": "Autres céréales", "category": "bulk_minor", "vessels": ["handysize"]},
    "11": {
        "label": "Produits de la minoterie (farines, semoules, malt)",
        "category": "bulk_minor",
        "vessels": ["handysize"],
        "threshold_t": 5000.0,
    },
    "1202": {
        "label": "Arachides",
        "category": "bulk_minor",
        "vessels": ["handysize"],
        "threshold_t": 5000.0,
        "note": "conteneur dominant sous le seuil",
    },
    "1205": {"label": "Colza", "category": "bulk_minor", "vessels": ["handysize", "supramax"]},
    "1206": {
        "label": "Tournesol (graines)",
        "category": "bulk_minor",
        "vessels": ["handysize", "supramax"],
    },
    "1207": {
        "label": "Autres graines oléagineuses",
        "category": "bulk_minor",
        "vessels": ["handysize", "supramax"],
    },
    "1701": {
        "label": "Sucre",
        "category": "bulk_minor",
        "vessels": ["handysize", "supramax"],
        "note": "brut en vrac ; sucre blanc souvent ensaché",
    },
    "1801": {
        "label": "Cacao (fèves)",
        "category": "bulk_minor",
        "vessels": ["supramax"],
        "threshold_t": 12000.0,
        "note": "méga-lot vrac réel (Abidjan/Tema→Europe) ; sacs/conteneurs en dessous",
    },
    "2302": {"label": "Sons et remoulages", "category": "bulk_minor", "vessels": ["handysize"]},
    "2304": {
        "label": "Tourteaux de soja",
        "category": "bulk_minor",
        "vessels": ["handysize", "supramax"],
    },
    "2305": {"label": "Tourteaux d'arachide", "category": "bulk_minor", "vessels": ["handysize"]},
    "2306": {
        "label": "Autres tourteaux",
        "category": "bulk_minor",
        "vessels": ["handysize", "supramax"],
    },
    "2308": {
        "label": "Matières végétales fourragères",
        "category": "bulk_minor",
        "vessels": ["handysize"],
    },
    "2309": {
        "label": "Préparations pour animaux",
        "category": "bulk_minor",
        "vessels": ["handysize"],
    },
    "0714": {
        "label": "Manioc séché (cossettes)",
        "category": "bulk_minor",
        "vessels": ["handysize"],
    },
    "2501": {"label": "Sel", "category": "bulk_minor", "vessels": ["handysize"]},
    "2503": {"label": "Soufre", "category": "bulk_minor", "vessels": ["handysize", "supramax"]},
    "2507": {"label": "Kaolin", "category": "bulk_minor", "vessels": ["handysize"]},
    "2508": {"label": "Argiles", "category": "bulk_minor", "vessels": ["handysize"]},
    "2515": {
        "label": "Marbre (blocs)",
        "category": "bulk_minor",
        "vessels": ["handysize"],
        "note": "conventionnel",
    },
    "2516": {
        "label": "Granit (blocs)",
        "category": "bulk_minor",
        "vessels": ["handysize"],
        "note": "conventionnel",
    },
    "2517": {"label": "Granulats", "category": "bulk_minor", "vessels": ["handysize"]},
    "2520": {"label": "Gypse", "category": "bulk_minor", "vessels": ["handysize"]},
    "2521": {
        "label": "Castines (pierres à chaux)",
        "category": "bulk_minor",
        "vessels": ["handysize"],
    },
    "2523": {
        "label": "Ciment et clinker",
        "category": "bulk_minor",
        "vessels": ["handysize", "supramax"],
    },
    "25": {"label": "Produits minéraux bruts", "category": "bulk_minor", "vessels": ["handysize"]},
    "2602": {
        "label": "Minerai de manganèse",
        "category": "bulk_minor",
        "vessels": ["supramax", "panamax"],
    },
    "2603": {
        "label": "Concentrés de cuivre",
        "category": "bulk_minor",
        "vessels": ["handysize", "supramax"],
    },
    "2604": {"label": "Minerai de nickel", "category": "bulk_minor", "vessels": ["handysize"]},
    "2605": {"label": "Minerai de cobalt", "category": "bulk_minor", "vessels": ["handysize"]},
    "2607": {"label": "Concentrés de plomb", "category": "bulk_minor", "vessels": ["handysize"]},
    "2608": {"label": "Concentrés de zinc", "category": "bulk_minor", "vessels": ["handysize"]},
    "2610": {"label": "Minerai de chrome", "category": "bulk_minor", "vessels": ["supramax"]},
    "2614": {
        "label": "Minerais de titane (sables minéralisés)",
        "category": "bulk_minor",
        "vessels": ["handysize"],
    },
    "2615": {
        "label": "Minerais de zirconium et niobium",
        "category": "bulk_minor",
        "vessels": ["handysize"],
    },
    "2618": {"label": "Laitiers granulés", "category": "bulk_minor", "vessels": ["handysize"]},
    "2619": {"label": "Scories et cendres", "category": "bulk_minor", "vessels": ["handysize"]},
    "26": {
        "label": "Minerais et concentrés (autres)",
        "category": "bulk_minor",
        "vessels": ["handysize", "supramax"],
    },
    "271311": {
        "label": "Coke de pétrole non calciné",
        "category": "bulk_minor",
        "vessels": ["supramax"],
    },
    "271312": {
        "label": "Coke de pétrole calciné",
        "category": "bulk_minor",
        "vessels": ["supramax"],
    },
    "31": {"label": "Engrais", "category": "bulk_minor", "vessels": ["handysize", "supramax"]},
    "7204": {"label": "Ferraille", "category": "bulk_minor", "vessels": ["handysize", "supramax"]},
    "27": {
        "label": "Combustibles minéraux (autres)",
        "category": "bulk_minor",
        "vessels": ["handysize"],
    },
    # --- Conventionnel / neo-bulk (A.3) ---
    "4401": {
        "label": "Copeaux et plaquettes de bois",
        "category": "neobulk",
        "vessels": ["handysize", "supramax"],
    },
    "4403": {"label": "Grumes (bois bruts)", "category": "neobulk", "vessels": ["handysize"]},
    "4406": {"label": "Traverses en bois", "category": "neobulk", "vessels": ["handysize"]},
    "4407": {"label": "Bois sciés", "category": "neobulk", "vessels": ["handysize"]},
    "47": {"label": "Pâtes de bois", "category": "neobulk", "vessels": ["handysize"]},
    "7201": {"label": "Fontes brutes", "category": "neobulk", "vessels": ["handysize"]},
    "7203": {
        "label": "Produits ferreux primaires",
        "category": "neobulk",
        "vessels": ["handysize"],
    },
    # --- Vrac liquide (A.4) — marché tanker, hors périmètre vraquier sec ---
    "2709": {"label": "Pétrole brut", "category": "liquid_bulk", "vessels": ["tanker"]},
    "2710": {
        "label": "Produits pétroliers raffinés",
        "category": "liquid_bulk",
        "vessels": ["tanker"],
    },
    "2711": {"label": "GPL / GNL", "category": "liquid_bulk", "vessels": ["tanker"]},
    "2712": {"label": "Paraffines et cires", "category": "liquid_bulk", "vessels": ["tanker"]},
    "2713": {"label": "Résidus bitumineux", "category": "liquid_bulk", "vessels": ["tanker"]},
    "2714": {"label": "Bitumes naturels", "category": "liquid_bulk", "vessels": ["tanker"]},
    "2715": {"label": "Mélanges bitumineux", "category": "liquid_bulk", "vessels": ["tanker"]},
    "1703": {"label": "Mélasses", "category": "liquid_bulk", "vessels": ["tanker"]},
    "2207": {"label": "Éthanol en vrac", "category": "liquid_bulk", "vessels": ["tanker"]},
    "2807": {"label": "Acide sulfurique", "category": "liquid_bulk", "vessels": ["tanker"]},
    "2814": {"label": "Ammoniac", "category": "liquid_bulk", "vessels": ["tanker"]},
}
# Aciers semi-finis, longs et plats (7207-7216) : neo-bulk.
for _hs in ("7207", "7208", "7209", "7210", "7211", "7212", "7213", "7214", "7215", "7216"):
    _BULK_COMMODITY_TABLE[_hs] = {
        "label": "Aciers semi-finis, longs et plats (neo-bulk)",
        "category": "neobulk",
        "vessels": ["handysize"],
    }
# Huiles végétales en vrac (1507-1518) : tanker ; flexitank/conteneur sous seuil.
for _hs in (
    "1507",
    "1508",
    "1509",
    "1510",
    "1511",
    "1512",
    "1513",
    "1514",
    "1515",
    "1516",
    "1517",
    "1518",
):
    _BULK_COMMODITY_TABLE[_hs] = {
        "label": "Huiles végétales en vrac",
        "category": "liquid_bulk",
        "vessels": ["tanker"],
        "note": "flexitank/conteneur sous le seuil de lot",
    }
del _hs


def classify_bulk_commodity(hs_code: str) -> Optional[Dict]:
    """
    Classification vrac d'un code SH selon la table de référence (Annexe A du
    plan fret vraquier) — ``None`` pour une marchandise générale
    (conteneurisable, aérien sous plafond de poids).

    Retour : ``category`` (bulk_major | bulk_minor | neobulk | liquid_bulk),
    ``label``, ``hs_match``, ``vessel_classes`` (classes de navires
    admissibles), ``container_threshold_tonnes`` (en dessous : conteneur
    ensaché/conditionné), ``bi_mode`` (seuil propre au produit),
    ``is_liquid`` (marché tanker) et ``note`` éventuelle.
    """
    normalized = (hs_code or "").strip().replace(".", "").replace(" ", "")
    for prefix_len in (6, 4, 2):
        prefix = normalized[:prefix_len]
        if len(prefix) < prefix_len:
            continue
        entry = _BULK_COMMODITY_TABLE.get(prefix)
        if entry is None:
            continue
        threshold = entry.get("threshold_t", BULK_CONTAINER_THRESHOLD_TONNES)
        return {
            "category": entry["category"],
            "label": entry["label"],
            "hs_match": prefix,
            "vessel_classes": list(entry["vessels"]),
            "container_threshold_tonnes": threshold,
            "bi_mode": "threshold_t" in entry,
            "is_liquid": entry["category"] == "liquid_bulk",
            "note": entry.get("note"),
        }
    return None


# Ratio valeur/poids (USD par kg) par chapitre SH (2 chiffres). Ordres de
# grandeur documentés (valeurs unitaires typiques du commerce mondial) — voir
# docstring. Un chapitre absent retombe sur _DEFAULT_USD_PER_KG.
_USD_PER_KG_BY_CHAPTER: Dict[str, float] = {
    # Animaux vivants & produits animaux (01–05)
    "01": 3.0,
    "02": 4.0,
    "03": 4.5,
    "04": 3.0,
    "05": 2.0,
    # Produits végétaux (06–14) — majorité de vrac agricole bon marché
    "06": 3.0,
    "07": 1.0,
    "08": 1.5,
    "09": 4.0,
    "10": 0.4,
    "11": 0.8,
    "12": 1.2,
    "13": 5.0,
    "14": 1.5,
    # Graisses & huiles (15)
    "15": 1.3,
    # Aliments préparés, boissons, tabac (16–24)
    "16": 5.0,
    "17": 0.8,
    "18": 3.5,
    "19": 2.5,
    "20": 2.0,
    "21": 4.0,
    "22": 2.0,
    "23": 0.5,
    "24": 12.0,
    # Produits minéraux (25–27) — très lourds, très bon marché
    "25": 0.3,
    "26": 0.2,
    "27": 0.6,
    # Chimie & industries connexes (28–38)
    "28": 2.0,
    "29": 6.0,
    "30": 60.0,
    "31": 0.5,
    "32": 4.0,
    "33": 20.0,
    "34": 3.0,
    "35": 3.0,
    "36": 6.0,
    "37": 15.0,
    "38": 3.5,
    # Plastiques & caoutchouc (39–40)
    "39": 3.0,
    "40": 3.5,
    # Cuirs, fourrures (41–43)
    "41": 4.0,
    "42": 25.0,
    "43": 40.0,
    # Bois, liège, vannerie (44–46)
    "44": 0.8,
    "45": 3.0,
    "46": 4.0,
    # Papier & pâte (47–49)
    "47": 0.7,
    "48": 1.5,
    "49": 5.0,
    # Textiles (50–63)
    "50": 30.0,
    "51": 12.0,
    "52": 5.0,
    "53": 3.0,
    "54": 6.0,
    "55": 5.0,
    "56": 5.0,
    "57": 8.0,
    "58": 12.0,
    "59": 8.0,
    "60": 10.0,
    "61": 18.0,
    "62": 18.0,
    "63": 8.0,
    # Chaussures, coiffures, etc. (64–67)
    "64": 15.0,
    "65": 15.0,
    "66": 10.0,
    "67": 12.0,
    # Pierres, plâtre, céramique, verre (68–70)
    "68": 1.5,
    "69": 2.0,
    "70": 3.0,
    # Perles, pierres & métaux précieux (71) — extrêmement cher au kg
    "71": 2000.0,
    # Métaux communs & ouvrages (72–83)
    "72": 0.9,
    "73": 2.5,
    "74": 8.0,
    "75": 15.0,
    "76": 4.0,
    "78": 2.5,
    "79": 3.0,
    "80": 25.0,
    "81": 30.0,
    "82": 12.0,
    "83": 6.0,
    # Machines & matériel électrique (84–85)
    "84": 15.0,
    "85": 40.0,
    # Matériel de transport (86–89)
    "86": 12.0,
    "87": 15.0,
    "88": 400.0,
    "89": 8.0,
    # Instruments de précision, optique, horlogerie (90–92)
    "90": 80.0,
    "91": 150.0,
    "92": 30.0,
    # Armes (93)
    "93": 50.0,
    # Meubles, jouets, ouvrages divers (94–96)
    "94": 6.0,
    "95": 12.0,
    "96": 15.0,
    # Objets d'art & antiquités (97)
    "97": 500.0,
}

# Défaut prudent (produit manufacturé « moyen ») quand le chapitre est inconnu.
_DEFAULT_USD_PER_KG = 8.0

# En-deçà, on considère qu'un seul 20′ suffit ; au-delà on bascule en 40′
# (plus économique pour les gros volumes). Seuil = capacité d'un TEU.
_TEU_MAX_KG = TEU_CAPACITY_KG

# Garde-fou commun à tout cours mondial : c'est un prix RÉEL et SOURCÉ, mais
# pour une qualité/grade standard sur un marché organisé — jamais un devis
# garanti pour une opération précise.
_NEGOTIATION_CAVEAT = (
    "Cours de référence pour une qualité/grade standard sur un marché organisé "
    "— PAS un devis garanti pour cette opération précise : qualité, origine, "
    "incoterm et conditions contractuelles font varier le prix réellement négocié."
)

# ---------------------------------------------------------------------------
# Cours mondiaux réels, datés et sourcés (classification_source: "cours_mondial")
# ---------------------------------------------------------------------------
# Clés : code SH à 6 chiffres quand une distinction de qualité l'exige (ex.
# café Arabica vs Robusta), sinon position à 4 chiffres. La recherche est
# effectuée par spécificité décroissante (6 puis 4 chiffres) avant de retomber
# sur l'estimation par chapitre (2 chiffres). Chaque entrée porte sa cotation
# brute AVANT conversion, sa date et sa source, pour audit — ce sont des cours
# de marché figés à la date de recherche : à rafraîchir périodiquement, jamais
# à présenter comme un flux temps réel.
_WORLD_MARKET_BENCHMARKS: Dict[str, Dict] = {
    # --- Softs (ICE) ---
    "090111": {
        "commodity": "Café Arabica (vert, non torréfié, non décaféiné)",
        "benchmark": "ICE Coffee C (contrat rapproché)",
        "raw_quote": "315.24 ¢/lb",
        "as_of": "2026-07-08",
        "usd_per_kg": round(315.24 / 100 / _LB_TO_KG, 4),
        "note": "Cours Arabica uniquement — le Robusta (SH 090121/090122, "
        "structurellement moins cher) n'est pas couvert ; estimation par "
        "chapitre utilisée pour le Robusta.",
    },
    "1801": {
        "commodity": "Cacao (fèves brutes)",
        "benchmark": "ICE Cocoa (contrat rapproché)",
        "raw_quote": "5 877.16 USD/tonne",
        "as_of": "2026-07-08",
        "usd_per_kg": round(5_877.16 / _TONNE_TO_KG, 4),
    },
    "5201": {
        "commodity": "Coton (brut, non cardé ni peigné)",
        "benchmark": "ICE Cotton No. 2 (contrat rapproché)",
        "raw_quote": "81.24 ¢/lb",
        "as_of": "2026-07-07",
        "usd_per_kg": round(81.24 / 100 / _LB_TO_KG, 4),
        "note": "Spécifique à la position 5201 (fibre brute) — non applicable "
        "aux fils/tissus de coton (chapitre 52), bien plus chers au kg.",
    },
    "1701": {
        "commodity": "Sucre (canne ou betterave, brut)",
        "benchmark": "ICE Sugar No. 11 (contrat rapproché)",
        "raw_quote": "15.20 ¢/lb",
        "as_of": "2026-07-08",
        "usd_per_kg": round(15.20 / 100 / _LB_TO_KG, 4),
    },
    # --- Métaux de base (LME) ---
    "7403": {
        "commodity": "Cuivre affiné (non ouvré)",
        "benchmark": "LME Copper (cash/spot)",
        "raw_quote": "13 335.00 USD/tonne",
        "as_of": "2026-07-06",
        "usd_per_kg": round(13_335.00 / _TONNE_TO_KG, 4),
    },
    "7601": {
        "commodity": "Aluminium (non ouvré)",
        "benchmark": "LME Aluminium",
        "raw_quote": "3 154.28 USD/tonne",
        "as_of": "2026-07-09",
        "usd_per_kg": round(3_154.28 / _TONNE_TO_KG, 4),
        "note": "Une source concurrente relevée le même jour indiquait 3 090 "
        "USD/tonne — écart de l'ordre de 2 %, non résolu par une lecture "
        "directe de la bourse.",
    },
    "7901": {
        "commodity": "Zinc (non ouvré)",
        "benchmark": "LME Zinc",
        "raw_quote": "3 466.55 USD/tonne",
        "as_of": "2026-07-09",
        "usd_per_kg": round(3_466.55 / _TONNE_TO_KG, 4),
        "note": "Une source concurrente relevée le même jour indiquait 3 572.00 "
        "USD/tonne — écart non résolu par une lecture directe de la bourse.",
    },
    "7502": {
        "commodity": "Nickel (non ouvré)",
        "benchmark": "LME Nickel",
        "raw_quote": "16 420.00 USD/tonne",
        "as_of": "2026-07-08",
        "usd_per_kg": round(16_420.00 / _TONNE_TO_KG, 4),
    },
    "8105": {
        "commodity": "Cobalt (mattes et autres produits intermédiaires)",
        "benchmark": "Fastmarkets MB Cobalt",
        "raw_quote": "56 290.00 USD/tonne",
        "as_of": "2026-07-08",
        "usd_per_kg": round(56_290.00 / _TONNE_TO_KG, 4),
    },
    # --- Céréales & oléagineux (CBOT) ---
    "1001": {
        "commodity": "Blé",
        "benchmark": "CBOT Wheat (contrat rapproché)",
        "raw_quote": "605.75 ¢/boisseau",
        "as_of": "2026-07 (approx.)",
        "usd_per_kg": round(605.75 / 100 / _BUSHEL_TO_KG["wheat"], 4),
        "note": "Confiance basse : une fourchette concurrente de 571.50 à "
        "614.00 ¢/bu a été relevée le même jour selon la source.",
    },
    "1005": {
        "commodity": "Maïs",
        "benchmark": "CBOT Corn (contrat rapproché)",
        "raw_quote": "464.25 ¢/boisseau",
        "as_of": "2026-07 (approx.)",
        "usd_per_kg": round(464.25 / 100 / _BUSHEL_TO_KG["corn"], 4),
        "note": "Confiance basse : une source concurrente indiquait 427.00 "
        "¢/bu le même jour, non réconciliée par une lecture directe.",
    },
    "1201": {
        "commodity": "Soja (fèves)",
        "benchmark": "CBOT Soybeans (contrat rapproché)",
        "raw_quote": "1 196.91 ¢/boisseau",
        "as_of": "2026-07-08",
        "usd_per_kg": round(1_196.91 / 100 / _BUSHEL_TO_KG["soybeans"], 4),
    },
    "1006": {
        "commodity": "Riz",
        "benchmark": "Riz blanc 5 % brisures, FOB Thaïlande",
        "raw_quote": "480 USD/tonne (fourchette 470-490)",
        "as_of": "2026-06",
        "usd_per_kg": round(480.0 / _TONNE_TO_KG, 4),
        "note": "Préféré au Rough Rice CBOT (cours contradictoires relevés) — "
        "moyenne de fourchette, pas une cotation ponctuelle unique.",
    },
    # --- Métaux précieux ---
    "7108": {
        "commodity": "Or (non monétaire, brut ou semi-ouvré)",
        "benchmark": "COMEX Gold (spot)",
        "raw_quote": "4 110.60 USD/once troy",
        "as_of": "2026-07-09",
        "usd_per_kg": round(4_110.60 / _TROY_OZ_TO_KG, 2),
        "note": "Spot COMEX retenu plutôt que le fixing LBMA PM (4 072.05 "
        "USD/oz, 2026-06-26), devenu daté de deux semaines au moment de la "
        "recherche.",
    },
    "7106": {
        "commodity": "Argent (brut ou semi-ouvré)",
        "benchmark": "Spot argent (FXStreet)",
        "raw_quote": "59.17 USD/once troy",
        "as_of": "2026-07-09",
        "usd_per_kg": round(59.17 / _TROY_OZ_TO_KG, 2),
        "note": "Spot du jour retenu plutôt que le fixing LBMA (70.38 USD/oz, "
        "2026-06-15), explicitement signalé comme dépassé après une baisse "
        "d'environ 30 % depuis les sommets de janvier.",
    },
    "7110": {
        "commodity": "Platine (brut ou semi-ouvré)",
        "benchmark": "Spot platine (JM Bullion)",
        "raw_quote": "1 594.20 USD/once troy",
        "as_of": "2026-07-08",
        "usd_per_kg": round(1_594.20 / _TROY_OZ_TO_KG, 2),
    },
    # --- Minerais & énergie ---
    "2601": {
        "commodity": "Minerai de fer (concentré, 62 % Fe)",
        "benchmark": "Platts IODEX 62% Fe CFR Chine",
        "raw_quote": "98.86 USD/tonne",
        "as_of": "2026-07-08",
        "usd_per_kg": round(98.86 / _TONNE_TO_KG, 5),
    },
    "2709": {
        "commodity": "Pétrole brut",
        "benchmark": "ICE Brent (contrat rapproché)",
        "raw_quote": "78.59 USD/baril",
        "as_of": "2026-07-09",
        "usd_per_kg": round(78.59 / _BARREL_TO_KG, 4),
        "note": "Brent retenu plutôt que WTI (74.18 USD/baril) comme "
        "référence plus globale pour le brut africain. Le gaz naturel "
        "(Henry Hub) est volontairement exclu : c'est un prix domestique "
        "US du gazoduc, non représentatif du prix export GNL perçu par les "
        "exportateurs africains (Nigéria, Algérie, Mozambique).",
    },
    # --- Agro-industriel ---
    "1511": {
        "commodity": "Huile de palme (brute)",
        "benchmark": "Bursa Malaysia FCPO",
        "raw_quote": "4 608 MYR/tonne (≈ 1 131.08 USD/tonne)",
        "as_of": "2026-07-08",
        "usd_per_kg": round(1_131.08 / _TONNE_TO_KG, 4),
    },
    "4001": {
        "commodity": "Caoutchouc naturel (TSR20)",
        "benchmark": "SICOM TSR20",
        "raw_quote": "≈ 210 ¢/kg (fourchette 204.10-212.20)",
        "as_of": "2026-07-08/09 (approx.)",
        "usd_per_kg": round(210.0 / 100, 4),
        "note": "Recoupé avec un prix SGX de 2 245 USD/tonne (≈ 2.245 USD/kg), "
        "cohérent avec cette fourchette.",
    },
    "0902": {
        "commodity": "Thé",
        "benchmark": "Enchères de thé de Mombasa",
        "raw_quote": "2.28 USD/kg (moyenne)",
        "as_of": "Janvier-juin 2026 (moyenne semestrielle)",
        "usd_per_kg": 2.28,
        "note": "Moyenne de période, pas une cotation ponctuelle.",
    },
}

# Fichier de cours rafraîchis quotidiennement par le workflow GitHub Actions
# « update_market_prices » (etl/update_world_market_prices.py). Quand il est
# présent et lisible, ses entrées PRIMENT sur les valeurs statiques ci-dessus
# (qui restent le repli daté si un symbole échoue ou si le fichier manque).
_LIVE_BENCHMARKS_PATH = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "..", "data", "json", "cours_mondiaux.json"
)


def _apply_live_benchmarks(static: Dict[str, Dict], live: Dict[str, Dict]) -> Dict[str, Dict]:
    """
    Fusionne les cours rafraîchis (live) par-dessus les statiques.

    Seuls les champs de cotation sont remplacés (usd_per_kg, raw_quote, as_of,
    benchmark, source) ; la `note` métier statique (ex. Robusta non couvert
    par le cours Arabica) est conservée. Une entrée live sans `usd_per_kg`
    numérique positif est ignorée — jamais de cours douteux appliqué.
    """
    merged = {k: dict(v) for k, v in static.items()}
    for hs, entry in (live or {}).items():
        usd_per_kg = entry.get("usd_per_kg")
        if not isinstance(usd_per_kg, (int, float)) or usd_per_kg <= 0:
            continue
        base = merged.get(hs, {})
        base.update(
            {
                "commodity": entry.get("commodity", base.get("commodity")),
                "benchmark": entry.get("benchmark", base.get("benchmark")),
                "raw_quote": entry.get("raw_quote", base.get("raw_quote")),
                "as_of": entry.get("as_of", base.get("as_of")),
                "usd_per_kg": float(usd_per_kg),
                "refresh": "auto (workflow quotidien update_market_prices)",
            }
        )
        merged[hs] = base
    return merged


def _load_live_benchmarks(path: str = _LIVE_BENCHMARKS_PATH) -> Dict[str, Dict]:
    """Charge cours_mondiaux.json ; dict vide si absent/corrompu (repli statique)."""
    try:
        with open(path, encoding="utf-8") as fh:
            data = json.load(fh)
        benchmarks = data.get("benchmarks")
        return benchmarks if isinstance(benchmarks, dict) else {}
    except (OSError, ValueError):
        return {}


_WORLD_MARKET_BENCHMARKS = _apply_live_benchmarks(_WORLD_MARKET_BENCHMARKS, _load_live_benchmarks())


def usd_per_kg_for_hs(hs_code: str) -> Dict:
    """
    Ratio valeur/poids (USD/kg) pour un code SH, avec sa base et son usage
    possible comme repère de négociation.

    Cherche d'abord un cours mondial réel (_WORLD_MARKET_BENCHMARKS, par
    spécificité décroissante : position à 6 puis 4 chiffres du SH) ; à défaut,
    retombe sur l'estimation par chapitre (2 chiffres) — ou le défaut prudent
    si le chapitre lui-même est inconnu.
    """
    normalized = (hs_code or "").strip().replace(".", "").replace(" ", "")
    chapter = normalized[:2] or None

    for prefix_len in (6, 4):
        prefix = normalized[:prefix_len]
        if len(prefix) < prefix_len:
            continue
        benchmark = _WORLD_MARKET_BENCHMARKS.get(prefix)
        if benchmark is None:
            continue
        return {
            "usd_per_kg": benchmark["usd_per_kg"],
            "hs_chapter": chapter,
            "hs_match": prefix,
            "classification_source": "cours_mondial",
            "commodity": benchmark["commodity"],
            "benchmark": benchmark["benchmark"],
            "raw_quote": benchmark["raw_quote"],
            "as_of": benchmark["as_of"],
            "source": f"{benchmark['benchmark']} — {benchmark['raw_quote']} "
            f"au {benchmark['as_of']}.",
            "note": benchmark.get("note"),
            "is_estimate": False,
            "negotiation": {
                "usable_as_price_reference": True,
                "caveat": _NEGOTIATION_CAVEAT,
            },
        }

    rate = _USD_PER_KG_BY_CHAPTER.get(chapter)
    if rate is not None:
        return {
            "usd_per_kg": rate,
            "hs_chapter": chapter,
            "classification_source": "estimation_chapitre",
            "source": "Valeur unitaire typique du commerce mondial par chapitre SH "
            "(ordre de grandeur UN Comtrade / BACI) — estimation de dimensionnement.",
            "is_estimate": True,
            "negotiation": {
                "usable_as_price_reference": False,
                "caveat": "Ordre de grandeur par chapitre SH, pas un cours de marché "
                "— à ne PAS utiliser comme base de négociation, seulement pour le "
                "dimensionnement logistique.",
            },
        }
    return {
        "usd_per_kg": _DEFAULT_USD_PER_KG,
        "hs_chapter": chapter,
        "classification_source": "estimation_chapitre",
        "source": "Chapitre SH inconnu — ratio manufacturé moyen par défaut "
        f"({_DEFAULT_USD_PER_KG} USD/kg). Estimation de dimensionnement.",
        "is_estimate": True,
        "negotiation": {
            "usable_as_price_reference": False,
            "caveat": "Chapitre SH inconnu — valeur par défaut, pas un cours de "
            "marché — à ne PAS utiliser comme base de négociation.",
        },
    }


def plan_containers(weight_kg: float) -> Dict:
    """Choisit le type de conteneur et le nombre nécessaire pour un poids donné."""
    weight_kg = max(float(weight_kg or 0), 0.0)
    if weight_kg <= 0:
        return {
            "container_type": "teu",
            "container_capacity_kg": TEU_CAPACITY_KG,
            "containers_needed": 0,
            "note": "Poids nul ou indéterminé.",
        }
    if weight_kg <= _TEU_MAX_KG:
        container_type, capacity = "teu", TEU_CAPACITY_KG
    else:
        container_type, capacity = "feu", FEU_CAPACITY_KG
    n = max(1, math.ceil(weight_kg / capacity))
    label = "20 pieds" if container_type == "teu" else "40 pieds"
    return {
        "container_type": container_type,
        "container_capacity_kg": capacity,
        "containers_needed": n,
        "note": f"{n} conteneur(s) {label} pour {round(weight_kg):,} kg estimés "
        f"(capacité {capacity:,} kg/conteneur).".replace(",", " "),
    }


def estimate_shipment(
    goods_value_usd: Optional[float],
    hs_code: str,
    weight_kg_override: Optional[float] = None,
) -> Dict:
    """
    Estime le poids et le plan de conteneurs d'une expédition à partir de sa
    valeur FOB et de son code SH.

    Si ``weight_kg_override`` est fourni (poids réel connu), il est utilisé tel
    quel et le ratio valeur/poids est ignoré (``weight_source: "fourni"``).

    Retourne un dict prêt à afficher : poids (estimé ou fourni), ratio utilisé,
    type et nombre de conteneurs, et les drapeaux de traçabilité. Renvoie
    ``available: False`` si ni le poids ni la valeur ne sont exploitables.
    """
    if weight_kg_override and weight_kg_override > 0:
        plan = plan_containers(weight_kg_override)
        return {
            "available": True,
            "weight_kg": round(float(weight_kg_override), 1),
            "weight_source": "fourni",
            "is_estimate": False,
            "value_to_weight": None,
            **plan,
        }

    if not goods_value_usd or goods_value_usd <= 0:
        return {
            "available": False,
            "note": "Ni poids réel ni valeur FOB exploitable — dimensionnement "
            "conteneur impossible.",
        }

    ratio = usd_per_kg_for_hs(hs_code)
    weight_kg = float(goods_value_usd) / ratio["usd_per_kg"]
    plan = plan_containers(weight_kg)
    return {
        "available": True,
        "weight_kg": round(weight_kg, 1),
        "weight_source": "estimé",
        "is_estimate": True,
        "value_to_weight": ratio,
        "goods_value_usd": float(goods_value_usd),
        "negotiation_reference": (
            {
                "usd_per_kg": ratio["usd_per_kg"],
                "commodity": ratio.get("commodity"),
                "benchmark": ratio.get("benchmark"),
                "as_of": ratio.get("as_of"),
                "caveat": ratio["negotiation"]["caveat"],
            }
            if ratio.get("negotiation", {}).get("usable_as_price_reference")
            else None
        ),
        **plan,
    }
