#!/usr/bin/env python3
"""
Sonde de couverture ILOSTAT — emploi par activité économique, Afrique
======================================================================
Mesure ce qu'ILOSTAT publie réellement pour les 54 pays africains, SANS rien
ingérer. À exécuter avant d'écrire la moindre ligne d'intégration, et à
rejouer avant d'élargir : une couverture annoncée n'est pas une couverture
constatée.

POURQUOI UNE SONDE PLUTÔT QU'UNE INTÉGRATION DIRECTE
-----------------------------------------------------
ILOSTAT a d'abord paru injoignable : l'endpoint ``rplumber.ilo.org`` répond
HTTP 200 mais renvoie **zéro octet**. Conclure « source bloquée » aurait été
faux — c'était le mauvais endpoint. L'interface SDMX (``sdmx.ilo.org``) sert
les données sans clé. D'où cette sonde : elle distingue une source absente
d'une source mal appelée.

CE QUE LA SOURCE APPORTE
------------------------
La colonne ``SOURCE`` de chaque observation nomme l'enquête d'origine — « LFS
- Labour Force Survey », « LFS - Enquête Nationale sur l'Emploi »… Ce sont les
enquêtes emploi des **offices nationaux de statistique**, harmonisées par
l'OIT. C'est donc une voie d'accès à la statistique nationale qui ne demande
ni de négocier avec 54 offices ni d'extraire des PDF.

RELEVÉ DU 2026-09-21 (fenêtre 2015+, dataflow DF_EMP_TEMP_SEX_ECO_NB)
----------------------------------------------------------------------
  • 48 pays sur 54 couverts ; manquants : CAF, COG, ERI, GIN, LBY, SSD
  • 6 204 observations utiles, années 2015-2025
  • 56 classifications d'activité (total, agriculture, industrie, services,
    puis détail ISIC)

CONTRAINTE RENCONTRÉE
---------------------
Une requête portant les 54 pays d'un coup est refusée (HTTP 403) : l'URL est
trop longue. D'où l'interrogation par lots.

Usage :
    python3 scripts/probe_ilostat_coverage.py            # résumé
    python3 scripts/probe_ilostat_coverage.py --json     # sortie machine
"""

from __future__ import annotations

import argparse
import collections
import csv
import io
import json
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
BACKEND_DIR = SCRIPT_DIR.parent
sys.path.insert(0, str(BACKEND_DIR))

from etl.iso3_m49 import ISO3_TO_M49  # noqa: E402

DATAFLOW = "ILO,DF_EMP_TEMP_SEX_ECO_NB"
BASE = "https://sdmx.ilo.org/rest/data"
FIRST_YEAR = 2015
# Lots de 8 pays : au-delà, l'URL dépasse ce que le service accepte (403).
CHUNK = 8
TIMEOUT_S = 180


def _fetch(batch: list[str]) -> list[dict]:
    key = "+".join(batch)
    url = f"{BASE}/{DATAFLOW}/{key}.A.EMP_TEMP_NB.SEX_T." f"?startPeriod={FIRST_YEAR}&format=csv"
    req = urllib.request.Request(url, headers={"Accept": "text/csv", "User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=TIMEOUT_S) as resp:  # nosec B310
        raw = resp.read().decode("utf-8", errors="replace")
    return list(csv.DictReader(io.StringIO(raw)))


def probe() -> dict:
    iso_codes = sorted(ISO3_TO_M49)
    rows: list[dict] = []
    failures: list[dict] = []

    for i in range(0, len(iso_codes), CHUNK):
        batch = iso_codes[i : i + CHUNK]
        try:
            rows += _fetch(batch)
        except urllib.error.HTTPError as exc:
            failures.append({"batch": batch, "error": f"HTTP {exc.code}"})
        except Exception as exc:  # pragma: no cover - dépend du réseau
            failures.append({"batch": batch, "error": type(exc).__name__})
        time.sleep(1)

    observed = [r for r in rows if r.get("OBS_VALUE") not in (None, "")]
    covered = sorted({r["REF_AREA"] for r in observed})
    years = sorted({int(r["TIME_PERIOD"]) for r in observed}) if observed else []
    eco = collections.Counter(r["ECO"] for r in observed)
    sources = collections.Counter((r.get("SOURCE") or "").strip() for r in observed)

    return {
        "dataflow": DATAFLOW,
        "first_year_requested": FIRST_YEAR,
        "observations": len(observed),
        "countries_covered": covered,
        "countries_missing": sorted(set(iso_codes) - set(covered)),
        "years": [years[0], years[-1]] if years else [],
        "economic_activity_classes": len(eco),
        "top_activity_classes": dict(eco.most_common(8)),
        "declared_sources": dict(sources.most_common(8)),
        "batch_failures": failures,
    }


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--json", action="store_true", help="Sortie JSON brute")
    args = ap.parse_args()

    result = probe()
    if args.json:
        print(json.dumps(result, indent=2, ensure_ascii=False))
        return

    total = len(ISO3_TO_M49)
    covered = len(result["countries_covered"])
    print("Sonde ILOSTAT — emploi par activité économique")
    print("=" * 52)
    print(f"  dataflow          : {result['dataflow']}")
    print(f"  observations      : {result['observations']:,}")
    print(f"  pays couverts     : {covered} / {total}")
    print(f"  pays manquants    : {', '.join(result['countries_missing']) or 'aucun'}")
    if result["years"]:
        print(f"  années            : {result['years'][0]}-{result['years'][1]}")
    print(f"  classes d'activité: {result['economic_activity_classes']}")
    print("  sources déclarées (enquêtes nationales) :")
    for name, count in list(result["declared_sources"].items())[:5]:
        print(f"      {count:6,}  {name[:60]}")
    if result["batch_failures"]:
        print(f"  ⚠ lots en échec   : {result['batch_failures']}")


if __name__ == "__main__":
    main()
