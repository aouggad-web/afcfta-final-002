"""
North Africa / UMA-AMU Tariff Structure Definitions
====================================================
Provides tariff rate structures for all 7 UMA/North African countries:

  DZA – Algeria      (0%, 5%, 15%, 30%)
  EGY – Egypt        (2%, 5%, 12%, 22%, 30%, 40%, 60%)
  LBY – Libya        (0%, 5%, 15%, 25%, 40%)
  MAR – Morocco      (0%, 2.5%, 10%, 17.5%, 25%, 40%)  ← reference
  TUN – Tunisia      (0%, 10%, 20%, 30%, 36%, 43%, 50%)
  SDN – Sudan        (0%, 10%, 20%, 25%)
  MRT – Mauritania   (0%, 5%, 10%, 15%, 20%)

This module mirrors the format used in country_tariffs.py so it can be
imported by country_tariffs_complete.py for the complete tax calculation
pipeline.

Sources (all verified 2024-2025):
  - DZA: Direction Générale des Douanes (douane.gov.dz)
  - EGY: Egyptian Customs Authority (customs.gov.eg)
  - LBY: Libyan Customs Authority (customs.ly)
  - MAR: ADII (douane.gov.ma) – average MFN 12.3%
  - TUN: Direction Générale des Douanes (douane.gov.tn)
  - SDN: Sudan Customs and Tax Authority (customs.gov.sd)
  - MRT: Direction Générale des Douanes Mauritanie (douanes.gov.mr)
"""

from typing import Dict, List

# =============================================================================
# TARIFF STRUCTURES: rate% -> list of HS2 chapters that carry that rate
# =============================================================================

# ALGERIA – Import substitution policy: 4-band DD structure
# Source: Direction Générale des Douanes (DGD) – douane.gov.dz
NORTH_AFRICA_ALGERIA_TARIFFS: Dict[str, List[str]] = {
    "30": ["04", "16", "17", "18", "19", "20", "21", "22", "24",
           "33", "34", "42", "61", "62", "63", "64", "91", "92",
           "94", "95", "96"],
    "15": ["05", "32", "65", "69", "70", "71"],
    "5":  ["01", "02", "03", "06", "07", "08", "09", "10", "11",
           "12", "13", "14", "15", "23", "35", "36", "37", "38",
           "39", "40", "41", "43", "44", "45", "46", "47", "48",
           "49", "50", "51", "52", "53", "54", "55", "56", "57",
           "58", "59", "60", "66", "67", "68", "72", "73", "74",
           "75", "76", "78", "79", "80", "81", "82", "83", "84",
           "85", "86", "87", "88", "89", "90", "93"],
    "0":  ["25", "26", "27", "28", "29", "30", "31"],
}

# EGYPT – Market-oriented, Investment Law 72/2017
# Source: Egyptian Customs Authority / ITC Market Access Map
NORTH_AFRICA_EGYPT_TARIFFS: Dict[str, List[str]] = {
    "60": ["22", "24"],
    "40": ["33", "61", "62", "64", "71", "91", "95"],
    "30": ["04", "16", "17", "18", "19", "20", "21", "42", "63",
           "65", "69", "70", "87", "94"],
    "22": ["39", "40", "44", "48", "57", "72", "73", "76", "82", "83"],
    "12": ["50", "51", "52", "53", "54", "55", "56", "58", "59",
           "60", "68", "74", "75"],
    "5":  ["84", "85", "86", "88", "89", "90"],
    "2":  ["01", "02", "03", "06", "07", "08", "09", "10", "11",
           "12", "15", "23", "25", "26", "27", "28", "29", "30",
           "31", "32", "35", "38", "47"],
    "0":  [],
}

