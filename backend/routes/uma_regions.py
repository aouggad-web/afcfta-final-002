"""
UMA/AMU North Africa Regional API Routes.

Provides intelligence endpoints for all 7 North African countries:
  MAR (Morocco), EGY (Egypt), TUN (Tunisia), DZA (Algeria),
  LBY (Libya), SDN (Sudan), MRT (Mauritania)

Endpoints:
  GET  /api/regions/north-africa/countries            # All 7 country profiles
  GET  /api/regions/uma/intelligence                  # UMA regional intelligence
  GET  /api/tariffs/north-africa/{country_code}       # Country tariff profile
  GET  /api/investment/north-africa/zones             # All SEZ data
  GET  /api/investment/north-africa/zones/{cc}        # Country-specific SEZs
  GET  /api/trade/north-africa/agreements             # Trade agreement matrix
  GET  /api/regions/north-africa/summary              # Regional overview summary
  GET  /api/regions/north-africa/compare              # Cross-country comparison
"""

import logging
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

logger = logging.getLogger(__name__)

# ── Routers ──────────────────────────────────────────────────────────────────

regions_router = APIRouter(prefix="/regions", tags=["North Africa Regions"])
tariffs_router = APIRouter(prefix="/tariffs", tags=["North Africa Tariffs"])
investment_router = APIRouter(prefix="/investment", tags=["North Africa Investment"])
trade_router = APIRouter(prefix="/trade", tags=["North Africa Trade"])

# Convenience re-export for registration
router = APIRouter()


# ── Helpers ───────────────────────────────────────────────────────────────────

def _constants():
    from crawlers.countries.north_africa.uma_constants import (
        COUNTRY_METADATA,
        UMA_COUNTRIES,
        UMA_TRADE_BLOCS,
        UMA_VAT_RATES,
        UMA_CORPORATE_TAX_RATES,
        UMA_INVESTMENT_LAWS,
        UMA_DATA_SOURCES,
        UMA_SECTOR_STRENGTHS,
        MULTILANG_NAMES,
    )
    return {
        "metadata": COUNTRY_METADATA,
        "countries": UMA_COUNTRIES,
        "trade_blocs": UMA_TRADE_BLOCS,
        "vat_rates": UMA_VAT_RATES,
        "cit_rates": UMA_CORPORATE_TAX_RATES,
        "investment_laws": UMA_INVESTMENT_LAWS,
        "data_sources": UMA_DATA_SOURCES,
        "sector_strengths": UMA_SECTOR_STRENGTHS,
        "multilang": MULTILANG_NAMES,
    }


def _tariff_structures():
    from crawlers.countries.north_africa.tariff_structures import (
        get_country_tariff_profile,
        get_all_profiles,
        get_regional_tariff_comparison,
        MOROCCO_TARIFFS,
    )
    return {
        "get_profile": get_country_tariff_profile,
        "get_all": get_all_profiles,
        "compare": get_regional_tariff_comparison,
        "morocco_bands": MOROCCO_TARIFFS,
    }


def _investment_zones():
    from crawlers.countries.north_africa.investment_zones import (
        get_investment_zones,
        get_all_sez_data,
        get_zone_summary,
    )
    return {
        "get_zones": get_investment_zones,
        "get_all": get_all_sez_data,
        "summary": get_zone_summary,
    }


# ── /api/regions/north-africa/countries ──────────────────────────────────────

