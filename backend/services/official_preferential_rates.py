"""Fail-closed access to reviewed official preferential tariff schedules."""

from __future__ import annotations

import gzip
import json
import re
from datetime import date
from functools import lru_cache
from pathlib import Path
from typing import Optional

DATA_DIR = Path(__file__).resolve().parents[1] / "data" / "official_preferential"
DATASETS = {
    "ZAF": DATA_DIR / "ZAF_afcfta_2026-08-06.json.gz",
    "EAC": DATA_DIR / "EAC_afcfta_etariff_2026-08-17.json.gz",
    "ECOWAS": DATA_DIR / "ECOWAS_afcfta_etariff_2026-08-17.json.gz",
    "CEMAC": DATA_DIR / "CEMAC_afcfta_etariff_2026-08-17.json.gz",
    "EGY": DATA_DIR / "EGY_afcfta_etariff_2026-08-17.json.gz",
    "TUN": DATA_DIR / "TUN_afcfta_etariff_2026-08-17.json.gz",
    "ETH": DATA_DIR / "ETH_afcfta_etariff_2026-08-17.json.gz",
    "ZMB": DATA_DIR / "ZMB_afcfta_etariff_2026-08-17.json.gz",
}

ISO3_TO_ISO2 = {
    "AGO": "AO",
    "BFA": "BF",
    "BDI": "BI",
    "BEN": "BJ",
    "BWA": "BW",
    "CAF": "CF",
    "CIV": "CI",
    "CMR": "CM",
    "COD": "CD",
    "COG": "CG",
    "COM": "KM",
    "CPV": "CV",
    "DJI": "DJ",
    "DZA": "DZ",
    "EGY": "EG",
    "ERI": "ER",
    "ETH": "ET",
    "GAB": "GA",
    "GHA": "GH",
    "GIN": "GN",
    "GMB": "GM",
    "GNB": "GW",
    "GNQ": "GQ",
    "KEN": "KE",
    "LBR": "LR",
    "LBY": "LY",
    "LSO": "LS",
    "MAR": "MA",
    "MDG": "MG",
    "MLI": "ML",
    "MOZ": "MZ",
    "MRT": "MR",
    "MUS": "MU",
    "MWI": "MW",
    "NAM": "NA",
    "NER": "NE",
    "NGA": "NG",
    "RWA": "RW",
    "SDN": "SD",
    "SEN": "SN",
    "SLE": "SL",
    "SOM": "SO",
    "SSD": "SS",
    "STP": "ST",
    "SWZ": "SZ",
    "SYC": "SC",
    "TCD": "TD",
    "TGO": "TG",
    "TUN": "TN",
    "TZA": "TZ",
    "UGA": "UG",
    "ZAF": "ZA",
    "ZMB": "ZM",
    "ZWE": "ZW",
}


@lru_cache(maxsize=None)
def _load_dataset(dataset_code: str) -> Optional[dict]:
    path = DATASETS.get(dataset_code)
    if path is None or not path.exists():
        return None
    if path.suffix == ".gz":
        payload = json.loads(gzip.decompress(path.read_bytes()).decode("utf-8"))
    else:
        payload = json.loads(path.read_text(encoding="utf-8"))
    if "lines" in payload:
        payload["_index"] = {line["hs_code"]: line for line in payload["lines"]}
    else:
        payload["_schedule_indexes"] = {
            schedule: {line["hs_code"]: line for line in lines}
            for schedule, lines in payload.get("schedules", {}).items()
        }
        payload["_published_lengths"] = {
            schedule: sorted({len(code) for code in index}, reverse=True)
            for schedule, index in payload["_schedule_indexes"].items()
        }
    return payload


def _candidate_codes(clean_code: str) -> list[str]:
    # Exact national line only. A broader HS6/HS8 parent can contain several
    # national tariff lines with different concessions and must never be used
    # as an implicit fallback. This also preserves Tunisia's 9-digit lines.
    return [clean_code] if 6 <= len(clean_code) <= 12 else []


