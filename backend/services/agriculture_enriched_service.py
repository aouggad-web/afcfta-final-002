"""
Service Agriculture enrichie — séries FAOSTAT dynamiques + projections étiquetées
=================================================================================
Construit la vue « Agriculture » du module Production à partir du dataset
enrichi réel (``agri_faostat`` : bulk FAOSTAT QCL, 54 pays, 2019-2024,
dédupliqué au chargement) au lieu des seules données curées codées en dur
(``etl/faostat_data.py``, 3-6 cultures/pays, évolution partielle).

Principes (alignés sur production_capacity_service) :
  - les séries affichées sont les valeurs RÉELLES publiées, toutes années
    disponibles (2019-2024) et tous produits du bulk ;
  - la couche curée (rangs Afrique, surfaces, rendements, indicateurs clés,
    élevage, pêche) est conservée comme ENRICHISSEMENT par label ;
  - les PROJECTIONS sont dérivées du CAGR réel observé, borné, explicitement
    étiquetées (``is_projection: true``) — aucune valeur inventée hors de
    cette tendance vérifiable ;
  - un pays sans série assez longue (1 point) n'a AUCUNE projection.
"""

from __future__ import annotations

import logging
from collections import Counter
from typing import Dict, List, Optional, Tuple

from production_data import get_agriculture_production

logger = logging.getLogger(__name__)

# ── Paramètres de projection ──────────────────────────────────────────────────
PROJECTION_HORIZON_YEARS = 3
CAGR_MIN_PCT = -15.0  # borne basse (effondrement plausibilité agricole)
CAGR_MAX_PCT = 20.0  # borne haute (boom plausibilité, cf. scénarios ZLECAf)
MIN_YEARS_FOR_CAGR = 2

# ── Traduction FR des libellés FAOSTAT bulk (69 labels) — fallback : libellé EN
LABEL_FR: Dict[str, str] = {
    "Almonds": "Amandes",
    "Apples": "Pommes",
    "Avocados": "Avocats",
    "Bananas": "Bananes",
    "Barley": "Orge",
    "Beans": "Haricots",
    "Cabbages": "Choux",
    "Carrots": "Carottes",
    "Cashew nuts": "Noix de cajou",
    "Cassava": "Manioc",
    "Cattle meat": "Viande bovine",
    "Cattle milk": "Lait de vache",
    "Cauliflowers": "Choux-fleurs",
    "Chicken meat": "Viande de volaille",
    "Chickpeas": "Pois chiches",
    "Chillies and peppers": "Piments et poivrons",
    "Cinnamon": "Cannelle",
    "Cloves": "Clous de girofle",
    "Cocoa beans": "Cacao",
    "Coconuts": "Noix de coco",
    "Coffee": "Café",
    "Cowpeas": "Niébé",
    "Cucumbers": "Concombres",
    "Dates": "Dattes",
    "Eggplants": "Aubergines",
    "Ginger": "Gingembre",
    "Grapes": "Raisins",
    "Groundnuts": "Arachides",
    "Hen eggs": "Œufs de poule",
    "Kola nuts": "Noix de kola",
    "Lemons and limes": "Citrons et limes",
    "Lentils": "Lentilles",
    "Lettuce": "Laitue",
    "Linseed": "Lin",
    "Maize (corn)": "Maïs",
    "Mangoes": "Mangues",
    "Millet": "Mil",
    "Oats": "Avoine",
    "Oil palm": "Huile de palme",
    "Okra": "Gombo",
    "Olives": "Olives",
    "Onions": "Oignons",
    "Oranges": "Oranges",
    "Papayas": "Papayes",
    "Peas": "Pois",
    "Pepper": "Poivre",
    "Pigeon peas": "Pois d'Angole",
    "Pineapples": "Ananas",
    "Plantain": "Plantain",
    "Potatoes": "Pommes de terre",
    "Rapeseed": "Colza",
    "Rice": "Riz",
    "Rubber": "Caoutchouc",
    "Seed cotton": "Coton graine",
    "Sesame": "Sésame",
    "Shea nuts": "Noix de karité",
    "Sorghum": "Sorgho",
    "Soybeans": "Soja",
    "Spinach": "Épinards",
    "Sugarcane": "Canne à sucre",
    "Sunflower seed": "Graines de tournesol",
    "Sweet potatoes": "Patates douces",
    "Tea": "Thé",
    "Tobacco": "Tabac",
    "Tomatoes": "Tomates",
    "Vanilla": "Vanille",
    "Watermelons": "Pastèques",
    "Wheat": "Blé",
    "Yam": "Igname",
}

