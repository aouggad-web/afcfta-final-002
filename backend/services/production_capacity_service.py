"""
Production Capacity Service
===========================
Croise les opportunités commerciales (codes HS) du module Opportunités avec les
capacités de production réelles des organismes de premier plan :

  • FAO   (FAOSTAT)        — production agricole (tonnes)
  • USGS  (Mineral Commodity Summaries) — production minière & hydrocarbures (tonnes)
  • UNIDO (INDSTAT4)       — valeur ajoutée manufacturière (USD)
  • World Bank (WDI)       — valeur ajoutée sectorielle (% PIB)

Aucune donnée n'est extrapolée : les valeurs de production sont lues telles quelles
dans data/json/production_africaine.json (2021-2024, 54 pays). Les *scénarios*
d'intégration africaine sont des projections clairement étiquetées, calculées à
partir du CAGR réel observé et de l'écart au leader continental — jamais inventées.
"""

from __future__ import annotations

import json
import os
from typing import Dict, List, Optional, Tuple

from production_data import load_production_data

# ── HS → commodité de production ────────────────────────────────────────────────
# Chaque entrée associe un préfixe HS (le plus spécifique l'emporte) au dataset et
# au libellé exact présent dans production_africaine.json. Le matching se fait par
# libellé (les codes commodité comportent des collisions dans la source).
#
# Format : (hs_prefix, dataset, commodity_label)
#   dataset ∈ {"agri", "mining", "manufacturing"}
HS_TO_COMMODITY: List[Tuple[str, str, str]] = [
    # ── Agriculture (FAO / FAOSTAT) ──
    ("0901", "agri", "Coffee"),
    ("0902", "agri", "Tea"),
    ("0905", "agri", "Vanilla"),
    ("0906", "agri", "Cinnamon"),
    ("0907", "agri", "Cloves"),
    ("1801", "agri", "Cocoa beans"),
    ("1802", "agri", "Cocoa beans"),
    ("1803", "agri", "Cocoa beans"),
    ("1804", "agri", "Cocoa beans"),
    ("1805", "agri", "Cocoa beans"),
    ("1806", "agri", "Cocoa beans"),
    ("1005", "agri", "Maize (corn)"),
    ("1006", "agri", "Rice"),
    ("1001", "agri", "Wheat"),
    ("1003", "agri", "Barley"),
    ("1007", "agri", "Sorghum"),
    ("1008", "agri", "Millet"),
    ("0714", "agri", "Cassava"),
    ("0803", "agri", "Plantain"),
    ("0801", "agri", "Cashew nuts"),
    ("0802", "agri", "Cashew nuts"),
    ("0805", "agri", "Citrus fruits"),
    ("0804", "agri", "Dates"),
    ("2401", "agri", "Tobacco"),
    ("0701", "agri", "Potatoes"),
    ("0713", "agri", "Cowpeas"),
    ("1202", "agri", "Groundnuts"),
    ("1207", "agri", "Sesame"),
    ("1212", "agri", "Sugarcane"),
    ("1701", "agri", "Sugarcane"),
    ("1511", "agri", "Oil palm"),
    ("1513", "agri", "Coconuts"),
    ("0709", "agri", "Olives"),
    ("1509", "agri", "Olives"),
    ("1510", "agri", "Olives"),
    ("4001", "agri", "Rubber"),
    ("3301", "agri", "Ylang-ylang"),
    # ── Agriculture : produits déjà présents dans les données FAOSTAT mais
    #    sans correspondance HS jusqu'ici (résolus désormais par le module
    #    Opportunités). Codes HS6 spécifiques d'abord (préfixe le plus long gagne).
    ("080390", "agri", "Bananas"),  # bananes (hors plantains 080310)
    ("080430", "agri", "Pineapples"),  # ananas (0804=dattes en repli)
    ("070310", "agri", "Onions"),  # oignons et échalotes
    ("0702", "agri", "Tomatoes"),  # tomates
    ("1201", "agri", "Soybeans"),  # fèves de soja
    ("1206", "agri", "Sunflower seed"),  # graines de tournesol
    ("071430", "agri", "Yam"),  # ignames
    ("071333", "agri", "Beans"),  # haricots (Phaseolus)
    ("5201", "agri", "Seed cotton"),  # coton (fibre) — proxy coton graine
    ("0603", "agri", "Cut flowers"),  # fleurs coupées
    ("130120", "agri", "Gum arabic"),  # gomme arabique
    ("0910", "agri", "Ginger"),  # gingembre/épices
    ("0708", "agri", "Beans"),  # légumineuses à cosse fraîches
    # ── Cultures ajoutées (importées au prochain build FAOSTAT ; HS spécifiques) ──
    ("080450", "agri", "Mangoes"),  # mangues, goyaves
    ("080440", "agri", "Avocados"),  # avocats
    ("0806", "agri", "Grapes"),  # raisins
    ("080711", "agri", "Watermelons"),  # pastèques
    ("080720", "agri", "Papayas"),  # papayes
    ("070320", "agri", "Garlic"),  # ail
    ("071420", "agri", "Sweet potatoes"),  # patates douces
    ("0704", "agri", "Cabbages"),  # choux
    ("070610", "agri", "Carrots"),  # carottes
    ("070930", "agri", "Eggplants"),  # aubergines
    ("070999", "agri", "Okra"),  # gombo
    ("0707", "agri", "Cucumbers"),  # concombres
    ("0705", "agri", "Lettuce"),  # laitue
    ("071340", "agri", "Lentils"),  # lentilles
    ("071320", "agri", "Chickpeas"),  # pois chiches
    ("071310", "agri", "Peas"),  # pois secs
    ("071360", "agri", "Pigeon peas"),  # pois d'Angole
    ("1205", "agri", "Rapeseed"),  # colza
    ("1204", "agri", "Linseed"),  # lin
    ("120799", "agri", "Shea nuts"),  # karité
    ("080270", "agri", "Kola nuts"),  # noix de kola
    ("0904", "agri", "Pepper"),  # poivre/piments
    ("080211", "agri", "Almonds"),  # amandes
    ("080810", "agri", "Apples"),  # pommes
    ("1004", "agri", "Oats"),  # avoine
    ("080510", "agri", "Oranges"),  # oranges (sous-position de 0805 Citrus)
    ("0401", "agri", "Cattle milk"),  # lait de vache
    ("0407", "agri", "Hen eggs"),  # œufs
    ("0201", "agri", "Cattle meat"),  # viande bovine
    ("0202", "agri", "Cattle meat"),
    ("0207", "agri", "Chicken meat"),  # viande de volaille
    # ── Industrie : positions HS4 spécifiques vers secteurs UNIDO ──
    ("2523", "manufacturing", "Manufacture of other non-metallic mineral products"),  # ciment
    ("3105", "manufacturing", "Manufacture of chemicals"),  # engrais composés
    ("3102", "manufacturing", "Manufacture of chemicals"),  # engrais azotés
    ("3103", "manufacturing", "Manufacture of chemicals"),  # engrais phosphatés
    # ── Hydrocarbures & Mines (USGS) ──
    ("2709", "mining", "Crude oil"),
    ("2710", "mining", "Crude oil"),
    ("2711", "mining", "Natural gas"),
    ("2701", "mining", "Coal"),
    ("2702", "mining", "Coal"),
    ("7108", "mining", "Gold"),
    ("7106", "mining", "Salt"),  # (placeholder rarely hit)
    ("7102", "mining", "Diamonds"),
    ("7103", "mining", "Diamonds"),
    ("7110", "mining", "Platinum"),
    ("2510", "mining", "Phosphate"),
    ("2603", "mining", "Copper"),
    ("7402", "mining", "Copper"),
    ("7403", "mining", "Copper"),
    ("2606", "mining", "Bauxite"),
    ("2844", "mining", "Uranium"),
    ("8105", "mining", "Cobalt"),
    ("2605", "mining", "Cobalt"),
    ("2601", "mining", "Iron ore"),
    ("2501", "mining", "Salt"),
    ("2615", "mining", "Tantalum"),
    ("8103", "mining", "Tantalum"),
    ("2608", "mining", "Zinc"),
    ("7901", "mining", "Zinc"),
    ("2604", "mining", "Nickel"),
    ("7502", "mining", "Nickel"),
    ("2521", "mining", "Limestone"),
    ("2602", "mining", "Manganese"),
    ("2609", "mining", "Tin"),
    ("8001", "mining", "Tin"),
    ("2529", "mining", "Fluorspar"),
    ("2836", "mining", "Soda ash"),
    ("2516", "mining", "Granite"),
    ("2513", "mining", "Pumice"),
    ("2530", "mining", "Perlite"),
    ("2614", "mining", "Ilmenite"),
]

