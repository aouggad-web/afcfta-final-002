#!/usr/bin/env python3
"""
Récupération UNSD (base ODD) — indicateurs manufacturiers mesurés
=================================================================
Interroge l'API publique des indicateurs ODD de l'ONU (sans clé) pour les 54
pays africains et écrit un module curé DÉTERMINISTE
``backend/etl/unsd_manufacturing_data.py``. Ce module est ensuite lu hors-ligne
par ``etl/manufacturing_unsd.py``.

POURQUOI CETTE SOURCE
---------------------
Le portail statistique d'UNIDO (stat.unido.org) répond **403** : INDSTAT n'a pas
d'endpoint de téléchargement libre. Le détail par division ISIC reste donc
inaccessible, et 32 pays sur 54 n'ont chez nous qu'une *structure estimée*.

L'UNSD republie librement, dans sa base ODD, les séries manufacturières
qu'UNIDO lui fournit comme agence dépositaire de la cible 9.2. Ce ne sont pas
les mêmes données : ce sont des **agrégats nationaux mesurés**, pas une
ventilation par division. Elles ne remplacent donc pas INDSTAT — elles
permettent de juger le manufacturier d'un pays sans dépendre de notre
estimation de structure.

SÉRIES RETENUES (couverture mesurée le 2026-09-21, fenêtre 2015+)
-----------------------------------------------------------------
  • NV_IND_MANFPC — valeur ajoutée manufacturière par habitant (USD constants
    2020) .............................................. 53 pays, 583 points
  • SL_TLF_MANF   — part de l'emploi manufacturier dans l'emploi total (%)
    ................................................... 44 pays, 166 points
  • NV_IND_TECH   — part de la moyenne et haute technologie dans la valeur
    ajoutée manufacturière (%) ......................... 26 pays, 163 points

SÉRIE ÉCARTÉE
-------------
  • NV_IND_SSIS (part des petites industries) : 2 pays, 7 points. Trop mince
    pour porter une lecture continentale ; l'ajouter donnerait l'illusion d'une
    dimension couverte. Écartée tant que la couverture ne progresse pas.

Usage (là où l'API UNSD est joignable) :

    python3 scripts/fetch_unsd_manufacturing.py

Principe : aucune valeur synthétisée. Un (pays, série, année) sans donnée
publiée est simplement omis.
"""

from __future__ import annotations

import json
import sys
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from pprint import pformat

SCRIPT_DIR = Path(__file__).resolve().parent
BACKEND_DIR = SCRIPT_DIR.parent
sys.path.insert(0, str(BACKEND_DIR))

from etl.iso3_m49 import ISO3_TO_M49  # noqa: E402

OUT_MODULE = BACKEND_DIR / "etl" / "unsd_manufacturing_data.py"

API_BASE = "https://unstats.un.org/sdgapi/v1/sdg/Series/Data"
TIMEOUT_S = 180
RETRIES = 4

# clef interne -> code de série UNSD
SERIES = {
    "mva_per_capita_usd": "NV_IND_MANFPC",
    "employment_share_pct": "SL_TLF_MANF",
    "medium_high_tech_share_pct": "NV_IND_TECH",
}

# Première année retenue. Avant 2015 les séries existent mais sortent de la
# fenêtre utile de la plateforme et tripleraient le module généré.
FIRST_YEAR = 2015

_M49_TO_ISO3 = {m49: iso3 for iso3, m49 in ISO3_TO_M49.items()}


def _get_json(url: str) -> dict:
    delay = 2.0
    last_exc: Exception = RuntimeError("unreachable")
    for _ in range(RETRIES):
        try:
            req = urllib.request.Request(url, headers={"Accept": "application/json"})
            with urllib.request.urlopen(req, timeout=TIMEOUT_S) as resp:  # nosec B310
                return json.loads(resp.read().decode("utf-8"))
        except Exception as exc:  # pragma: no cover - dépend du réseau
            last_exc = exc
            import time

            time.sleep(delay)
            delay *= 2
    raise last_exc


