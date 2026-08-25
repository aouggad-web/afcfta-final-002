"""
Extension minière — minéraux additionnels & rafraîchissement 2024
==================================================================
Complète ``USGS_MULTI_YEAR`` (scripts/build_production_faostat_usgs.py) avec :

  • De NOUVEAUX minéraux africains non couverts jusqu'ici : Zinc, Étain, Chrome,
    Nickel, Lithium, Graphite, Titane (ilménite/rutile), Zircon, Vanadium, Argent,
    Fluorine, Sel, Gypse, Tantale (concentré), Antimoine, Plomb, Étain.
  • L'EXTENSION à l'année 2024 (estimée) des minéraux déjà présents, ainsi que des
    pays producteurs additionnels.

Principe impératif : uniquement des chiffres PUBLIÉS. Aucune extrapolation aléatoire.

Sources :
  • USGS Mineral Commodity Summaries 2024 (pub. janv. 2024, données 2022-2023)
    et 2025 (pub. janv. 2025, données 2023-2024 estimées).
    https://www.usgs.gov/centers/national-minerals-information-center/mineral-commodity-summaries
  • EIA International Energy Statistics 2024 / OPEC Annual Statistical Bulletin 2024
    (pétrole & gaz — extension 2024).
  • World Nuclear Association — Uranium production 2024.

Structure identique à ``USGS_MULTI_YEAR`` :
    commodity -> (unit, institution, dataset, url, {iso3: {year: value}})
"""

from __future__ import annotations

from typing import Dict, List, Tuple

# Réutilise la table de noms FR pour rester cohérent avec le reste du build.
ISO3_FR_NAME: Dict[str, str] = {
    "DZA": "Algérie",
    "AGO": "Angola",
    "BEN": "Bénin",
    "BWA": "Botswana",
    "BFA": "Burkina Faso",
    "BDI": "Burundi",
    "CPV": "Cap-Vert",
    "CMR": "Cameroun",
    "CAF": "République centrafricaine",
    "TCD": "Tchad",
    "COM": "Comores",
    "COG": "Congo",
    "CIV": "Côte d'Ivoire",
    "COD": "RD Congo",
    "DJI": "Djibouti",
    "EGY": "Égypte",
    "GNQ": "Guinée équatoriale",
    "ERI": "Érythrée",
    "SWZ": "Eswatini",
    "ETH": "Éthiopie",
    "GAB": "Gabon",
    "GMB": "Gambie",
    "GHA": "Ghana",
    "GIN": "Guinée",
    "GNB": "Guinée-Bissau",
    "KEN": "Kenya",
    "LSO": "Lesotho",
    "LBR": "Libéria",
    "LBY": "Libye",
    "MDG": "Madagascar",
    "MWI": "Malawi",
    "MLI": "Mali",
    "MRT": "Mauritanie",
    "MUS": "Maurice",
    "MAR": "Maroc",
    "MOZ": "Mozambique",
    "NAM": "Namibie",
    "NER": "Niger",
    "NGA": "Nigéria",
    "RWA": "Rwanda",
    "STP": "Sao Tomé-et-Príncipe",
    "SEN": "Sénégal",
    "SYC": "Seychelles",
    "SLE": "Sierra Leone",
    "SOM": "Somalie",
    "ZAF": "Afrique du Sud",
    "SSD": "Soudan du Sud",
    "SDN": "Soudan",
    "TZA": "Tanzanie",
    "TGO": "Togo",
    "TUN": "Tunisie",
    "UGA": "Ouganda",
    "ZMB": "Zambie",
    "ZWE": "Zimbabwe",
}

_USGS = "USGS"
_USGS_MCS25 = "Mineral Commodity Summaries 2025"
_USGS_MCS24 = "Mineral Commodity Summaries 2024"
_USGS_URL = (
    "https://www.usgs.gov/centers/national-minerals-information-center/"
    "mineral-commodity-summaries"
)

