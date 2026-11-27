"""
Mines et énergie — enregistrements DÉRIVÉS des sources publiées
================================================================
Émet les enregistrements « mining_usgs » de ``data/json/production_africaine.json``
à partir de fichiers GÉNÉRÉS par script depuis les publications des sources,
jamais recopiés à la main :

  • ``etl/mining_usgs_tables.py`` — fiches USGS Mineral Commodity Summaries
    2024, 2025 et 2026 (pubs.usgs.gov) ; ``scripts/build_mining_from_usgs_pdfs.py``.
  • ``etl/energy_eia.py`` — pétrole, gaz et charbon, EIA International Energy
    Statistics (fichier INTL) ; ``scripts/build_energy_from_eia.py``.
  • ``etl/uranium_wna.py`` — uranium, World Nuclear Association ;
    ``scripts/build_uranium_from_wna.py``.

Les tables qui vivaient ici étaient saisies à la main et citaient l'USGS,
l'EIA, l'OPEP ou l'AIE sans correspondre à leurs publications : sur 327
valeurs citées « MCS », 24 seulement concordaient avec les fiches de l'USGS.

Chaque enregistrement porte la mesure de sa source (``usgs_table_name`` :
« <produit> — <mesure> <année> ») et l'édition qui publie l'année.
"""

from __future__ import annotations

from typing import Dict, List

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


# Codes courts par commodité (traçabilité). Codes UNIQUES là où le repli
# commodity[:2] provoquait des collisions (Tin/Titanium → « TI », Zinc/Zircon →
# « ZI ») : get_mining_production filtre par commodity_code exact, et un même
# code aurait renvoyé deux minéraux distincts.
_COMMODITY_CODE: Dict[str, str] = {
    # Existants (énergie / codes déjà distincts)
    "Iron ore": "FE",
    "Crude oil": "OIL",
    "Natural gas": "GAS",
    # Nouveaux minéraux (mining_extended) — codes uniques, sans collision [:2]
    "Zinc": "ZNC",
    "Tin": "SN",
    "Chromium": "CRM",
    "Lithium": "LIT",
    "Graphite": "GPH",
    "Tantalum": "TNT",
    "Vanadium": "VDM",
    "Palladium": "PLD",
    "Titanium (ilmenite)": "ILM",
    "Zircon": "ZRC",
    "Fluorspar": "FLR",
    "Salt": "SLT",
    "Gypsum": "GYP",
}


_ENERGY = {"Crude oil", "Natural gas"}


def _record(
    commodity: str,
    iso3: str,
    year: int,
    value: float,
    unit: str,
    measure: str,
    institution: str,
    dataset: str,
    url: str,
    indicator_code: str,
    is_estimate: bool,
) -> Dict:
    return {
        "country_name": ISO3_FR_NAME.get(iso3, iso3),
        "country_iso3": iso3,
        "year": year,
        "sector_isic_section": "B",
        "sector_detail": "Energy — extraction" if commodity in _ENERGY else "Mining and quarrying",
        "indicator_code": indicator_code,
        "indicator_label": "Production",
        "value": value,
        "unit": unit,
        "currency": None,
        "price_base_year": None,
        "source_institution": institution,
        "source_dataset": dataset,
        "source_url": url,
        "commodity_code": _COMMODITY_CODE.get(commodity, commodity[:2].upper()),
        "commodity_label": commodity,
        # La MESURE est portée jusqu'à l'écran : « Mine production » et
        # « Refinery production » ne se comparent pas.
        "usgs_table_name": f"{commodity} — {measure} {year}",
        "is_estimate": is_estimate,
    }


def build_mcs_tables() -> List[Dict]:
    """Minerais des fiches USGS MCS, chaque valeur rattachée à l'édition qui la publie."""
    from etl.mining_usgs_tables import MCS_TABLES, URL_FICHE

    records: List[Dict] = []
    for commodity, spec in MCS_TABLES.items():
        for iso3, by_year in spec["by_country"].items():
            for year, (value, edition) in sorted(by_year.items()):
                records.append(
                    _record(
                        commodity, iso3, year, value, spec["unit"], spec["measure"],
                        "USGS", f"Mineral Commodity Summaries {edition}",
                        URL_FICHE.format(edition=edition, slug=spec["slug"]),
                        "USGS_PROD",
                        # Chaque édition publie sa dernière année en estimation.
                        is_estimate=year == edition - 1,
                    )
                )
    return records


def build_eia() -> List[Dict]:
    """Pétrole, gaz et charbon de l'EIA (International Energy Statistics)."""
    from etl.energy_eia import EIA_DATASET, EIA_SERIES, EIA_SOURCE_URL

    records: List[Dict] = []
    for commodity, spec in EIA_SERIES.items():
        for iso3, by_year in spec["by_country"].items():
            for year, value in sorted(by_year.items()):
                records.append(
                    _record(
                        commodity, iso3, year, value, spec["unit"], spec["measure"],
                        "EIA", EIA_DATASET, EIA_SOURCE_URL, "EIA_PROD", is_estimate=False,
                    )
                )
    return records


def build_wna() -> List[Dict]:
    """Uranium de la World Nuclear Association (production des mines, tU)."""
    from etl.uranium_wna import WNA_DATASET, WNA_MEASURE, WNA_SOURCE_URL, WNA_URANIUM

    return [
        _record(
            "Uranium", iso3, year, value, "tonnes", WNA_MEASURE,
            "World Nuclear Association", WNA_DATASET, WNA_SOURCE_URL, "WNA_PROD",
            is_estimate=False,
        )
        for iso3, by_year in WNA_URANIUM.items()
        for year, value in sorted(by_year.items())
    ]


def build_all() -> List[Dict]:
    """Tous les enregistrements mines et énergie, dérivés des sources publiées."""
    return build_mcs_tables() + build_eia() + build_wna()


if __name__ == "__main__":
    recs = build_all()
    commodities = sorted({r["commodity_label"] for r in recs})
    years = sorted({r["year"] for r in recs})
    print(f"{len(recs)} enregistrements — {len(commodities)} minéraux — années {years}")
    for c in commodities:
        print(f"  • {c}")
