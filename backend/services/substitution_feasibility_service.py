"""
Sous-module « faisabilité de substitution » du module Opportunités.

Substituer les importations « reste du monde » par des importations africaines
n'est PAS également faisable pour tous les produits : un dollar de blé importé
se remplace par du blé africain équivalent, mais un dollar de véhicule allemand
ou de smartphone coréen ne se remplace pas par le simple fait qu'une capacité
d'export africaine existe dans le même chapitre SH — l'EFFET MARQUE, l'écart
technologique, le réseau après-vente et les certifications s'y opposent.

Ce module attribue à chaque code SH un COEFFICIENT DE SUBSTITUABILITÉ (0-1),
part de la valeur importée réalistement adressable par une offre africaine à
horizon commercial (3-5 ans), avec les barrières non tarifaires qui le
justifient. Ordres de grandeur assumés comme hypothèses de modélisation
(``is_estimation`` implicite) : chaque coefficient est exposé avec sa classe,
ses barrières et sa justification — surchargeable par l'appelant, jamais une
boîte noire.

Grille de lecture des coefficients :
  ~0,9  produit homogène (commodité) : la décision est prix/logistique.
  ~0,7  différenciation modérée (agroalimentaire transformé, textile) :
        marques présentes mais offre africaine crédible et substituable.
  ~0,5  barrière réglementaire ou de confiance (pharma) ou effet marque
        partiellement contourné par l'assemblage africain de marques
        mondiales (véhicules ZAF/MAR/EGY).
  ~0,2  effet marque + écart technologique dominants (téléphonie,
        informatique) : la substitution ne porte que sur les segments
        d'entrée de gamme / accessoires / assemblage local.
"""

from typing import Dict, List, Optional, Tuple

# Intensité des barrières : libellés normalisés pour l'UI.
_FAIBLE, _MOYEN, _FORT = "faible", "moyen", "fort"

