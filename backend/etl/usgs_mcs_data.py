"""
USGS MCS — production minière africaine multi-années (curée, vintages publiés)
===============================================================================
Table canonique partagée par les deux builders de production
(``build_production_faostat_usgs.py`` et ``build_production_real.py``).

Vintages (aucune valeur inventée — uniquement chiffres publiés) :
  • MCS 2024  (pub. fév. 2024)  → données 2022 + 2023e
  • MCS 2026  (pub. 6 fév. 2026) → données 2024 + 2025e
  • Chapitre Gemstones MCS 2024/2026 → diamant de qualité gemme (le chapitre
    « Diamond » ne couvre que le diamant INDUSTRIEL, non comparable).
  • Hydrocarbures : EIA International Energy Statistics / OPEC ASB 2024.
  • Uranium : WNA ; Charbon : IEA (absents de MCS 2026).

Structure :
  commodity → (unit, institution, url, {iso3: {year: {"value", "dataset"}}})

Un pays non listé dans une édition garde son dernier vintage publié : jamais
d'extrapolation, jamais de doublon de vintage (la déduplication
``production_dedup`` protégerait une réingestion, mais chaque (pays, année)
n'apparaît qu'une fois ici par construction).
"""

from __future__ import annotations

from typing import Dict, Tuple

MCS2024 = "Mineral Commodity Summaries 2024"
MCS2026 = "Mineral Commodity Summaries 2026"
GEM2024 = "Mineral Commodity Summaries 2024 — Gemstones (diamant gemme)"
GEM2026 = "Mineral Commodity Summaries 2026 — Gemstones (diamant gemme)"
OPEC_ASB = "OPEC Annual Statistical Bulletin 2024 / EIA International Energy Statistics"
EIA_2023 = "EIA International Energy Statistics 2023"
IEA_COAL = "IEA Coal 2023"
WNA = "WNA Uranium Production 2023"

URL_MCS2024 = (
    "https://pubs.usgs.gov/periodicals/mcs2024/mcs2024.pdf"
)
URL_MCS2026 = (
    "https://pubs.usgs.gov/periodicals/mcs2026/mcs2026.pdf"
)
URL_EIA = "https://www.eia.gov/international/data/world"
URL_IEA_COAL = "https://www.iea.org/reports/coal-2023"
URL_WNA = (
    "https://world-nuclear.org/information-library/nuclear-fuel-cycle/"
    "mining-of-uranium/world-uranium-mining-production"
)


def _g(unit: str, inst: str, url: str, table: Dict[str, Tuple[str, Dict[int, float]]]):
    """Aide : (unité, institution, url, {iso3: (dataset vintage, {année: valeur})})."""
    return (unit, inst, url, table)


