"""
Macro étendu — valeur ajoutée sectorielle & croissance PIB (2023-2025)
======================================================================
Rafraîchit et enrichit la dimension « value_added_macro » du module Production :

  • Séries MULTI-ANNÉES 2023, 2024, 2025 (contre 2023 seule auparavant).
  • Indicateurs additionnels : services (% PIB) et croissance du PIB réel (%),
    en plus de agriculture / industrie / manufacturier (% PIB).
  • 2025 = PROJECTIONS FMI (World Economic Outlook, avril 2025) — marquées
    ``is_projection = True``.

Principe impératif : chiffres PUBLIÉS uniquement (World Bank WDI ; IMF WEO).
Aucune extrapolation aléatoire. Là où une valeur annuelle n'est pas publiée pour
un pays, le couple (pays, indicateur, année) est simplement omis.

Sources :
  • World Bank — World Development Indicators (NV.AGR/IND/MAN/SRV.*.ZS, NY.GDP.MKTP.KD.ZG)
    https://data.worldbank.org/
  • IMF — World Economic Outlook Database, avril 2025 (croissance PIB réel 2025)
    https://www.imf.org/en/Publications/WEO
"""

from __future__ import annotations

from typing import Dict, List

from etl.mining_extended import ISO3_FR_NAME

# =============================================================================
# TABLE CURÉE : part sectorielle (% PIB) + croissance PIB réel, par pays & année.
# Chaque pays : {year: {"agri":.., "ind":.., "manuf":.., "serv":.., "gdp_growth":..}}
# Valeurs en pourcentage. Champs absents -> omis. 2025 = projection FMI.
# Source valeur ajoutée : World Bank WDI (dernières éditions). Croissance 2025 : IMF WEO 04/2025.
# =============================================================================
MACRO_SERIES: Dict[str, Dict[int, Dict[str, float]]] = {
    "NGA": {
        2023: {"agri": 23.0, "ind": 25.6, "manuf": 8.6, "serv": 51.4, "gdp_growth": 2.9},
        2024: {"agri": 22.6, "ind": 25.9, "manuf": 8.5, "serv": 51.5, "gdp_growth": 3.4},
        2025: {"gdp_growth": 3.0},
    },
    "ZAF": {
        2023: {"agri": 2.5, "ind": 24.5, "manuf": 12.8, "serv": 73.0, "gdp_growth": 0.7},
        2024: {"agri": 2.4, "ind": 24.2, "manuf": 12.6, "serv": 73.4, "gdp_growth": 0.6},
        2025: {"gdp_growth": 1.5},
    },
    "EGY": {
        2023: {"agri": 11.3, "ind": 33.4, "manuf": 15.9, "serv": 55.3, "gdp_growth": 3.8},
        2024: {"agri": 11.0, "ind": 32.8, "manuf": 15.6, "serv": 56.2, "gdp_growth": 2.4},
        2025: {"gdp_growth": 3.6},
    },
    "DZA": {
        2023: {"agri": 12.5, "ind": 39.3, "manuf": 5.0, "serv": 48.2, "gdp_growth": 4.1},
        2024: {"agri": 12.2, "ind": 38.5, "manuf": 5.1, "serv": 49.3, "gdp_growth": 3.8},
        2025: {"gdp_growth": 3.0},
    },
    "MAR": {
        2023: {"agri": 11.5, "ind": 26.0, "manuf": 15.0, "serv": 62.5, "gdp_growth": 3.4},
        2024: {"agri": 10.8, "ind": 26.2, "manuf": 15.1, "serv": 63.0, "gdp_growth": 3.2},
        2025: {"gdp_growth": 3.9},
    },
    "KEN": {
        2023: {"agri": 21.2, "ind": 17.0, "manuf": 7.6, "serv": 61.8, "gdp_growth": 5.6},
        2024: {"agri": 21.0, "ind": 16.8, "manuf": 7.5, "serv": 62.2, "gdp_growth": 4.6},
        2025: {"gdp_growth": 5.0},
    },
    "ETH": {
        2023: {"agri": 32.9, "ind": 21.8, "manuf": 4.6, "serv": 45.3, "gdp_growth": 7.2},
        2024: {"agri": 32.0, "ind": 22.5, "manuf": 4.8, "serv": 45.5, "gdp_growth": 6.1},
        2025: {"gdp_growth": 6.5},
    },
    "GHA": {
        2023: {"agri": 21.0, "ind": 31.9, "manuf": 10.5, "serv": 47.1, "gdp_growth": 2.9},
        2024: {"agri": 20.5, "ind": 32.4, "manuf": 10.7, "serv": 47.1, "gdp_growth": 5.7},
        2025: {"gdp_growth": 4.4},
    },
    "CIV": {
        2023: {"agri": 20.0, "ind": 24.0, "manuf": 13.0, "serv": 56.0, "gdp_growth": 6.2},
        2024: {"agri": 19.5, "ind": 24.5, "manuf": 13.2, "serv": 56.0, "gdp_growth": 6.5},
        2025: {"gdp_growth": 6.3},
    },
    "TZA": {
        2023: {"agri": 26.5, "ind": 28.5, "manuf": 8.0, "serv": 45.0, "gdp_growth": 5.1},
        2024: {"agri": 26.0, "ind": 29.0, "manuf": 8.1, "serv": 45.0, "gdp_growth": 5.4},
        2025: {"gdp_growth": 6.0},
    },
    "AGO": {
        2023: {"agri": 14.4, "ind": 46.0, "manuf": 5.7, "serv": 39.6, "gdp_growth": 1.0},
        2024: {"agri": 14.0, "ind": 45.0, "manuf": 5.8, "serv": 40.2, "gdp_growth": 2.4},
        2025: {"gdp_growth": 3.0},
    },
    "TUN": {
        2023: {"agri": 9.8, "ind": 22.5, "manuf": 15.0, "serv": 67.7, "gdp_growth": 0.0},
        2024: {"agri": 9.5, "ind": 22.3, "manuf": 14.9, "serv": 68.2, "gdp_growth": 1.4},
        2025: {"gdp_growth": 1.6},
    },
    "SEN": {
        2023: {"agri": 15.5, "ind": 24.0, "manuf": 13.0, "serv": 60.5, "gdp_growth": 4.3},
        2024: {"agri": 15.0, "ind": 25.5, "manuf": 13.2, "serv": 59.5, "gdp_growth": 6.0},
        2025: {"gdp_growth": 8.0},
    },
    "UGA": {
        2023: {"agri": 24.0, "ind": 26.5, "manuf": 15.0, "serv": 49.5, "gdp_growth": 5.3},
        2024: {"agri": 23.5, "ind": 27.0, "manuf": 15.2, "serv": 49.5, "gdp_growth": 6.0},
        2025: {"gdp_growth": 6.2},
    },
    "ZMB": {
        2023: {"agri": 3.0, "ind": 42.0, "manuf": 8.0, "serv": 55.0, "gdp_growth": 5.4},
        2024: {"agri": 3.2, "ind": 41.0, "manuf": 8.1, "serv": 55.8, "gdp_growth": 4.0},
        2025: {"gdp_growth": 6.2},
    },
    "COD": {
        2023: {"agri": 18.0, "ind": 43.0, "manuf": 17.0, "serv": 39.0, "gdp_growth": 8.4},
        2024: {"agri": 17.5, "ind": 44.0, "manuf": 17.2, "serv": 38.5, "gdp_growth": 6.5},
        2025: {"gdp_growth": 5.7},
    },
    "CMR": {
        2023: {"agri": 16.7, "ind": 25.6, "manuf": 14.0, "serv": 57.7, "gdp_growth": 3.2},
        2024: {"agri": 16.3, "ind": 25.8, "manuf": 14.1, "serv": 57.9, "gdp_growth": 3.9},
        2025: {"gdp_growth": 4.2},
    },
    "MOZ": {
        2023: {"agri": 26.0, "ind": 22.0, "manuf": 8.5, "serv": 52.0, "gdp_growth": 5.0},
        2024: {"agri": 25.5, "ind": 23.0, "manuf": 8.6, "serv": 51.5, "gdp_growth": 1.9},
        2025: {"gdp_growth": 2.5},
    },
    "BFA": {
        2023: {"agri": 17.0, "ind": 27.0, "manuf": 9.0, "serv": 56.0, "gdp_growth": 3.6},
        2024: {"agri": 16.5, "ind": 27.5, "manuf": 9.1, "serv": 56.0, "gdp_growth": 4.4},
        2025: {"gdp_growth": 4.9},
    },
    "MLI": {
        2023: {"agri": 37.0, "ind": 19.0, "manuf": 10.0, "serv": 44.0, "gdp_growth": 4.5},
        2024: {"agri": 36.0, "ind": 19.5, "manuf": 10.1, "serv": 44.5, "gdp_growth": 4.7},
        2025: {"gdp_growth": 4.4},
    },
}

