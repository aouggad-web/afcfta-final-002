"""
Real Country Comparison Service (the "Comparaison" tab).

Replaces the LLM-generated comparison with real, sourced figures:

- economic comparison (GDP, growth, HDI): country_data.REAL_COUNTRY_DATA
  (IMF WEO / World Bank / UNDP);
- bilateral trade A<->B: real OEC (BACI/UN Comtrade) directional flows;
- trade complementarity: computed from each country's real export/import
  structure (where A's real exports meet B's real imports, by HS chapter).

No value is fabricated. Fields with no sourced value (e.g. inflation) are
returned as null rather than invented; barriers/tariff savings are omitted
rather than guessed.
"""

import asyncio
import logging
from collections import defaultdict
from datetime import datetime
from typing import Dict, List, Optional, Tuple

from country_data import REAL_COUNTRY_DATA
from services.real_trade_data_service import (
    AFRICAN_COUNTRIES,
    get_country_name,
    real_trade_service,
)

logger = logging.getLogger(__name__)

_CACHE: Dict[str, tuple] = {}
_CACHE_TTL = 3600


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


def _resolve_iso3(country: str) -> Optional[str]:
    """Resolve an ISO3 code or a FR/EN country name to an ISO3 code."""
    if not country:
        return None
    key = country.strip()
    if key.upper() in AFRICAN_COUNTRIES:
        return key.upper()
    low = key.lower()
    for iso3, info in AFRICAN_COUNTRIES.items():
        if info.get("name_fr", "").lower() == low or info.get("name_en", "").lower() == low:
            return iso3
    return None


def _parse_pct(value) -> Optional[float]:
    """Parse a growth string like '3.5%' into a float; passthrough numbers."""
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    try:
        return float(str(value).replace("%", "").strip())
    except (ValueError, TypeError):
        return None


def _economic(iso3: str) -> Dict:
    d = REAL_COUNTRY_DATA.get(iso3, {})
    return {
        "gdp_billion": d.get("gdp_usd_2024"),
        "gdp_growth": _parse_pct(d.get("growth_projection_2025")),
        "hdi": d.get("development_index"),
        # Inflation is not in the sourced dataset; do not fabricate it.
        "inflation": None,
    }


def _exports_by_chapter(products: List[Dict]) -> Dict[str, Dict]:
    """Aggregate OEC export/import records into {chapter: {value, name, top_hs6}}.

    ``top_hs6`` is the single real 6-digit product code with the highest trade
    value inside the chapter — used downstream for an actual tariff lookup
    (a 2-digit chapter is too coarse to price a duty rate)."""
    by_chapter: Dict[str, Dict] = defaultdict(
        lambda: {"value": 0.0, "name": "", "top_hs6": None, "top_hs6_value": 0.0}
    )
    for p in products:
        hs_code = p.get("hs_code") or ""
        chapter = hs_code[:2]
        if not chapter:
            continue
        entry = by_chapter[chapter]
        value = p.get("trade_value", 0) or 0
        entry["value"] += value
        if not entry["name"]:
            entry["name"] = p.get("product_name", "")
        hs6 = hs_code[:6]
        if len(hs6) == 6 and value > entry["top_hs6_value"]:
            entry["top_hs6"] = hs6
            entry["top_hs6_value"] = value
    return by_chapter


