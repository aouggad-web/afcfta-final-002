"""
Regional configuration for the North African tariff intelligence system.

Covers: DZA (Algeria), MAR (Morocco), EGY (Egypt), TUN (Tunisia)
"""

NORTH_AFRICA_COUNTRIES = ["DZA", "MAR", "EGY", "TUN"]

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