@regions_router.get("/north-africa/countries")
async def get_north_africa_countries(
    include_extended: bool = Query(
        True,
        description="Include extended countries (LBY, SDN, MRT). False returns only core 4.",
    ),
    language: str = Query(
        "en",
        description="Name language: en | fr | ar",
    ),
):
    """
    Get profiles for all North African countries on the UMA/AMU platform.

    Returns metadata including GDP, population, currency, trade agreements,
    customs authority, investment agency, and data reliability.
    """
    try:
        c = _constants()
        core_4 = {"MAR", "EGY", "TUN", "DZA"}

        countries = []
        for code in c["countries"]:
            if not include_extended and code not in core_4:
                continue

            meta = c["metadata"].get(code, {})
            ml = c["multilang"].get(code, {})

            name = ml.get(language, ml.get("en", meta.get("name_en", code)))

            countries.append({
                "iso3": code,
                "name": name,
                "name_en": meta.get("name_en", ""),
                "name_fr": meta.get("name_fr", ""),
                "name_ar": meta.get("name_ar", ""),
                "capital": meta.get("capital", ""),
                "currency": meta.get("currency", ""),
                "currency_name": meta.get("currency_name", ""),
                "population_m": meta.get("population_m"),
                "gdp_bn_usd": meta.get("gdp_bn_usd"),
                "languages": meta.get("languages", []),
                "uma_member": meta.get("uma_member", False),
                "wto_member": meta.get("wto_member", False),
                "afcfta_ratified": meta.get("afcfta_ratified", False),
                "trade_blocs": c["trade_blocs"].get(code, []),
                "vat_rate": c["vat_rates"].get(code),
                "corporate_tax_rate": c["cit_rates"].get(code),
                "investment_law": c["investment_laws"].get(code, ""),
                "sector_strengths": c["sector_strengths"].get(code, []),
                "customs_authority": meta.get("customs_authority", ""),
                "customs_url": meta.get("customs_url", ""),
                "investment_agency": meta.get("investment_agency", ""),
                "investment_url": meta.get("investment_url", ""),
                "data_reliability": meta.get("data_reliability", "unknown"),
            })

        return {
            "region": "North Africa",
            "total_countries": len(countries),
            "uma_core_members": ["MAR", "DZA", "TUN", "LBY", "MRT"],
            "extended_members": ["EGY", "SDN"],
            "countries": countries,
        }
    except Exception as exc:
        logger.error(f"get_north_africa_countries failed: {exc}")
        raise HTTPException(status_code=500, detail=str(exc))


# ── /api/regions/uma/intelligence ────────────────────────────────────────────

@regions_router.get("/uma/intelligence")
async def get_uma_intelligence():
    """
    Get comprehensive UMA/AMU regional intelligence overview.

    Returns:
    - Regional macro context (GDP, population, trade bloc memberships)
    - Country intelligence summaries for all 7 countries
    - Key strategic corridors
    - Investment climate overview
    - Multi-language support status
    """
    try:
        c = _constants()
        ts = _tariff_structures()
        iz = _investment_zones()

        zone_summary = iz["summary"]()
        all_profiles = ts["get_all"]()

        intelligence = {}
        for code in c["countries"]:
            meta = c["metadata"].get(code, {})
            profile = all_profiles.get(code, {})
            intelligence[code] = {
                "country": code,
                "name_en": meta.get("name_en", code),
                "gdp_bn_usd": meta.get("gdp_bn_usd"),
                "population_m": meta.get("population_m"),
                "uma_member": meta.get("uma_member", False),
                "trade_blocs": c["trade_blocs"].get(code, []),
                "vat_rate": c["vat_rates"].get(code),
                "corporate_tax_rate": c["cit_rates"].get(code),
                "investment_law": c["investment_laws"].get(code, ""),
                "sector_strengths": c["sector_strengths"].get(code, []),
                "tariff_bands": profile.get("bands", {}),
                "data_quality": profile.get("data_quality", "unknown"),
                "data_reliability": meta.get("data_reliability", "unknown"),
                "special_zones_count": len(iz["get_zones"](code)),
            }

        total_gdp = sum(
            c["metadata"].get(cc, {}).get("gdp_bn_usd", 0) or 0
            for cc in c["countries"]
        )
        total_pop = sum(
            c["metadata"].get(cc, {}).get("population_m", 0) or 0
            for cc in c["countries"]
        )

        return {
            "region": "North Africa (UMA/AMU + Extended)",
            "region_ar": "أفريقيا الشمالية (اتحاد المغرب العربي)",
            "uma_core_members": ["MAR", "DZA", "TUN", "LBY", "MRT"],
            "extended_members": ["EGY", "SDN"],
            "total_countries": len(c["countries"]),
            "combined_gdp_bn_usd": total_gdp,
            "combined_population_m": total_pop,
            "common_agreements": [
                "AfCFTA", "GAFTA", "UMA/AMU Framework", "Agadir Agreement"
            ],
            "investment_zones": zone_summary,
            "country_intelligence": intelligence,
            "strategic_corridors": {
                "atlantic_gateway": {
                    "anchor": "MAR",
                    "description": "Morocco as Atlantic/Mediterranean gateway for sub-Saharan Africa",
                    "key_infrastructure": "Tanger-Med Port (9M TEU capacity)",
                },
                "suez_hub": {
                    "anchor": "EGY",
                    "description": "Egypt Suez Canal gateway, 21,000 vessels/year",
                    "key_infrastructure": "SCZONE – 461,000 ha",
                },
                "sahel_gateway": {
                    "anchor": "DZA",
                    "description": "Algeria as Northern gateway to Sahel",
                    "key_infrastructure": "Trans-Saharan Highway",
                },
                "maghreb_west_africa_bridge": {
                    "anchor": "MRT",
                    "description": "Mauritania bridging Maghreb and West Africa",
                    "key_infrastructure": "Nouakchott Port",
                },
            },
            "multilanguage_support": {
                "arabic": "Primary – all 7 countries",
                "french": "Secondary – MAR, DZA, TUN, MRT",
                "english": "Secondary – EGY, SDN, LBY",
                "tamazight": "Cultural recognition – MAR, DZA",
            },
        }
    except Exception as exc:
        logger.error(f"get_uma_intelligence failed: {exc}")
        raise HTTPException(status_code=500, detail=str(exc))


