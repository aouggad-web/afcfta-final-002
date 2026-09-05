"""
Données UNIDO IDSB + INDSTAT - Niveau ISIC Rev.4 4 chiffres (classe)
=====================================================================
Source: UNIDO Statistics Data Portal (https://stat.unido.org)
Fichier fourni par l'utilisateur, exporté depuis le portail UNIDO :
- IDSB (Industrial Demand-Supply Balance), ISIC Rev.4 : Output, Imports
  World, Exports World, Apparent Consumption. Nature: UNIDO_DERIVED_ESTIMATE
  (estimations dérivées par UNIDO, pas des relevés statistiques bruts).
- INDSTAT (International Yearbook of Industrial Statistics), ISIC Rev.4 :
  Establishments, Employees, Female employees, Wages and salaries, Output,
  Value added, Gross fixed capital formation. Nature: OFFICIAL_STATISTICS.

Couverture : 20 pays africains (voir `list_covered_countries()`), années
2018-2024 (filtré depuis la source d'origine 2005-2024 sur demande),
niveau ISIC 4 chiffres (isic_level=4).

Ce module charge et indexe le CSV compressé une seule fois (cache en
mémoire) et expose des fonctions d'agrégation utilisées par les routes
`production` (voir routes/production.py, endpoints `/unido/idsb/*`).
"""

import csv
import gzip
import os
from collections import defaultdict
from functools import lru_cache
from typing import Dict, List, Optional

_DATA_FILE = os.path.join(
    os.path.dirname(__file__), "..", "data", "unido", "unido_idsb_indstat_isic4_2018plus.csv.gz"
)

# indicator_code -> clé normalisée exposée dans l'API
_IDSB_INDICATORS = {
    "100": "output_usd",
    "101": "imports_world_usd",
    "104": "exports_world_usd",
    "107": "apparent_consumption_usd",
}
_INDSTAT_INDICATORS = {
    "01": "establishments",
    "04": "employees",
    "31": "female_employees",
    "05": "wages_salaries_usd",
    "14": "output_usd_official",
    "20": "value_added_usd",
    "21": "gross_fixed_capital_formation_usd",
}


@lru_cache(maxsize=1)
def _load_records() -> List[Dict]:
    """Charge et parse le CSV compressé une seule fois (mémoïsé)."""
    if not os.path.exists(_DATA_FILE):
        return []
    records = []
    with gzip.open(_DATA_FILE, mode="rt", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            try:
                value = float(row["value"])
            except (ValueError, KeyError):
                continue
            records.append(
                {
                    "dataset_code": row["dataset_code"],
                    "country_iso3": row["country_iso3"],
                    "country_name": row["country_name_en"],
                    "isic_code": row["isic_code"],
                    "isic_description": row["isic_description_en"],
                    "year": int(row["year"]),
                    "indicator_code": row["indicator_code"],
                    "indicator_name": row["indicator_name_en"],
                    "value": value,
                    "unit": row["unit"],
                    "data_nature": row["data_nature"],
                }
            )
    return records


@lru_cache(maxsize=1)
def list_covered_countries() -> List[str]:
    """Liste des pays (ISO3) couverts par ce jeu de données réel UNIDO."""
    return sorted({r["country_iso3"] for r in _load_records()})


def list_covered_countries_filtered(official_only: bool = False) -> List[str]:
    """
    Liste des pays couverts, optionally filtered.

    Args:
        official_only: If True, return only countries with OFFICIAL_STATISTICS data.
                      If False, return all countries (including those with only estimates).
    """
    records = _load_records()
    if official_only:
        return sorted(
            {r["country_iso3"] for r in records if r["data_nature"] == "OFFICIAL_STATISTICS"}
        )
    return sorted({r["country_iso3"] for r in records})


def is_country_covered(country_iso3: str) -> bool:
    return country_iso3.upper() in list_covered_countries()


def get_country_isic4_summary(country_iso3: str) -> Optional[Dict]:
    """
    Pour un pays donné, retourne par code ISIC 4 chiffres la dernière année
    disponible de chaque indicateur (IDSB: output/imports/exports/apparent
    consumption ; INDSTAT: establishments/employees/wages/value added/...).
    Données réelles UNIDO (pas d'estimation de répartition), voir le champ
    `data_nature` par indicateur pour distinguer OFFICIAL_STATISTICS de
    UNIDO_DERIVED_ESTIMATE.
    """
    iso3 = country_iso3.upper()
    records = [r for r in _load_records() if r["country_iso3"] == iso3]
    if not records:
        return None

    by_isic: Dict[str, Dict] = defaultdict(
        lambda: {"isic4": None, "isic_description": None, "indicators": {}}
    )

    for r in records:
        key = r["isic_code"]
        entry = by_isic[key]
        entry["isic4"] = key
        entry["isic_description"] = r["isic_description"]

        field_name = _IDSB_INDICATORS.get(r["indicator_code"]) or _INDSTAT_INDICATORS.get(
            r["indicator_code"]
        )
        if not field_name:
            continue

        current = entry["indicators"].get(field_name)
        if current is None or r["year"] > current["year"]:
            entry["indicators"][field_name] = {
                "value": r["value"],
                "unit": r["unit"],
                "year": r["year"],
                "data_nature": r["data_nature"],
            }

    country_name = records[0]["country_name"]
    return {
        "country_iso3": iso3,
        "country_name": country_name,
        "classification": "ISIC Rev.4 (4 chiffres / classe)",
        "source": "UNIDO Statistics Data Portal — IDSB + INDSTAT, ISIC Rev.4",
        "years_covered": "2018-2024 (filtré depuis la source d'origine 2005-2024)",
        "sectors": sorted(by_isic.values(), key=lambda x: x["isic4"]),
    }


def get_isic4_timeseries(country_iso3: str, isic4_code: str) -> Optional[Dict]:
    """Série temporelle complète (2018+) pour un pays et un code ISIC 4 chiffres donnés."""
    iso3 = country_iso3.upper()
    records = [
        r for r in _load_records() if r["country_iso3"] == iso3 and r["isic_code"] == isic4_code
    ]
    if not records:
        return None

    by_indicator: Dict[str, List[Dict]] = defaultdict(list)
    for r in records:
        field_name = _IDSB_INDICATORS.get(r["indicator_code"]) or _INDSTAT_INDICATORS.get(
            r["indicator_code"]
        )
        if not field_name:
            continue
        by_indicator[field_name].append(
            {"year": r["year"], "value": r["value"], "data_nature": r["data_nature"]}
        )

    for series in by_indicator.values():
        series.sort(key=lambda x: x["year"])

    return {
        "country_iso3": iso3,
        "isic4": isic4_code,
        "isic_description": records[0]["isic_description"],
        "series": by_indicator,
    }