# (préfixes SH — le plus spécifique l'emporte, coefficient, classe, barrières, justification)
# barrières : {brand_effect, technology_gap, after_sales_network, certification}
_SUBSTITUTABILITY_CLASSES: List[Tuple[List[str], float, str, Dict[str, str], str]] = [
    # ── Cas spécifiques (préfixes longs d'abord à l'évaluation) ──
    (
        ["8703"],
        0.5,
        "véhicules de tourisme",
        {
            "brand_effect": _FORT,
            "technology_gap": _MOYEN,
            "after_sales_network": _FORT,
            "certification": _MOYEN,
        },
        "L'achat automobile est dominé par la marque, le financement et le réseau "
        "après-vente. La substitution africaine crédible passe par les véhicules de "
        "MARQUES MONDIALES assemblés en Afrique (Afrique du Sud, Maroc, Égypte : VW, "
        "Toyota, Renault, Stellantis...) — pas par des marques africaines nouvelles, "
        "marginales à cet horizon. Coefficient médian 0,5 : la moitié de la demande "
        "(volumes, entrée/milieu de gamme des marques assemblées localement) est "
        "adressable, le haut de gamme importé reste hors de portée.",
    ),
    (
        ["8708"],
        0.65,
        "pièces et accessoires automobiles",
        {
            "brand_effect": _MOYEN,
            "technology_gap": _MOYEN,
            "after_sales_network": _FAIBLE,
            "certification": _MOYEN,
        },
        "Le marché de la pièce (rechange indépendante, consommables) est moins "
        "sensible à la marque que le véhicule neuf ; les écosystèmes ZAF/MAR/TUN/EGY "
        "produisent déjà pour les constructeurs mondiaux (câblage, sièges, filtres).",
    ),
    (
        ["8517"],
        0.2,
        "téléphonie et équipements télécoms",
        {
            "brand_effect": _FORT,
            "technology_gap": _FORT,
            "after_sales_network": _MOYEN,
            "certification": _MOYEN,
        },
        "Marché dominé par des marques mondiales (Samsung, Apple, Transsion, Xiaomi) "
        "à technologie propriétaire : le branding et l'écart technologique rendent la "
        "substitution limitée aux segments d'assemblage local (Égypte, Algérie...) et "
        "d'entrée de gamme — environ un cinquième de la valeur importée.",
    ),
    (
        ["8471", "8473"],
        0.15,
        "informatique (ordinateurs et périphériques)",
        {
            "brand_effect": _FORT,
            "technology_gap": _FORT,
            "after_sales_network": _MOYEN,
            "certification": _FAIBLE,
        },
        "Concentration mondiale extrême (marques + chaînes de valeur asiatiques) et "
        "écart technologique majeur : la substitution africaine réaliste se limite à "
        "l'assemblage/configuration locale et aux accessoires.",
    ),
    # ── Classes par plage de chapitres ──
    (
        # Agriculture brute et commodités alimentaires homogènes
        ["01", "02", "03", "04", "05", "06", "07", "08", "09", "10", "11", "12", "14", "15", "17"],
        0.9,
        "produits agricoles et alimentaires homogènes",
        {
            "brand_effect": _FAIBLE,
            "technology_gap": _FAIBLE,
            "after_sales_network": _FAIBLE,
            "certification": _FAIBLE,
        },
        "Produit homogène : à qualité sanitaire équivalente, la décision d'achat est "
        "prix + logistique — un blé, un sucre ou un café africain remplace son "
        "équivalent extra-continental sans barrière de marque.",
    ),
    (
        ["13", "16", "18", "19", "20", "21", "22", "23", "24"],
        0.75,
        "agroalimentaire transformé",
        {
            "brand_effect": _MOYEN,
            "technology_gap": _FAIBLE,
            "after_sales_network": _FAIBLE,
            "certification": _FAIBLE,
        },
        "Des marques et habitudes de consommation existent (biscuiterie, boissons, "
        "conserves) mais l'offre africaine est technologiquement équivalente — la "
        "substitution est surtout une affaire de distribution et de notoriété.",
    ),
    (
        ["25", "26", "27"],
        0.9,
        "minéraux et combustibles (commodités)",
        {
            "brand_effect": _FAIBLE,
            "technology_gap": _FAIBLE,
            "after_sales_network": _FAIBLE,
            "certification": _FAIBLE,
        },
        "Commodités par excellence : la substitution dépend du prix, de la qualité "
        "physique (teneur, grade) et de la logistique, pas de la marque.",
    ),
    (
        ["30"],
        0.45,
        "produits pharmaceutiques",
        {
            "brand_effect": _MOYEN,
            "technology_gap": _MOYEN,
            "after_sales_network": _FAIBLE,
            "certification": _FORT,
        },
        "La barrière est réglementaire et de confiance (AMM, préqualification OMS, "
        "pharmacovigilance, confiance des prescripteurs), pas seulement industrielle. "
        "Les génériques africains (EGY, MAR, ZAF, TUN) sont crédibles sur une part "
        "significative mais pas majoritaire du panier importé (princeps, biologiques).",
    ),
    (
        ["28", "29", "31", "32", "33", "34", "35", "36", "37", "38", "39", "40"],
        0.7,
        "chimie, plastiques et caoutchouc",
        {
            "brand_effect": _FAIBLE,
            "technology_gap": _MOYEN,
            "after_sales_network": _FAIBLE,
            "certification": _MOYEN,
        },
        "Intrants industriels largement banalisés (engrais, polymères de base, "
        "peintures) : substitution élevée quand la capacité existe ; les spécialités "
        "à haute technicité restent importées.",
    ),
    (
        [str(c) for c in range(41, 50)],
        0.8,
        "cuirs, bois, papier",
        {
            "brand_effect": _FAIBLE,
            "technology_gap": _FAIBLE,
            "after_sales_network": _FAIBLE,
            "certification": _FAIBLE,
        },
        "Filières à faible différenciation de marque où l'Afrique dispose de matières "
        "premières et de capacités de première transformation.",
    ),
    (
        [str(c) for c in range(50, 64)],
        0.7,
        "textiles et habillement",
        {
            "brand_effect": _MOYEN,
            "technology_gap": _FAIBLE,
            "after_sales_network": _FAIBLE,
            "certification": _FAIBLE,
        },
        "Hors marques mondiales de mode (part minoritaire de la valeur importée), le "
        "textile-habillement africain (EGY, MAR, TUN, ETH, MUS) est substituable — "
        "c'est déjà une filière d'export continentale établie.",
    ),
    (
        ["64", "65", "66", "67"],
        0.7,
        "chaussures et accessoires",
        {
            "brand_effect": _MOYEN,
            "technology_gap": _FAIBLE,
            "after_sales_network": _FAIBLE,
            "certification": _FAIBLE,
        },
        "Différenciation de marque réelle mais non bloquante hors segment sport/luxe.",
    ),
    (
        [str(c) for c in range(68, 72)],
        0.75,
        "verre, céramique, pierres et métaux précieux",
        {
            "brand_effect": _FAIBLE,
            "technology_gap": _FAIBLE,
            "after_sales_network": _FAIBLE,
            "certification": _FAIBLE,
        },
        "Matériaux et ouvrages standardisés, faible effet marque (hors joaillerie de "
        "marque, minoritaire en valeur dans les flux considérés).",
    ),
    (
        [str(c) for c in range(72, 84)],
        0.75,
        "métaux et ouvrages en métal",
        {
            "brand_effect": _FAIBLE,
            "technology_gap": _MOYEN,
            "after_sales_network": _FAIBLE,
            "certification": _MOYEN,
        },
        "Acier, aluminium et ouvrages : produits normés (grades) où la capacité "
        "africaine (ZAF, EGY, DZA, MAR) substitue directement, hors aciers spéciaux.",
    ),
    (
        ["84"],
        0.4,
        "machines et équipements mécaniques",
        {
            "brand_effect": _MOYEN,
            "technology_gap": _FORT,
            "after_sales_network": _FORT,
            "certification": _MOYEN,
        },
        "L'achat d'équipement engage la fiabilité, la maintenance et les pièces sur "
        "10-20 ans : la réputation constructeur et le réseau SAV pèsent autant que le "
        "prix. Substitution réaliste sur les équipements simples et l'occasion "
        "reconditionnée, pas sur les machines-outils de précision.",
    ),
    (
        ["85"],
        0.35,
        "machines et appareils électriques",
        {
            "brand_effect": _FORT,
            "technology_gap": _FORT,
            "after_sales_network": _MOYEN,
            "certification": _MOYEN,
        },
        "Hors téléphonie/informatique (traitées à part, plus restrictives), "
        "l'électrique mêle produits banalisés substituables (câbles, "
        "transformateurs — TUN et EGY exportent déjà) et électronique de marque "
        "difficilement substituable.",
    ),
    (
        ["86", "88", "89"],
        0.15,
        "matériel ferroviaire, aéronautique et naval",
        {
            "brand_effect": _FORT,
            "technology_gap": _FORT,
            "after_sales_network": _FORT,
            "certification": _FORT,
        },
        "Industries à certification extrême et duopoles mondiaux : substitution "
        "africaine marginale à cet horizon (hors maintenance et pièces simples).",
    ),
    (
        ["87"],
        0.45,
        "véhicules et matériel de transport terrestre (hors 8703/8708)",
        {
            "brand_effect": _FORT,
            "technology_gap": _MOYEN,
            "after_sales_network": _FORT,
            "certification": _MOYEN,
        },
        "Utilitaires, bus, deux-roues, remorques : effet marque réel mais l'assemblage "
        "africain (bus et utilitaires ZAF/MAR/EGY/NGA) offre une base de substitution "
        "supérieure aux voitures particulières haut de gamme.",
    ),
    (
        ["90"],
        0.25,
        "instruments de précision, optique et médical",
        {
            "brand_effect": _FORT,
            "technology_gap": _FORT,
            "after_sales_network": _MOYEN,
            "certification": _FORT,
        },
        "Instruments médicaux et de précision : confiance clinique, certification et "
        "technologie concentrées chez quelques fabricants mondiaux — substitution "
        "limitée aux consommables et au matériel simple.",
    ),
    (
        ["91", "92"],
        0.3,
        "horlogerie et instruments de musique",
        {
            "brand_effect": _FORT,
            "technology_gap": _MOYEN,
            "after_sales_network": _FAIBLE,
            "certification": _FAIBLE,
        },
        "Fort contenu de marque (horlogerie notamment) ; substitution sur l'entrée de "
        "gamme uniquement.",
    ),
    (
        ["94", "95", "96"],
        0.65,
        "mobilier, jouets et articles divers",
        {
            "brand_effect": _MOYEN,
            "technology_gap": _FAIBLE,
            "after_sales_network": _FAIBLE,
            "certification": _FAIBLE,
        },
        "Biens de consommation à différenciation modérée : le mobilier et les "
        "articles ménagers africains substituent largement ; le jouet de marque "
        "mondiale moins.",
    ),
]

