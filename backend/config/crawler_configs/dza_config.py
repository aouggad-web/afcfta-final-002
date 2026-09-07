"""
Algeria (DZA) crawler configuration.

Source: conformepro.dz (data from douane.gov.dz)
Tax structure: DD, TVA, PRCT, TCS, DAPS
"""

DZA_CONFIG = {
    "country_iso3": "DZA",
    "country_name": "Algeria",
    "country_name_fr": "Algérie",
    "country_name_ar": "الجزائر",
    "primary_source": "https://conformepro.dz/resources/tarif-douanier",
    "official_source": "https://www.douane.gov.dz",
    "nomenclature": "SH (Système Harmonisé)",
    "hs_level": "HS10",
    "tax_structure": {
        "DD": {
            "name": "Droit de douane",
            "name_en": "Customs Duty",
            "base": "CIF",
            "rates": [0, 5, 15, 30],
        },
        "TVA": {
            "name": "Taxe sur la Valeur Ajoutée",
            "name_en": "Value Added Tax",
            "standard_rate": 19.0,
            "reduced_rate": 9.0,
        },
        "PRCT": {
            "name": "Provision pour Rentes des Travailleurs",
            "name_en": "Workers Annuity Provision",
            "rate": 2.0,
        },
        "TCS": {
            "name": "Taxe de Consommation Spécifique",
            "name_en": "Specific Consumption Tax",
            "rate": None,  # varies by product
        },
        "DAPS": {
            "name": "Droit Additionnel Provisoire de Sauvegarde",
            "name_en": "Provisional Additional Safeguard Duty",
            "rate": None,  # varies by product
        },
    },
    "preferential_agreements": [
        "AFCFTA",
        "Arab Free Trade Area (GAFTA)",
        "Pan-Arab Free Trade Area",
        "Arab Maghreb Union (UMA)",
    ],
    "crawl_settings": {
        "rate_limit_delay": 1.5,
        "max_retries": 3,
        "timeout": 30,
        "batch_size": 50,
        "async_enabled": True,
        "performance_boost": "10x-20x",
    },
    "data_paths": {
        "raw": "data/raw/DZA",
        "parsed": "data/parsed/DZA",
        "published": "data/published/DZA",
    },
}
