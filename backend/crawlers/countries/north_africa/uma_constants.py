"""
UMA/AMU North Africa Regional Constants.

Arab Maghreb Union (UMA/AMU) + Extended North African countries:
  MAR, DZA, TUN, LBY, MRT  (core UMA members)
  EGY, SDN                  (extended North Africa / AfCFTA coverage)

Language codes:
  ar  = Arabic (official across all countries)
  fr  = French (secondary: MAR, DZA, TUN, MRT)
  en  = English (secondary: EGY, SDN, LBY)
  tzm = Tamazight/Berber (cultural recognition: MAR, DZA)
"""

from typing import Dict, List, Any

# ── Core UMA member states ──────────────────────────────────────────────────
UMA_CORE_MEMBERS: List[str] = ["MAR", "DZA", "TUN", "LBY", "MRT"]

# ── Extended North Africa (AfCFTA platform full coverage) ───────────────────
UMA_EXTENDED_MEMBERS: List[str] = ["EGY", "SDN"]

# ── Full North Africa roster ────────────────────────────────────────────────
NORTH_AFRICA_EXTENDED: List[str] = UMA_CORE_MEMBERS + UMA_EXTENDED_MEMBERS

# ── Alias used by the rest of the platform ─────────────────────────────────
UMA_COUNTRIES: List[str] = NORTH_AFRICA_EXTENDED

# ── Regional trade blocs each country belongs to ───────────────────────────
UMA_TRADE_BLOCS: Dict[str, List[str]] = {
    "MAR": ["UMA", "GAFTA", "Agadir", "EU-Association", "US-FTA", "EFTA", "AfCFTA"],
    "DZA": ["UMA", "GAFTA", "EU-Association", "AfCFTA"],
    "TUN": ["UMA", "GAFTA", "Agadir", "EU-Association", "COMESA", "AfCFTA"],
    "LBY": ["UMA", "GAFTA", "AfCFTA"],
    "MRT": ["UMA", "GAFTA", "ECOWAS-Observer", "AfCFTA"],
    "EGY": ["COMESA", "GAFTA", "Agadir", "QIZ-US", "EU-Partnership", "AfCFTA"],
    "SDN": ["COMESA", "GAFTA", "AfCFTA"],
}

