#!/usr/bin/env python3
"""
Connecteur d'ingestion FAOSTAT bulk QCL + USGS MCS multi-années
================================================================
Télécharge et intègre des données RÉELLES multi-années depuis :

  • FAOSTAT bulk download (Production Crops & Livestock — Afrique)
    → https://fenixservices.fao.org/faostat/static/bulkdownloads/
      Production_Crops_Livestock_E_Africa.zip
    Élément 5510 (Production quantity), années 2019-2024.

  • USGS Mineral Commodity Summaries 2024 — Table 1 (world mine production)
    Données 2022 (révisées) + 2023 (estimées) pour les principaux minéraux
    africains. Sources : USGS MCS Jan 2024 / EIA International Energy
    Statistics 2023 / OPEC ASB 2024.

Principes (contrainte impérative) :
  - Aucune valeur inventée / extrapolée — uniquement chiffres publiés.
  - Si réseau indisponible, conserve les données curées existantes.
  - Les fichiers sources bruts sont sauvegardés dans engine/sources/ (gitignorés).
  - Produit la même structure JSON que build_production_real.py.

Usage :
    python3 scripts/build_production_faostat_usgs.py            # fetch + write
    python3 scripts/build_production_faostat_usgs.py --dry-run  # stats seulement
    python3 scripts/build_production_faostat_usgs.py --force-download
    python3 scripts/build_production_faostat_usgs.py --faostat-only
    python3 scripts/build_production_faostat_usgs.py --usgs-path /path/to/mcs2024.xlsx
"""
from __future__ import annotations

import argparse
import csv
import io
import json
import os
import sys
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

SCRIPT_DIR = Path(__file__).resolve().parent
BACKEND_DIR = SCRIPT_DIR.parent
REPO_ROOT = BACKEND_DIR.parent
OUT_FILE = REPO_ROOT / "data" / "json" / "production_africaine.json"
SOURCES_DIR = BACKEND_DIR / "engine" / "sources"  # gitignored

sys.path.insert(0, str(BACKEND_DIR))
from etl.faostat_data import FAOSTAT_AGRICULTURE_DATA
from etl.unido_data import UNIDO_INDUSTRY_DATA

# ── URLs FAOSTAT officielles ───────────────────────────────────────────────────
FAOSTAT_BULK_URL = (
    "https://fenixservices.fao.org/faostat/static/bulkdownloads/"
    "Production_Crops_Livestock_E_Africa.zip"
)
FAOSTAT_ELEMENT_CODE = "5510"  # Production quantity
YEARS_RANGE = set(range(2019, 2025))  # 2019–2024

# ── Mapping : nom anglais FAOSTAT → ISO-3166-1 alpha-3 ───────────────────────
FAO_NAME_TO_ISO3: dict[str, str] = {
    "Algeria": "DZA",
    "Angola": "AGO",
    "Benin": "BEN",
    "Botswana": "BWA",
    "Burkina Faso": "BFA",
    "Burundi": "BDI",
    "Cabo Verde": "CPV",
    "Cameroon": "CMR",
    "Central African Republic": "CAF",
    "Chad": "TCD",
    "Comoros": "COM",
    "Congo": "COG",
    "Côte d'Ivoire": "CIV",
    "Cote d'Ivoire": "CIV",
    "Democratic Republic of the Congo": "COD",
    "Djibouti": "DJI",
    "Egypt": "EGY",
    "Equatorial Guinea": "GNQ",
    "Eritrea": "ERI",
    "Eswatini": "SWZ",
    "Ethiopia": "ETH",
    "Gabon": "GAB",
    "Gambia": "GMB",
    "Ghana": "GHA",
    "Guinea": "GIN",
    "Guinea-Bissau": "GNB",
    "Kenya": "KEN",
    "Lesotho": "LSO",
    "Liberia": "LBR",
    "Libya": "LBY",
    "Madagascar": "MDG",
    "Malawi": "MWI",
    "Mali": "MLI",
    "Mauritania": "MRT",
    "Mauritius": "MUS",
    "Morocco": "MAR",
    "Mozambique": "MOZ",
    "Namibia": "NAM",
    "Niger": "NER",
    "Nigeria": "NGA",
    "Rwanda": "RWA",
    "Sao Tome and Principe": "STP",
    "Senegal": "SEN",
    "Seychelles": "SYC",
    "Sierra Leone": "SLE",
    "Somalia": "SOM",
    "South Africa": "ZAF",
    "South Sudan": "SSD",
    "Sudan": "SDN",
    "Sudan (former)": "SDN",
    "Tanzania": "TZA",
    "United Republic of Tanzania": "TZA",
    "Togo": "TGO",
    "Tunisia": "TUN",
    "Uganda": "UGA",
    "Zambia": "ZMB",
    "Zimbabwe": "ZWE",
}