def _fetch_series(series_code: str) -> dict[str, dict[int, float]]:
    """{iso3: {year: value}} pour une série, tous pays africains."""
    out: dict[str, dict[int, float]] = {}
    page = 1
    while True:
        params = [("seriesCode", series_code), ("pageSize", "5000"), ("page", str(page))]
        params += [("areaCode", m49) for m49 in ISO3_TO_M49.values()]
        payload = _get_json(API_BASE + "?" + urllib.parse.urlencode(params))
        for row in payload.get("data") or []:
            iso3 = _M49_TO_ISO3.get(str(row.get("geoAreaCode")))
            value = row.get("value")
            period = row.get("timePeriodStart")
            if not iso3 or value in (None, "") or period is None:
                continue
            try:
                year = int(float(period))
                numeric = float(value)
            except (TypeError, ValueError):
                continue
            if year < FIRST_YEAR:
                continue
            out.setdefault(iso3, {})[year] = round(numeric, 2)
        if page >= (payload.get("totalPages") or 1):
            return out
        page += 1


def main() -> None:
    print(f"Récupération UNSD ODD (54 pays africains, {FIRST_YEAR}+) …")
    # {iso3: {year: {clef: valeur}}}
    data: dict[str, dict[int, dict[str, float]]] = {}
    per_series_countries: dict[str, int] = {}
    for key, series_code in SERIES.items():
        print(f"  • {key:27s} ({series_code}) …")
        by_country = _fetch_series(series_code)
        per_series_countries[key] = len(by_country)
        for iso3, year_vals in by_country.items():
            for year, value in year_vals.items():
                data.setdefault(iso3, {}).setdefault(year, {})[key] = value

    # Tri déterministe (pays, année) pour un diff stable.
    sorted_data = {
        iso3: {year: dict(sorted(data[iso3][year].items())) for year in sorted(data[iso3])}
        for iso3 in sorted(data)
    }

    n_countries = len(sorted_data)
    n_points = sum(len(v) for c in sorted_data.values() for v in c.values())
    fetched_at = datetime.now(timezone.utc).isoformat()
    coverage = ", ".join(f"{k}={v}" for k, v in sorted(per_series_countries.items()))

    header = f'''"""
Indicateurs manufacturiers UNSD (base ODD, source UNIDO) — données curées.

GÉNÉRÉ AUTOMATIQUEMENT par ``scripts/fetch_unsd_manufacturing.py`` — NE PAS
ÉDITER À LA MAIN. Régénérer là où l'API UNSD est joignable :

    python3 scripts/fetch_unsd_manufacturing.py

Valeurs RÉELLES publiées, aucune synthèse. Ce sont des agrégats NATIONAUX : ils
ne ventilent rien par division ISIC et ne remplacent donc pas INDSTAT, dont le
portail reste fermé (403).

Structure : {{iso3: {{year: {{clef: valeur}}}}}}.
Clefs : mva_per_capita_usd=NV_IND_MANFPC (USD constants 2020),
employment_share_pct=SL_TLF_MANF (%),
medium_high_tech_share_pct=NV_IND_TECH (%).

Source     : https://unstats.un.org/sdgapi/ (API ODD, sans clé)
Récupéré   : {fetched_at}
Couverture : {n_countries} pays, {n_points} points (pays×année).
Par série  : {coverage}
"""

UNSD_FETCHED_AT = "{fetched_at}"

UNSD_MANUFACTURING = '''

    OUT_MODULE.write_text(
        header + pformat(sorted_data, width=100, sort_dicts=False) + "\n", "utf-8"
    )
    print(f"\n✅ Écrit : {OUT_MODULE.relative_to(BACKEND_DIR)}")
    print(f"   {n_countries} pays, {n_points} points (pays×année).")
    print(f"   Couverture par série : {coverage}")


if __name__ == "__main__":
    main()
