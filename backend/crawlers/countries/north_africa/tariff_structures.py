"""
North Africa (UMA/AMU) Country-Specific Tariff Structures.

Morocco serves as the reference country (most reliable data).
Other countries are derived using Morocco base tariffs with
country-specific adjustments to reflect actual trade policy.

Tariff band sources:
  MAR: ADII (Agence des Douanes et Impôts Indirects) – verified
  EGY: Egyptian Customs Authority / WTO schedule
  TUN: Direction Générale des Douanes de Tunisie / EU DCFTA schedule
  DZA: Direction Générale des Douanes d'Algérie
  LBY: Libyan Customs Authority (pre-conflict 2010 schedule, partially active)
  SDN: Sudan Customs Administration / COMESA schedule
  MRT: Direction Générale des Douanes de Mauritanie
"""

from typing import Dict, Any, List, Optional

# ── Morocco reference tariff bands ─────────────────────────────────────────
MOROCCO_TARIFFS: Dict[str, float] = {
    "raw_materials": 2.5,       # Industrial inputs (Chapter 25, 26, 28 …)
    "intermediate_goods": 10.0,  # Semi-finished products (Chapter 39, 72 …)
    "final_goods": 25.0,         # Consumer products (Chapter 61, 62, 64 …)
    "agricultural": 40.0,        # Food products (Chapter 01-24) – protection
    "luxury_goods": 45.0,        # High-value items (Chapter 71, 97 …)
}

# ── Country-specific tariff profiles ───────────────────────────────────────
# Each entry provides the four standard HS-band rates plus additional taxes.
# Rates are indicative averages; actual rates are HS-code specific.