# Repli par chapitre HS (2 chiffres) — moins précis mais utile pour couverture large.
# Couvre les grands secteurs manufacturiers (UNIDO, valeur ajoutée) et agro/mines.
HS_CHAPTER_FALLBACK: Dict[str, Tuple[str, str]] = {
    "09": ("agri", "Coffee"),
    "10": ("agri", "Maize (corn)"),
    "18": ("agri", "Cocoa beans"),
    "27": ("mining", "Crude oil"),
    "71": ("mining", "Gold"),
    # Métallurgie de base (UNIDO)
    "72": ("manufacturing", "Manufacture of basic metals"),
    "73": ("manufacturing", "Manufacture of basic metals"),
    "74": ("manufacturing", "Manufacture of basic metals"),
    "75": ("manufacturing", "Manufacture of basic metals"),
    "76": ("manufacturing", "Manufacture of basic metals"),
    "78": ("manufacturing", "Manufacture of basic metals"),
    "79": ("manufacturing", "Manufacture of basic metals"),
    # Agro-alimentaire (UNIDO)
    "16": ("manufacturing", "Manufacture of food products"),
    "19": ("manufacturing", "Manufacture of food products"),
    "20": ("manufacturing", "Manufacture of food products"),
    "21": ("manufacturing", "Manufacture of food products"),
    "22": ("manufacturing", "Manufacture of beverages"),
    # Chimie & pharmacie (UNIDO)
    "28": ("manufacturing", "Manufacture of chemicals"),
    "29": ("manufacturing", "Manufacture of chemicals"),
    "30": ("manufacturing", "Produits pharmaceutiques"),
    "31": ("manufacturing", "Manufacture of chemicals"),
    "32": ("manufacturing", "Manufacture of chemicals"),
    "33": ("manufacturing", "Manufacture of chemicals"),
    "34": ("manufacturing", "Manufacture of chemicals"),
    "38": ("manufacturing", "Manufacture of chemicals"),
    # Caoutchouc & plastiques (UNIDO)
    "39": ("manufacturing", "Caoutchouc et plastiques"),
    "40": ("manufacturing", "Caoutchouc et plastiques"),
    # Textiles & habillement (UNIDO)
    "50": ("manufacturing", "Manufacture of textiles"),
    "51": ("manufacturing", "Manufacture of textiles"),
    "52": ("manufacturing", "Manufacture of textiles"),
    "53": ("manufacturing", "Manufacture of textiles"),
    "54": ("manufacturing", "Manufacture of textiles"),
    "55": ("manufacturing", "Manufacture of textiles"),
    "56": ("manufacturing", "Manufacture of textiles"),
    "57": ("manufacturing", "Manufacture of textiles"),
    "58": ("manufacturing", "Manufacture of textiles"),
    "59": ("manufacturing", "Manufacture of textiles"),
    "60": ("manufacturing", "Manufacture of textiles"),
    "61": ("manufacturing", "Articles d'habillement"),
    "62": ("manufacturing", "Articles d'habillement"),
    "63": ("manufacturing", "Articles d'habillement"),
    # Électronique & équipements électriques (UNIDO)
    "85": ("manufacturing", "Produits électroniques"),
    # Véhicules automobiles (UNIDO)
    "87": ("manufacturing", "Manufacture of motor vehicles"),
    # Minéraux non métalliques : ciment, verre, céramique (UNIDO — 18 pays)
    "68": ("manufacturing", "Manufacture of other non-metallic mineral products"),
    "69": ("manufacturing", "Manufacture of other non-metallic mineral products"),
    "70": ("manufacturing", "Manufacture of other non-metallic mineral products"),
    # Agro-industrie complémentaire : farines, huiles, aliments pour animaux
    "11": ("manufacturing", "Manufacture of food products"),
    "15": ("manufacturing", "Manufacture of food products"),
    "17": ("agri", "Sugarcane"),
    "23": ("manufacturing", "Manufacture of food products"),
    "24": ("agri", "Tobacco"),
    # Ouvrages en métaux (outillage, coutellerie)
    "82": ("manufacturing", "Manufacture of basic metals"),
    "83": ("manufacturing", "Manufacture of basic metals"),
}