# ── Cultures curées FR → libellé FAOSTAT EN (aligné sur build_production_real)
CROP_FR_TO_EN: Dict[str, str] = {
    "Maïs": "Maize (corn)",
    "Manioc": "Cassava",
    "Riz": "Rice",
    "Sorgho": "Sorghum",
    "Banane": "Bananas",
    "Bananes": "Bananas",
    "Mil": "Millet",
    "Blé": "Wheat",
    "Café": "Coffee",
    "Canne à sucre": "Sugarcane",
    "Coton": "Seed cotton",
    "Cacao": "Cocoa beans",
    "Arachide": "Groundnuts",
    "Arachides": "Groundnuts",
    "Thé": "Tea",
    "Olives": "Olives",
    "Agrumes": "Citrus fruits",
    "Oranges": "Citrus fruits",
    "Noix de cajou": "Cashew nuts",
    "Huile de palme": "Oil palm",
    "Orge": "Barley",
    "Dattes": "Dates",
    "Tomate": "Tomatoes",
    "Tomates": "Tomatoes",
    "Igname": "Yam",
    "Plantain": "Plantain",
    "Soja": "Soybeans",
    "Hévéa": "Rubber",
    "Vanille": "Vanilla",
    "Tabac": "Tobacco",
    "Pomme de terre": "Potatoes",
    "Niébé": "Cowpeas",
    "Oignon": "Onions",
    "Ananas": "Pineapples",
    "Fonio": "Millet",
    "Teff": "Teff",
    "Fleurs coupées": "Cut flowers",
    "Haricot": "Beans",
    "Clou de girofle": "Cloves",
    "Sésame": "Sesame",
    "Gomme arabique": "Gum arabic",
    "Légumes": "Vegetables",
    "Ylang-ylang": "Ylang-ylang",
    "Noix de coco": "Coconuts",
    "Cannelle": "Cinnamon",
    "Tournesol": "Sunflower seed",
}


def _cagr_pct(first_val: float, last_val: float, years: int) -> Optional[float]:
    """CAGR réel observé en %, ou None si non calculable."""
    if not first_val or first_val <= 0 or not last_val or last_val <= 0 or years <= 0:
        return None
    return ((last_val / first_val) ** (1.0 / years) - 1.0) * 100.0


def _build_series_with_projections(
    points: List[Dict], latest_year: int, unit: str
) -> Tuple[List[Dict], Optional[float], List[Dict]]:
    """
    Série historique + projections CAGR bornées, explicitement étiquetées.

    Returns:
        (series_complètes, cagr_observé_pct, points_de_projection)
    """
    historical = sorted(
        [
            {"year": int(p["year"]), "value": p["value"], "is_projection": False}
            for p in points
            if p.get("value") is not None
        ],
        key=lambda x: x["year"],
    )
    if not historical:
        return [], None, []

    latest = historical[-1]
    cagr = None
    if len(historical) >= MIN_YEARS_FOR_CAGR:
        cagr = _cagr_pct(
            historical[0]["value"], latest["value"], latest["year"] - historical[0]["year"]
        )

    projections: List[Dict] = []
    if cagr is not None:
        bounded = max(CAGR_MIN_PCT, min(CAGR_MAX_PCT, cagr))
        for n in range(1, PROJECTION_HORIZON_YEARS + 1):
            projections.append(
                {
                    "year": latest_year + n,
                    "value": round(latest["value"] * ((1.0 + bounded / 100.0) ** n), 1),
                    "is_projection": True,
                }
            )
    return historical + projections, cagr, projections


def _unit_for(records: List[Dict]) -> str:
    """Unité la plus fréquente parmi les records d'une culture."""
    units = Counter(r.get("unit") or "tonnes" for r in records)
    return units.most_common(1)[0][0]


def _curated_enrichment(curated: Dict) -> Dict[str, Dict]:
    """label EN → enrichissements curés (rang Afrique, surface, rendement)."""
    out: Dict[str, Dict] = {}
    for fr, info in (curated.get("production_2023") or {}).items():
        en = CROP_FR_TO_EN.get(fr)
        if not en or en in out:
            continue
        enrich = {
            k: info.get(k) for k in ("rank_africa", "area_ha", "yield_kg_ha") if info.get(k)
        }
        if enrich:
            out[en] = enrich
    return out


def _curated_only_crop(fr: str, info: Dict, curated: Dict) -> Optional[Dict]:
    """Culture curée sans correspondance bulk → entrée autonome (fallback)."""
    value = info.get("value")
    if not value:
        return None
    evo = (curated.get("evolution") or {}).get(fr) or []
    historical = sorted(
        [
            {"year": int(p["year"]), "value": p["value"], "is_projection": False}
            for p in evo
            if p.get("value")
        ],
        key=lambda x: x["year"],
    )
    if not any(p["year"] == 2023 for p in historical):
        historical.append({"year": 2023, "value": value, "is_projection": False})
    series, cagr, _ = _build_series_with_projections(historical, 2023, info.get("unit", "tonnes"))
    return {
        "name": fr,
        "name_en": CROP_FR_TO_EN.get(fr, fr),
        "value": value,
        "latest_year": 2023,
        "value_2023": value,
        "unit": info.get("unit", "tonnes"),
        "rank_africa": info.get("rank_africa"),
        "area_ha": info.get("area_ha"),
        "yield_kg_ha": info.get("yield_kg_ha"),
        "cagr_pct": round(cagr, 1) if cagr is not None else None,
        "series": series,
        "has_projection": any(p["is_projection"] for p in series),
        "source": "curated",
    }