def _complementarity(
    supplier_exports: Dict[str, Dict], buyer_imports: Dict[str, Dict]
) -> Tuple[List[Dict], float, float]:
    """Products the supplier really exports that the buyer really imports.

    Potential per chapter is bounded by min(supplier export, buyer import).
    Returns (top-5 flows, total matched potential, buyer imports in the matched
    chapters) — all in USD. The matched-chapter import base is the denominator
    used for the complementarity score."""
    flows = []
    total_potential = 0.0
    matched_import_base = 0.0
    for chapter, exp in supplier_exports.items():
        imp = buyer_imports.get(chapter)
        if not imp:
            continue
        potential = min(exp["value"], imp["value"])
        if potential <= 0:
            continue
        total_potential += potential
        matched_import_base += imp["value"]
        flows.append(
            {
                "product": exp["name"] or imp["name"] or f"Chapitre {chapter}",
                "hs6Code": exp.get("top_hs6") or chapter,
                "chapter": chapter,
                "potential_musd": round(potential / 1_000_000, 2),
                "potential_usd": potential,
            }
        )
    flows.sort(key=lambda f: f["potential_musd"], reverse=True)
    return flows[:5], total_potential, matched_import_base


def _tariff_savings_for_flows(
    flows: List[Dict], origin_iso3: str, destination_iso3: str
) -> Tuple[float, int, int]:
    """Real ZLECAf vs NPF duty saving for each supplier→buyer flow.

    Calls the same calculation engine as the Calculateur tab
    (services/authentic_tariff_service.calculate_import_taxes), which already
    encodes bilateral ZLECAf reciprocity (ratification + real implementation
    evidence, see zlecaf_active_implementers.py) — a flow only contributes a
    saving when a preference genuinely reduces the duty for that HS6/pair.

    Returns (total_saving_usd, flows_with_usable_tariff_data, total_flows).
    Never fabricates: a flow with no crawled/ETL tariff line for the
    destination simply contributes 0 and is excluded from the coverage count.
    """
    from services.authentic_tariff_service import calculate_import_taxes

    total_saving = 0.0
    covered = 0
    for flow in flows:
        hs6 = flow.get("hs6Code")
        value_usd = flow.get("potential_usd", 0) or 0
        if not hs6 or len(hs6) != 6 or value_usd <= 0:
            continue
        try:
            result = calculate_import_taxes(
                destination_iso3, hs6, value_usd, apply_zlecaf=True, origin_country=origin_iso3
            )
        except Exception as exc:
            logger.debug(f"tariff lookup failed for {destination_iso3}/{hs6}: {exc}")
            continue
        if not result or "error" in result:
            continue
        rates = result.get("rates", {})
        dd_pct = rates.get("dd_rate_pct")
        zlecaf_dd_pct = rates.get("zlecaf_rate_pct")
        if dd_pct is None or zlecaf_dd_pct is None or not result.get("zlecaf_preference_applied"):
            covered += 1  # tariff data found, even if no reduction applies
            continue
        saving = max(dd_pct - zlecaf_dd_pct, 0) / 100.0 * value_usd
        total_saving += saving
        covered += 1
    return total_saving, covered, len(flows)