def _parse_offer_rate(expression: Optional[str]) -> Optional[float]:
    value = (expression or "").strip().lower().replace(",", ".")
    if value in {"free", "exempt", "zero"}:
        return 0.0
    if not re.fullmatch(r"\d+(?:\.\d+)?%?", value):
        return None
    return float(value.rstrip("%"))


def _offer_schedule_year(as_of_year: int) -> int:
    # Category A annual column 1 began on 1 January 2021.
    return max(1, as_of_year - 2020)


def _offer_schedule_index(dataset: dict, origin: str) -> tuple[Optional[str], Optional[dict]]:
    """Return the (schedule id, line index) an origin is served by."""
    schedule_map = dataset.get("origin_schedule_map", {})
    # New snapshots store ISO3 keys. Keep ISO2 lookup for the already archived
    # EGY/TUN snapshots collected from the e-Tariff Book regions endpoint.
    schedule = (
        schedule_map.get(origin)
        or schedule_map.get(ISO3_TO_ISO2.get(origin, ""))
        or schedule_map.get("*")
    )
    return schedule, dataset.get("_schedule_indexes", {}).get(schedule or "")


def _resolve_offer_line(
    dataset: dict,
    country: str,
    origin: str,
    clean_code: str,
    as_of_year: int,
) -> Optional[dict]:
    # A PSTC snapshot is intentionally tagged OFFER_ONLY. Reaching this
    # function means the independent implementation registry has already
    # approved the exact destination/origin corridor.
    if (
        dataset.get("legal_effect_status") != "OFFER_ONLY"
        or dataset.get("execution_authorized") is not False
    ):
        return None

    schedule, schedule_index = _offer_schedule_index(dataset, origin)
    if schedule_index is None:
        return None
    line = next(
        (
            schedule_index[candidate]
            for candidate in _candidate_codes(clean_code)
            if candidate in schedule_index
        ),
        None,
    )
    if line is None:
        return None

    annual_expressions = line.get("annual_rate_expressions", {})
    published_years = sorted(int(year) for year in annual_expressions if str(year).isdigit())
    if not published_years:
        return None
    requested_year = _offer_schedule_year(as_of_year)
    # After the phase-down calendar ends, the final published concession
    # remains the applicable tier; never fall back to NOT_AVAILABLE or 0.
    year_index = min(requested_year, published_years[-1])
    expression = annual_expressions.get(str(year_index))
    rate = _parse_offer_rate(expression)
    display_expression = (
        f"{expression}%" if expression and not expression.endswith("%") else expression
    )
    return {
        **line,
        "country_iso3": country,
        "agreement": dataset["agreement"],
        "source_title": dataset["source_title"],
        "source_date": dataset.get("source_revision_date") or dataset.get("collected_at"),
        "source_url": dataset["source_url"],
        "source_api_url": dataset["source_api_url"],
        "source_column": f"year{year_index}",
        "schedule": schedule,
        "schedule_year": year_index,
        "rate_expression": display_expression,
        "ad_valorem_rate_pct": rate,
        "rate_kind": "AD_VALOREM" if rate is not None else "NOT_AVAILABLE",
        "calculation_status": "CALCULABLE" if rate is not None else "NOT_AVAILABLE",
    }