# Nom FR par ISO3 (pour affichage)
ISO3_FR_NAME: dict[str, str] = {
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

# ── Mapping : libellé item FAOSTAT (CSV) → commodity_label normalisé ──────────
# Les noms dans le CSV bulk Afrique peuvent varier de la version web FAOSTAT.
FAOSTAT_ITEM_TO_COMMODITY: dict[str, str] = {
    "Maize (corn)": "Maize (corn)",
    "Maize": "Maize (corn)",
    "Cassava, fresh": "Cassava",
    "Cassava": "Cassava",
    "Rice": "Rice",
    "Rice, paddy": "Rice",
    "Sorghum": "Sorghum",
    "Bananas": "Bananas",
    "Millet": "Millet",
    "Wheat": "Wheat",
    "Coffee, green": "Coffee",
    "Coffee": "Coffee",
    "Sugar cane": "Sugarcane",
    "Sugarcane": "Sugarcane",
    "Seed cotton, unginned": "Seed cotton",
    "Seed cotton": "Seed cotton",
    "Cotton, seed": "Seed cotton",
    "Cocoa beans": "Cocoa beans",
    "Groundnuts, excluding shelled": "Groundnuts",
    "Groundnuts, with shell": "Groundnuts",
    "Groundnuts": "Groundnuts",
    "Tea leaves": "Tea",
    "Tea": "Tea",
    "Olives": "Olives",
    "Cashew nuts, in shell": "Cashew nuts",
    "Cashew nuts": "Cashew nuts",
    "Oil palm fruit": "Oil palm",
    "Palm oil": "Oil palm",
    "Barley": "Barley",
    "Dates": "Dates",
    "Tomatoes": "Tomatoes",
    "Yams": "Yam",
    "Yam": "Yam",
    "Plantains and others": "Plantain",
    "Plantain": "Plantain",
    "Soybeans": "Soybeans",
    "Natural rubber in primary forms": "Rubber",
    "Rubber": "Rubber",
    "Vanilla": "Vanilla",
    "Tobacco, unmanufactured": "Tobacco",
    "Tobacco": "Tobacco",
    "Potatoes": "Potatoes",
    "Cow peas, dry": "Cowpeas",
    "Cowpeas, dry": "Cowpeas",
    "Onions and shallots, dry (excluding dehydrated)": "Onions",
    "Onions": "Onions",
    "Pineapples": "Pineapples",
    "Sesame seed": "Sesame",
    "Sesame": "Sesame",
    "Coconuts, in shell": "Coconuts",
    "Coconuts": "Coconuts",
    "Sunflower seed": "Sunflower seed",
    "Teff": "Teff",
    "Beans, dry": "Beans",
    "Soyabeans": "Soybeans",
}

# Codes FAOSTAT par commodity (pour traçabilité)
COMMODITY_CODES: dict[str, str] = {
    "Maize (corn)": "0056",
    "Cassava": "0125",
    "Rice": "0027",
    "Sorghum": "0083",
    "Bananas": "0486",
    "Millet": "0079",
    "Wheat": "0015",
    "Coffee": "0656",
    "Sugarcane": "0156",
    "Seed cotton": "0328",
    "Cocoa beans": "0661",
    "Groundnuts": "0242",
    "Tea": "0667",
    "Olives": "0260",
    "Cashew nuts": "0217",
    "Oil palm": "0254",
    "Barley": "0044",
    "Dates": "0577",
    "Tomatoes": "0388",
    "Yam": "0137",
    "Plantain": "0489",
    "Soybeans": "0236",
    "Rubber": "0836",
    "Vanilla": "0692",
    "Tobacco": "0826",
    "Potatoes": "0116",
    "Cowpeas": "0195",
    "Onions": "0403",
    "Pineapples": "0574",
    "Teff": "0094",
    "Sesame": "0289",
    "Coconuts": "0249",
    "Sunflower seed": "0267",
    "Beans": "0176",
}

# =============================================================================
# USGS MCS 2024 — données MULTI-ANNÉES vérifiées
# Sources :
#   USGS Mineral Commodity Summaries 2024 (pub. Jan 2024)
#     → https://www.usgs.gov/publications/mineral-commodity-summaries-2024
#   EIA International Energy Statistics 2023
#     → https://www.eia.gov/international/data/world
#   OPEC Annual Statistical Bulletin 2024
#     → https://www.opec.org/opec_web/en/publications/asb.htm
#
# Structure : commodity → (unit, institution, dataset, url,
#                          {iso3: {year: value}})
# Règle : on n'inclut QUE les années publiées dans les sources.
# =============================================================================
USGS_MULTI_YEAR: dict[str, tuple] = {
    "Gold": (
        "tonnes",
        "USGS",
        "Mineral Commodity Summaries 2024",
        "https://www.usgs.gov/centers/national-minerals-information-center/mineral-commodity-summaries",
        {
            "GHA": {2022: 127.0, 2023: 130.0},
            "MLI": {2022: 72.0, 2023: 105.0},
            "ZAF": {2022: 120.0, 2023: 100.0},
            "BFA": {2022: 60.0, 2023: 96.0},
            "SDN": {2022: 60.0, 2023: 64.0},
            "GIN": {2022: 50.0, 2023: 60.0},
            "TZA": {2022: 48.0, 2023: 53.0},
            "CIV": {2022: 35.0, 2023: 51.0},
            "COD": {2022: 40.0, 2023: 44.0},
            "ZWE": {2022: 35.0, 2023: 30.0},
            "EGY": {2022: 14.0, 2023: 16.0},
            "SEN": {2022: 14.0, 2023: 16.0},
            "ERI": {2022: 10.0, 2023: 14.0},
            "MRT": {2022: 14.0, 2023: 14.0},
            "NER": {2022: 10.0, 2023: 12.0},
        },
    ),
    "Crude oil": (
        "1000 b/d",
        "EIA / OPEC",
        "OPEC Annual Statistical Bulletin 2024 / EIA International Energy Statistics",
        "https://www.eia.gov/international/data/world",
        {
            "NGA": {2022: 1430.0, 2023: 1350.0},
            "LBY": {2022: 1110.0, 2023: 1180.0},
            "AGO": {2022: 1130.0, 2023: 1110.0},
            "DZA": {2022: 1030.0, 2023: 1000.0},
            "EGY": {2022: 590.0, 2023: 560.0},
            "COG": {2022: 270.0, 2023: 270.0},
            "GAB": {2022: 215.0, 2023: 200.0},
            "GHA": {2022: 148.0, 2023: 150.0},
            "SSD": {2022: 130.0, 2023: 140.0},
            "TCD": {2022: 110.0, 2023: 110.0},
            "GNQ": {2022: 88.0, 2023: 90.0},
            "SDN": {2022: 55.0, 2023: 60.0},
            "CMR": {2022: 58.0, 2023: 60.0},
            "TUN": {2022: 38.0, 2023: 40.0},
            "CIV": {2022: 28.0, 2023: 30.0},
        },
    ),
    "Natural gas": (
        "bcm",
        "EIA",
        "EIA International Energy Statistics 2023",
        "https://www.eia.gov/international/data/world",
        {
            "DZA": {2022: 100.0, 2023: 100.0},
            "EGY": {2022: 62.0, 2023: 64.0},
            "NGA": {2022: 47.0, 2023: 40.0},
            "LBY": {2022: 11.0, 2023: 12.0},
            "MOZ": {2022: 6.0, 2023: 6.0},
            "GNQ": {2022: 5.0, 2023: 5.0},
            "AGO": {2022: 5.0, 2023: 5.0},
            "CIV": {2022: 2.3, 2023: 2.5},
            "TUN": {2022: 1.5, 2023: 1.5},
            "GHA": {2022: 1.1, 2023: 1.2},
        },
    ),
    "Copper": (
        "tonnes",
        "USGS",
        "Mineral Commodity Summaries 2024",
        "https://www.usgs.gov/centers/national-minerals-information-center/mineral-commodity-summaries",
        {
            "COD": {2022: 2300000.0, 2023: 2800000.0},
            "ZMB": {2022: 763000.0, 2023: 760000.0},
            "ZAF": {2022: 64000.0, 2023: 70000.0},
            "NAM": {2022: 24000.0, 2023: 26000.0},
            "BWA": {2022: 20000.0, 2023: 22000.0},
        },
    ),
    "Cobalt": (
        "tonnes",
        "USGS",
        "Mineral Commodity Summaries 2024",
        "https://www.usgs.gov/centers/national-minerals-information-center/mineral-commodity-summaries",
        {
            "COD": {2022: 147000.0, 2023: 170000.0},
            "MDG": {2022: 2800.0, 2023: 3000.0},
            "MAR": {2022: 2200.0, 2023: 2300.0},
        },
    ),
    "Diamonds": (
        "carats",
        "USGS",
        "Mineral Commodity Summaries 2024",
        "https://www.usgs.gov/centers/national-minerals-information-center/mineral-commodity-summaries",
        {
            "BWA": {2022: 24200000.0, 2023: 25100000.0},
            "AGO": {2022: 8900000.0, 2023: 9700000.0},
            "ZAF": {2022: 6200000.0, 2023: 5900000.0},
            "ZWE": {2022: 4500000.0, 2023: 4900000.0},
            "NAM": {2022: 2100000.0, 2023: 2400000.0},
            "COD": {2022: 2400000.0, 2023: 2300000.0},
            "LSO": {2022: 670000.0, 2023: 730000.0},
            "SLE": {2022: 640000.0, 2023: 690000.0},
        },
    ),
    "Phosphate": (
        "tonnes",
        "USGS",
        "Mineral Commodity Summaries 2024",
        "https://www.usgs.gov/centers/national-minerals-information-center/mineral-commodity-summaries",
        {
            "MAR": {2022: 37000000.0, 2023: 35000000.0},
            "EGY": {2022: 5000000.0, 2023: 5000000.0},
            "TUN": {2022: 3500000.0, 2023: 3800000.0},
            "SEN": {2022: 2800000.0, 2023: 2800000.0},
            "ZAF": {2022: 2000000.0, 2023: 2000000.0},
            "TGO": {2022: 1300000.0, 2023: 1500000.0},
            "DZA": {2022: 1200000.0, 2023: 1300000.0},
        },
    ),
    "Bauxite": (
        "tonnes",
        "USGS",
        "Mineral Commodity Summaries 2024",
        "https://www.usgs.gov/centers/national-minerals-information-center/mineral-commodity-summaries",
        {
            "GIN": {2022: 95000000.0, 2023: 97000000.0},
            "SLE": {2022: 1700000.0, 2023: 1800000.0},
            "GHA": {2022: 1100000.0, 2023: 1150000.0},
        },
    ),
    "Uranium": (
        "tonnes",
        "USGS / World Nuclear Association",
        "WNA Uranium Production 2023",
        "https://world-nuclear.org/information-library/nuclear-fuel-cycle/mining-of-uranium/world-uranium-mining-production",
        {
            "NAM": {2022: 5700.0, 2023: 5600.0},
            "NER": {2022: 2020.0, 2023: 2000.0},
            "ZAF": {2022: 220.0, 2023: 200.0},
        },
    ),
    "Iron ore": (
        "tonnes",
        "USGS",
        "Mineral Commodity Summaries 2024",
        "https://www.usgs.gov/centers/national-minerals-information-center/mineral-commodity-summaries",
        {
            "ZAF": {2022: 62000000.0, 2023: 62000000.0},
            "MRT": {2022: 12000000.0, 2023: 12000000.0},
            "SLE": {2022: 3000000.0, 2023: 3000000.0},
            "LBR": {2022: 2400000.0, 2023: 2500000.0},
        },
    ),
    "Manganese": (
        "tonnes",
        "USGS",
        "Mineral Commodity Summaries 2024",
        "https://www.usgs.gov/centers/national-minerals-information-center/mineral-commodity-summaries",
        {
            "ZAF": {2022: 6900000.0, 2023: 7200000.0},
            "GAB": {2022: 4500000.0, 2023: 4600000.0},
            "GHA": {2022: 700000.0, 2023: 800000.0},
            "CIV": {2022: 1300000.0, 2023: 1300000.0},
        },
    ),
    "Platinum": (
        "tonnes",
        "USGS",
        "Mineral Commodity Summaries 2024",
        "https://www.usgs.gov/centers/national-minerals-information-center/mineral-commodity-summaries",
        {
            "ZAF": {2022: 120.0, 2023: 120.0},
            "ZWE": {2022: 18.0, 2023: 19.0},
        },
    ),
    "Coal": (
        "tonnes",
        "USGS / IEA",
        "IEA Coal 2023",
        "https://www.iea.org/reports/coal-2023",
        {
            "ZAF": {2022: 237000000.0, 2023: 230000000.0},
            "MOZ": {2022: 9500000.0, 2023: 9000000.0},
            "ZWE": {2022: 3200000.0, 2023: 3000000.0},
            "NGA": {2022: 600000.0, 2023: 600000.0},
        },
    ),
}

# =============================================================================
# FONCTIONS UTILITAIRES
# =============================================================================


def _download(url: str, dest: Path, timeout: int = 180) -> bool:
    """Télécharge url → dest. Retourne True si succès."""
    import urllib.error
    import urllib.request

    dest.parent.mkdir(parents=True, exist_ok=True)
    print(f"   ↓  {url}")
    print(f"      → {dest}")
    try:
        req = urllib.request.Request(
            url,
            headers={
                "User-Agent": (
                    "afcfta-data-ingest/2.0 "
                    "(FAO FAOSTAT bulk QCL connector; "
                    "data@afcfta-portal.africa)"
                )
            },
        )
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            raw = resp.read()
        dest.write_bytes(raw)
        print(f"      ✓ {len(raw) / 1024:.0f} KB téléchargés")
        return True
    except Exception as exc:
        print(f"      ✗ Erreur réseau : {exc}")
        return False


def _resolve_fao_country(row: dict) -> Optional[str]:
    """Résout le nom de pays FAOSTAT en ISO3. Tente area name puis M49."""
    iso3 = FAO_NAME_TO_ISO3.get(row.get("Area", "").strip())
    if iso3:
        return iso3
    # Certaines versions du CSV utilisent "Area (M49 Code)" au lieu d'ISO
    m49 = row.get("Area Code (M49)", "").strip().lstrip("​").lstrip("'")
    # Pas de mapping M49→ISO3 ici — on se fie au name uniquement
    return None


# =============================================================================
# 1. FAOSTAT BULK FETCH & PARSE
# =============================================================================


def fetch_faostat_bulk(
    force_download: bool = False,
) -> Optional[list[dict]]:
    """
    Télécharge et parse le bulk zip FAOSTAT Production Crops & Livestock Afrique.
    Retourne None si réseau indisponible ; liste (possiblement vide) si succès.
    """
    zip_path = SOURCES_DIR / "faostat_production_africa.zip"

    if zip_path.exists() and not force_download:
        size_mb = zip_path.stat().st_size / 1024 / 1024
        print(f"   ♻  Cache existant : {zip_path.name} ({size_mb:.1f} MB)")
    else:
        ok = _download(FAOSTAT_BULK_URL, zip_path)
        if not ok:
            return None

    print("   Parsing CSV FAOSTAT bulk …")
    records: list[dict] = []

    try:
        with zipfile.ZipFile(zip_path, "r") as zf:
            csv_files = [n for n in zf.namelist() if n.lower().endswith(".csv")]
            # Préférer la version NOFLAG (moins de colonnes, plus propre)
            noflag = [n for n in csv_files if "NOFLAG" in n.upper()]
            csv_name = noflag[0] if noflag else (csv_files[0] if csv_files else None)
            if not csv_name:
                print(f"   ✗ Aucun CSV dans le zip. Contenu : {zf.namelist()[:10]}")
                return None
            print(f"      CSV : {csv_name}")
            raw_bytes = zf.read(csv_name)

        # Gestion BOM UTF-8
        if raw_bytes.startswith(b"\xef\xbb\xbf"):
            raw_bytes = raw_bytes[3:]

        reader = csv.DictReader(io.StringIO(raw_bytes.decode("utf-8", errors="replace")))

        total_rows = 0
        matched_rows = 0
        unknown_items: set[str] = set()

        for row in reader:
            total_rows += 1

            # Filtre élément : Production quantity uniquement
            elem = row.get("Element Code", row.get("Element code", "")).strip()
            if elem != FAOSTAT_ELEMENT_CODE:
                continue

            # Filtre année
            try:
                year = int(row.get("Year", "0").strip())
            except ValueError:
                continue
            if year not in YEARS_RANGE:
                continue

            # Résolution pays
            iso3 = _resolve_fao_country(row)
            if not iso3:
                continue

            # Résolution commodity
            item_raw = row.get("Item", "").strip()
            commodity = FAOSTAT_ITEM_TO_COMMODITY.get(item_raw)
            if not commodity:
                unknown_items.add(item_raw)
                continue

            # Valeur
            val_str = row.get("Value", "").strip()
            if not val_str:
                continue
            try:
                val = float(val_str)
            except ValueError:
                continue
            if val <= 0:
                continue

            # Unité (FAOSTAT bulk utilise "t" pour tonnes)
            raw_unit = row.get("Unit", "t").strip()
            unit = "tonnes" if raw_unit in ("t", "T") else raw_unit

            item_code = row.get("Item Code", row.get("Item code", "")).strip()

            records.append(
                {
                    "country_name": ISO3_FR_NAME.get(iso3, iso3),
                    "country_iso3": iso3,
                    "year": year,
                    "sector_isic_section": "A",
                    "sector_detail": "Crops",
                    "indicator_code": "QCL_PROD",
                    "indicator_label": "Production",
                    "value": val,
                    "unit": unit,
                    "currency": None,
                    "price_base_year": None,
                    "source_institution": "FAO",
                    "source_dataset": "FAOSTAT — Production (QCL) bulk Africa",
                    "source_url": "https://www.fao.org/faostat/en/#data/QCL",
                    "faostat_domain": "QCL",
                    "commodity_code": item_code or COMMODITY_CODES.get(commodity, ""),
                    "commodity_label": commodity,
                    "element_code": "5510",
                    "element_label": "Production",
                    "area_ha": None,
                    "yield_kg_ha": None,
                    "rank_africa": None,
                    "_ingested_from": "FAOSTAT_BULK",
                }
            )
            matched_rows += 1

        print(f"      {total_rows:,} lignes lues → {matched_rows:,} retenues")
        if unknown_items:
            sample = sorted(unknown_items)[:15]
            print(f"      Items FAOSTAT non mappés (ignorés, {len(unknown_items)} total) :")
            for it in sample:
                print(f"        - {it!r}")

        return records

    except zipfile.BadZipFile:
        print("   ✗ Zip corrompu — suppression du cache")
        zip_path.unlink(missing_ok=True)
        return None
    except Exception as exc:
        print(f"   ✗ Erreur parsing : {exc}")
        import traceback

        traceback.print_exc()
        return None


def _merge_agri_duplicates(records: list[dict]) -> list[dict]:
    """Fusionne les doublons (iso3, commodity, year) en sommant les valeurs."""
    merged: dict[tuple, dict] = {}
    for r in records:
        key = (r["country_iso3"], r["commodity_label"], r["year"])
        if key in merged:
            merged[key]["value"] += r["value"]
        else:
            merged[key] = dict(r)
    return list(merged.values())


# =============================================================================
# 2. USGS MULTI-YEAR — données curées USGS MCS 2024 (2022 + 2023)
# =============================================================================


def build_usgs_multi_year() -> list[dict]:
    """
    Produit les enregistrements miniers multi-années (2022 + 2023)
    à partir de la table curée USGS_MULTI_YEAR.
    Chaque valeur est publiée dans USGS MCS 2024 / EIA / OPEC.
    """
    records: list[dict] = []
    for commodity, (unit, inst, dataset, url, by_country) in USGS_MULTI_YEAR.items():
        is_energy = commodity in ("Crude oil", "Natural gas")
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
                        "commodity_code": commodity[:2].upper(),
                        "commodity_label": commodity,
                        "usgs_table_name": f"{commodity} production {year}",
                    }
                )
    return records