def get_country_agriculture_enriched(iso3: str, language: str = "fr") -> Optional[Dict]:
    """
    Vue agriculture enrichie d'un pays : TOUTES les cultures FAOSTAT bulk
    (séries réelles 2019-2024) + projections CAGR étiquetées, enrichies de la
    couche curée (rangs, surfaces, rendements). Retourne None si le pays n'a
    aucune donnée bulk (le caller retombera sur le curé).
    """
    iso3 = (iso3 or "").strip().upper()
    if not iso3:
        return None

    records = get_agriculture_production(country_iso3=iso3)
    if not records:
        return None

    # Import paresseux pour éviter tout cycle (faostat_data est volumineux)
    from etl.faostat_data import FAOSTAT_AGRICULTURE_DATA

    curated = FAOSTAT_AGRICULTURE_DATA.get(iso3, {})
    enrichment = _curated_enrichment(curated)

    # ── Groupement par culture (dataset dédupliqué au chargement) ──
    by_crop: Dict[str, List[Dict]] = {}
    for r in records:
        by_crop.setdefault(r.get("commodity_label") or "Unknown", []).append(r)

    years_covered = sorted({int(r["year"]) for r in records if r.get("year") is not None})
    latest_year = years_covered[-1] if years_covered else None
    projection_horizon = (
        list(range(latest_year + 1, latest_year + 1 + PROJECTION_HORIZON_YEARS))
        if latest_year
        else []
    )

    cultures: List[Dict] = []
    evolution: Dict[str, Dict[str, float]] = {}
    evolution_with_projections: Dict[str, List[Dict]] = {}

    for label, crop_records in by_crop.items():
        unit = _unit_for(crop_records)
        series, cagr, _ = _build_series_with_projections(crop_records, latest_year or 0, unit)
        if not series:
            continue
        historical = [p for p in series if not p["is_projection"]]
        real_latest = historical[-1]
        value_2023 = next(
            (p["value"] for p in historical if p["year"] == 2023), None
        )
        extra = enrichment.get(label, {})
        display_name = LABEL_FR.get(label, label) if language == "fr" else label
        cultures.append(
            {
                "name": display_name,
                "name_en": label,
                "value": real_latest["value"],
                "latest_year": real_latest["year"],
                "value_2023": value_2023,
                "unit": unit,
                "rank_africa": extra.get("rank_africa"),
                "area_ha": extra.get("area_ha"),
                "yield_kg_ha": extra.get("yield_kg_ha"),
                "cagr_pct": round(cagr, 1) if cagr is not None else None,
                "series": series,
                "has_projection": any(p["is_projection"] for p in series),
                "source": "FAOSTAT bulk QCL",
            }
        )
        # Indexé par nom affiché : le frontend trace directement les lignes.
        evolution[display_name] = {str(p["year"]): p["value"] for p in historical}
        evolution_with_projections[display_name] = series

    cultures.sort(key=lambda c: c["value"] or 0, reverse=True)

    # ── Cultures curées sans données bulk (données réelles curées conservées) ──
    bulk_labels = set(by_crop)
    for fr, info in (curated.get("production_2023") or {}).items():
        en = CROP_FR_TO_EN.get(fr)
        if en and en in bulk_labels:
            continue
        fallback = _curated_only_crop(fr, info, curated)
        if fallback:
            cultures.append(fallback)
            evolution[fr] = {
                str(p["year"]): p["value"] for p in fallback["series"] if not p["is_projection"]
            }
            evolution_with_projections[fr] = fallback["series"]

    return {
        "available": True,
        "data_mode": "FAOSTAT bulk QCL (séries réelles multi-années) + projections CAGR étiquetées",
        "years_covered": years_covered,
        "latest_year": latest_year,
        "projection_horizon": projection_horizon,
        "projection_method": (
            f"CAGR observé borné [{CAGR_MIN_PCT:.0f}%, +{CAGR_MAX_PCT:.0f}%], "
            f"horizon {PROJECTION_HORIZON_YEARS} ans — étiqueté is_projection"
        ),
        "cultures": cultures,
        "evolution": evolution,
        "evolution_with_projections": evolution_with_projections,
    }