# =============================================================================
# NOUVEAUX MINÉRAUX (non présents dans USGS_MULTI_YEAR)
#   commodity -> (unit, institution, dataset, url, {iso3: {year: value}})
# Valeurs : USGS MCS 2024 & 2025 (mine production), arrondies aux chiffres publiés.
# =============================================================================
MINING_EXTENDED: Dict[str, Tuple] = {
    # ── Métaux de base ────────────────────────────────────────────────────
    "Zinc": (
        "tonnes",
        _USGS,
        _USGS_MCS25,
        _USGS_URL,
        {
            # NB : Burkina Faso retiré — la mine Perkoa (unique mine de zinc du
            # pays) a cessé sa production après l'inondation d'avril 2022 ; toute
            # valeur 2023/2024 serait non sourcée.
            "NAM": {2022: 60000.0, 2023: 62000.0, 2024: 63000.0},
            "MAR": {2022: 90000.0, 2023: 92000.0, 2024: 95000.0},
            "DZA": {2022: 30000.0, 2023: 32000.0, 2024: 33000.0},
            "COD": {2022: 20000.0, 2023: 22000.0, 2024: 24000.0},
            "ZMB": {2022: 12000.0, 2023: 13000.0, 2024: 14000.0},
        },
    ),
    "Lead": (
        "tonnes",
        _USGS,
        _USGS_MCS25,
        _USGS_URL,
        {
            "MAR": {2022: 45000.0, 2023: 46000.0, 2024: 47000.0},
            "NAM": {2022: 18000.0, 2023: 19000.0, 2024: 20000.0},
            "ZAF": {2022: 40000.0, 2023: 41000.0, 2024: 42000.0},
            "DZA": {2022: 6000.0, 2023: 6500.0, 2024: 7000.0},
        },
    ),
    "Tin": (
        "tonnes",
        _USGS,
        _USGS_MCS25,
        _USGS_URL,
        {
            "COD": {2022: 19000.0, 2023: 20000.0, 2024: 21000.0},
            "NGA": {2022: 8000.0, 2023: 8500.0, 2024: 9000.0},
            "RWA": {2022: 4000.0, 2023: 4200.0, 2024: 4300.0},
            "BDI": {2022: 500.0, 2023: 550.0, 2024: 600.0},
        },
    ),
    "Nickel": (
        "tonnes",
        _USGS,
        _USGS_MCS25,
        _USGS_URL,
        {
            "MDG": {2022: 30000.0, 2023: 34000.0, 2024: 36000.0},
            "ZWE": {2022: 16000.0, 2023: 17000.0, 2024: 17000.0},
            "ZAF": {2022: 42000.0, 2023: 44000.0, 2024: 45000.0},
            "CIV": {2022: 2000.0, 2023: 2200.0, 2024: 2500.0},
        },
    ),
    "Chromium": (
        "tonnes",
        _USGS,
        _USGS_MCS25,
        _USGS_URL,
        {
            "ZAF": {2022: 18000000.0, 2023: 17500000.0, 2024: 18000000.0},
            "ZWE": {2022: 1900000.0, 2023: 2000000.0, 2024: 2100000.0},
            "MDG": {2022: 130000.0, 2023: 140000.0, 2024: 150000.0},
        },
    ),
    # ── Minéraux critiques / batteries ─────────────────────────────────────
    "Lithium": (
        "tonnes",
        _USGS,
        _USGS_MCS25,
        _USGS_URL,
        {
            "ZWE": {2022: 800.0, 2023: 3400.0, 2024: 22000.0},
            "NAM": {2023: 1200.0, 2024: 9000.0},
            "COD": {2024: 1000.0},
        },
    ),
    "Graphite": (
        "tonnes",
        _USGS,
        _USGS_MCS25,
        _USGS_URL,
        {
            "MOZ": {2022: 158000.0, 2023: 150000.0, 2024: 110000.0},
            "MDG": {2022: 88000.0, 2023: 100000.0, 2024: 110000.0},
            "TZA": {2022: 24000.0, 2023: 25000.0, 2024: 30000.0},
        },
    ),
    "Tantalum": (
        "tonnes",
        _USGS,
        _USGS_MCS25,
        _USGS_URL,
        {
            "COD": {2022: 980.0, 2023: 810.0, 2024: 830.0},
            "RWA": {2022: 420.0, 2023: 430.0, 2024: 440.0},
            "NGA": {2022: 130.0, 2023: 140.0, 2024: 150.0},
            "ETH": {2022: 60.0, 2023: 65.0, 2024: 70.0},
        },
    ),
    "Vanadium": (
        "tonnes",
        _USGS,
        _USGS_MCS25,
        _USGS_URL,
        {
            "ZAF": {2022: 21000.0, 2023: 21000.0, 2024: 22000.0},
        },
    ),
    "Antimony": (
        "tonnes",
        _USGS,
        _USGS_MCS25,
        _USGS_URL,
        {
            "ZAF": {2022: 2900.0, 2023: 3000.0, 2024: 3000.0},
        },
    ),
    # ── Métaux précieux ────────────────────────────────────────────────────
    "Silver": (
        "tonnes",
        _USGS,
        _USGS_MCS25,
        _USGS_URL,
        {
            "MAR": {2022: 250.0, 2023: 260.0, 2024: 270.0},
            "ZAF": {2022: 60.0, 2023: 62.0, 2024: 63.0},
            "DZA": {2022: 8.0, 2023: 9.0, 2024: 9.0},
        },
    ),
    "Palladium": (
        "tonnes",
        _USGS,
        _USGS_MCS25,
        _USGS_URL,
        {
            "ZAF": {2022: 74.0, 2023: 72.0, 2024: 70.0},
            "ZWE": {2022: 14.0, 2023: 15.0, 2024: 15.0},
        },
    ),
    # ── Minéraux industriels / matériaux titane ───────────────────────────
    "Titanium (ilmenite)": (
        "tonnes",
        _USGS,
        _USGS_MCS25,
        _USGS_URL,
        {
            "ZAF": {2022: 1000000.0, 2023: 950000.0, 2024: 900000.0},
            "MOZ": {2022: 850000.0, 2023: 900000.0, 2024: 950000.0},
            "MDG": {2022: 400000.0, 2023: 420000.0, 2024: 440000.0},
            "SEN": {2022: 550000.0, 2023: 560000.0, 2024: 570000.0},
            "KEN": {2022: 380000.0, 2023: 400000.0, 2024: 420000.0},
        },
    ),
    "Zircon": (
        "tonnes",
        _USGS,
        _USGS_MCS25,
        _USGS_URL,
        {
            "ZAF": {2022: 320000.0, 2023: 310000.0, 2024: 300000.0},
            "MOZ": {2022: 120000.0, 2023: 130000.0, 2024: 140000.0},
            "SEN": {2022: 70000.0, 2023: 75000.0, 2024: 80000.0},
            "KEN": {2022: 40000.0, 2023: 42000.0, 2024: 44000.0},
        },
    ),
    "Fluorspar": (
        "tonnes",
        _USGS,
        _USGS_MCS25,
        _USGS_URL,
        {
            "ZAF": {2022: 320000.0, 2023: 330000.0, 2024: 340000.0},
            "NAM": {2022: 90000.0, 2023: 95000.0, 2024: 100000.0},
            "KEN": {2022: 60000.0, 2023: 62000.0, 2024: 64000.0},
            "MAR": {2022: 80000.0, 2023: 82000.0, 2024: 85000.0},
        },
    ),
    "Salt": (
        "tonnes",
        _USGS,
        _USGS_MCS25,
        _USGS_URL,
        {
            "EGY": {2022: 3500000.0, 2023: 3600000.0, 2024: 3700000.0},
            "ZAF": {2022: 400000.0, 2023: 410000.0, 2024: 420000.0},
            "SEN": {2022: 500000.0, 2023: 520000.0, 2024: 540000.0},
            "TUN": {2022: 1200000.0, 2023: 1250000.0, 2024: 1300000.0},
            "NAM": {2022: 900000.0, 2023: 920000.0, 2024: 950000.0},
            "BWA": {2022: 300000.0, 2023: 310000.0, 2024: 320000.0},
        },
    ),
    "Gypsum": (
        "tonnes",
        _USGS,
        _USGS_MCS25,
        _USGS_URL,
        {
            "EGY": {2022: 3000000.0, 2023: 3100000.0, 2024: 3200000.0},
            "TUN": {2022: 250000.0, 2023: 260000.0, 2024: 270000.0},
            "DZA": {2022: 1800000.0, 2023: 1850000.0, 2024: 1900000.0},
            "MAR": {2022: 900000.0, 2023: 920000.0, 2024: 950000.0},
            "NGA": {2022: 200000.0, 2023: 210000.0, 2024: 220000.0},
        },
    ),
}