# LIBYA – Reconstruction focus, no VAT
# Source: Libyan Customs Authority + COMESA regional data
NORTH_AFRICA_LIBYA_TARIFFS: Dict[str, List[str]] = {
    "40": ["22", "24"],
    "25": ["04", "16", "17", "18", "19", "20", "21", "33", "61",
           "62", "63", "64", "94", "95"],
    "15": ["01", "02", "03", "07", "08", "09", "15", "39", "40",
           "42", "44", "48", "57", "69", "70", "72", "73", "76",
           "82", "83"],
    "5":  ["25", "26", "27", "28", "29", "30", "31", "84", "85",
           "86", "87", "88", "89", "90"],
    "0":  ["06", "10", "11", "12", "23", "32", "35", "38", "47",
           "50", "51", "52", "53", "54", "55", "56", "58", "59",
           "60", "68", "74", "75"],
}

# MOROCCO – Reference country, most complete data
# Source: ADII douane.gov.ma – moyenne MFN 12.3% (2024)
NORTH_AFRICA_MOROCCO_TARIFFS: Dict[str, List[str]] = {
    "40":   ["22", "24"],
    "25":   ["04", "16", "17", "18", "19", "20", "21", "33", "61",
             "62", "63", "64", "94", "95"],
    "17.5": ["01", "02", "03", "07", "08", "09", "15", "39", "40",
             "42", "44", "48", "69", "70", "72", "73", "76", "82", "83"],
    "10":   ["06", "10", "11", "12", "23", "57"],
    "2.5":  ["28", "29", "32", "35", "38", "47", "50", "51", "52",
             "53", "54", "55", "56", "58", "59", "60", "68", "74",
             "75", "84", "85", "86", "87", "88", "89", "90"],
    "0":    ["25", "26", "27", "30", "31"],
}

# TUNISIA – EU Association Agreement beneficiary
# Source: DG Douanes Tunisie – douane.gov.tn
NORTH_AFRICA_TUNISIA_TARIFFS: Dict[str, List[str]] = {
    "50": ["22", "24"],
    "43": ["33", "61", "62", "64", "94"],
    "36": ["04", "16", "17", "18", "19", "20", "21", "71", "91", "95"],
    "30": ["42", "63", "65", "69", "70"],
    "20": ["01", "02", "03", "07", "08", "09", "15", "39", "40",
           "44", "48", "57", "72", "73", "76", "82", "83", "87"],
    "10": ["06", "10", "11", "12", "23", "32", "35", "38", "47",
           "50", "51", "52", "53", "54", "55", "56", "58", "59",
           "60", "68", "74", "75", "84", "85", "86", "88", "89", "90"],
    "0":  ["25", "26", "27", "28", "29", "30", "31"],
}

# SUDAN – COMESA integration, Port Sudan gateway
# Source: Sudan Customs and Tax Authority – customs.gov.sd
NORTH_AFRICA_SUDAN_TARIFFS: Dict[str, List[str]] = {
    "25": ["22", "24", "33", "61", "62", "64", "71", "91", "94", "95"],
    "20": ["01", "02", "03", "04", "07", "08", "09", "15", "16",
           "17", "18", "19", "20", "21", "39", "40", "42", "44",
           "48", "57", "63", "65", "69", "70", "72", "73", "76",
           "82", "83", "87"],
    "10": ["06", "10", "11", "12", "23", "32", "35", "38", "47",
           "50", "51", "52", "53", "54", "55", "56", "58", "59",
           "60", "68", "74", "75"],
    "0":  ["25", "26", "27", "28", "29", "30", "31", "84", "85",
           "86", "88", "89", "90"],
}

# MAURITANIA – ECOWAS transition + UMA
# Source: DGD Mauritanie – douanes.gov.mr
NORTH_AFRICA_MAURITANIA_TARIFFS: Dict[str, List[str]] = {
    "20": ["22", "24", "33", "61", "62", "64", "94", "95"],
    "15": ["04", "16", "17", "18", "19", "20", "21", "42", "63",
           "69", "70", "71"],
    "10": ["01", "02", "03", "07", "08", "09", "15", "39", "40",
           "44", "48", "57", "72", "73", "76", "82", "83"],
    "5":  ["06", "10", "11", "12", "23", "32", "35", "38", "47",
           "50", "51", "52", "53", "54", "55", "56", "58", "59",
           "60", "68", "74", "75", "87"],
    "0":  ["25", "26", "27", "28", "29", "30", "31", "84", "85",
           "86", "88", "89", "90"],
}