USGS_MCS_MULTI_YEAR: Dict[str, Tuple] = {
    # ── OR (tonnes) — MCS 2024 : 15 producteurs 2022+2023 ; MCS 2026 : GHA/ZAF ──
    "Gold": _g(
        "tonnes", "USGS", URL_MCS2024,
        {
            "GHA": (MCS2026, {2022: 127.0, 2023: 130.0, 2024: 149.0, 2025: 150.0}),
            "MLI": (MCS2024, {2022: 72.0, 2023: 105.0}),
            "ZAF": (MCS2026, {2022: 120.0, 2023: 100.0, 2024: 90.0, 2025: 90.0}),
            "BFA": (MCS2024, {2022: 60.0, 2023: 96.0}),
            "SDN": (MCS2024, {2022: 60.0, 2023: 64.0}),
            "GIN": (MCS2024, {2022: 50.0, 2023: 60.0}),
            "TZA": (MCS2024, {2022: 48.0, 2023: 53.0}),
            "CIV": (MCS2024, {2022: 35.0, 2023: 51.0}),
            "COD": (MCS2024, {2022: 40.0, 2023: 44.0}),
            "ZWE": (MCS2024, {2022: 35.0, 2023: 30.0}),
            "EGY": (MCS2024, {2022: 14.0, 2023: 16.0}),
            "SEN": (MCS2024, {2022: 14.0, 2023: 16.0}),
            "ERI": (MCS2024, {2022: 10.0, 2023: 14.0}),
            "MRT": (MCS2024, {2022: 14.0, 2023: 14.0}),
            "NER": (MCS2024, {2022: 10.0, 2023: 12.0}),
        },
    ),
    # ── PÉTROLE BRUT (1000 b/d) — EIA/OPEC, pas couvert par MCS ──
    "Crude oil": _g(
        "1000 b/d", "EIA / OPEC", URL_EIA,
        {
            "NGA": (OPEC_ASB, {2022: 1430.0, 2023: 1350.0}),
            "LBY": (OPEC_ASB, {2022: 1110.0, 2023: 1180.0}),
            "AGO": (OPEC_ASB, {2022: 1130.0, 2023: 1110.0}),
            "DZA": (OPEC_ASB, {2022: 1030.0, 2023: 1000.0}),
            "EGY": (OPEC_ASB, {2022: 590.0, 2023: 560.0}),
            "COG": (OPEC_ASB, {2022: 270.0, 2023: 270.0}),
            "GAB": (OPEC_ASB, {2022: 215.0, 2023: 200.0}),
            "GHA": (OPEC_ASB, {2022: 148.0, 2023: 150.0}),
            "SSD": (OPEC_ASB, {2022: 130.0, 2023: 140.0}),
            "TCD": (OPEC_ASB, {2022: 110.0, 2023: 110.0}),
            "GNQ": (OPEC_ASB, {2022: 88.0, 2023: 90.0}),
            "SDN": (OPEC_ASB, {2022: 55.0, 2023: 60.0}),
            "CMR": (OPEC_ASB, {2022: 58.0, 2023: 60.0}),
            "TUN": (OPEC_ASB, {2022: 38.0, 2023: 40.0}),
            "CIV": (OPEC_ASB, {2022: 28.0, 2023: 30.0}),
        },
    ),
    # ── GAZ NATUREL (bcm) — EIA ──
    "Natural gas": _g(
        "bcm", "EIA", URL_EIA,
        {
            "DZA": (EIA_2023, {2022: 100.0, 2023: 100.0}),
            "EGY": (EIA_2023, {2022: 62.0, 2023: 64.0}),
            "NGA": (EIA_2023, {2022: 47.0, 2023: 40.0}),
            "LBY": (EIA_2023, {2022: 11.0, 2023: 12.0}),
            "MOZ": (EIA_2023, {2022: 6.0, 2023: 6.0}),
            "GNQ": (EIA_2023, {2022: 5.0, 2023: 5.0}),
            "AGO": (EIA_2023, {2022: 5.0, 2023: 5.0}),
            "CIV": (EIA_2023, {2022: 2.3, 2023: 2.5}),
            "TUN": (EIA_2023, {2022: 1.5, 2023: 1.5}),
            "GHA": (EIA_2023, {2022: 1.1, 2023: 1.2}),
        },
    ),
    # ── CUIVRE (tonnes) — MCS 2026 : COD/ZMB ──
    "Copper": _g(
        "tonnes", "USGS", URL_MCS2024,
        {
            "COD": (MCS2026, {2022: 2300000.0, 2023: 2800000.0, 2024: 2990000.0, 2025: 3200000.0}),
            "ZMB": (MCS2026, {2022: 763000.0, 2023: 760000.0, 2024: 823000.0, 2025: 940000.0}),
            "ZAF": (MCS2024, {2022: 64000.0, 2023: 70000.0}),
            "NAM": (MCS2024, {2022: 24000.0, 2023: 26000.0}),
            "BWA": (MCS2024, {2022: 20000.0, 2023: 22000.0}),
        },
    ),
    # ── COBALT (tonnes) — MCS 2026 : COD/MDG ──
    "Cobalt": _g(
        "tonnes", "USGS", URL_MCS2024,
        {
            "COD": (MCS2026, {2022: 147000.0, 2023: 170000.0, 2024: 226000.0, 2025: 230000.0}),
            "MDG": (MCS2026, {2022: 2800.0, 2023: 3000.0, 2024: 3100.0, 2025: 3900.0}),
            "MAR": (MCS2024, {2022: 2200.0, 2023: 2300.0}),
        },
    ),
    # ── DIAMANTS GEMME (carats) — Gemstones MCS 2024 + MCS 2026 (périmètre cohérent) ──
    "Diamonds": _g(
        "carats", "USGS", URL_MCS2024,
        {
            "AGO": (GEM2026, {2022: 7890000.0, 2023: 7900000.0, 2024: 12600000.0, 2025: 13000000.0}),
            "BWA": (GEM2026, {2022: 17100000.0, 2023: 17000000.0, 2024: 12700000.0, 2025: 13000000.0}),
            "COD": (GEM2026, {2022: 1980000.0, 2023: 2000000.0, 2024: 1960000.0, 2025: 2000000.0}),
            "LSO": (GEM2026, {2022: 728000.0, 2023: 730000.0, 2024: 696000.0, 2025: 700000.0}),
            "NAM": (GEM2026, {2022: 2050000.0, 2023: 2000000.0, 2024: 2320000.0, 2025: 2300000.0}),
            "SLE": (GEM2026, {2022: 551000.0, 2023: 550000.0, 2024: 459000.0, 2025: 460000.0}),
            "ZAF": (GEM2026, {2022: 3860000.0, 2023: 3800000.0, 2024: 2140000.0, 2025: 2100000.0}),
            "ZWE": (GEM2026, {2022: 446000.0, 2023: 440000.0, 2024: 529000.0, 2025: 530000.0}),
            "GHA": (GEM2026, {2024: 333000.0, 2025: 330000.0}),
            "TZA": (GEM2026, {2024: 318000.0, 2025: 320000.0}),
        },
    ),
    # ── PHOSPHATE (tonnes) — MCS 2026 : 7 producteurs africains ──
    "Phosphate": _g(
        "tonnes", "USGS", URL_MCS2024,
        {
            "MAR": (MCS2026, {2022: 37000000.0, 2023: 35000000.0, 2024: 35300000.0, 2025: 36000000.0}),
            "EGY": (MCS2026, {2022: 5000000.0, 2023: 5000000.0, 2024: 5300000.0, 2025: 5500000.0}),
            "TUN": (MCS2026, {2022: 3500000.0, 2023: 3800000.0, 2024: 3280000.0, 2025: 3300000.0}),
            "SEN": (MCS2026, {2022: 2800000.0, 2023: 2800000.0, 2024: 2800000.0, 2025: 2800000.0}),
            "ZAF": (MCS2026, {2022: 2000000.0, 2023: 2000000.0, 2024: 2220000.0, 2025: 2200000.0}),
            "TGO": (MCS2026, {2022: 1300000.0, 2023: 1500000.0, 2024: 1560000.0, 2025: 1600000.0}),
            "DZA": (MCS2026, {2022: 1200000.0, 2023: 1300000.0, 2024: 2000000.0, 2025: 2000000.0}),
        },
    ),
    # ── BAUXITE (tonnes) — MCS 2026 : GIN ──
    "Bauxite": _g(
        "tonnes", "USGS", URL_MCS2024,
        {
            "GIN": (MCS2026, {2022: 95000000.0, 2023: 97000000.0, 2024: 142000000.0, 2025: 150000000.0}),
            "SLE": (MCS2024, {2022: 1700000.0, 2023: 1800000.0}),
            "GHA": (MCS2024, {2022: 1100000.0, 2023: 1150000.0}),
        },
    ),
    # ── URANIUM (tonnes) — WNA (hors MCS) ──
    "Uranium": _g(
        "tonnes", "USGS / World Nuclear Association", URL_WNA,
        {
            "NAM": (WNA, {2022: 5700.0, 2023: 5600.0}),
            "NER": (WNA, {2022: 2020.0, 2023: 2000.0}),
            "ZAF": (WNA, {2022: 220.0, 2023: 200.0}),
        },
    ),
    # ── MINERAI DE FER (tonnes, minerai utilisable) — MCS 2026 : MRT/ZAF ──
    "Iron ore": _g(
        "tonnes", "USGS", URL_MCS2024,
        {
            "ZAF": (MCS2026, {2022: 62000000.0, 2023: 62000000.0, 2024: 64000000.0, 2025: 66000000.0}),
            "MRT": (MCS2026, {2022: 12000000.0, 2023: 12000000.0, 2024: 14300000.0, 2025: 15000000.0}),
            "SLE": (MCS2024, {2022: 3000000.0, 2023: 3000000.0}),
            "LBR": (MCS2024, {2022: 2400000.0, 2023: 2500000.0}),
        },
    ),
    # ── MANGANÈSE (tonnes) — MCS 2026 : ZAF/GAB/GHA/CIV ──
    "Manganese": _g(
        "tonnes", "USGS", URL_MCS2024,
        {
            "ZAF": (MCS2026, {2022: 6900000.0, 2023: 7200000.0, 2024: 7490000.0, 2025: 7600000.0}),
            "GAB": (MCS2026, {2022: 4500000.0, 2023: 4600000.0, 2024: 4640000.0, 2025: 5000000.0}),
            "GHA": (MCS2026, {2022: 700000.0, 2023: 800000.0, 2024: 1280000.0, 2025: 2000000.0}),
            "CIV": (MCS2026, {2022: 1300000.0, 2023: 1300000.0, 2024: 340000.0, 2025: 350000.0}),
        },
    ),
    # ── PLATINE (tonnes) — MCS 2026 : ZAF/ZWE ──
    "Platinum": _g(
        "tonnes", "USGS", URL_MCS2024,
        {
            "ZAF": (MCS2026, {2022: 120.0, 2023: 120.0, 2024: 126.0, 2025: 120.0}),
            "ZWE": (MCS2026, {2022: 18.0, 2023: 19.0, 2024: 18.4, 2025: 18.0}),
        },
    ),
    # ── CHARBON (tonnes) — IEA (hors MCS) ──
    "Coal": _g(
        "tonnes", "USGS / IEA", URL_IEA_COAL,
        {
            "ZAF": (IEA_COAL, {2022: 237000000.0, 2023: 230000000.0}),
            "MOZ": (IEA_COAL, {2022: 9500000.0, 2023: 9000000.0}),
            "ZWE": (IEA_COAL, {2022: 3200000.0, 2023: 3000000.0}),
            "NGA": (IEA_COAL, {2022: 600000.0, 2023: 600000.0}),
        },
    ),
}


