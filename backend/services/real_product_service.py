"""
Real Product Analysis Service.

Builds the "Par Produit" view of the Opportunités module from REAL data instead
of LLM-generated figures:

- top African exporters / importers: OEC (BACI / UN Comtrade) via
  ``real_trade_data_service``;
- production capacities: FAO / USGS / UNIDO via ``production_capacity_service``;
- product nomenclature: WCO HS labels via ``get_product_name``.

No value is fabricated. When OEC is unreachable the trade tables come back empty
(rather than invented); the product nomenclature and the real production data are
still returned. ``is_estimation`` is True only when *no* real data at all is
available (neither trade nor production); ``data_quality`` further distinguishes
``real`` (real trade), ``partial`` (production only) and ``unavailable``.
"""

import logging
from datetime import datetime
from typing import Dict, List, Tuple

from services import production_capacity_service
from services.real_trade_data_service import (
    get_country_name,
    get_product_name,
    real_trade_service,
)

logger = logging.getLogger(__name__)

_CACHE: Dict[str, tuple] = {}
_CACHE_TTL = 3600  # 1 hour


def _cache_get(key: str):
    entry = _CACHE.get(key)
    if not entry:
        return None
    ts, value = entry
    if (datetime.utcnow() - ts).total_seconds() > _CACHE_TTL:
        _CACHE.pop(key, None)
        return None
    return value


def _cache_set(key: str, value) -> None:
    _CACHE[key] = (datetime.utcnow(), value)


def _product_info(hs_code: str, lang: str) -> Dict:
    """Real HS nomenclature info; the frontend merges /hs-codes for any gaps."""
    hs2 = hs_code[:2]
    # Do not pad: a 2-digit input keeps its raw value for hs4 (matches the
    # previous response contract; the frontend reads product.hs4_code directly).
    hs4 = hs_code[:4] if len(hs_code) >= 4 else hs_code
    hs6 = hs_code.zfill(6) if len(hs_code) <= 6 else hs_code[:6]
    name = get_product_name(hs_code, lang)
    return {
        "hs6Code": hs6,
        "hs4Code": hs4,
        "hs2Code": hs2,
        "hs2_code": hs2,
        "hs4_code": hs4,
        "name": name,
        "description": name,
    }


def _rank(entries: List[Dict], value_key: str, lang: str, out_key: str) -> Tuple[List[Dict], float]:
    """Convert raw OEC per-country aggregates into the frontend table shape."""
    total = sum(e.get(value_key, 0) for e in entries) or 0
    ranked = []
    for e in entries[:10]:
        value = e.get(value_key, 0)
        musd = round(value / 1_000_000, 2)
        ranked.append(
            {
                "country": get_country_name(e["country_iso3"], lang),
                "iso3": e["country_iso3"],
                "value_musd": musd,
                out_key: musd,
                "share_percent": round(value / total * 100, 1) if total else 0.0,
            }
        )
    return ranked, total


async def analyze_product_by_hs_code(hs_code: str, lang: str = "fr", year: int = 2022) -> Dict:
    """Real-data product analysis for an HS code (matches the previous response shape)."""
    cache_key = f"product_{hs_code}_{lang}_{year}"
    cached = _cache_get(cache_key)
    if cached is not None:
        return cached

    product = _product_info(hs_code, lang)

    # --- Real African trade flows (OEC) ---
    exporters_raw = await real_trade_service.get_african_exporters_for_product(hs_code, year=year)
    importers_raw = await real_trade_service.get_african_importers_for_product(hs_code, year=year)

    top_exporters, total_exp = _rank(exporters_raw, "export_value", lang, "export_value_musd")
    top_importers, total_imp = _rank(importers_raw, "import_value", lang, "import_value_musd")

    # --- Real production capacity (FAO / USGS / UNIDO) ---
    producers = production_capacity_service.get_continental_producers(hs_code)
    production_capacities: List[Dict] = []
    prod_sources: List[str] = []
    if producers.get("available"):
        unit = producers.get("unit")
        src = producers.get("source", {}) or {}
        institution = src.get("institution") or "FAO/USGS/UNIDO"
        dataset = src.get("dataset") or ""
        prod_sources.append(f"{institution} {dataset}".strip())
        for p in producers.get("top_producers", []):
            production_capacities.append(
                {
                    "country": p.get("country_name"),
                    "iso3": p.get("country_iso3"),
                    "capacity": p.get("value"),
                    "unit": unit,
                    "share": p.get("share_pct"),
                    "source": institution,
                }
            )

    has_trade = bool(top_exporters or top_importers)
    has_data = has_trade or bool(production_capacities)

    sources = ["OEC BACI", "UN Comtrade"] + prod_sources
    result = {
        "product": product,
        "african_trade_summary": {
            "total_african_exports_musd": round(total_exp / 1_000_000, 2),
            "total_african_imports_musd": round(total_imp / 1_000_000, 2),
            "year": year,
        },
        "top_african_exporters": top_exporters,
        "top_african_importers": top_importers,
        "production_capacities": production_capacities,
        # Substitutes are intentionally empty: no real relationship dataset exists
        # yet, and we do not fabricate them.
        "substitution_opportunities": [],
        "sources": [s for s in sources if s],
        "data_source": "OEC (BACI/UN Comtrade) + FAO/USGS/UNIDO",
        "generated_by": "Données réelles (OEC, FAO/USGS/UNIDO)",
        "data_quality": "real" if has_trade else ("partial" if has_data else "unavailable"),
        "is_estimation": not has_data,
    }

    if has_data:
        _cache_set(cache_key, result)
    return result


class RealProductService:
    """Thin OO wrapper for symmetry with the other real_* services."""

    async def analyze_product_by_hs_code(
        self, hs_code: str, lang: str = "fr", year: int = 2022
    ) -> Dict:
        return await analyze_product_by_hs_code(hs_code, lang=lang, year=year)


real_product_service = RealProductService()