# ── /api/regions/north-africa/summary ────────────────────────────────────────

@regions_router.get("/north-africa/summary")
async def get_regional_summary():
    """Get a concise regional overview for dashboards."""
    try:
        c = _constants()
        iz = _investment_zones()

        zone_summary = iz["summary"]()
        total_gdp = sum(
            c["metadata"].get(cc, {}).get("gdp_bn_usd", 0) or 0
            for cc in c["countries"]
        )
        total_pop = sum(
            c["metadata"].get(cc, {}).get("population_m", 0) or 0
            for cc in c["countries"]
        )

        return {
            "region": "North Africa",
            "total_countries": len(c["countries"]),
            "combined_gdp_bn_usd": total_gdp,
            "combined_population_m": total_pop,
            "investment_zones_total": zone_summary["total_zones"],
            "investment_zones_operational": zone_summary["operational_zones"],
            "port_connected_zones": zone_summary["port_connected_zones"],
            "high_reliability_countries": ["MAR", "EGY", "TUN"],
            "medium_reliability_countries": ["DZA"],
            "low_reliability_countries": ["LBY", "SDN", "MRT"],
        }
    except Exception as exc:
        logger.error(f"get_regional_summary failed: {exc}")
        raise HTTPException(status_code=500, detail=str(exc))


# ── /api/regions/north-africa/compare ────────────────────────────────────────

@regions_router.get("/north-africa/compare")
async def compare_countries(
    countries: Optional[str] = Query(
        None,
        description="Comma-separated ISO-3 codes (e.g. MAR,EGY,TUN). Defaults to all 7.",
    ),
    chapter: Optional[int] = Query(
        None,
        description="HS chapter (1-97) for tariff comparison.",
    ),
):
    """
    Cross-country comparison of key trade and investment metrics.

    Includes VAT, corporate tax, investment law, sector strengths,
    and optionally a tariff comparison for a specific HS chapter.
    """
    try:
        c = _constants()
        ts = _tariff_structures()

        target_codes = (
            [cc.strip().upper() for cc in countries.split(",")]
            if countries
            else c["countries"]
        )

        comparison = {}
        for code in target_codes:
            meta = c["metadata"].get(code, {})
            comparison[code] = {
                "name_en": meta.get("name_en", code),
                "gdp_bn_usd": meta.get("gdp_bn_usd"),
                "population_m": meta.get("population_m"),
                "vat_rate": c["vat_rates"].get(code),
                "corporate_tax_rate": c["cit_rates"].get(code),
                "investment_law": c["investment_laws"].get(code, ""),
                "trade_blocs": c["trade_blocs"].get(code, []),
                "sector_strengths": c["sector_strengths"].get(code, []),
                "data_reliability": meta.get("data_reliability", "unknown"),
            }
            if chapter is not None:
                from crawlers.countries.north_africa.tariff_structures import get_chapter_rate
                comparison[code]["indicative_dd_rate_chapter"] = get_chapter_rate(code, chapter)

        return {
            "comparison": comparison,
            "chapter_compared": chapter,
            "note": "Tariff rates are indicative MFN averages for the HS chapter band.",
        }
    except Exception as exc:
        logger.error(f"compare_countries failed: {exc}")
        raise HTTPException(status_code=500, detail=str(exc))