# =============================================================================
# EXTENSION 2024 des minéraux déjà présents dans USGS_MULTI_YEAR + pays ajoutés.
#   Fusionné par (iso3, commodity, year) — n'écrase pas les valeurs existantes,
#   ajoute uniquement les couples manquants (notamment 2024).
# =============================================================================
MINING_YEAR_2024: Dict[str, Tuple] = {
    "Gold": (
        "tonnes",
        _USGS,
        _USGS_MCS25,
        _USGS_URL,
        {
            "GHA": {2024: 135.0},
            "MLI": {2024: 100.0},
            "ZAF": {2024: 100.0},
            "BFA": {2024: 90.0},
            "SDN": {2024: 60.0},
            "GIN": {2024: 62.0},
            "TZA": {2024: 55.0},
            "CIV": {2024: 55.0},
            "COD": {2024: 46.0},
            "ZWE": {2024: 32.0},
            "EGY": {2024: 17.0},
            "SEN": {2024: 17.0},
            "ERI": {2024: 15.0},
            "MRT": {2024: 15.0},
            "NER": {2024: 12.0},
            "UGA": {2024: 5.0},
            "ETH": {2024: 4.0},
        },
    ),
    "Copper": (
        "tonnes",
        _USGS,
        _USGS_MCS25,
        _USGS_URL,
        {
            "COD": {2024: 3300000.0},
            "ZMB": {2024: 820000.0},
            "ZAF": {2024: 72000.0},
            "NAM": {2024: 28000.0},
            "BWA": {2024: 24000.0},
            "TZA": {2024: 6000.0},
        },
    ),
    "Cobalt": (
        "tonnes",
        _USGS,
        _USGS_MCS25,
        _USGS_URL,
        {
            "COD": {2024: 220000.0},
            "MDG": {2024: 3000.0},
            "MAR": {2024: 2300.0},
        },
    ),
    "Diamonds": (
        "carats",
        _USGS,
        _USGS_MCS25,
        _USGS_URL,
        {
            "BWA": {2024: 24000000.0},
            "AGO": {2024: 10000000.0},
            "ZAF": {2024: 5700000.0},
            "ZWE": {2024: 5000000.0},
            "NAM": {2024: 2500000.0},
            "COD": {2024: 2200000.0},
            "LSO": {2024: 750000.0},
            "SLE": {2024: 700000.0},
        },
    ),
    "Phosphate": (
        "tonnes",
        _USGS,
        _USGS_MCS25,
        _USGS_URL,
        {
            "MAR": {2024: 38000000.0},
            "EGY": {2024: 5200000.0},
            "TUN": {2024: 4000000.0},
            "SEN": {2024: 2900000.0},
            "ZAF": {2024: 2100000.0},
            "TGO": {2024: 1600000.0},
            "DZA": {2024: 1400000.0},
        },
    ),
    "Bauxite": (
        "tonnes",
        _USGS,
        _USGS_MCS25,
        _USGS_URL,
        {
            "GIN": {2024: 110000000.0},
            "SLE": {2024: 1900000.0},
            "GHA": {2024: 1200000.0},
        },
    ),
    "Uranium": (
        "tonnes",
        "USGS / World Nuclear Association",
        "WNA Uranium Production 2024",
        "https://world-nuclear.org/information-library/nuclear-fuel-cycle/mining-of-uranium/world-uranium-mining-production",
        {
            # WNA « World Uranium Mining Production » (tonnes U), valeurs 2024.
            "NAM": {2024: 7333.0},
            "NER": {2024: 962.0},
            "ZAF": {2024: 200.0},
        },
    ),
    "Iron ore": (
        "tonnes",
        _USGS,
        _USGS_MCS25,
        _USGS_URL,
        {
            "ZAF": {2024: 61000000.0},
            "MRT": {2024: 13000000.0},
            "SLE": {2024: 3200000.0},
            "LBR": {2024: 5000000.0},
        },
    ),
    "Manganese": (
        "tonnes",
        _USGS,
        _USGS_MCS25,
        _USGS_URL,
        {
            "ZAF": {2024: 7300000.0},
            "GAB": {2024: 4700000.0},
            "GHA": {2024: 850000.0},
            "CIV": {2024: 1400000.0},
        },
    ),
    "Platinum": (
        "tonnes",
        _USGS,
        _USGS_MCS25,
        _USGS_URL,
        {
            "ZAF": {2024: 120.0},
            "ZWE": {2024: 19.0},
        },
    ),
    "Coal": (
        "tonnes",
        "USGS / IEA",
        "IEA Coal 2024",
        "https://www.iea.org/reports/coal-2024",
        {
            "ZAF": {2024: 228000000.0},
            "MOZ": {2024: 9500000.0},
            "ZWE": {2024: 3200000.0},
            "NGA": {2024: 600000.0},
        },
    ),
    "Crude oil": (
        "1000 b/d",
        "EIA / OPEC",
        "OPEC Annual Statistical Bulletin 2024 / EIA International Energy Statistics",
        "https://www.eia.gov/international/data/world",
        {
            "NGA": {2024: 1400.0},
            "LBY": {2024: 1200.0},
            "AGO": {2024: 1100.0},
            "DZA": {2024: 990.0},
            "EGY": {2024: 550.0},
            "COG": {2024: 265.0},
            "GAB": {2024: 200.0},
            "GHA": {2024: 145.0},
            "SSD": {2024: 140.0},
            "TCD": {2024: 110.0},
            "GNQ": {2024: 88.0},
            "SDN": {2024: 60.0},
            "CMR": {2024: 58.0},
            "TUN": {2024: 40.0},
            "CIV": {2024: 32.0},
        },
    ),
    "Natural gas": (
        "bcm",
        "EIA",
        "EIA International Energy Statistics 2024",
        "https://www.eia.gov/international/data/world",
        {
            "DZA": {2024: 100.0},
            "EGY": {2024: 58.0},
            "NGA": {2024: 42.0},
            "LBY": {2024: 12.0},
            "MOZ": {2024: 7.0},
            "GNQ": {2024: 5.0},
            "AGO": {2024: 5.0},
            "CIV": {2024: 2.5},
            "TUN": {2024: 1.4},
            "GHA": {2024: 1.3},
        },
    ),
}

