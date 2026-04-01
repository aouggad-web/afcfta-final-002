"""
Egypt (EGY) crawler configuration.

Sources:
  Primary: customs.gov.eg
  Secondary: egyptariffs.com (based on Egyptian Customs Authority data)
  Reference: goeic.gov.eg (General Organization for Export & Import Control)
Tax structure: CD, VAT (14%), SD, DT, ST
"""

EGY_CONFIG = {
    "country_iso3": "EGY",
    "country_name": "Egypt",
    "country_name_fr": "Égypte",
    "country_name_ar": "مصر",
    "primary_source": "https://www.egyptariffs.com",
    "sitemap_url": "https://www.egyptariffs.com/sitemap.xml",
    "official_source": "https://www.customs.gov.eg",
    "goeic_source": "https://www.goeic.gov.eg",
    "nomenclature": "Egyptian Customs Tariff (HS2022)",
    "hs_level": "HS10",
    "legal_reference": "Presidential Decree 419/2018, updated through 218/2025",
    "tax_structure": {
        "CD": {
            "name": "Customs Duty (ضريبة الوارد)",
            "name_en": "Import Duty",
            "base": "CIF",
            "rate_range": [0, 60],
            "note": "Up to 3000% for alcohol",
        },
        "VAT": {
            "name": "Value Added Tax (ضريبة القيمة المضافة)",
            "name_en": "Value Added Tax",
            "standard_rate": 14.0,
        },
        "SD": {
            "name": "Sales Duty",
            "name_en": "Sales Duty",
            "rate": None,  # varies by product
        },
        "DT": {
            "name": "Development Taxes",
            "name_en": "Development Taxes",
            "rate": None,  # varies by product
        },
        "ST": {
            "name": "Special Taxes",
            "name_en": "Special Taxes",
            "rate": None,  # varies by product
        },
    },
    "preferential_agreements": [
        "AFCFTA",
        "COMESA",
        "Arab Free Trade Area (GAFTA)",
        "EFTA Agreement",
        "Turkey Free Trade Agreement",
        "EU Partnership Agreement",
        "QIZ (Qualified Industrial Zones - US market access)",
    ],
    "special_zones": [
        "Suez Canal Economic Zone (SCZONE)",
        "QIZ Zones (US-Egypt-Israel qualifying industrial zones)",
        "New Administrative Capital Free Zone",
        "Port Said Special Economic Zone",
    ],
    "investment_incentives": [
        "Investment Law 72/2017",
        "COMESA preferential rates",
        "QIZ special US market access rates",
    ],
    "crawl_settings": {
        "rate_limit_delay": 1.5,
        "max_retries": 3,
        "timeout": 15,
        "batch_size": 50,
        "async_enabled": False,  # uses sync requests
        "expected_positions": 8816,
    },
    "data_paths": {
        "raw": "data/raw/EGY",
        "parsed": "data/parsed/EGY",
        "published": "data/published/EGY",
    },
}