# ── /api/tariffs/north-africa/{country_code} ─────────────────────────────────

@tariffs_router.get("/north-africa/{country_code}")
async def get_country_tariff_profile(country_code: str):
    """
    Get the full tariff profile for a North African country.

    Returns tariff bands, VAT, additional taxes, preferential agreements,
    special regimes, and data quality metadata.

    Path parameter:
    - country_code: ISO-3 code (MAR, EGY, TUN, DZA, LBY, SDN, MRT)
    """
    try:
        ts = _tariff_structures()
        profile = ts["get_profile"](country_code.upper())
        if profile is None:
            raise HTTPException(
                status_code=404,
                detail=(
                    f"Country '{country_code}' not found. "
                    "Valid codes: MAR, EGY, TUN, DZA, LBY, SDN, MRT"
                ),
            )
        return profile
    except HTTPException:
        raise
    except Exception as exc:
        logger.error(f"get_country_tariff_profile({country_code}) failed: {exc}")
        raise HTTPException(status_code=500, detail=str(exc))


@tariffs_router.get("/north-africa")
async def get_all_north_africa_tariffs():
    """
    Get tariff profiles for all 7 North African countries in a single call.

    Also includes the Morocco reference tariff bands for comparison.
    """
    try:
        ts = _tariff_structures()
        return {
            "region": "North Africa",
            "morocco_reference_bands": ts["morocco_bands"],
            "country_profiles": ts["get_all"](),
        }
    except Exception as exc:
        logger.error(f"get_all_north_africa_tariffs failed: {exc}")
        raise HTTPException(status_code=500, detail=str(exc))


# ── /api/investment/north-africa/zones ───────────────────────────────────────

@investment_router.get("/north-africa/zones")
async def get_all_investment_zones(
    type_filter: Optional[str] = Query(
        None,
        description="Filter by zone type (e.g. industrial_free_zone, financial_center)",
    ),
    port_connected: Optional[bool] = Query(
        None,
        description="Filter: only port-connected zones",
    ),
):
    """
    Get all special economic zones and investment areas across North Africa.

    Returns zones for all 7 countries with location, incentives,
    target sectors, employment, and port connectivity data.
    """
    try:
        iz = _investment_zones()
        all_zones = iz["get_all"]()
        summary = iz["summary"]()

        # Apply filters
        if type_filter or port_connected is not None:
            filtered: Dict[str, List] = {}
            for country, zones in all_zones.items():
                country_zones = []
                for z in zones:
                    if type_filter and z.get("type") != type_filter:
                        continue
                    if port_connected is not None and z.get("port_connected") != port_connected:
                        continue
                    country_zones.append(z)
                if country_zones:
                    filtered[country] = country_zones
            all_zones = filtered

        return {
            "summary": summary,
            "zones_by_country": all_zones,
        }
    except Exception as exc:
        logger.error(f"get_all_investment_zones failed: {exc}")
        raise HTTPException(status_code=500, detail=str(exc))


@investment_router.get("/north-africa/zones/{country_code}")
async def get_country_investment_zones(country_code: str):
    """
    Get special economic zones for a specific North African country.

    Path parameter:
    - country_code: ISO-3 code (MAR, EGY, TUN, DZA, LBY, SDN, MRT)
    """
    try:
        iz = _investment_zones()
        zones = iz["get_zones"](country_code.upper())

        c = _constants()
        meta = c["metadata"].get(country_code.upper(), {})

        return {
            "country": country_code.upper(),
            "country_name": meta.get("name_en", country_code),
            "investment_law": c["investment_laws"].get(country_code.upper(), ""),
            "investment_agency": meta.get("investment_agency", ""),
            "investment_url": meta.get("investment_url", ""),
            "total_zones": len(zones),
            "zones": zones,
        }
    except Exception as exc:
        logger.error(f"get_country_investment_zones({country_code}) failed: {exc}")
        raise HTTPException(status_code=500, detail=str(exc))


# ── /api/trade/north-africa/agreements ───────────────────────────────────────