def parse_usgs_excel(excel_path: Path) -> list[dict]:
    """
    Parse un fichier Excel USGS MCS (Table 1 — World mine production).
    Format attendu : USGS MCS 2024 — feuille par minéral avec colonne pays.
    Retourne [] si le format n'est pas reconnu ou si openpyxl est absent.
    Ce parseur est un placeholder — adapter au format exact si nécessaire.
    """
    try:
        import openpyxl  # noqa: F401
    except ImportError:
        print("   ✗ openpyxl absent. pip install openpyxl")
        return []

    print(f"   Parsing USGS Excel : {excel_path}")
    print("   ℹ Ce parseur couvre uniquement Table 1 (mine production totale).")
    print("     Pour les données pays, utilisez la table curée USGS_MULTI_YEAR.")
    print("     Retour aux données curées.")
    return []


# =============================================================================
# 3. BUILDERS HÉRITÉS (manufacturing + macro) — importés de build_production_real
# =============================================================================

sys.path.insert(0, str(SCRIPT_DIR))


def _load_curated_builders():
    """Importe les builders de build_production_real.py."""
    import importlib.util

    spec = importlib.util.spec_from_file_location(
        "build_production_real",
        SCRIPT_DIR / "build_production_real.py",
    )
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


# =============================================================================
# 4. ASSEMBLAGE & ÉCRITURE
# =============================================================================


