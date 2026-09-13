#!/usr/bin/env python3
"""Snapshot official AfCFTA e-Tariff Book schedules line by line.

Only the production service behind https://etariff.au-afcfta.org is used.
The QA endpoint is intentionally rejected because it contains test records.
"""

from __future__ import annotations

import argparse
import concurrent.futures
import gzip
import json
import re
import time
import urllib.request
from collections import Counter
from pathlib import Path

PUBLIC_URL = "https://etariff.au-afcfta.org/"
API_URL = "https://prod-afcfta-api.azurewebsites.net"
SEARCH_URL = f"{API_URL}/TariffSchedule/TariffScheduleSearch"
REGIONS_URL = f"{API_URL}/Region/GetRegions"
# Date des instantanés déjà publiés. Elle reste la valeur par défaut pour
# reproduire ces fichiers à l'identique ; toute nouvelle collecte doit passer
# --collected-at, sinon le fichier porterait une date de collecte fausse.
COLLECTED_AT = "2026-08-17"

# One representative importing country exposes each customs-union schedule.
# Egypt and Tunisia publish two schedules selected by the exporting country.
OFFERS = {
    "EAC": {"destination": "KE", "region": "EAC", "origins": {"1": "DZ"}},
    "ECOWAS": {"destination": "GH", "region": "ECOWAS", "origins": {"1": "DZ"}},
    "CEMAC": {"destination": "CM", "region": "CEMAC", "origins": {"1": "DZ"}},
    "EGY": {"destination": "EG", "region": "EG", "origins": {"1": "DZ", "2": "RW"}},
    "TUN": {"destination": "TN", "region": "TN", "origins": {"1": "DZ", "2": "RW"}},
    "ETH": {"destination": "ET", "region": "ET", "origins": {"1": "DZ"}},
    "ZMB": {"destination": "ZM", "region": "ZM", "origins": {"1": "DZ"}},
    # Maroc et Zimbabwe publient un barème dans l'e-Tariff Book sans figurer
    # dans les instantanés du dépôt. Sélection du barème vérifiée sur l'API :
    # pour MA, une origine DZ rend le barème 1 et RW le barème 2 — même schéma
    # que l'Égypte et la Tunisie ; ZW n'en publie qu'un.
    "MAR": {"destination": "MA", "region": "MA", "origins": {"1": "DZ", "2": "RW"}},
    "ZWE": {"destination": "ZW", "region": "ZW", "origins": {"1": "DZ"}},
}

AFRICAN_ISO2_TO_ISO3 = {
    "AO": "AGO",
    "BF": "BFA",
    "BI": "BDI",
    "BJ": "BEN",
    "BW": "BWA",
    "CD": "COD",
    "CF": "CAF",
    "CG": "COG",
    "CI": "CIV",
    "CM": "CMR",
    "CV": "CPV",
    "DJ": "DJI",
    "DZ": "DZA",
    "EG": "EGY",
    "ER": "ERI",
    "ET": "ETH",
    "GA": "GAB",
    "GH": "GHA",
    "GM": "GMB",
    "GN": "GIN",
    "GQ": "GNQ",
    "GW": "GNB",
    "KE": "KEN",
    "KM": "COM",
    "LR": "LBR",
    "LS": "LSO",
    "LY": "LBY",
    "MA": "MAR",
    "MG": "MDG",
    "ML": "MLI",
    "MR": "MRT",
    "MU": "MUS",
    "MW": "MWI",
    "MZ": "MOZ",
    "NA": "NAM",
    "NE": "NER",
    "NG": "NGA",
    "RW": "RWA",
    "SC": "SYC",
    "SD": "SDN",
    "SL": "SLE",
    "SN": "SEN",
    "SO": "SOM",
    "SS": "SSD",
    "ST": "STP",
    "SZ": "SWZ",
    "TD": "TCD",
    "TG": "TGO",
    "TN": "TUN",
    "TZ": "TZA",
    "UG": "UGA",
    "ZA": "ZAF",
    "ZM": "ZMB",
    "ZW": "ZWE",
}