DATASET_KEY = {
    "agri": "agri_faostat",
    "mining": "mining_usgs",
    "manufacturing": "manufacturing_unido",
}

SOURCE_META = {
    "agri": {
        "institution": "FAO",
        "dataset": "FAOSTAT — Production",
        "url": "https://www.fao.org/faostat/",
        "measure": "Production",
        "unit": "tonnes",
    },
    "mining": {
        "institution": "USGS",
        "dataset": "Mineral Commodity Summaries",
        "url": "https://www.usgs.gov/centers/national-minerals-information-center/mineral-commodity-summaries",
        "measure": "Production minière",
        "unit": "tonnes",
    },
    "manufacturing": {
        "institution": "UNIDO",
        "dataset": "INDSTAT4 (ISIC Rev.4)",
        "url": "https://stat.unido.org/",
        "measure": "Valeur ajoutée manufacturière",
        "unit": "USD",
    },
}


def _normalize_hs(hs_code: Optional[str]) -> str:
    if not hs_code:
        return ""
    return "".join(ch for ch in str(hs_code) if ch.isdigit())


def _match_commodity(hs_code: str) -> Optional[Tuple[str, str, str]]:
    """Retourne (dataset, commodity_label, match_level) ou None."""
    code = _normalize_hs(hs_code)
    if not code:
        return None
    # Match le plus spécifique d'abord (préfixe le plus long)
    for prefix, dataset, label in sorted(HS_TO_COMMODITY, key=lambda x: -len(x[0])):
        if code.startswith(prefix):
            return dataset, label, f"HS{len(prefix)}"
    # Repli par chapitre
    chapter = code[:2]
    if chapter in HS_CHAPTER_FALLBACK:
        dataset, label = HS_CHAPTER_FALLBACK[chapter]
        return dataset, label, "HS2 (chapitre)"
    return None