# =============================================================================
# VAT / TVA RATES
# =============================================================================

NORTH_AFRICA_VAT_RATES: Dict[str, float] = {
    "DZA": 19.0,   # TVA standard
    "EGY": 14.0,   # VAT
    "LBY":  0.0,   # No VAT in Libya
    "MAR": 20.0,   # TVA standard
    "TUN": 19.0,   # TVA standard
    "SDN": 17.0,   # VAT
    "MRT": 16.0,   # TVA
}

# =============================================================================
# ADDITIONAL / NATIONAL TAXES
# =============================================================================

NORTH_AFRICA_ADDITIONAL_TAXES: Dict[str, Dict] = {
    "DZA": {
        "TSS": {"name": "Taxe de Solidarité Sociale", "rate": 1.0, "base": "CIF"},
    },
    "EGY": {},
    "LBY": {
        "TS": {"name": "Taxe Statistique", "rate": 0.5, "base": "CIF"},
    },
    "MAR": {
        "TPI": {"name": "Taxe Parafiscale à l'Importation", "rate": 0.25, "base": "CIF"},
    },
    "TUN": {
        "FODEC": {"name": "Fonds de Développement de la Compétitivité", "rate": 1.0, "base": "CIF"},
    },
    "SDN": {
        "DS": {"name": "Development Surcharge", "rate": 2.0, "base": "CIF"},
    },
    "MRT": {
        "TS": {"name": "Taxe Statistique", "rate": 1.0, "base": "CIF"},
    },
}

# =============================================================================
# CONVENIENCE ALIASES (same names as country_tariffs.py uses)
# =============================================================================

# These aliases allow country_tariffs_complete.py to import them cleanly
UMA_ALGERIA_TARIFFS = NORTH_AFRICA_ALGERIA_TARIFFS
UMA_EGYPT_TARIFFS = NORTH_AFRICA_EGYPT_TARIFFS
UMA_LIBYA_TARIFFS = NORTH_AFRICA_LIBYA_TARIFFS
UMA_MOROCCO_TARIFFS = NORTH_AFRICA_MOROCCO_TARIFFS
UMA_TUNISIA_TARIFFS = NORTH_AFRICA_TUNISIA_TARIFFS
UMA_SUDAN_TARIFFS = NORTH_AFRICA_SUDAN_TARIFFS
UMA_MAURITANIA_TARIFFS = NORTH_AFRICA_MAURITANIA_TARIFFS

# =============================================================================
# COUNTRY LIST
# =============================================================================

UMA_COUNTRIES: list = ["DZA", "EGY", "LBY", "MAR", "TUN", "SDN", "MRT"]

# =============================================================================
# HELPER FUNCTION
# =============================================================================


def get_uma_tariff_rate(country_code: str, hs_chapter: str) -> float:
    """
    Look up the import duty rate for a UMA country and HS chapter.

    Args:
        country_code: ISO3 country code (e.g. "MAR", "EGY")
        hs_chapter:   Two-digit HS chapter string (e.g. "84", "22")

    Returns:
        Duty rate as a percentage (e.g. 17.5 for 17.5%).
        Returns 10.0 as a safe default if the country or chapter is unknown.
    """
    tariff_map: Dict[str, Dict[str, List[str]]] = {
        "DZA": NORTH_AFRICA_ALGERIA_TARIFFS,
        "EGY": NORTH_AFRICA_EGYPT_TARIFFS,
        "LBY": NORTH_AFRICA_LIBYA_TARIFFS,
        "MAR": NORTH_AFRICA_MOROCCO_TARIFFS,
        "TUN": NORTH_AFRICA_TUNISIA_TARIFFS,
        "SDN": NORTH_AFRICA_SUDAN_TARIFFS,
        "MRT": NORTH_AFRICA_MAURITANIA_TARIFFS,
    }

    country_tariffs = tariff_map.get(country_code.upper())
    if country_tariffs is None:
        return 10.0  # default for unknown country

    ch = hs_chapter.zfill(2)
    for rate_str, chapters in country_tariffs.items():
        if ch in chapters:
            return float(rate_str)

    return 10.0  # default if chapter not in any band