async def compare_countries(country_a: str, country_b: str, lang: str = "fr") -> Dict:
    """Real-data comparison of two AfCFTA countries (previous response shape)."""
    iso_a = _resolve_iso3(country_a)
    iso_b = _resolve_iso3(country_b)
    if not iso_a or not iso_b:
        return {"error": "Country not found in AfCFTA dataset"}

    cache_key = f"compare_{iso_a}_{iso_b}_{lang}"
    cached = _cache_get(cache_key)
    if cached is not None:
        return cached

    name_a = get_country_name(iso_a, lang)
    name_b = get_country_name(iso_b, lang)
    year = 2022

    # Real flows + structures, fetched concurrently
    a_to_b, b_to_a, exports_a, imports_a, exports_b, imports_b = await asyncio.gather(
        real_trade_service.get_bilateral_trade(iso_a, iso_b, year=year),
        real_trade_service.get_bilateral_trade(iso_b, iso_a, year=year),
        real_trade_service.get_oec_exports(iso_a, year=year, limit=100),
        real_trade_service.get_oec_imports(iso_a, year=year, limit=100),
        real_trade_service.get_oec_exports(iso_b, year=year, limit=100),
        real_trade_service.get_oec_imports(iso_b, year=year, limit=100),
        return_exceptions=True,
    )

    def _safe(v, default):
        return default if isinstance(v, Exception) or v is None else v

    a_to_b = _safe(a_to_b, {"total_value": 0, "year": year})
    b_to_a = _safe(b_to_a, {"total_value": 0, "year": year})
    exp_a_ch = _exports_by_chapter(_safe(exports_a, []))
    imp_a_ch = _exports_by_chapter(_safe(imports_a, []))
    exp_b_ch = _exports_by_chapter(_safe(exports_b, []))
    imp_b_ch = _exports_by_chapter(_safe(imports_b, []))

    exp_ab = a_to_b.get("total_value", 0)
    exp_ba = b_to_a.get("total_value", 0)

    a_supply, pot_ab, base_ab = _complementarity(exp_a_ch, imp_b_ch)
    b_supply, pot_ba, base_ba = _complementarity(exp_b_ch, imp_a_ch)

    # Complementarity score: matched potential as a share of the buyers' imports
    # in the matched chapters, scaled to /10. Deterministic and bounded (potential
    # <= matched imports, so coverage <= 1 => score <= 10).
    matched_import_base = base_ab + base_ba
    coverage = ((pot_ab + pot_ba) / matched_import_base) if matched_import_base else 0
    score = round(min(coverage * 10, 10.0), 1)

    econ_a = _economic(iso_a)
    econ_b = _economic(iso_b)

    # Real tariff savings (NPF vs ZLECAf) on the top matched flows — same
    # calculation engine as the Calculateur tab (authentic_tariff_service),
    # so the bilateral ZLECAf reciprocity rules (ratification + real
    # implementation evidence) are honoured rather than assumed.
    saving_ab, covered_ab, total_ab = _tariff_savings_for_flows(a_supply, iso_a, iso_b)
    saving_ba, covered_ba, total_ba = _tariff_savings_for_flows(b_supply, iso_b, iso_a)
    tariff_savings_usd = saving_ab + saving_ba
    tariff_flows_covered = covered_ab + covered_ba
    tariff_flows_total = total_ab + total_ba
    if tariff_flows_total == 0:
        tariff_savings_musd = None
        tariff_savings_note = None
    else:
        tariff_savings_musd = round(tariff_savings_usd / 1_000_000, 3)
        tariff_savings_note = (
            f"Calculé sur {tariff_flows_covered}/{tariff_flows_total} filière(s) "
            f"disposant d'une donnée tarifaire (Calculateur) ; réciprocité ZLECAf "
            f"bilatérale appliquée."
            if lang == "fr"
            else f"Computed over {tariff_flows_covered}/{tariff_flows_total} flow(s) "
            f"with usable tariff data (Calculateur); bilateral AfCFTA reciprocity applied."
        )

    has_trade = bool(exp_ab or exp_ba or a_supply or b_supply)

    note = None
    if not has_trade:
        note = (
            "Flux commerciaux (OEC) temporairement indisponibles : les indicateurs "
            "économiques réels (PIB, croissance, IDH) sont affichés, mais le commerce "
            "bilatéral et la complémentarité nécessitent la source OEC."
        )

    if lang == "fr":
        explanation = (
            f"Complémentarité estimée à partir des structures réelles d'exportation "
            f"et d'importation : {len(a_supply)} filière(s) où {name_a} peut fournir "
            f"{name_b}, et {len(b_supply)} dans l'autre sens (source OEC)."
        )
    else:
        explanation = (
            f"Complementarity derived from real export/import structures: "
            f"{len(a_supply)} value chain(s) where {name_a} can supply {name_b}, and "
            f"{len(b_supply)} the other way around (OEC source)."
        )

    key_opportunities = [f["product"] for f in (a_supply + b_supply)][:5]

    # Real logistics profile (multimodal freight cost + free zones) both ways —
    # same adapter as the Reports module (services/logistics_opportunity_adapter.py).
    # Routes/costs can differ by direction, so both A→B and B→A are computed.
    try:
        from services.logistics_opportunity_adapter import (
            get_logistics_profile,
            summarize_logistics_accessibility,
        )

        profile_ab = get_logistics_profile(iso_a, iso_b)
        profile_ba = get_logistics_profile(iso_b, iso_a)
        logistics = {
            "a_to_b": {
                "available": profile_ab["freight"].get("available", False),
                "best_operational_cost_usd": profile_ab.get("best_operational_cost_usd"),
                "accessibility_index": summarize_logistics_accessibility(profile_ab).get("index"),
                "free_zones_at_destination": [
                    z.get("name") for z in profile_ab["free_zones"].get("zones", [])[:3]
                ],
            },
            "b_to_a": {
                "available": profile_ba["freight"].get("available", False),
                "best_operational_cost_usd": profile_ba.get("best_operational_cost_usd"),
                "accessibility_index": summarize_logistics_accessibility(profile_ba).get("index"),
                "free_zones_at_destination": [
                    z.get("name") for z in profile_ba["free_zones"].get("zones", [])[:3]
                ],
            },
        }
    except Exception as e:
        logger.warning(f"Logistics profile failed for {iso_a}/{iso_b}: {e}")
        logistics = {"a_to_b": {"available": False}, "b_to_a": {"available": False}}

    result = {
        "country_a": name_a,
        "country_b": name_b,
        "bilateral_trade": {
            "exports_a_to_b_musd": round(exp_ab / 1_000_000, 2),
            "exports_b_to_a_musd": round(exp_ba / 1_000_000, 2),
            "balance_musd": round((exp_ab - exp_ba) / 1_000_000, 2),
            "year": year,
            "main_products_a_to_b": [
                p.get("product_name", "") for p in a_to_b.get("top_products", [])[:5]
            ],
            "main_products_b_to_a": [
                p.get("product_name", "") for p in b_to_a.get("top_products", [])[:5]
            ],
        },
        "economic_comparison": {
            "gdp_a_billion": econ_a["gdp_billion"],
            "gdp_b_billion": econ_b["gdp_billion"],
            "gdp_growth_a": econ_a["gdp_growth"],
            "gdp_growth_b": econ_b["gdp_growth"],
            "hdi_a": econ_a["hdi"],
            "hdi_b": econ_b["hdi"],
            "inflation_a": econ_a["inflation"],
            "inflation_b": econ_b["inflation"],
        },
        "trade_complementarity": {
            "score": score,
            "explanation": explanation,
            "a_can_supply_to_b": a_supply,
            "b_can_supply_to_a": b_supply,
        },
        "afcfta_potential": {
            "total_potential_musd": round((pot_ab + pot_ba) / 1_000_000, 2),
            # Calculé réellement via le Calculateur (authentic_tariff_service) sur
            # les filières de complémentarité — None seulement si aucune des
            # filières n'a de donnée tarifaire exploitable (jamais fabriqué).
            "tariff_savings_musd": tariff_savings_musd,
            "tariff_savings_note": tariff_savings_note,
            "key_opportunities": key_opportunities,
            "barriers": [],
        },
        "logistics": logistics,
        "sources": ["OEC BACI", "UN Comtrade", "IMF WEO", "World Bank", "UNDP"],
        "data_source": "OEC (BACI/UN Comtrade) + IMF/World Bank/UNDP (country_data)",
        "generated_by": "Données réelles (OEC, IMF/BM/PNUD)",
        "is_estimation": not has_trade,
        "oec_available": has_trade,
        "note": note,
    }

    if has_trade:
        _cache_set(cache_key, result)
    return result


class RealComparisonService:
    """Thin OO wrapper for symmetry with the other real_* services."""

    async def compare_countries(self, country_a: str, country_b: str, lang: str = "fr") -> Dict:
        return await compare_countries(country_a, country_b, lang=lang)


real_comparison_service = RealComparisonService()