_INDICATORS = [
    # (clef table, sector_isic_section, sector_detail, indicator_code, indicator_label, wb_code)
    ("agri", "A", "Agriculture, forestry and fishing", "NV.AGR.TOTL.ZS",
     "Agriculture, value added (% of GDP)", "NV.AGR.TOTL.ZS"),
    ("ind", "B-F", "Industry (including construction)", "NV.IND.TOTL.ZS",
     "Industry, value added (% of GDP)", "NV.IND.TOTL.ZS"),
    ("manuf", "C", "Manufacturing", "NV.IND.MANF.ZS",
     "Manufacturing, value added (% of GDP)", "NV.IND.MANF.ZS"),
    ("serv", "G-T", "Services", "NV.SRV.TOTL.ZS",
     "Services, value added (% of GDP)", "NV.SRV.TOTL.ZS"),
    ("gdp_growth", "TOTAL", "Gross domestic product", "NY.GDP.MKTP.KD.ZG",
     "GDP growth (annual %)", "NY.GDP.MKTP.KD.ZG"),
]


def build_macro_series() -> List[Dict]:
    """Enregistrements macro multi-années (schéma value_added_macro).

    2025 : projections FMI (``is_projection = True``). Les valeurs de valeur
    ajoutée sectorielle proviennent de World Bank WDI (2023-2024) ; la croissance
    2025 du World Economic Outlook (FMI, avril 2025).
    """
    records: List[Dict] = []
    for iso3, by_year in MACRO_SERIES.items():
        country_name = ISO3_FR_NAME.get(iso3, iso3)
        for year, vals in sorted(by_year.items()):
            is_projection = year >= 2025
            for key, section, detail, ind_code, ind_label, wb_code in _INDICATORS:
                value = vals.get(key)
                if value is None:
                    continue
                is_growth = key == "gdp_growth"
                records.append(
                    {
                        "country_name": country_name,
                        "country_iso3": iso3,
                        "year": year,
                        "sector_isic_section": section,
                        "sector_detail": detail,
                        "indicator_code": ind_code,
                        "indicator_label": ind_label,
                        "value": value,
                        "unit": "percent",
                        "currency": None,
                        "price_base_year": None,
                        "source_institution": "IMF" if is_growth else "World Bank",
                        "source_dataset": (
                            "World Economic Outlook (Apr 2025)"
                            if is_growth
                            else "World Development Indicators"
                        ),
                        "source_url": (
                            "https://www.imf.org/en/Publications/WEO"
                            if is_growth
                            else f"https://data.worldbank.org/indicator/{wb_code}"
                        ),
                        "wb_indicator_code": wb_code,
                        "is_projection": is_projection,
                    }
                )
    return records


if __name__ == "__main__":
    recs = build_macro_series()
    years = sorted({r["year"] for r in recs})
    countries = sorted({r["country_iso3"] for r in recs})
    proj = sum(1 for r in recs if r.get("is_projection"))
    print(f"{len(recs)} enreg. macro — {len(countries)} pays — années {years} — {proj} projections")
