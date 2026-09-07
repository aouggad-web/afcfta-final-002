"""
Tunisia (TUN) crawler configuration.

Sources:
  Primary: douane.finances.tn (tarifweb2025)
  Secondary: customs.gov.tn
Tax structure: DD, TVA (19%), FODEC, TCL, Consumption taxes
"""

TUN_CONFIG = {
    "country_iso3": "TUN",
    "country_name": "Tunisia",
    "country_name_fr": "Tunisie",
    "country_name_ar": "تونس",
    "primary_source": "https://www.douane.gov.tn/tarifwebnew/getresultat.php",
    "official_source": "https://www.douane.finances.tn",
    "secondary_source": "https://www.customs.gov.tn",
    "nomenclature": "Nomenclature Douanière de Produits (NDP)",
    "hs_level": "HS11",
    "tax_structure": {
        "DD": {
            "name": "Droit de Douane",
            "name_en": "Customs Duty",
            "base": "CIF",
            "rates": [0, 10, 20, 30, 36],
        },
        "TVA": {
            "name": "Taxe sur la Valeur Ajoutée",
            "name_en": "Value Added Tax",
            "standard_rate": 19.0,
            "reduced_rates": [7.0, 13.0],
        },
        "FODEC": {
            "name": "Fonds de Développement de la Compétitivité",
            "name_en": "Competitiveness Development Fund",
            "rate": 1.0,
        },
        "TCL": {
            "name": "Taxe au profit des Collectivités Locales",
            "name_en": "Local Authorities Tax",
            "rate": None,  # varies by product
        },
        "DC": {
            "name": "Droit de Consommation",
            "name_en": "Consumption Tax",
            "rate": None,  # varies by product
        },
    },
    "preferential_agreements": [
        "EU Association Agreement (most advanced in region)",
        "DCFTA (Deep and Comprehensive Free Trade Area - preparation)",
        "Arab Free Trade Area (GAFTA)",
        "Agadir Agreement",
        "AFCFTA",
        "Turkey Free Trade Agreement",
        "EFTA Agreement",
    ],
    "special_regimes": [
        "Offshore regime (export-oriented enterprises)",
        "Economic development zones",
        "Textile industry incentives",
        "Automotive industry incentives",
    ],
    "eu_integration_level": "Most advanced EU association agreement in region",
    "crawl_settings": {
        "rate_limit_delay": 1.5,
        "max_retries": 3,
        "timeout": 30,
        "batch_size": 50,
        "async_enabled": True,
        "chapters": [f"{i:02d}" for i in range(1, 98) if i != 77],
    },
    "data_paths": {
        "raw": "data/raw/TUN",
        "parsed": "data/parsed/TUN",
        "published": "data/published/TUN",
    },
}