@trade_router.get("/north-africa/agreements")
async def get_trade_agreements(
    country_code: Optional[str] = Query(
        None,
        description="Filter by country ISO-3 code (MAR, EGY, TUN, DZA, LBY, SDN, MRT)",
    ),
):
    """
    Get trade agreement data for North African countries.

    Returns bilateral and multilateral agreement details including:
    - Agreement name and partners
    - Applicable tariff preferences
    - Market access conditions
    - Country-specific notes

    Optional filter:
    - country_code: Return agreements for a single country
    """
    try:
        c = _constants()
        ts = _tariff_structures()

        agreements_db = {
            "MAR": [
                {
                    "name": "EU-Morocco Association Agreement",
                    "type": "bilateral",
                    "signed": 1996,
                    "in_force": 2000,
                    "coverage": "industrial goods (full), agricultural (partial)",
                    "industrial_rate": "0%",
                    "status": "active",
                    "notes": "Full industrial liberalisation since 2012; ALECA negotiations ongoing",
                },
                {
                    "name": "US-Morocco Free Trade Agreement",
                    "type": "bilateral",
                    "signed": 2004,
                    "in_force": 2006,
                    "coverage": "most goods",
                    "industrial_rate": "0%",
                    "status": "active",
                },
                {
                    "name": "EFTA-Morocco Free Trade Agreement",
                    "type": "multilateral",
                    "in_force": 1999,
                    "coverage": "industrial goods",
                    "industrial_rate": "0%",
                    "status": "active",
                },
                {
                    "name": "Agadir Agreement",
                    "type": "multilateral",
                    "members": ["MAR", "TUN", "EGY", "JOR"],
                    "in_force": 2007,
                    "industrial_rate": "0%",
                    "status": "active",
                },
                {
                    "name": "Greater Arab Free Trade Area (GAFTA)",
                    "type": "multilateral",
                    "members": "Arab League countries",
                    "in_force": 2005,
                    "rate": "0%",
                    "status": "active",
                },
                {
                    "name": "African Continental Free Trade Area (AfCFTA)",
                    "type": "multilateral",
                    "in_force": 2021,
                    "status": "active",
                    "notes": "Progressive liberalisation for African goods",
                },
            ],
            "EGY": [
                {
                    "name": "COMESA Free Trade Agreement",
                    "type": "multilateral",
                    "members": "21 COMESA member states",
                    "in_force": 2000,
                    "rate": "0% for qualifying goods",
                    "status": "active",
                },
                {
                    "name": "QIZ Agreement (Egypt-US-Israel)",
                    "type": "trilateral",
                    "in_force": 2005,
                    "coverage": "qualifying manufactured goods",
                    "us_rate": "0% (duty-free)",
                    "conditions": "Min 35% value-added in QIZ; 10.5% Israeli content",
                    "status": "active",
                },
                {
                    "name": "EU-Egypt Partnership Agreement",
                    "type": "bilateral",
                    "in_force": 2004,
                    "coverage": "industrial goods",
                    "status": "active",
                },
                {
                    "name": "Agadir Agreement",
                    "type": "multilateral",
                    "members": ["MAR", "TUN", "EGY", "JOR"],
                    "in_force": 2007,
                    "rate": "0%",
                    "status": "active",
                },
                {
                    "name": "GAFTA",
                    "type": "multilateral",
                    "rate": "0%",
                    "status": "active",
                },
                {
                    "name": "AfCFTA",
                    "type": "multilateral",
                    "status": "active",
                },
            ],
            "TUN": [
                {
                    "name": "EU-Tunisia Association Agreement",
                    "type": "bilateral",
                    "in_force": 1998,
                    "coverage": "industrial goods (full)",
                    "rate": "0% for industrial goods",
                    "status": "active",
                    "notes": "DCFTA/ALECA negotiations ongoing for agriculture/services",
                },
                {
                    "name": "EFTA-Tunisia Free Trade Agreement",
                    "type": "multilateral",
                    "in_force": 2005,
                    "coverage": "industrial goods",
                    "status": "active",
                },
                {
                    "name": "Agadir Agreement",
                    "type": "multilateral",
                    "members": ["MAR", "TUN", "EGY", "JOR"],
                    "in_force": 2007,
                    "rate": "0%",
                    "status": "active",
                },
                {
                    "name": "GAFTA",
                    "type": "multilateral",
                    "rate": "0%",
                    "status": "active",
                },
                {
                    "name": "COMESA",
                    "type": "multilateral",
                    "status": "active",
                    "notes": "Partial COMESA engagement",
                },
                {
                    "name": "AfCFTA",
                    "type": "multilateral",
                    "status": "active",
                },
            ],
            "DZA": [
                {
                    "name": "EU-Algeria Association Agreement",
                    "type": "bilateral",
                    "in_force": 2005,
                    "coverage": "industrial goods (progressive)",
                    "status": "active",
                    "notes": "Industrial goods liberalised by 2020",
                },
                {
                    "name": "GAFTA",
                    "type": "multilateral",
                    "rate": "0%",
                    "status": "active",
                },
                {
                    "name": "AfCFTA",
                    "type": "multilateral",
                    "status": "active",
                },
            ],
            "LBY": [
                {
                    "name": "GAFTA",
                    "type": "multilateral",
                    "rate": "0%",
                    "status": "active",
                    "notes": "Enforcement limited by political situation",
                },
                {
                    "name": "EU-Libya Framework Agreement (planned)",
                    "type": "bilateral",
                    "status": "pending",
                    "notes": "Awaiting political stabilisation",
                },
                {
                    "name": "AfCFTA",
                    "type": "multilateral",
                    "status": "pending_ratification",
                },
            ],
            "SDN": [
                {
                    "name": "COMESA Free Trade Agreement",
                    "type": "multilateral",
                    "members": "21 COMESA member states",
                    "in_force": 2000,
                    "rate": "0% for qualifying goods",
                    "status": "active",
                },
                {
                    "name": "GAFTA",
                    "type": "multilateral",
                    "rate": "0%",
                    "status": "active",
                },
                {
                    "name": "AfCFTA",
                    "type": "multilateral",
                    "status": "active",
                },
            ],
            "MRT": [
                {
                    "name": "GAFTA",
                    "type": "multilateral",
                    "rate": "0%",
                    "status": "active",
                },
                {
                    "name": "ECOWAS (Observer)",
                    "type": "multilateral",
                    "status": "observer",
                    "notes": "Observer status; partial trade benefits",
                },
                {
                    "name": "AfCFTA",
                    "type": "multilateral",
                    "status": "active",
                },
                {
                    "name": "EU Fisheries Agreement",
                    "type": "bilateral",
                    "coverage": "Atlantic fisheries access",
                    "status": "active",
                },
            ],
        }

        if country_code:
            cc = country_code.upper()
            if cc not in agreements_db:
                raise HTTPException(
                    status_code=404,
                    detail=f"Country '{cc}' not found. Valid: MAR, EGY, TUN, DZA, LBY, SDN, MRT",
                )
            return {
                "country": cc,
                "country_name": c["metadata"].get(cc, {}).get("name_en", cc),
                "agreements": agreements_db[cc],
            }

        return {
            "region": "North Africa",
            "agreements_by_country": agreements_db,
            "key_multilateral": [
                {
                    "name": "AfCFTA",
                    "description": "African Continental Free Trade Area",
                    "members_north_africa": ["MAR", "EGY", "TUN", "DZA", "SDN", "MRT"],
                    "pending": ["LBY"],
                },
                {
                    "name": "GAFTA",
                    "description": "Greater Arab Free Trade Area",
                    "members_north_africa": ["MAR", "EGY", "TUN", "DZA", "LBY", "SDN", "MRT"],
                },
                {
                    "name": "Agadir Agreement",
                    "description": "Euro-Mediterranean Arab Free Trade Agreement",
                    "members": ["MAR", "TUN", "EGY", "JOR"],
                },
                {
                    "name": "COMESA",
                    "description": "Common Market for Eastern and Southern Africa",
                    "members_north_africa": ["EGY", "TUN", "SDN"],
                },
            ],
        }
    except HTTPException:
        raise
    except Exception as exc:
        logger.error(f"get_trade_agreements failed: {exc}")
        raise HTTPException(status_code=500, detail=str(exc))


# ── Mount sub-routers onto the main router ────────────────────────────────────

router.include_router(regions_router)
router.include_router(tariffs_router)
router.include_router(investment_router)
router.include_router(trade_router)