_TARIFF_PROFILES: Dict[str, Dict[str, Any]] = {
    "MAR": {
        "country": "MAR",
        "country_name": "Morocco",
        "currency": "MAD",
        "nomenclature": "Nomenclature Tarifaire et Statistique (NTS) HS10",
        "trade_bloc": "UMA + EU-Association + US-FTA",
        "bands": {
            "raw_materials": 2.5,
            "intermediate_goods": 10.0,
            "final_goods": 25.0,
            "agricultural": 40.0,
            "luxury_goods": 45.0,
        },
        "vat": {
            "standard": 20.0,
            "reduced": [7.0, 10.0, 14.0],
        },
        "additional_taxes": {
            "PI": {"name": "Taxe Parafiscale à l'Importation", "rate_range": "0.25–1.0%"},
            "TIC": {"name": "Taxe Intérieure de Consommation", "applies_to": "fuel, tobacco, beverages"},
            "TPCE": {"name": "Taxe Protection Environnement", "applies_to": "packaging"},
        },
        "preferential_zero_rate": ["EU goods under AA", "US goods under FTA", "EFTA goods"],
        "special_regimes": [
            "Admission temporaire",
            "Entrepôt sous douane",
            "Zone franche (Tanger-Med)",
        ],
        "notes": [
            "EU Association Agreement: progressive tariff elimination (full 2035)",
            "US FTA 2006: most industrial goods 0%",
            "Agricultural goods subject to seasonal import calendars",
        ],
        "data_quality": "high",
        "source": "https://www.douane.gov.ma",
        "last_reviewed": "2024",
    },
    "EGY": {
        "country": "EGY",
        "country_name": "Egypt",
        "currency": "EGP",
        "nomenclature": "Egyptian Customs Tariff HS10",
        "trade_bloc": "COMESA + GAFTA + QIZ + EU-Partnership",
        "bands": {
            "raw_materials": 2.0,
            "intermediate_goods": 12.0,
            "final_goods": 30.0,
            "agricultural": 20.0,   # lower than MAR – food security policy
            "luxury_goods": 40.0,
        },
        "vat": {
            "standard": 14.0,
            "reduced": [5.0],
        },
        "additional_taxes": {
            "Sales_Tax": {"name": "Sales Tax (replaced by VAT 2016)", "rate": 14.0},
            "Tableware_Tax": {"name": "Tableware & Luxury Excise", "applies_to": "luxury goods"},
            "Development_Tax": {"name": "Development Duty", "rate_range": "1–2%"},
        },
        "preferential_zero_rate": [
            "COMESA goods (progressive)",
            "QIZ goods to US (duty-free)",
            "Agadir countries",
            "GAFTA Arab countries",
        ],
        "special_regimes": [
            "SCZONE free zone (Suez Canal)",
            "QIZ (Qualifying Industrial Zones)",
            "Export Processing Zones",
            "New Capital Investment Zone",
        ],
        "notes": [
            "COMESA: up to 100% preference for member-state goods",
            "QIZ: manufactured goods qualifying for US duty-free access",
            "Ongoing WTO accession commitments on agricultural tariffs",
        ],
        "data_quality": "high",
        "source": "https://www.gafinet.org",
        "last_reviewed": "2024",
    },
    "TUN": {
        "country": "TUN",
        "country_name": "Tunisia",
        "currency": "TND",
        "nomenclature": "Nomenclature Tarifaire Tunisienne HS10",
        "trade_bloc": "UMA + EU-DCFTA + GAFTA + Agadir",
        "bands": {
            "raw_materials": 0.0,    # most industrial raw materials duty-free under EU AA
            "intermediate_goods": 8.0,
            "final_goods": 22.0,
            "agricultural": 36.0,
            "luxury_goods": 43.0,
        },
        "vat": {
            "standard": 19.0,
            "reduced": [7.0, 13.0],
        },
        "additional_taxes": {
            "TCL": {"name": "Taxe de Compensation des Loyers", "applies_to": "selected goods"},
            "HDR": {"name": "Droit de Timbre", "rate": 1.0},
            "Consumption_Tax": {"name": "Droit de Consommation", "applies_to": "luxury & alcohol"},
        },
        "preferential_zero_rate": [
            "EU goods (AA – full liberalisation by 2017 for industrial)",
            "EFTA goods",
            "Agadir countries",
            "GAFTA Arab countries",
        ],
        "special_regimes": [
            "Offshore regime (fully export-oriented enterprises)",
            "Economic development zones (Bizerte, Sousse, Sfax)",
            "Free export zones",
        ],
        "notes": [
            "EU AA 1998: industrial goods largely duty-free",
            "DCFTA (ALECA) negotiations ongoing for agriculture/services",
            "Offshore regime: 10% CIT vs 15% standard",
        ],
        "data_quality": "high",
        "source": "https://www.douane.gov.tn",
        "last_reviewed": "2024",
    },
    "DZA": {
        "country": "DZA",
        "country_name": "Algeria",
        "currency": "DZD",
        "nomenclature": "Tarif Douanier Algérien HS10",
        "trade_bloc": "UMA + EU-Association + GAFTA",
        "bands": {
            "raw_materials": 5.0,     # higher than MAR – import substitution policy
            "intermediate_goods": 15.0,
            "final_goods": 30.0,
            "agricultural": 30.0,
            "luxury_goods": 60.0,    # luxury goods tax (additional 30% excise)
        },
        "vat": {
            "standard": 19.0,
            "reduced": [9.0],
        },
        "additional_taxes": {
            "TAP": {"name": "Taxe sur l'Activité Professionnelle", "rate": 2.0},
            "TIC": {"name": "Taxe Intérieure de Consommation", "applies_to": "fuel, tobacco"},
            "Local_Content": {"name": "Local Content Requirement surcharge", "rate_range": "0–30%"},
        },
        "preferential_zero_rate": [
            "EU goods under AA (industrial, progressive to 2020)",
            "Arab goods under GAFTA",
        ],
        "special_regimes": [
            "Free zones (limited: Bellara steel complex area)",
            "Customs warehouses",
        ],
        "notes": [
            "Import substitution: complementary tax (DCP) on many consumer goods",
            "Local content requirements in automotive, construction",
            "Luxury tax: 30% additional excise on luxury items",
            "WTO observer status – not yet a full member",
        ],
        "data_quality": "medium",
        "source": "https://www.douane.dz",
        "last_reviewed": "2024",
    },
    "LBY": {
        "country": "LBY",
        "country_name": "Libya",
        "currency": "LYD",
        "nomenclature": "Libyan Customs Tariff HS8 (2010 schedule)",
        "trade_bloc": "UMA + GAFTA",
        "bands": {
            "raw_materials": 0.0,    # reconstruction incentives – waived
            "intermediate_goods": 5.0,
            "final_goods": 15.0,
            "agricultural": 10.0,
            "luxury_goods": 20.0,
        },
        "vat": {
            "standard": 0.0,   # no VAT; sales tax applies
            "notes": "Sales tax ~4%; no formal VAT system",
        },
        "additional_taxes": {
            "Sales_Tax": {"name": "Sales Tax", "rate": 4.0},
            "Stamp_Duty": {"name": "Stamp Duty", "rate": 0.5},
        },
        "preferential_zero_rate": [
            "GAFTA Arab countries",
            "Reconstruction materials (government waiver)",
        ],
        "special_regimes": [
            "Misrata Free Zone",
            "Reconstruction Free Zones (planned)",
        ],
        "notes": [
            "Post-conflict reconstruction: many tariffs suspended/waived",
            "Dual administration (Tripoli/Tobruk) creates enforcement inconsistencies",
            "Oil sector: separate fiscal regime (NOC)",
            "Data based on pre-2011 schedule; current application varies",
        ],
        "data_quality": "low",
        "source": "https://customs.gov.ly",
        "last_reviewed": "2023",
    },
    "SDN": {
        "country": "SDN",
        "country_name": "Sudan",
        "currency": "SDG",
        "nomenclature": "Sudan Customs Tariff HS8",
        "trade_bloc": "COMESA + GAFTA + AfCFTA",
        "bands": {
            "raw_materials": 0.0,
            "intermediate_goods": 10.0,
            "final_goods": 25.0,
            "agricultural": 15.0,   # food security focus – moderate protection
            "luxury_goods": 40.0,
        },
        "vat": {
            "standard": 17.0,
            "reduced": [0.0],   # basic foods exempt
        },
        "additional_taxes": {
            "Service_Tax": {"name": "Service Tax", "rate": 17.0},
            "Development_Levy": {"name": "Development Levy", "rate_range": "1–5%"},
        },
        "preferential_zero_rate": [
            "COMESA goods (COMESA FTA schedule)",
            "GAFTA Arab countries",
        ],
        "special_regimes": [
            "Khartoum Free Trade Zone",
            "Port Sudan Trade Zone",
        ],
        "notes": [
            "Post-sanctions economy: US sanctions lifted 2017",
            "COMESA FTA: full implementation for qualified goods",
            "Agriculture: gum arabic, cotton, sesame – main export commodities",
            "Data reliability limited due to ongoing political transition",
        ],
        "data_quality": "low",
        "source": "https://www.customs.gov.sd",
        "last_reviewed": "2023",
    },
    "MRT": {
        "country": "MRT",
        "country_name": "Mauritania",
        "currency": "MRU",
        "nomenclature": "Tarif Douanier de Mauritanie HS8",
        "trade_bloc": "UMA + GAFTA + ECOWAS-Observer + AfCFTA",
        "bands": {
            "raw_materials": 0.0,
            "intermediate_goods": 10.0,
            "final_goods": 20.0,
            "agricultural": 20.0,
            "luxury_goods": 30.0,
        },
        "vat": {
            "standard": 16.0,
            "reduced": [0.0],
        },
        "additional_taxes": {
            "Solidarity_Tax": {"name": "Solidarity Tax", "rate": 1.5},
            "Statistical_Tax": {"name": "Statistical Tax", "rate": 1.0},
        },
        "preferential_zero_rate": [
            "UMA preferential schedule (partial)",
            "GAFTA Arab countries",
            "ECOWAS observer benefits (partial)",
        ],
        "special_regimes": [
            "Nouakchott Free Zone",
            "Fishing sector special regime",
        ],
        "notes": [
            "Transition country: ECOWAS observer → UMA deepening",
            "Mining sector: iron ore, gold, copper dominate exports",
            "Fisheries: major Atlantic fishery access agreements (EU, China)",
            "Renewable energy: significant potential, limited development",
        ],
        "data_quality": "low",
        "source": "https://www.douane.mr",
        "last_reviewed": "2023",
    },
}