def _records_for(dataset: str, label: str) -> List[Dict]:
    data = load_production_data()
    key = DATASET_KEY[dataset]
    return [
        r
        for r in data.get(key, [])
        if r.get("commodity_label") == label
        or r.get("isic_label") == label
        or r.get("sector_detail") == label
    ]


def _cagr(first_val: float, last_val: float, years: int) -> Optional[float]:
    if not first_val or first_val <= 0 or years <= 0 or last_val <= 0:
        return None
    return ((last_val / first_val) ** (1.0 / years) - 1.0) * 100.0


def _build_scenarios(
    latest: float,
    cagr_pct: Optional[float],
    unit: str,
    country_share_pct: Optional[float],
    leader_value: Optional[float],
) -> Dict:
    """
    Projections d'intégration africaine — explicitement étiquetées comme scénarios.
    Calculées à partir du CAGR réel et de l'écart au leader continental ; aucun chiffre
    n'est inventé hors de ces fondations vérifiables.
    """
    if not latest or latest <= 0:
        return {}
    # CAGR de référence : observé, borné à [0%, 12%] pour rester réaliste
    base_cagr = cagr_pct if cagr_pct is not None else 2.0
    base_cagr = max(0.0, min(base_cagr, 12.0))

    def project(rate_pct: float, years: int) -> float:
        return round(latest * ((1.0 + rate_pct / 100.0) ** years), 1)

    scenarios = {
        "conservateur": {
            "label": "Conservateur — tendance actuelle",
            "annual_growth_pct": round(base_cagr, 2),
            "horizon_2030": project(base_cagr, 6),
            "hypothesis": "Maintien du CAGR observé 2021-2024, sans réforme additionnelle.",
        },
        "integration_zlecaf": {
            "label": "Intégration ZLECAf — accès marché élargi",
            "annual_growth_pct": round(base_cagr + 3.0, 2),
            "horizon_2030": project(base_cagr + 3.0, 6),
            "hypothesis": "Démantèlement tarifaire intra-africain (+3 pts de croissance via "
            "débouchés régionaux et réduction des barrières).",
        },
        "transformation_locale": {
            "label": "Transformation locale + ZLECAf",
            "annual_growth_pct": round(base_cagr + 6.0, 2),
            "horizon_2030": project(base_cagr + 6.0, 6),
            "hypothesis": "Montée en gamme industrielle (règles d'origine favorisant la "
            "valeur ajoutée locale) cumulée à l'accès marché ZLECAf.",
        },
    }
    # Écart au leader : potentiel de rattrapage tangible
    if leader_value and leader_value > latest:
        scenarios["potentiel_rattrapage"] = {
            "label": "Potentiel de rattrapage continental",
            "leader_production": round(leader_value, 1),
            "gap_pct": round((leader_value - latest) / leader_value * 100.0, 1),
            "hypothesis": f"Production additionnelle mobilisable si alignement sur le leader "
            f"continental ({unit}).",
        }
    return scenarios


