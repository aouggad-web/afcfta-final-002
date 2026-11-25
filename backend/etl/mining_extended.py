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
            # Seule l'Afrique du Sud figure au tableau. Namibie, Maroc, RD Congo, Zambie
            # et Burkina Faso (Perkoa, fermée en 2022) en sont absents.
            "ZAF": {2022: 238000.0, 2023: 198000.0, 2024: 120000.0},
        },
    ),
    "Tin": (
        "tonnes",
        _USGS,
        _USGS_MCS25,
        _USGS_URL,
        {
            "COD": {2022: 18600.0, 2023: 20000.0, 2024: 25000.0},
            "NGA": {2022: 7000.0, 2023: 7000.0, 2024: 7000.0},
            "RWA": {2022: 3300.0, 2023: 3600.0, 2024: 3600.0},
        },
    ),
    "Chromium": (
        "tonnes",
        _USGS,
        _USGS_MCS25,
        _USGS_URL,
        {
            # Production commercialisable (poids brut) ; Zimbabwe absent de MCS 2024.
            "ZAF": {2022: 19100000.0, 2023: 19700000.0, 2024: 21000000.0},
            "ZWE": {2023: 1070000.0, 2024: 1100000.0},
        },
    ),
    # ── Minéraux critiques / batteries ─────────────────────────────────────
    "Lithium": (
        "tonnes",
        _USGS,
        _USGS_MCS25,
        _USGS_URL,
        {
            "ZWE": {2022: 1030.0, 2023: 14900.0, 2024: 22000.0},
            "NAM": {2023: 2700.0, 2024: 2700.0},
        },
    ),
    "Graphite": (
        "tonnes",
        _USGS,
        _USGS_MCS25,
        _USGS_URL,
        {
            "MOZ": {2022: 166000.0, 2023: 98000.0, 2024: 75000.0},
            "MDG": {2022: 130000.0, 2023: 63000.0, 2024: 89000.0},
            "TZA": {2022: 6120.0, 2023: 13200.0, 2024: 25000.0},
        },
    ),
    "Tantalum": (
        "tonnes",
        _USGS,
        _USGS_MCS25,
        _USGS_URL,
        {
            "COD": {2022: 890.0, 2023: 920.0, 2024: 880.0},
            "RWA": {2022: 347.0, 2023: 350.0, 2024: 350.0},
            "NGA": {2022: 110.0, 2023: 390.0, 2024: 390.0},
            "ETH": {2023: 40.0, 2024: 40.0},
            "BDI": {2022: 59.0, 2023: 1.0, 2024: 2.0},
            "MOZ": {2023: 51.0, 2024: 55.0},
        },
    ),
    "Vanadium": (
        "tonnes",
        _USGS,
        _USGS_MCS25,
        _USGS_URL,
        {
            "ZAF": {2022: 8870.0, 2023: 8670.0, 2024: 8000.0},
        },
    ),
    # ── Métaux précieux ────────────────────────────────────────────────────
    "Palladium": (
        "tonnes",
        _USGS,
        _USGS_MCS25,
        _USGS_URL,
        {
            # MCS publie en kilogrammes : convertis en tonnes.
            "ZAF": {2022: 73.1, 2023: 74.9, 2024: 72.0},
            "ZWE": {2022: 14.3, 2023: 15.9, 2024: 15.0},
        },
    ),
    # ── Minéraux industriels / matériaux titane ───────────────────────────
    "Titanium (ilmenite)": (
        "tonnes",
        _USGS,
        _USGS_MCS25,
        _USGS_URL,
        {
            # Ilménite, en tonnes de TiO2 contenu (unité de MCS). Kenya : la mine
            # Kwale n'apparaît plus au tableau de MCS 2025.
            "ZAF": {2022: 1100000.0, 2023: 1260000.0, 2024: 1300000.0},
            "MOZ": {2022: 1400000.0, 2023: 1860000.0, 2024: 1900000.0},
            "MDG": {2022: 320000.0, 2023: 300000.0, 2024: 240000.0},
            "SEN": {2022: 410000.0, 2023: 260000.0, 2024: 300000.0},
            "KEN": {2022: 190000.0},
        },
    ),
    "Zircon": (
        "tonnes",
        _USGS,
        _USGS_MCS25,
        _USGS_URL,
        {
            # Concentrés de minerai de zirconium, poids brut.
            "ZAF": {2022: 300000.0, 2023: 289000.0, 2024: 300000.0},
            "MOZ": {2022: 104000.0, 2023: 144000.0, 2024: 160000.0},
            "SEN": {2022: 57000.0, 2023: 48000.0, 2024: 60000.0},
            "KEN": {2022: 27000.0, 2023: 20000.0, 2024: 20000.0},
            "MDG": {2022: 27000.0, 2023: 34000.0, 2024: 30000.0},
            "SLE": {2022: 34000.0, 2023: 28000.0, 2024: 20000.0},
        },
    ),
    "Fluorspar": (
        "tonnes",
        _USGS,
        _USGS_MCS25,
        _USGS_URL,
        {
            "ZAF": {2022: 406000.0, 2023: 345000.0, 2024: 380000.0},
        },
    ),
    "Salt": (
        "tonnes",
        _USGS,
        _USGS_MCS25,
        _USGS_URL,
        {
            "EGY": {2022: 2300000.0, 2023: 2300000.0, 2024: 2300000.0},
        },
    ),
    "Gypsum": (
        "tonnes",
        _USGS,
        _USGS_MCS25,
        _USGS_URL,
        {
            "DZA": {2022: 2500000.0, 2023: 2500000.0, 2024: 2500000.0},
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
            # MCS 2025 : 2023 (révisée) et 2024 (estimée).
            "BFA": {2023: 57.0, 2024: 60.0},
            "GHA": {2023: 126.0, 2024: 130.0},
            "MLI": {2023: 67.0, 2024: 70.0},
            "ZAF": {2023: 104.0, 2024: 100.0},
            "TZA": {2023: 55.0, 2024: 60.0},
        },
    ),
    "Copper": (
        "tonnes",
        _USGS,
        _USGS_MCS25,
        _USGS_URL,
        {
            # MCS 2025 : 2023 (révisée) et 2024 (estimée).
            "COD": {2023: 2930000.0, 2024: 3300000.0},
            "ZMB": {2023: 712000.0, 2024: 680000.0},
        },
    ),
    "Cobalt": (
        "tonnes",
        _USGS,
        _USGS_MCS25,
        _USGS_URL,
        {
            # MCS 2025 : 2023 (révisée) et 2024 (estimée).
            "COD": {2023: 175000.0, 2024: 220000.0},
            "MDG": {2023: 4000.0, 2024: 2600.0},
        },
    ),
    "Diamonds": (
        "carats",
        _USGS,
        _USGS_MCS25,
        _USGS_URL,
        {
            # Diamant NATUREL INDUSTRIEL (tableau « Natural Industrial Diamond » de MCS) ;
            # le diamant de qualité gemme est la série « Gemstones ».
            # MCS 2025 : 2023 (révisée) et 2024 (estimée).
            "AGO": {2023: 1000000.0, 2024: 1000000.0},
            "BWA": {2023: 8000000.0, 2024: 8000000.0},
            "COD": {2023: 7000000.0, 2024: 7000000.0},
            "ZAF": {2023: 4000000.0, 2024: 4000000.0},
            "ZWE": {2023: 4000000.0, 2024: 4000000.0},
        },
    ),
    "Phosphate": (
        "tonnes",
        _USGS,
        _USGS_MCS25,
        _USGS_URL,
        {
            # MCS 2025 : 2023 (révisée) et 2024 (estimée).
            "DZA": {2023: 2000000.0, 2024: 2000000.0},
            "EGY": {2023: 5000000.0, 2024: 5000000.0},
            "MAR": {2023: 33000000.0, 2024: 30000000.0},
            "SEN": {2023: 2400000.0, 2024: 2500000.0},
            "ZAF": {2023: 1720000.0, 2024: 2200000.0},
            "TGO": {2023: 1610000.0, 2024: 1500000.0},
            "TUN": {2023: 3600000.0, 2024: 3300000.0},
        },
    ),
    "Bauxite": (
        "tonnes",
        _USGS,
        _USGS_MCS25,
        _USGS_URL,
        {
            # MCS 2025 : 2023 (révisée) et 2024 (estimée).
            "GIN": {2023: 123000000.0, 2024: 130000000.0},
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
            # MCS 2025 : 2023 (révisée) et 2024 (estimée).
            "ZAF": {2023: 63200000.0, 2024: 66000000.0},
            "MRT": {2023: 14100000.0, 2024: 15000000.0},
        },
    ),
    "Manganese": (
        "tonnes",
        _USGS,
        _USGS_MCS25,
        _USGS_URL,
        {
            # MCS 2025 : 2023 (révisée) et 2024 (estimée).
            "ZAF": {2023: 7300000.0, 2024: 7400000.0},
            "GAB": {2023: 4490000.0, 2024: 4600000.0},
            "GHA": {2023: 818000.0, 2024: 820000.0},
            "CIV": {2023: 357000.0, 2024: 360000.0},
        },
    ),
    "Platinum": (
        "tonnes",
        _USGS,
        _USGS_MCS25,
        _USGS_URL,
        {
            # MCS publie en kilogrammes : convertis en tonnes.
            # MCS 2025 : 2023 (révisée) et 2024 (estimée).
            "ZAF": {2023: 125.0, 2024: 120.0},
            "ZWE": {2023: 19.2, 2024: 19.0},
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
            # Provenance PAR ANNÉE pour les séries USGS MCS : l'édition MCS 2024
            # publie 2022 (révisé) et 2023 (estimé) ; l'édition MCS 2025 publie
            # 2023 (révisé) et 2024 (estimé). On rattache donc chaque enregistrement
            # à l'édition qui l'a réellement publié (2022 → MCS 2024, ≥2023 → MCS 2025)
            # plutôt que d'estampiller toute la série avec une seule édition.
            if is_usgs_mcs:
                dataset_year = _USGS_MCS24 if year <= 2022 else _USGS_MCS25
            else:
                dataset_year = dataset
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
                    "source_dataset": dataset_year,
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


def build_mcs_derived() -> List[Dict]:
    """Minerais DÉRIVÉS du fichier USGS, par opposition aux tables saisies.

    Les données viennent de ``etl/mining_usgs_mcs.py``, généré depuis le
    membre CSV de la publication ScienceBase (voir
    ``scripts/build_mining_from_usgs_mcs.py``). L'émission reste ici, écrite à
    la main : un fichier généré porte des données, pas de la logique — sans
    quoi la prochaine régénération effacerait toute correction apportée au
    code d'émission.

    Ces commodités ne recoupent aucune des tables curées : le générateur les
    exclut, pour qu'un même minerai n'ait jamais deux séries concurrentes.
    """
    from etl.mining_usgs_mcs import MCS_DERIVED, USGS_MCS_EDITION, USGS_MCS_SOURCE_URL

    records: List[Dict] = []
    for commodity, spec in MCS_DERIVED.items():
        for iso3, by_year in spec["by_country"].items():
            for year, value in sorted(by_year.items()):
                records.append(
                    {
                        "country_name": ISO3_FR_NAME.get(iso3, iso3),
                        "country_iso3": iso3,
                        "year": year,
                        "sector_isic_section": "B",
                        "sector_detail": "Mining and quarrying",
                        "indicator_code": "USGS_PROD",
                        "indicator_label": "Production",
                        "value": value,
                        "unit": spec["unit"],
                        "currency": None,
                        "price_base_year": None,
                        "source_institution": "USGS",
                        "source_dataset": USGS_MCS_EDITION,
                        "source_url": USGS_MCS_SOURCE_URL,
                        "commodity_code": _COMMODITY_CODE.get(
                            commodity, commodity[:2].upper()
                        ),
                        "commodity_label": commodity,
                        # La MESURE est portée jusqu'ici : « Mine production »
                        # et « Plant production » ne se comparent pas, et le
                        # lecteur doit pouvoir le voir.
                        "usgs_table_name": f"{commodity} — {spec['measure']} {year}",
                        # MCS 2025 publie 2023 révisé et 2024 estimé.
                        "is_estimate": year >= 2024,
                    }
                )
    return records


def build_all() -> List[Dict]:
    """Toutes les additions minières : tables curées + dérivation USGS."""
    return build_mining_extended() + build_mining_year_2024() + build_mcs_derived()


if __name__ == "__main__":
    recs = build_all()
    commodities = sorted({r["commodity_label"] for r in recs})
    years = sorted({r["year"] for r in recs})
    print(f"{len(recs)} enregistrements — {len(commodities)} minéraux — années {years}")
    for c in commodities:
        print(f"  • {c}")