# ── Country metadata ────────────────────────────────────────────────────────
COUNTRY_METADATA: Dict[str, Dict[str, Any]] = {
    "MAR": {
        "iso3": "MAR",
        "iso2": "MA",
        "name_en": "Morocco",
        "name_fr": "Maroc",
        "name_ar": "المغرب",
        "capital": "Rabat",
        "currency": "MAD",
        "currency_name": "Moroccan Dirham",
        "population_m": 37,
        "gdp_bn_usd": 134,
        "languages": ["ar", "fr", "tzm"],
        "customs_authority": "Administration des Douanes et Impôts Indirects (ADII)",
        "customs_url": "https://www.douane.gov.ma",
        "trade_portal_url": "https://portail.adii.gov.ma",
        "investment_agency": "Investissement au Maroc / Invest In Morocco",
        "investment_url": "https://www.invest.gov.ma",
        "wto_member": True,
        "afcfta_ratified": True,
        "uma_member": True,
        "data_reliability": "high",
    },
    "EGY": {
        "iso3": "EGY",
        "iso2": "EG",
        "name_en": "Egypt",
        "name_fr": "Égypte",
        "name_ar": "مصر",
        "capital": "Cairo",
        "currency": "EGP",
        "currency_name": "Egyptian Pound",
        "population_m": 105,
        "gdp_bn_usd": 400,
        "languages": ["ar", "en"],
        "customs_authority": "Egyptian Customs Authority (ECA)",
        "customs_url": "https://www.gafinet.org",
        "trade_portal_url": "https://www.mti.gov.eg",
        "investment_agency": "General Authority for Investment and Free Zones (GAFI)",
        "investment_url": "https://www.gafi.gov.eg",
        "wto_member": True,
        "afcfta_ratified": True,
        "uma_member": False,
        "data_reliability": "high",
    },
    "TUN": {
        "iso3": "TUN",
        "iso2": "TN",
        "name_en": "Tunisia",
        "name_fr": "Tunisie",
        "name_ar": "تونس",
        "capital": "Tunis",
        "currency": "TND",
        "currency_name": "Tunisian Dinar",
        "population_m": 12,
        "gdp_bn_usd": 46,
        "languages": ["ar", "fr"],
        "customs_authority": "Direction Générale des Douanes",
        "customs_url": "https://www.douane.gov.tn",
        "trade_portal_url": "https://www.tradenet.tn",
        "investment_agency": "Foreign Investment Promotion Agency (FIPA)",
        "investment_url": "https://www.investintunisia.tn",
        "wto_member": True,
        "afcfta_ratified": True,
        "uma_member": True,
        "data_reliability": "high",
    },
    "DZA": {
        "iso3": "DZA",
        "iso2": "DZ",
        "name_en": "Algeria",
        "name_fr": "Algérie",
        "name_ar": "الجزائر",
        "capital": "Algiers",
        "currency": "DZD",
        "currency_name": "Algerian Dinar",
        "population_m": 45,
        "gdp_bn_usd": 191,
        "languages": ["ar", "fr", "tzm"],
        "customs_authority": "Direction Générale des Douanes (DGD)",
        "customs_url": "https://www.douane.dz",
        "trade_portal_url": "https://www.andi.dz",
        "investment_agency": "Agence Nationale de Développement de l'Investissement (ANDI)",
        "investment_url": "https://www.andi.dz",
        "wto_member": False,
        "afcfta_ratified": True,
        "uma_member": True,
        "data_reliability": "medium",
    },
    "LBY": {
        "iso3": "LBY",
        "iso2": "LY",
        "name_en": "Libya",
        "name_fr": "Libye",
        "name_ar": "ليبيا",
        "capital": "Tripoli",
        "currency": "LYD",
        "currency_name": "Libyan Dinar",
        "population_m": 7,
        "gdp_bn_usd": 35,
        "languages": ["ar", "en"],
        "customs_authority": "Libyan Customs Authority",
        "customs_url": "https://customs.gov.ly",
        "trade_portal_url": "https://customs.gov.ly",
        "investment_agency": "Libya Investment Authority",
        "investment_url": "https://lia.ly",
        "wto_member": False,
        "afcfta_ratified": False,
        "uma_member": True,
        "data_reliability": "low",
    },
    "SDN": {
        "iso3": "SDN",
        "iso2": "SD",
        "name_en": "Sudan",
        "name_fr": "Soudan",
        "name_ar": "السودان",
        "capital": "Khartoum",
        "currency": "SDG",
        "currency_name": "Sudanese Pound",
        "population_m": 46,
        "gdp_bn_usd": 34,
        "languages": ["ar", "en"],
        "customs_authority": "Sudan Customs Administration",
        "customs_url": "https://www.customs.gov.sd",
        "trade_portal_url": "https://www.customs.gov.sd",
        "investment_agency": "Investment Encouragement Act Authority",
        "investment_url": "https://www.mof.gov.sd",
        "wto_member": True,
        "afcfta_ratified": True,
        "uma_member": False,
        "data_reliability": "low",
    },
    "MRT": {
        "iso3": "MRT",
        "iso2": "MR",
        "name_en": "Mauritania",
        "name_fr": "Mauritanie",
        "name_ar": "موريتانيا",
        "capital": "Nouakchott",
        "currency": "MRU",
        "currency_name": "Mauritanian Ouguiya",
        "population_m": 5,
        "gdp_bn_usd": 9,
        "languages": ["ar", "fr"],
        "customs_authority": "Direction Générale des Douanes",
        "customs_url": "https://www.douane.mr",
        "trade_portal_url": "https://www.douane.mr",
        "investment_agency": "Agence de Promotion des Investissements en Mauritanie (APIM)",
        "investment_url": "https://www.mauritania-invest.mr",
        "wto_member": True,
        "afcfta_ratified": True,
        "uma_member": True,
        "data_reliability": "low",
    },
}

# ── VAT rates by country ────────────────────────────────────────────────────
UMA_VAT_RATES: Dict[str, float] = {
    "MAR": 20.0,
    "EGY": 14.0,
    "TUN": 19.0,
    "DZA": 19.0,
    "LBY": 0.0,   # no VAT; sales tax ~4%
    "SDN": 17.0,
    "MRT": 16.0,
}