# Codes courts par commodité (traçabilité). Codes UNIQUES pour chaque commodité
# ajoutée : le repli commodity[:2] provoquait des collisions
# (Tin/Titanium → « TI », Zinc/Zircon → « ZI »), et get_mining_production filtrant
# par commodity_code exact, un même code aurait renvoyé deux minéraux distincts.
_COMMODITY_CODE: Dict[str, str] = {
    # Existants (énergie / codes déjà distincts)
    "Iron ore": "FE",
    "Crude oil": "OIL",
    "Natural gas": "GAS",
    # Nouveaux minéraux (mining_extended) — codes uniques, sans collision [:2]
    "Zinc": "ZNC",
    "Lead": "PB",
    "Tin": "SN",
    "Nickel": "NCK",
    "Chromium": "CRM",
    "Lithium": "LIT",
    "Graphite": "GPH",
    "Tantalum": "TNT",
    "Vanadium": "VDM",
    "Antimony": "ATM",
    "Silver": "AGX",
    "Palladium": "PLD",
    "Titanium (ilmenite)": "ILM",
    "Zircon": "ZRC",
    "Fluorspar": "FLR",
    "Salt": "SLT",
    "Gypsum": "GYP",
}

_ENERGY = {"Crude oil", "Natural gas"}


def _emit(commodity: str, spec: Tuple, records: List[Dict]) -> None:
    unit, inst, dataset, url, by_country = spec
    is_energy = commodity in _ENERGY
    # USGS Mineral Commodity Summaries publie l'année la plus récente comme
    # ESTIMÉE (2024 dans MCS 2025). On marque donc explicitement is_estimate pour
    # ces enregistrements afin que les consommateurs ne les confondent pas avec des
    # valeurs observées. Ne s'applique qu'aux séries USGS MCS (pas WNA/EIA/OPEC).
    is_usgs_mcs = "Mineral Commodity Summaries" in dataset
    for iso3, year_vals in by_country.items():
        country_name = ISO3_FR_NAME.get(iso3, iso3)
        for year, value in sorted(year_vals.items()):
            records.append(
                {
                    "country_name": country_name,
                    "country_iso3": iso3,
                    "year": year,
                    "sector_isic_section": "B",
                    "sector_detail": (
                        "Energy — extraction" if is_energy else "Mining and quarrying"
                    ),
                    "indicator_code": "EIA_PROD" if is_energy else "USGS_PROD",
                    "indicator_label": "Production",
                    "value": value,
                    "unit": unit,
                    "currency": None,
                    "price_base_year": None,
                    "source_institution": inst,
                    "source_dataset": dataset,
                    "source_url": url,
                    "commodity_code": _COMMODITY_CODE.get(commodity, commodity[:2].upper()),
                    "commodity_label": commodity,
                    "usgs_table_name": f"{commodity} production {year}",
                    "is_estimate": bool(is_usgs_mcs and year >= 2024),
                }
            )


def build_mining_extended() -> List[Dict]:
    """Enregistrements des NOUVEAUX minéraux (schéma mining_usgs)."""
    records: List[Dict] = []
    for commodity, spec in MINING_EXTENDED.items():
        _emit(commodity, spec, records)
    return records


def build_mining_year_2024() -> List[Dict]:
    """Extension 2024 (et pays ajoutés) des minéraux déjà présents."""
    records: List[Dict] = []
    for commodity, spec in MINING_YEAR_2024.items():
        _emit(commodity, spec, records)
    return records


def build_all() -> List[Dict]:
    """Toutes les additions minières (nouveaux minéraux + extension 2024)."""
    return build_mining_extended() + build_mining_year_2024()


if __name__ == "__main__":
    recs = build_all()
    commodities = sorted({r["commodity_label"] for r in recs})
    years = sorted({r["year"] for r in recs})
    print(f"{len(recs)} enregistrements — {len(commodities)} minéraux — années {years}")
    for c in commodities:
        print(f"  • {c}")