def get_capacity(country_iso3: str, hs_code: str) -> Dict:
    """
    Capacité de production réelle d'un pays pour un produit (code HS), enrichie de
    son rang continental, de sa part africaine et de scénarios d'intégration.
    """
    iso3 = (country_iso3 or "").strip().upper()
    match = _match_commodity(hs_code)
    if not match:
        return {"available": False, "reason": "no_mapping", "hs_code": hs_code}

    dataset, label, match_level = match
    meta = SOURCE_META[dataset]
    all_recs = _records_for(dataset, label)
    if not all_recs:
        return {"available": False, "reason": "no_data", "commodity": label, "hs_code": hs_code}

    # Série temporelle du pays
    country_recs = sorted(
        [r for r in all_recs if r.get("country_iso3") == iso3],
        key=lambda r: r.get("year", 0),
    )
    timeseries = [
        {"year": r["year"], "value": r["value"], "unit": r.get("unit", meta["unit"])}
        for r in country_recs
    ]

    latest_rec = country_recs[-1] if country_recs else None
    latest_val = latest_rec["value"] if latest_rec else None
    latest_year = latest_rec["year"] if latest_rec else None

    cagr_pct = None
    if len(country_recs) >= 2:
        cagr_pct = _cagr(
            country_recs[0]["value"],
            country_recs[-1]["value"],
            country_recs[-1]["year"] - country_recs[0]["year"],
        )

    # Classement continental sur la dernière année commune
    ranking_year = latest_year
    year_recs = [r for r in all_recs if r.get("year") == ranking_year and r.get("value")]
    year_recs.sort(key=lambda r: r["value"], reverse=True)
    continental_total = sum(r["value"] for r in year_recs)
    rank = next((i + 1 for i, r in enumerate(year_recs) if r.get("country_iso3") == iso3), None)
    leader = year_recs[0] if year_recs else None
    country_share = (
        round(latest_val / continental_total * 100.0, 2)
        if latest_val and continental_total
        else None
    )

    top_producers = [
        {
            "country_iso3": r["country_iso3"],
            "country_name": r.get("country_name", r["country_iso3"]),
            "value": r["value"],
            "share_pct": (
                round(r["value"] / continental_total * 100.0, 1) if continental_total else None
            ),
        }
        for r in year_recs[:5]
    ]

    # Unité & source réelles de l'enregistrement (le pétrole/gaz ont leurs propres
    # unités/sources qui diffèrent du défaut du dataset).
    ref_rec = latest_rec or (year_recs[0] if year_recs else None)
    actual_unit = (ref_rec.get("unit") if ref_rec else None) or meta["unit"]
    actual_source = {
        "institution": (ref_rec.get("source_institution") if ref_rec else None)
        or meta["institution"],
        "dataset": (ref_rec.get("source_dataset") if ref_rec else None) or meta["dataset"],
        "url": (ref_rec.get("source_url") if ref_rec else None) or meta["url"],
    }

    scenarios = {}
    if latest_val:
        scenarios = _build_scenarios(
            latest_val,
            cagr_pct,
            actual_unit,
            country_share,
            leader["value"] if leader else None,
        )

    return {
        "available": bool(country_recs),
        "hs_code": hs_code,
        "match_level": match_level,
        "commodity": label,
        "dimension": dataset,
        "measure": meta["measure"],
        "unit": actual_unit,
        "source": actual_source,
        "country_iso3": iso3,
        "latest_value": latest_val,
        "latest_year": latest_year,
        "cagr_pct": round(cagr_pct, 2) if cagr_pct is not None else None,
        "timeseries": timeseries,
        "continental": {
            "ranking_year": ranking_year,
            "rank": rank,
            "total_countries": len(year_recs),
            "continental_total": round(continental_total, 1) if continental_total else None,
            "country_share_pct": country_share,
            "leader": (
                {
                    "country_iso3": leader["country_iso3"],
                    "country_name": leader.get("country_name"),
                    "value": leader["value"],
                }
                if leader
                else None
            ),
            "top_producers": top_producers,
        },
        "integration_scenarios": scenarios,
    }