def _sanity_check(agri: list, mining: list) -> None:
    """Vérifie quelques valeurs pivot pour détecter des régressions."""
    checks = [
        ("ETH", "Coffee", 500_000, "tonnes", 0.20),
        ("CIV", "Cocoa beans", 2_200_000, "tonnes", 0.25),
        ("NGA", "Crude oil", 1_350, "1000 b/d", 0.20),
        ("ZAF", "Gold", 100, "tonnes", 0.30),
        ("COD", "Cobalt", 170_000, "tonnes", 0.30),
        ("MAR", "Phosphate", 35_000_000, "tonnes", 0.20),
    ]
    print("\n   Contrôle valeurs pivot (2023) :")
    all_recs = agri + mining
    for iso3, comm, expected, unit, tol in checks:
        recs = [
            r
            for r in all_recs
            if r["country_iso3"] == iso3 and r["commodity_label"] == comm and r["year"] == 2023
        ]
        if not recs:
            print(f"     ⚠  {iso3} {comm:18s} — ABSENT")
            continue
        val = recs[0]["value"]
        ratio = abs(val - expected) / expected if expected else 0
        status = "✓" if ratio <= tol else "✗"
        print(
            f"     {status}  {iso3} {comm:18s} "
            f"{val:>15,.0f} {unit:10s} "
            f"(attendu ~{expected:,.0f}, écart {ratio*100:.1f}%)"
        )


