"""
Statistiques officielles NATIONALES (bulletins des agences de promotion /
offices statistiques nationaux) — complément aux sources internationales
(OEC/UN Comtrade, FAOSTAT, USGS, UNIDO).

Intérêt : certaines distinctions n'existent que dans les statistiques
nationales — en premier lieu la séparation exportations DOMESTIQUES vs
RÉEXPORTATIONS, décisive pour les règles d'origine ZLECAf (une marchandise
réexportée depuis une zone franche n'acquiert pas l'origine locale ; seule la
production/transformation domestique peut y prétendre).

Garde-fous « zéro fabrication » :
- Les valeurs sont reprises TELLES QUE PUBLIÉES, dans la monnaie de
  publication (ex. millions de MUR pour Maurice) — aucune conversion USD
  maison, aucun chiffre complété.
- Chaque bloc porte sa source (éditeur, publication, année des données).

Première source intégrée : EDB Mauritius (Economic Development Board),
newsletter de juillet 2024 — « Maurice commerce avec le monde 2023 (MUR Mn) ».
https://edbmauritius.org/newsletter2024/july/overview.html
"""

from typing import Dict, List, Optional

_MUS_EDB_2023: Dict = {
    "country_iso3": "MUS",
    "country_name": "Maurice",
    "source": {
        "publisher": "EDB Mauritius (Economic Development Board)",
        "publication": "Newsletter juillet 2024 — Industry Overview",
        "url": "https://edbmauritius.org/newsletter2024/july/overview.html",
        "data_year": 2023,
        "currency": "MUR",
        "unit": "millions de MUR",
    },
    # Le produit d'exportation NATIONALE (domestique) n°1 en 2023.
    "top_domestic_export_product": {
        "hs4": "1604",
        "label": "Thon en conserve",
        "value_mur_mn": 11_500,
    },
    # Produits d'exportation domestique cités par l'EDB (par continent,
    # dédupliqués) — tous issus de transformation locale ou de collecte,
    # PAS de réexportation.
    "domestic_export_products": [
        {"hs4": "1604", "label": "Thon en conserve"},
        {"hs4": "1701", "label": "Sucre de canne"},
        {"hs4": "6203", "label": "Vêtements en denim — hommes"},
        {"hs4": "6204", "label": "Vêtements en denim — femmes"},
        {"hs4": "6109", "label": "T-shirts"},
        {"hs4": "6205", "label": "Chemises pour hommes"},
        {"hs4": "6105", "label": "Chemises pour hommes (maille)"},
        {"hs4": "6006", "label": "Tissu"},
        {"hs4": "9018", "label": "Dispositifs médicaux"},
        {"hs4": "2301", "label": "Aliments pour animaux"},
        {"hs4": "1504", "label": "Graisses et huiles de poisson"},
        {"hs4": "7204", "label": "Déchets ferreux"},
        {"hs4": "7403", "label": "Cuivre"},
        {"hs4": "0106", "label": "Animaux vivants"},
        {"hs4": "0603", "label": "Fleurs coupées"},
    ],
    # Top marchés des exportations DOMESTIQUES (2023, millions MUR, part %).
    "top_domestic_export_markets": [
        {"market": "Afrique du Sud", "iso3": "ZAF", "value_mur_mn": 7_664, "share_pct": 13},
        {"market": "Royaume-Uni", "iso3": "GBR", "value_mur_mn": 7_489, "share_pct": 12},
        {"market": "France", "iso3": "FRA", "value_mur_mn": 6_597, "share_pct": 11},
        {"market": "États-Unis", "iso3": "USA", "value_mur_mn": 6_543, "share_pct": 11},
        {"market": "Espagne", "iso3": "ESP", "value_mur_mn": 4_943, "share_pct": 8},
        {"market": "Madagascar", "iso3": "MDG", "value_mur_mn": 4_910, "share_pct": 8},
        {"market": "Italie", "iso3": "ITA", "value_mur_mn": 3_819, "share_pct": 6},
        {"market": "Pays-Bas", "iso3": "NLD", "value_mur_mn": 2_946, "share_pct": 5},
        {"market": "Inde", "iso3": "IND", "value_mur_mn": 2_111, "share_pct": 3},
        {"market": "Kenya", "iso3": "KEN", "value_mur_mn": 1_571, "share_pct": 3},
    ],
    # Top marchés de RÉEXPORTATION (suivis séparément par l'EDB) — ces flux
    # ne confèrent PAS l'origine mauricienne au sens ZLECAf.
    "top_reexport_markets": [
        {"market": "Vietnam", "iso3": "VNM", "value_mur_mn": 3_082, "share_pct": 13},
        {"market": "Réunion", "iso3": "REU", "value_mur_mn": 1_967, "share_pct": 8},
        {"market": "États-Unis", "iso3": "USA", "value_mur_mn": 1_385, "share_pct": 6},
        {"market": "Afrique du Sud", "iso3": "ZAF", "value_mur_mn": 1_353, "share_pct": 6},
        {"market": "France", "iso3": "FRA", "value_mur_mn": 1_336, "share_pct": 6},
        {"market": "Taïwan, Chine", "iso3": "TWN", "value_mur_mn": 1_261, "share_pct": 5},
        {"market": "Madagascar", "iso3": "MDG", "value_mur_mn": 1_239, "share_pct": 5},
        {"market": "Mayotte", "iso3": "MYT", "value_mur_mn": 1_040, "share_pct": 4},
        {"market": "Émirats arabes unis", "iso3": "ARE", "value_mur_mn": 918, "share_pct": 4},
        {"market": "Thaïlande", "iso3": "THA", "value_mur_mn": 841, "share_pct": 4},
    ],
}