def list_tracked_products() -> List[Dict]:
    """
    Univers des produits traçables par le référentiel production (FAOSTAT /
    USGS / UNIDO) : un représentant HS par (dataset, commodity), uniquement
    ceux qui ont des enregistrements réels. Sert de liste de candidats au
    scénario S4 (opportunités d'importation par pays) du module Opportunités.
    """
    seen = set()
    products: List[Dict] = []
    for prefix, dataset, label in HS_TO_COMMODITY:
        key = (dataset, label)
        if key in seen:
            continue
        seen.add(key)
        if not _records_for(dataset, label):
            continue
        products.append({"hs_code": prefix, "dataset": dataset, "commodity": label})
    return products


def get_continental_producers(hs_code: str) -> Dict:
    """
    Vue continentale (sans pays) : top producteurs africains réels pour un code HS.
    Utilisé par la recherche HS6 du module Chaînes de Valeur.
    """
    match = _match_commodity(hs_code)
    if not match:
        return {"available": False, "reason": "no_mapping", "hs_code": hs_code}
    dataset, label, match_level = match
    meta = SOURCE_META[dataset]
    all_recs = _records_for(dataset, label)
    if not all_recs:
        return {"available": False, "reason": "no_data", "commodity": label, "hs_code": hs_code}

    latest_year = max(r["year"] for r in all_recs)
    year_recs = sorted(
        [r for r in all_recs if r.get("year") == latest_year and r.get("value")],
        key=lambda r: r["value"],
        reverse=True,
    )
    total = sum(r["value"] for r in year_recs)
    ref_rec = year_recs[0] if year_recs else None
    actual_unit = (ref_rec.get("unit") if ref_rec else None) or meta["unit"]
    actual_source = {
        "institution": (ref_rec.get("source_institution") if ref_rec else None)
        or meta["institution"],
        "dataset": (ref_rec.get("source_dataset") if ref_rec else None) or meta["dataset"],
        "url": (ref_rec.get("source_url") if ref_rec else None) or meta["url"],
    }
    return {
        "available": True,
        "hs_code": hs_code,
        "match_level": match_level,
        "commodity": label,
        "dimension": dataset,
        "measure": meta["measure"],
        "unit": actual_unit,
        "source": actual_source,
        "year": latest_year,
        "continental_total": round(total, 1) if total else None,
        "top_producers": [
            {
                "country_iso3": r["country_iso3"],
                "country_name": r.get("country_name", r["country_iso3"]),
                "value": r["value"],
                "share_pct": round(r["value"] / total * 100.0, 1) if total else None,
            }
            for r in year_recs[:10]
        ],
    }


def enrich_opportunities(opportunities: List[Dict], country_iso3: str) -> List[Dict]:
    """
    Attache `production_capacity` à chaque opportunité disposant d'un code HS,
    pour le pays analysé (producteur dans les modes export / industriel).
    """
    if not country_iso3:
        return opportunities
    for opp in opportunities:
        product = opp.get("product") or {}
        hs = (
            product.get("hs6Code")
            or product.get("hs_code")
            or opp.get("hs6Code")
            or opp.get("hs_code")
        )
        if not hs:
            continue
        cap = get_capacity(country_iso3, hs)
        if cap.get("available"):
            opp["production_capacity"] = cap
    return opportunities