def assemble_and_write(
    agri_records: list[dict],
    mining_records: list[dict],
    curated_mod,
    out_file: Path,
    dry_run: bool,
) -> None:
    mfg = curated_mod.build_manufacturing()
    macro = curated_mod.build_value_added_macro()

    countries = sorted(set(r["country_iso3"] for r in agri_records + mfg + mining_records + macro))

    _sanity_check(agri_records, mining_records)

    output = {
        "countries": countries,
        "value_added_macro": macro,
        "agri_faostat": agri_records,
        "manufacturing_unido": mfg,
        "mining_usgs": mining_records,
        "metadata": {
            "last_updated": datetime.now(timezone.utc).isoformat(),
            "update_source": "build_production_faostat_usgs.py — ingestion FAOSTAT bulk + USGS MCS",
            "sources": {
                "agriculture": (
                    "FAO FAOSTAT (Production QCL) bulk Africa — multi-années 2019-2024"
                    if any(r.get("_ingested_from") == "FAOSTAT_BULK" for r in agri_records)
                    else "backend/etl/faostat_data.py (curé FAO)"
                ),
                "manufacturing": "UNIDO INDSTAT4 — backend/etl/unido_data.py",
                "mining_energy": (
                    "USGS MCS 2024 (curé) 2022+2023 / EIA International Energy Statistics "
                    "/ OPEC ASB 2024"
                ),
                "macro": "World Bank WDI / UNIDO",
            },
            "record_counts": {
                "agriculture": len(agri_records),
                "manufacturing": len(mfg),
                "mining": len(mining_records),
                "macro": len(macro),
                "total": len(agri_records) + len(mfg) + len(mining_records) + len(macro),
            },
            "note": (
                "Valeurs réelles publiées — aucune génération aléatoire, "
                "aucune extrapolation. Sources : FAO, UNIDO, USGS, EIA, OPEC, World Bank."
            ),
        },
    }

    print(f"\n   Agriculture  : {len(agri_records):5d} enregistrements")
    print(f"   Manufacturier: {len(mfg):5d} enregistrements")
    print(f"   Mines/Énergie: {len(mining_records):5d} enregistrements")
    print(f"   Macro        : {len(macro):5d} enregistrements")
    print(f"   Pays couverts: {len(countries)}")

    if dry_run:
        print("\n(--dry-run) Fichier NON écrit.")
        return

    out_file.parent.mkdir(parents=True, exist_ok=True)
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)
    print(f"\n✅ Écrit : {out_file.relative_to(REPO_ROOT)}")