# Coefficient par défaut quand aucun préfixe ne correspond : différenciation
# modérée, ni commodité ni produit de marque — mieux vaut un défaut moyen
# étiqueté qu'un 100 % implicite.
DEFAULT_COEFFICIENT = 0.6
DEFAULT_CLASS = "défaut (classe non mappée)"


def _normalize_hs(hs_code: str) -> str:
    return "".join(ch for ch in str(hs_code or "") if ch.isdigit())


def substitutability_for_hs(hs_code: str, override: Optional[float] = None) -> Dict:
    """
    Coefficient de substituabilité (0-1) et barrières non tarifaires pour un
    code SH (SH2/SH4/SH6). Le préfixe le plus long l'emporte (8703 avant 87).

    ``override`` : coefficient imposé par l'appelant (0-1) — exposé comme tel.
    """
    hs = _normalize_hs(hs_code)
    if override is not None:
        return {
            "hs_code": hs_code,
            "coefficient": max(0.0, min(1.0, float(override))),
            "product_class": "surcharge appelant",
            "barriers": None,
            "rationale": "Coefficient imposé par l'appelant.",
            "is_estimation": True,
        }

    best: Optional[Tuple[int, float, str, Dict[str, str], str]] = None
    for prefixes, coef, label, barriers, rationale in _SUBSTITUTABILITY_CLASSES:
        for prefix in prefixes:
            if hs.startswith(prefix) and (best is None or len(prefix) > best[0]):
                best = (len(prefix), coef, label, barriers, rationale)

    if best is None:
        return {
            "hs_code": hs_code,
            "coefficient": DEFAULT_COEFFICIENT,
            "product_class": DEFAULT_CLASS,
            "barriers": None,
            "rationale": (
                "Aucune classe de substituabilité mappée pour ce code SH — "
                "coefficient par défaut (différenciation modérée)."
            ),
            "is_estimation": True,
        }

    _, coef, label, barriers, rationale = best
    return {
        "hs_code": hs_code,
        "coefficient": coef,
        "product_class": label,
        "barriers": barriers,
        "rationale": rationale,
        "is_estimation": True,
    }


def realistic_substitution_potential(
    import_value_usd: float,
    african_capacity_usd: float,
    hs_code: str,
    override_coefficient: Optional[float] = None,
) -> Dict:
    """
    Potentiel de substitution RÉALISTE d'un flux importé hors Afrique :

        min(valeur importée × coefficient de substituabilité, capacité africaine)

    La borne capacité (offre réelle) reste, la borne substituabilité (demande
    adressable compte tenu des barrières marque/techno/certification) s'ajoute.
    Retourne les deux bornes et celle qui contraint, pour une lecture honnête.
    """
    feasibility = substitutability_for_hs(hs_code, override=override_coefficient)
    coef = feasibility["coefficient"]
    addressable = float(import_value_usd or 0.0) * coef
    potential = min(addressable, float(african_capacity_usd or 0.0))
    binding = "capacité africaine" if african_capacity_usd < addressable else "substituabilité"
    return {
        "potential_usd": int(potential),
        "addressable_value_usd": int(addressable),
        "african_capacity_usd": int(african_capacity_usd or 0),
        "binding_constraint": binding,
        "feasibility": feasibility,
    }
