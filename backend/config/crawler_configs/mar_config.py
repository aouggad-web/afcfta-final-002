"""
Morocco (MAR) crawler configuration.

Sources:
  Primary: portail.adii.gov.ma (ADIL Portal)
  Secondary: douane.gov.ma
Tax structure: DD, TVA (20%), PI (Parafiscal Import), TIC, TPCE
"""

MAR_CONFIG = {
    "country_iso3": "MAR",
    "country_name": "Morocco",
    "country_name_fr": "Maroc",
    "country_name_ar": "المغرب",
    "primary_source": "https://www.douane.gov.ma/adil/info_0.asp",
    "secondary_source": "https://portail.adii.gov.ma",
    "official_source": "https://www.douane.gov.ma",
    "nomenclature": "Nomenclature Tarifaire et Statistique (NTS)",
    "hs_level": "HS10",
    "tax_structure": {
        "DD": {
            "name": "Droit d'Importation",
            "name_en": "Import Duty",
            "base": "CIF",
            "rates": [2.5, 10, 17.5, 25, 32.5, 40],
        },
        "TVA": {
            "name": "Taxe sur la Valeur Ajoutée",
            "name_en": "Value Added Tax",
            "standard_rate": 20.0,
            "reduced_rates": [7.0, 10.0, 14.0],
        },
        "PI": {
            "name": "Taxe Parafiscale à l'Importation",
            "name_en": "Parafiscal Import Tax",
            "rate": None,  # varies by product
        },
        "TIC": {
            "name": "Taxe Intérieure de Consommation",
            "name_en": "Domestic Consumption Tax",
            "rate": None,  # varies by product
        },
        "TPCE": {
            "name": "Taxe pour la Protection de l'Environnement",
            "name_en": "Environmental Protection Tax",
            "rate": None,  # varies by product
        },
    },
    "preferential_agreements": [
        "EU Association Agreement",
        "Agadir Agreement (Arab countries)",
        "EFTA Agreement",
        "US Free Trade Agreement",
        "Turkey Free Trade Agreement",
        "AFCFTA",
        "Arab Free Trade Area (GAFTA)",
    ],
    "special_zones": [
        "Tanger-Med Free Zone",
        "Casablanca Finance City",
        "Dakhla Offshore City",
    ],
    "agricultural_seasonal_variations": True,
    "crawl_settings": {
        "rate_limit_delay": 2.0,
        "max_retries": 3,
        "timeout": 60,
        "batch_size": 10,
        "async_enabled": True,
        "chapters": [f"{i:02d}" for i in range(1, 98) if i != 77],
    },
    "data_paths": {
        "raw": "data/raw/MAR",
        "parsed": "data/parsed/MAR",
        "published": "data/published/MAR",
    },
}