def get_country_tariff_profile(country_code: str) -> Optional[Dict[str, Any]]:
    """
    Return the full tariff profile for a North African country.

    Args:
        country_code: ISO-3 country code (MAR, EGY, TUN, DZA, LBY, SDN, MRT)

    Returns:
        Dict with tariff bands, VAT, additional taxes and metadata,
        or None if the country is not in the North Africa roster.
    """
    return _TARIFF_PROFILES.get(country_code.upper())


def get_chapter_rate(country_code: str, chapter: int) -> float:
    """
    Return indicative import duty rate for an HS chapter in a given country.

    Uses simplified band mapping:
      Chapters 01-24  → agricultural
      Chapters 25-27  → raw_materials
      Chapters 28-38  → intermediate_goods (chemicals)
      Chapters 39-49  → intermediate_goods
      Chapters 50-67  → final_goods (textiles/footwear)
      Chapters 68-83  → intermediate_goods (metals/articles)
      Chapters 84-92  → final_goods (machinery/electronics)
      Chapters 93-97  → luxury_goods / final_goods

    Args:
        country_code: ISO-3 code
        chapter: HS chapter number (1-97)

    Returns:
        Indicative MFN duty rate as a float.
    """
    profile = get_country_tariff_profile(country_code)
    if not profile:
        return 0.0

    bands = profile["bands"]

    if 1 <= chapter <= 24:
        return bands["agricultural"]
    elif 25 <= chapter <= 27:
        return bands["raw_materials"]
    elif 28 <= chapter <= 49:
        return bands["intermediate_goods"]
    elif 50 <= chapter <= 67:
        return bands["final_goods"]
    elif 68 <= chapter <= 83:
        return bands["intermediate_goods"]
    elif 84 <= chapter <= 92:
        return bands["final_goods"]
    else:
        return bands.get("luxury_goods", bands["final_goods"])


def get_all_profiles() -> Dict[str, Dict[str, Any]]:
    """Return tariff profiles for all 7 North African countries."""
    return dict(_TARIFF_PROFILES)


def get_regional_tariff_comparison(chapter: int) -> Dict[str, float]:
    """
    Compare indicative duty rates for a given HS chapter across all countries.

    Args:
        chapter: HS chapter number (1-97)

    Returns:
        Dict mapping country codes to indicative duty rates.
    """
    return {
        cc: get_chapter_rate(cc, chapter)
        for cc in _TARIFF_PROFILES
    }