def _request_json(url: str, payload: dict | None = None, attempts: int = 4):
    data = json.dumps(payload).encode("utf-8") if payload is not None else None
    headers = {"Content-Type": "application/json", "User-Agent": "AfCFTA-data-pipeline/1.0"}
    for attempt in range(attempts):
        try:
            request = urllib.request.Request(url, data=data, headers=headers)
            with urllib.request.urlopen(request, timeout=90) as response:
                return json.load(response)
        except Exception:
            if attempt == attempts - 1:
                raise
            time.sleep(2**attempt)


def _search_payload(origin: str, destination: str, search_text: str) -> dict:
    return {
        "countryFrom": origin,
        "countryTo": destination,
        "searchText": search_text,
        "afCFTACategory": None,
        "stepDownTimeFrame": None,
        "yearView": None,
        "languageCode": "en",
    }


def _collect_schedule(destination: str, region: str, origin: str, schedule: str) -> list[dict]:
    def collect_chapter(chapter: int):
        return _request_json(SEARCH_URL, _search_payload(origin, destination, f"{chapter:02d}"))

    rows_by_code = {}
    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        for response_rows in executor.map(collect_chapter, range(1, 100)):
            for row in response_rows:
                if row.get("isHeading") or row.get("regionCode") != region:
                    continue
                if str(row.get("schedule") or "1") != schedule:
                    continue
                clean_code = "".join(ch for ch in str(row.get("tariffCode", "")) if ch.isdigit())
                if len(clean_code) < 6:
                    continue
                normalized = {
                    "hs_code": clean_code,
                    "description": row.get("tariffDescription", "").strip(),
                    "category": (row.get("afCFTACategory") or "").strip() or None,
                    "time_frame_years": row.get("timeFrame"),
                    "mfn_rate_expression": str(row.get("mfnRate") or "").strip() or None,
                    "annual_rate_expressions": {
                        str(year): str(row.get(f"year{year}") or "").strip()
                        for year in range(1, 14)
                        if str(row.get(f"year{year}") or "").strip()
                    },
                }
                previous = rows_by_code.get(clean_code)
                if previous is not None and previous != normalized:
                    raise ValueError(f"Conflicting duplicate {region}/{schedule}/{clean_code}")
                rows_by_code[clean_code] = normalized

    rows = sorted(rows_by_code.values(), key=lambda row: row["hs_code"])
    # Most published PSTCs still cover Category A (~90% of the national
    # nomenclature), so a valid official schedule can be slightly below 5,000
    # lines.  Below 4,000 indicates a truncated chapter sweep.
    if len(rows) < 4000:
        raise ValueError(f"Suspiciously small {region} schedule {schedule}: {len(rows)} lines")
    return rows


def _origin_schedule_map(destination: str, region: str, country_codes: list[str]) -> dict:
    def probe(origin: str):
        try:
            rows = _request_json(SEARCH_URL, _search_payload(origin, destination, "010121"))
        except Exception:
            # The production API returns HTTP 500 for a few country pairs that
            # have no selectable reciprocal schedule.  Absence remains closed.
            return origin, None
        schedules = {
            str(row.get("schedule") or "1")
            for row in rows
            if not row.get("isHeading") and row.get("regionCode") == region
        }
        return origin, next(iter(schedules)) if len(schedules) == 1 else None

    mapping = {}
    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        for origin, schedule in executor.map(probe, country_codes):
            if schedule:
                iso3 = AFRICAN_ISO2_TO_ISO3.get(origin.upper())
                if iso3 is None:
                    raise ValueError(f"Unknown African ISO2 origin returned by API: {origin}")
                mapping[iso3] = schedule
    return dict(sorted(mapping.items()))


def _localized(node: list | None) -> dict:
    """Textes multilingues de l'API, réduits aux langues utiles."""
    if not node:
        return {}
    out = {}
    for item in node:
        lang = str(item.get("language") or "").strip()
        text = str(item.get("text") or "").strip()
        if lang in {"en", "fr"} and text:
            out[lang] = text
    return out