def build_usgs_multi_year_records() -> list:
    """Émet les enregistrements miniers multi-années (2022-2025) avec source
    par vintage : chaque valeur est publiée dans l'édition citée. Le dataset
    USGS est dérivé PAR ANNÉE (MCS 2024 pour 2022-2023, MCS 2026 pour 2024-2025,
    variante Gemstones pour les diamants) — jamais attribué en bloc."""
    records = []
    for commodity, (unit, inst, url, by_country) in USGS_MCS_MULTI_YEAR.items():
        is_energy = commodity in ("Crude oil", "Natural gas")
        is_usgs = commodity not in ("Crude oil", "Natural gas", "Coal", "Uranium")
        for iso3, (dataset_default, year_vals) in by_country.items():
            for year, value in sorted(year_vals.items()):
                if is_usgs and commodity == "Diamonds":
                    dataset = GEM2026 if year >= 2024 else GEM2024
                elif is_usgs:
                    dataset = MCS2026 if year >= 2024 else MCS2024
                else:
                    dataset = dataset_default
                records.append(
                    {
                        "country_iso3": iso3,
                        "year": year,
                        "value": value,
                        "unit": unit,
                        "source_institution": inst,
                        "source_dataset": dataset,
                        "source_url": URL_MCS2026 if (is_usgs and year >= 2024) else url,
                        "commodity_label": commodity,
                        "is_energy": is_energy,
                        "sector_isic_section": "B",
                        "sector_detail": (
                            "Energy — extraction" if is_energy else "Mining and quarrying"
                        ),
                        "indicator_code": "EIA_PROD" if is_energy else "USGS_PROD",
                        "indicator_label": "Production",
                        "usgs_table_name": f"{commodity} production {year}",
                    }
                )
    return records
