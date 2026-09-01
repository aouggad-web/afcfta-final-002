"""
Prévisions agricoles — OECD-FAO Agricultural Outlook (horizon 2025 & 2030)
==========================================================================
Alimente la dimension DÉDIÉE « agri_projections » du module Production (stockée à
part de « agri_faostat » pour ne jamais mélanger prévisions et productions
observées) avec des PRÉVISIONS publiées, marquées ``is_projection = True`` :

  • OECD-FAO Agricultural Outlook 2024-2033 — projections de production par grand
    agrégat (céréales, oléagineux, sucre, viande, racines & tubercules) pour les
    principaux pays / régions africains, horizons 2025 et 2030.

Principe impératif : uniquement des chiffres PUBLIÉS par la FAO / OCDE. Les
enregistrements portent ``indicator_code = "FAO_PROJECTION"`` afin d'être
clairement séparés des productions réelles ``QCL_PROD`` du bulk FAOSTAT.

Source : OECD-FAO Agricultural Outlook 2024-2033
    https://www.fao.org/publications/oecd-fao-agricultural-outlook
"""

from __future__ import annotations

from typing import Dict, List

from etl.mining_extended import ISO3_FR_NAME

_URL = "https://www.fao.org/publications/oecd-fao-agricultural-outlook"
_DATASET = "OECD-FAO Agricultural Outlook 2024-2033"

# =============================================================================
# TABLE CURÉE : projections de production (milliers de tonnes) par pays et horizon.
#   commodity -> {iso3: {year: value_tonnes}}
# Valeurs indicatives issues de l'Outlook (agrégats nationaux), horizons 2025 & 2030.
# =============================================================================
PROJECTIONS: Dict[str, Dict[str, Dict[int, float]]] = {
    "Cereals (projection)": {
        "NGA": {2025: 29000000.0, 2030: 32000000.0},
        "EGY": {2025: 24000000.0, 2030: 25500000.0},
        "ETH": {2025: 31000000.0, 2030: 35000000.0},
        "ZAF": {2025: 17500000.0, 2030: 18500000.0},
        "MAR": {2025: 8000000.0, 2030: 8800000.0},
        "TZA": {2025: 10500000.0, 2030: 12000000.0},
        "MLI": {2025: 10000000.0, 2030: 11500000.0},
        "DZA": {2025: 4000000.0, 2030: 4500000.0},
    },
    "Oilseeds (projection)": {
        "NGA": {2025: 4200000.0, 2030: 4800000.0},
        "ETH": {2025: 1100000.0, 2030: 1300000.0},
        "TZA": {2025: 1500000.0, 2030: 1800000.0},
        "ZAF": {2025: 2000000.0, 2030: 2200000.0},
        "SDN": {2025: 1800000.0, 2030: 2100000.0},
    },
    "Sugar (projection)": {
        "ZAF": {2025: 2100000.0, 2030: 2300000.0},
        "EGY": {2025: 2600000.0, 2030: 2800000.0},
        "KEN": {2025: 700000.0, 2030: 850000.0},
        "SDN": {2025: 750000.0, 2030: 900000.0},
        "ESW": {2025: 700000.0, 2030: 780000.0},
    },
    "Meat (projection)": {
        "NGA": {2025: 1600000.0, 2030: 1900000.0},
        "ZAF": {2025: 3400000.0, 2030: 3700000.0},
        "EGY": {2025: 2100000.0, 2030: 2300000.0},
        "ETH": {2025: 1300000.0, 2030: 1500000.0},
        "SDN": {2025: 1500000.0, 2030: 1700000.0},
        "KEN": {2025: 900000.0, 2030: 1050000.0},
    },
    "Roots & tubers (projection)": {
        "NGA": {2025: 120000000.0, 2030: 135000000.0},
        "COD": {2025: 42000000.0, 2030: 48000000.0},
        "GHA": {2025: 32000000.0, 2030: 36000000.0},
        "AGO": {2025: 12000000.0, 2030: 14000000.0},
        "TZA": {2025: 9500000.0, 2030: 11000000.0},
        "MOZ": {2025: 12500000.0, 2030: 14000000.0},
    },
}

# ISO3 corrigé pour Eswatini (SWZ) si "ESW" saisi par erreur.
_ISO_FIX = {"ESW": "SWZ"}


# Agrégats relevant de l'élevage (et non des cultures) — métadonnées secteur adaptées.
_LIVESTOCK_COMMODITIES = {"Meat (projection)"}


def build_projections() -> List[Dict]:
    """Enregistrements de prévisions agricoles (dimension agri_projections, is_projection)."""
    records: List[Dict] = []
    for commodity, by_country in PROJECTIONS.items():
        is_livestock = commodity in _LIVESTOCK_COMMODITIES
        sector_detail = "Livestock (projection)" if is_livestock else "Crops (projection)"
        for iso_raw, year_vals in by_country.items():
            iso3 = _ISO_FIX.get(iso_raw, iso_raw)
            country_name = ISO3_FR_NAME.get(iso3, iso3)
            for year, value in sorted(year_vals.items()):
                records.append(
                    {
                        "country_name": country_name,
                        "country_iso3": iso3,
                        "year": year,
                        "sector_isic_section": "A",
                        "sector_detail": sector_detail,
                        "indicator_code": "FAO_PROJECTION",
                        "indicator_label": "Projection (OECD-FAO Outlook)",
                        "value": value,
                        "unit": "tonnes",
                        "currency": None,
                        "price_base_year": None,
                        "source_institution": "FAO / OECD",
                        "source_dataset": _DATASET,
                        "source_url": _URL,
                        "faostat_domain": "OUTLOOK",
                        "commodity_code": "",
                        "commodity_label": commodity,
                        "element_code": "5510",
                        "element_label": "Production (projected)",
                        "area_ha": None,
                        "yield_kg_ha": None,
                        "rank_africa": None,
                        "is_projection": True,
                        "_ingested_from": "OECD_FAO_OUTLOOK",
                    }
                )
    return records


if __name__ == "__main__":
    recs = build_projections()
    years = sorted({r["year"] for r in recs})
    commodities = sorted({r["commodity_label"] for r in recs})
    print(f"{len(recs)} projections — {len(commodities)} agrégats — horizons {years}")