def collect_offer(offer_code: str, regions: list[dict], collected_at: str = COLLECTED_AT) -> dict:
    config = OFFERS[offer_code]
    schedules = {
        schedule: _collect_schedule(config["destination"], config["region"], origin, schedule)
        for schedule, origin in config["origins"].items()
    }
    if len(config["origins"]) == 1:
        origin_map = {"*": next(iter(config["origins"]))}
    else:
        country_codes = sorted(region["code"] for region in regions if not region.get("isRegion"))
        origin_map = _origin_schedule_map(config["destination"], config["region"], country_codes)
    region_metadata = next(region for region in regions if region["code"] == config["region"])
    return {
        "schema_version": 1,
        "offer_code": offer_code,
        "agreement": "AfCFTA",
        # Verdict du dépôt, et non celui de l'Union africaine : même adopté et
        # inclus dans une directive ministérielle, un barème provisoire ne suffit
        # pas à liquider un droit. L'effet en droit interne, la date d'entrée en
        # vigueur, la réciprocité bilatérale et la preuve d'origine restent des
        # conditions distinctes. La déclaration de la source figure à part, dans
        # `source_status_statement`.
        "legal_effect_status": "OFFER_ONLY",
        "execution_authorized": False,
        "execution_warning": (
            "Do not calculate from this dataset without a separately reviewed "
            "domestic implementation instrument and an accepted origin country."
        ),
        "source_title": "AfCFTA e-Tariff Book — Tariff Concession Schedule",
        # Ce que l'Union africaine déclare elle-même du statut de ce barème, mot
        # pour mot. Sans cela, le fichier ne portait que le verdict du dépôt
        # (`legal_effect_status`) et non la position de la source : or l'UA
        # n'écrit pas « offre en attente » mais « offre adoptée et incluse dans
        # la directive ministérielle relative à la liste provisoire de
        # concessions tarifaires ». La nuance est juridique et doit rester
        # lisible sans réinterroger l'API.
        "source_status_statement": _localized(region_metadata.get("overview")),
        "schedule_names": {
            str(item.get("code") or ""): _localized(item.get("name"))
            for item in (region_metadata.get("schedules") or [])
        },
        "source_is_ldc": region_metadata.get("isLDC"),
        "source_url": PUBLIC_URL,
        "source_api_url": SEARCH_URL,
        "collected_at": collected_at,
        "source_revision_date": region_metadata.get("lastRevisionDate"),
        "hs_version": region_metadata.get("hsVersion") or None,
        "destination_query_code": config["destination"],
        "region_code": config["region"],
        "origin_schedule_map": origin_map,
        "schedule_line_counts": {schedule: len(lines) for schedule, lines in schedules.items()},
        "category_counts": {
            schedule: dict(
                sorted(Counter(line["category"] or "UNSPECIFIED" for line in lines).items())
            )
            for schedule, lines in schedules.items()
        },
        "schedules": schedules,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("output_dir", type=Path)
    parser.add_argument("offers", nargs="*", choices=sorted(OFFERS), default=sorted(OFFERS))
    parser.add_argument(
        "--collected-at",
        default=COLLECTED_AT,
        help=(
            "Date de collecte (AAAA-MM-JJ) portée par le fichier et ses "
            "métadonnées. Par défaut la date des instantanés existants, pour les "
            "reproduire ; passer la date du jour pour toute nouvelle collecte."
        ),
    )
    args = parser.parse_args()

    if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", args.collected_at):
        raise SystemExit(f"--collected-at attend AAAA-MM-JJ, reçu {args.collected_at!r}")

    regions = _request_json(REGIONS_URL)
    if any(region.get("code") == "asareb" for region in regions):
        raise RuntimeError("QA/test data detected: refusing to publish")

    args.output_dir.mkdir(parents=True, exist_ok=True)
    for offer_code in args.offers:
        dataset = collect_offer(offer_code, regions, args.collected_at)
        output = args.output_dir / f"{offer_code}_afcfta_etariff_{args.collected_at}.json.gz"
        serialized = (json.dumps(dataset, ensure_ascii=False, separators=(",", ":")) + "\n").encode(
            "utf-8"
        )
        output.write_bytes(gzip.compress(serialized, compresslevel=9, mtime=0))
        print(offer_code, dataset["schedule_line_counts"], output, flush=True)


if __name__ == "__main__":
    main()