_OFFICIAL_STATS: Dict[str, Dict] = {"MUS": _MUS_EDB_2023}


def get_official_stats(country_iso3: str) -> Optional[Dict]:
    """Bloc de statistiques officielles nationales pour un pays, s'il existe."""
    return _OFFICIAL_STATS.get((country_iso3 or "").strip().upper())


def grounding_lines(country_iso3: str) -> List[str]:
    """
    Lignes prêtes à injecter dans un bloc VERIFIED REAL DATA de prompt LLM.
    Vide si aucune statistique officielle n'est intégrée pour ce pays.
    """
    stats = get_official_stats(country_iso3)
    if not stats:
        return []
    src = stats["source"]
    lines = [
        f"OFFICIAL NATIONAL STATISTICS FOR {stats['country_name']} "
        f"({src['publisher']}, {src['publication']}, data year {src['data_year']}, "
        f"values in {src['unit']} — LOCAL CURRENCY, not USD):"
    ]
    top = stats.get("top_domestic_export_product")
    if top:
        lines.append(
            f"- #1 DOMESTIC export product {src['data_year']}: {top['label']} "
            f"(HS {top['hs4']}), {top['value_mur_mn']:,} MUR Mn"
        )
    products = stats.get("domestic_export_products") or []
    if products:
        lines.append(
            "- Domestic export products (local processing, NOT re-exports): "
            + ", ".join(f"{p['label']} (HS {p['hs4']})" for p in products)
        )
    markets = stats.get("top_domestic_export_markets") or []
    if markets:
        lines.append(
            "- Top domestic export markets: "
            + ", ".join(f"{m['market']} ({m['share_pct']}%)" for m in markets[:6])
        )
    reexports = stats.get("top_reexport_markets") or []
    if reexports:
        lines.append(
            "- RE-EXPORTS are tracked SEPARATELY by the national source; top re-export "
            "markets: "
            + ", ".join(f"{m['market']} ({m['share_pct']}%)" for m in reexports[:5])
            + " — re-exported merchandise does NOT acquire local AfCFTA origin and must "
            "never be presented as domestic production or origin-qualifying supply."
        )
    return lines
