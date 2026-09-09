#!/usr/bin/env python3
"""
Récupération World Bank WDI — valeur ajoutée sectorielle & croissance PIB
========================================================================
Interroge l'API publique World Bank WDI (sans clé) pour les 54 pays africains et
écrit un module curé DÉTERMINISTE ``backend/etl/macro_wdi_data.py`` (valeurs
réelles + date de récupération). Ce module est ensuite lu hors-ligne par
``etl/macro_extended.py`` : l'enrichissement du dataset production ne dépend donc
d'aucun réseau, tout en servant des chiffres réellement publiés par le World Bank.

Indicateurs (par pays, années 2023-2024) :
  • NV.AGR.TOTL.ZS — Agriculture, valeur ajoutée (% du PIB)
  • NV.IND.TOTL.ZS — Industrie (y c. construction), valeur ajoutée (% du PIB)
  • NV.IND.MANF.ZS — Manufacturier, valeur ajoutée (% du PIB)
  • NV.SRV.TOTL.ZS — Services, valeur ajoutée (% du PIB)
  • NY.GDP.MKTP.KD.ZG — Croissance du PIB réel (% annuel)

Usage (là où l'API World Bank est joignable — bloquée par la politique d'egress
de certains bacs à sable CI/dev) :

    python3 scripts/fetch_wdi_macro.py

Principe : aucune valeur synthétisée. Un (pays, indicateur, année) sans donnée
publiée est simplement omis.
"""

from __future__ import annotations

import sys
from datetime import datetime, timezone
from pathlib import Path
from pprint import pformat

SCRIPT_DIR = Path(__file__).resolve().parent
BACKEND_DIR = SCRIPT_DIR.parent
sys.path.insert(0, str(BACKEND_DIR))

from etl.fetch_wb_gdp import AFRICA_ISO3
from etl.wb_fetch import _CHUNK_SIZE, WB_BASE, _get_json

OUT_MODULE = BACKEND_DIR / "etl" / "macro_wdi_data.py"

# clef interne -> code indicateur WDI
INDICATORS = {
    "agri": "NV.AGR.TOTL.ZS",
    "ind": "NV.IND.TOTL.ZS",
    "manuf": "NV.IND.MANF.ZS",
    "serv": "NV.SRV.TOTL.ZS",
    "gdp_growth": "NY.GDP.MKTP.KD.ZG",
}
YEARS = (2023, 2024)


def _fetch_indicator_by_year(indicator: str) -> dict[str, dict[int, float]]:
    """{iso3: {year: value}} pour les années demandées, par lots de pays."""
    out: dict[str, dict[int, float]] = {}
    for i in range(0, len(AFRICA_ISO3), _CHUNK_SIZE):
        chunk = AFRICA_ISO3[i : i + _CHUNK_SIZE]
        url = (
            f"{WB_BASE}/country/{';'.join(chunk)}/indicator/{indicator}"
            f"?format=json&per_page=20000&date={YEARS[0]}:{YEARS[-1]}"
        )
        payload = _get_json(url)
        if not isinstance(payload, list) or len(payload) < 2 or payload[1] is None:
            continue
        for row in payload[1]:
            iso3 = (row.get("countryiso3code") or "").upper()
            value = row.get("value")
            year = row.get("date")
            if not iso3 or value is None or year is None:
                continue
            year = int(year)
            if year not in YEARS:
                continue
            out.setdefault(iso3, {})[year] = round(float(value), 2)
    return out


def main() -> None:
    print("Récupération World Bank WDI (54 pays africains, 2023-2024) …")
    # {iso3: {year: {key: value}}}
    macro: dict[str, dict[int, dict[str, float]]] = {}
    for key, indicator in INDICATORS.items():
        print(f"  • {key:11s} ({indicator}) …")
        by_country = _fetch_indicator_by_year(indicator)
        for iso3, year_vals in by_country.items():
            for year, value in year_vals.items():
                macro.setdefault(iso3, {}).setdefault(year, {})[key] = value

    # Tri déterministe (pays, année) pour un diff stable.
    macro_sorted = {
        iso3: {year: dict(sorted(macro[iso3][year].items())) for year in sorted(macro[iso3])}
        for iso3 in sorted(macro)
    }

    n_countries = len(macro_sorted)
    n_points = sum(len(v) for c in macro_sorted.values() for v in c.values())
    fetched_at = datetime.now(timezone.utc).isoformat()

    header = f'''"""
Données World Bank WDI curées — valeur ajoutée sectorielle & croissance PIB.

GÉNÉRÉ AUTOMATIQUEMENT par ``scripts/fetch_wdi_macro.py`` — NE PAS ÉDITER À LA MAIN.
Régénérer là où l'API World Bank est joignable :

    python3 scripts/fetch_wdi_macro.py

Valeurs RÉELLES publiées (World Bank World Development Indicators), aucune
synthèse. Structure : {{iso3: {{year: {{indicateur: valeur_%}}}}}}.
Indicateurs : agri=NV.AGR.TOTL.ZS, ind=NV.IND.TOTL.ZS, manuf=NV.IND.MANF.ZS,
serv=NV.SRV.TOTL.ZS, gdp_growth=NY.GDP.MKTP.KD.ZG.

Source   : https://data.worldbank.org/ (API v2, sans clé)
Récupéré : {fetched_at}
Couverture : {n_countries} pays, {n_points} points (pays×année).
"""

WDI_FETCHED_AT = "{fetched_at}"

WDI_MACRO = '''

    OUT_MODULE.write_text(
        header + pformat(macro_sorted, width=100, sort_dicts=False) + "\n", "utf-8"
    )
    print(f"\n✅ Écrit : {OUT_MODULE.relative_to(BACKEND_DIR)}")
    print(f"   {n_countries} pays, {n_points} points (pays×année).")
    # Contrôle rapide
    for iso3, key in (("NGA", "ind"), ("ZAF", "agri")):
        vals = {y: macro_sorted.get(iso3, {}).get(y, {}).get(key) for y in YEARS}
        print(f"   {iso3} {key}: {vals}")


if __name__ == "__main__":
    main()
