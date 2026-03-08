"""
Regional configuration for the African tariff intelligence system.

Covers:
- North Africa: DZA (Algeria), MAR (Morocco), EGY (Egypt), TUN (Tunisia)
- CEMAC: CMR (Cameroon), CAF (Central African Republic), TCD (Chad),
          COG (Republic of the Congo), GNQ (Equatorial Guinea), GAB (Gabon)
"""

NORTH_AFRICA_COUNTRIES = ["DZA", "MAR", "EGY", "TUN"]

CEMAC_COUNTRIES = ["CMR", "CAF", "TCD", "COG", "GNQ", "GAB"]

REGIONAL_CONFIG = {
    "region_name": "North Africa",
    "region_name_fr": "Afrique du Nord",
    "countries": NORTH_AFRICA_COUNTRIES,
    "regional_gdp_coverage_pct": 80,  # ~80% of African North African region GDP
    "common_agreements": [
        "AFCFTA",
        "Arab Free Trade Area (GAFTA)",
        "Agadir Agreement",
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
}

# Country-specific VAT rates for quick reference
NORTH_AFRICA_VAT_RATES = {
    "DZA": 19.0,
    "MAR": 20.0,
    "EGY": 14.0,
    "TUN": 19.0,
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