# ── Corporate income tax rates ──────────────────────────────────────────────
UMA_CORPORATE_TAX_RATES: Dict[str, float] = {
    "MAR": 26.0,
    "EGY": 22.5,
    "TUN": 15.0,   # standard; higher rates for banking/insurance
    "DZA": 26.0,
    "LBY": 20.0,
    "SDN": 35.0,
    "MRT": 25.0,
}

# ── Key investment laws ─────────────────────────────────────────────────────
UMA_INVESTMENT_LAWS: Dict[str, str] = {
    "MAR": "Investment Charter Law 03-22 (2022)",
    "EGY": "Investment Law 72/2017",
    "TUN": "Investment Law 2016-71",
    "DZA": "Investment Law 09-22 (2022)",
    "LBY": "Foreign Investment Law 9/2010 (partial implementation)",
    "SDN": "Investment Encouragement Act (2013, amended 2021)",
    "MRT": "Investment Code 2012 (amended 2017)",
}

# ── Data source URLs ────────────────────────────────────────────────────────
UMA_DATA_SOURCES: Dict[str, Dict[str, str]] = {
    "MAR": {
        "tariffs": "https://www.douane.gov.ma",
        "trade": "https://www.commerce.gov.ma",
        "investment": "https://www.invest.gov.ma",
    },
    "EGY": {
        "tariffs": "https://www.gafinet.org",
        "trade": "https://www.mti.gov.eg",
        "investment": "https://www.gafi.gov.eg",
    },
    "TUN": {
        "tariffs": "https://www.douane.gov.tn",
        "trade": "https://www.tradenet.tn",
        "investment": "https://www.investintunisia.tn",
    },
    "DZA": {
        "tariffs": "https://www.douane.dz",
        "trade": "https://www.andi.dz",
        "investment": "https://www.andi.dz",
    },
    "LBY": {
        "tariffs": "https://customs.gov.ly",
        "trade": "https://customs.gov.ly",
        "investment": "https://lia.ly",
    },
    "SDN": {
        "tariffs": "https://www.customs.gov.sd",
        "trade": "https://www.customs.gov.sd",
        "investment": "https://www.mof.gov.sd",
    },
    "MRT": {
        "tariffs": "https://www.douane.mr",
        "trade": "https://www.douane.mr",
        "investment": "https://www.mauritania-invest.mr",
    },
}

# ── Sector strengths by country ─────────────────────────────────────────────
UMA_SECTOR_STRENGTHS: Dict[str, List[str]] = {
    "MAR": ["automotive", "aerospace", "phosphates", "textiles", "renewable_energy", "tourism"],
    "EGY": ["textiles", "food_processing", "ict", "petrochemicals", "construction", "tourism"],
    "TUN": ["textiles", "automotive_components", "ict", "olive_oil", "tourism", "aerospace"],
    "DZA": ["hydrocarbons", "agriculture", "construction_materials", "steel", "renewable_energy"],
    "LBY": ["oil_gas", "infrastructure", "construction", "fisheries"],
    "SDN": ["agriculture", "gum_arabic", "livestock", "cotton", "gold_mining"],
    "MRT": ["iron_ore", "gold", "copper", "fisheries", "renewable_energy"],
}

# ── Multi-language country names ────────────────────────────────────────────
MULTILANG_NAMES: Dict[str, Dict[str, str]] = {
    "MAR": {"en": "Morocco", "fr": "Maroc", "ar": "المغرب", "tzm": "ⵍⵎⵖⵔⵉⴱ"},
    "EGY": {"en": "Egypt", "fr": "Égypte", "ar": "مصر"},
    "TUN": {"en": "Tunisia", "fr": "Tunisie", "ar": "تونس"},
    "DZA": {"en": "Algeria", "fr": "Algérie", "ar": "الجزائر", "tzm": "ⵍⴷⵣⴰⵢⴻⵔ"},
    "LBY": {"en": "Libya", "fr": "Libye", "ar": "ليبيا"},
    "SDN": {"en": "Sudan", "fr": "Soudan", "ar": "السودان"},
    "MRT": {"en": "Mauritania", "fr": "Mauritanie", "ar": "موريتانيا"},
}