def resolve_published_offer_rate(
    destination_iso3: str,
    hs_code: str,
    origin_iso3: Optional[str] = None,
    *,
    as_of_year: Optional[int] = None,
) -> Optional[dict]:
    """Resolve the officially published AfCFTA offer line, for display only.

    This deliberately bypasses the implementation registry's applicability
    gate: it answers "what does the official AfCFTA e-Tariff Book publish for
    this line?", never "what duty is legally payable?". The returned rate is
    therefore INFORMATIONAL — callers must never use it to compute a duty, a
    total or a saving. It exists so a published offer can be surfaced as
    « à vérifier avec les douanes locales » instead of being silently dropped,
    which would look identical to a total absence of source.

    Returns None when the destination has no archived offer dataset, or when
    the requested code cannot be matched. When the requested code is finer
    than the published offer granularity (e.g. an 11-digit national line
    against an 8-digit offer), the code is truncated to the published level
    — the sub-position is included in that offer line. The reverse (coarser
    request resolved to a finer offer sub-position) is never attempted.
    """
    from services.zlecaf_implementation_registry import (
        APPLIED,
        OFFER_DATASETS,
        implementation_record,
    )

    country = (destination_iso3 or "").upper().strip()
    origin = (origin_iso3 or "").upper().strip()
    clean_code = re.sub(r"\D", "", hs_code or "")

    record = implementation_record(country)
    if record is not None:
        # An APPLIED corridor is served by the legally usable resolver above;
        # this display-only path must not shadow it.
        if record.status == APPLIED:
            return None
        dataset_code = record.tariff_dataset
    else:
        dataset_code = OFFER_DATASETS.get(country)

    if not dataset_code:
        return None

    dataset = _load_dataset(dataset_code)
    if dataset is None:
        return None

    # Granularité pilotée par la source, jamais par le code demandé :
    #  * pays dont l'offre est collectée en lignes nationales (8 à 10 chiffres) :
    #    ces lignes sont appliquées rigoureusement ;
    #  * pays dont l'offre n'existe qu'au SH6 (barèmes des groupements
    #    économiques régionaux) : le SH6 EST la granularité officielle.
    year = as_of_year or date.today().year
    exact = _resolve_offer_line(dataset, country, origin, clean_code, year)
    if exact is not None:
        return exact

    # Le code demandé peut être PLUS FIN que l'offre publiée (ex. ligne
    # nationale éthiopienne 01012100000 pour une offre publiée en 01012100,
    # tunisienne 01012100015 pour 010121000, zambienne 0101210010 pour
    # 01012100). Lire l'offre au niveau où elle est publiée n'invente rien :
    # la sous-position demandée est incluse dans cette ligne d'offre.
    #
    # L'inverse reste INTERDIT : jamais descendre d'un SH6 vers l'une de ses
    # sous-positions d'offre, qui portent des concessions différentes — on ne
    # choisirait alors qu'arbitrairement. On ne tronque donc que vers le bas,
    # et jamais en-deçà du SH6.
    schedule, schedule_index = _offer_schedule_index(dataset, origin)
    if not schedule_index:
        return None

    published_lengths = dataset.get("_published_lengths", {}).get(schedule, [])
    for length in published_lengths:
        if 6 <= length < len(clean_code):
            parent = _resolve_offer_line(dataset, country, origin, clean_code[:length], year)
            if parent is not None:
                return {**parent, "requested_hs_code": clean_code}
    return None


def resolve_official_preferential_rate(
    destination_iso3: str,
    hs_code: str,
    origin_iso3: Optional[str] = None,
    *,
    as_of_year: Optional[int] = None,
) -> Optional[dict]:
    """Resolve an exact legally usable line; fail closed for offers alone."""
    country = (destination_iso3 or "").upper().strip()
    origin = (origin_iso3 or "").upper().strip()
    clean_code = re.sub(r"\D", "", hs_code or "")
    dataset_code = country

    if country != "ZAF":
        from services.zlecaf_implementation_registry import implementation_decision

        decision = implementation_decision(country, origin)
        if not decision["applied"]:
            return None
        dataset_code = decision["tariff_dataset"]

    dataset = _load_dataset(dataset_code)
    if dataset is None:
        return None

    if dataset_code != "ZAF":
        return _resolve_offer_line(
            dataset,
            country,
            origin,
            clean_code,
            as_of_year or date.today().year,
        )

    line = next(
        (
            dataset["_index"][candidate]
            for candidate in _candidate_codes(clean_code)
            if candidate in dataset["_index"]
        ),
        None,
    )
    if line is None:
        return None

    return {
        **line,
        "country_iso3": country,
        "agreement": dataset["agreement"],
        "source_title": dataset["source_title"],
        "source_date": dataset["source_date"],
        "source_url": dataset["source_url"],
        "source_pdf_url": dataset["source_pdf_url"],
        "source_pdf_sha256": dataset["source_pdf_sha256"],
        "source_column": dataset["source_column"],
    }