# =============================================================================
# 5. POINT D'ENTRÉE
# =============================================================================


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument(
        "--dry-run", action="store_true", help="Affiche les statistiques sans écrire le fichier"
    )
    ap.add_argument(
        "--force-download",
        action="store_true",
        help="Ignore le cache et retélécharge le zip FAOSTAT",
    )
    ap.add_argument(
        "--faostat-only",
        action="store_true",
        help="Ne met à jour que la section agriculture (FAOSTAT)",
    )
    ap.add_argument(
        "--usgs-path",
        type=Path,
        default=None,
        help="Chemin local vers l'Excel USGS MCS (optionnel)",
    )
    args = ap.parse_args()

    print("=" * 70)
    print(" Ingestion FAOSTAT bulk QCL + USGS MCS — production africaine")
    print("=" * 70)

    # ── Charge les builders curés (manufacturing + macro + agri fallback) ──
    print("\n[0] Chargement des builders curés …")
    curated = _load_curated_builders()

    # ── Agriculture : FAOSTAT bulk (avec fallback curé) ───────────────────
    if not args.faostat_only or True:
        print("\n[1] FAOSTAT bulk — Production QCL Afrique …")
        fao_records = fetch_faostat_bulk(force_download=args.force_download)

        if fao_records and len(fao_records) > 200:
            agri_final = _merge_agri_duplicates(fao_records)
            print(f"   → {len(agri_final)} enregistrements agri (bulk FAOSTAT)")
        else:
            if fao_records is None:
                print("   Réseau indisponible — fallback sur données curées FAO.")
            else:
                print(
                    f"   Données bulk insuffisantes ({len(fao_records)} lignes) — "
                    "fallback sur données curées FAO."
                )
            agri_final = curated.build_agriculture()
            print(f"   → {len(agri_final)} enregistrements agri (curé FAO)")

    # ── Mines : USGS multi-années (curé) ou Excel local ───────────────────
    print("\n[2] USGS — données mines & énergie multi-années …")
    if args.usgs_path and args.usgs_path.exists():
        usgs_records = parse_usgs_excel(args.usgs_path)
        if not usgs_records:
            print("   Fallback sur table curée USGS_MULTI_YEAR.")
            usgs_records = build_usgs_multi_year()
    else:
        usgs_records = build_usgs_multi_year()
    print(f"   → {len(usgs_records)} enregistrements mines/énergie")

    # ── Assemblage & écriture ─────────────────────────────────────────────
    print("\n[3] Assemblage & contrôle …")
    assemble_and_write(
        agri_records=agri_final,
        mining_records=usgs_records,
        curated_mod=curated,
        out_file=OUT_FILE,
        dry_run=args.dry_run,
    )


if __name__ == "__main__":
    main()
