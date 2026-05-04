"""
Regional configuration for the African tariff intelligence system.

Covers all 7 North African (UMA/AMU + extended) countries:
  DZA (Algeria), MAR (Morocco), EGY (Egypt), TUN (Tunisia),
  LBY (Libya), SDN (Sudan), MRT (Mauritania)
Covers:
- North Africa: DZA (Algeria), MAR (Morocco), EGY (Egypt), TUN (Tunisia)
- CEMAC: CMR (Cameroon), CAF (Central African Republic), TCD (Chad),
          COG (Republic of the Congo), GNQ (Equatorial Guinea), GAB (Gabon)
"""

# Core 4 countries with high-quality scrapers (existing coverage)
NORTH_AFRICA_COUNTRIES = ["DZA", "MAR", "EGY", "TUN"]

# Full UMA/AMU + extended North Africa roster (7 countries)
UMA_COUNTRIES = ["MAR", "DZA", "TUN", "LBY", "MRT", "EGY", "SDN"]

# Core UMA members only (Arab Maghreb Union)
UMA_CORE_MEMBERS = ["MAR", "DZA", "TUN", "LBY", "MRT"]

# Extended North Africa (full AfCFTA coverage)
NORTH_AFRICA_EXTENDED = UMA_COUNTRIES
CEMAC_COUNTRIES = ["CMR", "CAF", "TCD", "COG", "GNQ", "GAB"]

REGIONAL_CONFIG = {
    "region_name": "North Africa",
    "region_name_fr": "Afrique du Nord",
    "region_name_ar": "أفريقيا الشمالية",
    "uma_name": "Union du Maghreb Arabe (UMA/AMU)",
    "countries": NORTH_AFRICA_COUNTRIES,
    "uma_countries": UMA_COUNTRIES,
    "uma_core_members": UMA_CORE_MEMBERS,
    "regional_gdp_coverage_pct": 95,  # ~95% of North African GDP with all 7 countries
    "common_agreements": [
        "AFCFTA",
        "Arab Free Trade Area (GAFTA)",
        "Agadir Agreement",
        "UMA/AMU Framework",
    ],
    "cross_validation": {
        "enabled": True,
        "tolerance_pct": 5.0,  # acceptable rate difference for same HS code
        "min_coverage_pct": 70.0,  # minimum data completeness per country
    },
    "performance_targets": {
        "crawl_speed_boost": "10x-20x",
        "data_freshness_days": 1,
        "api_response_simple_ms": 500,
        "api_response_regional_ms": 2000,
        "full_region_scrape_s": 30,  # target: < 30s full region scrape
        "uptime_pct": 99.5,
    },
    "data_paths": {
        "raw": "data/raw",
        "parsed": "data/parsed",
        "published": "data/published",
        "regional": "data/regional",
    },
    "orchestrator": {
        "max_concurrency": 4,
        "retry_failed": True,
        "max_retries": 3,
    },
    "multilanguage": {
        "primary": "ar",        # Arabic – official across all countries
        "secondary": ["fr", "en"],
        "tamazight": ["MAR", "DZA"],  # Tamazight cultural recognition
    },
}

# Country-specific VAT rates for quick reference (all 7 countries)
NORTH_AFRICA_VAT_RATES = {
    "DZA": 19.0,
    "MAR": 20.0,
    "EGY": 14.0,
    "TUN": 19.0,
    "LBY": 0.0,    # no VAT; sales tax ~4%
    "SDN": 17.0,
    "MRT": 16.0,
}

# Country data reliability tiers
COUNTRY_DATA_RELIABILITY = {
    "MAR": "high",
    "EGY": "high",
    "TUN": "high",
    "DZA": "medium",
    "LBY": "low",
    "SDN": "low",
    "MRT": "low",
}

# CEMAC regional configuration
CEMAC_CONFIG = {
    "region_name": "CEMAC",
    "region_name_fr": "Afrique Centrale (CEMAC)",
    "countries": CEMAC_COUNTRIES,
    "regional_gdp_coverage_pct": 65,  # ~65% of Central African region GDP
    "common_agreements": [
        "AFCFTA",
        "CEMAC Customs Union",
        "ECCAS",
    ],
    "cross_validation": {
        "enabled": True,
        "tolerance_pct": 5.0,
        "min_coverage_pct": 60.0,
    },
    "performance_targets": {
        "crawl_speed_boost": "10x-20x",
        "data_freshness_days": 1,
        "api_response_simple_ms": 500,
        "api_response_regional_ms": 2000,
        "uptime_pct": 99.5,
    },
    "data_paths": {
        "raw": "data/raw",
        "parsed": "data/parsed",
        "published": "data/published",
        "regional": "data/regional",
    },
    "orchestrator": {
        "max_concurrency": 6,
        "retry_failed": True,
        "max_retries": 3,
    },
}

# CEMAC country VAT rates
# CEMAC uses a harmonized external tariff (TEC) with a standard VAT of 19.25%
CEMAC_VAT_RATES = {
    "CMR": 19.25,   # Cameroon
    "CAF": 19.0,    # Central African Republic
    "TCD": 18.0,    # Chad
    "COG": 18.0,    # Republic of the Congo
    "GNQ": 15.0,    # Equatorial Guinea
    "GAB": 18.0,    # Gabon
}

# Country-specific preferential agreements for cross-validation
COMMON_HS_SECTIONS = [
    "01",  # Live animals
    "10",  # Cereals
    "27",  # Mineral fuels
    "39",  # Plastics
    "72",  # Iron and steel
    "84",  # Machinery
    "87",  # Vehicles
]
