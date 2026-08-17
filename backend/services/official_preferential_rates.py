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
    return payload


def _candidate_codes(clean_code: str) -> list[str]:
    if len(clean_code) in (6, 8):
        return [clean_code]
    if len(clean_code) >= 10:
        return [clean_code[:10], clean_code[:8], clean_code[:6]]
    if len(clean_code) == 9:
        return [clean_code[:8], clean_code[:6]]
    if len(clean_code) == 7:
        return [clean_code[:6]]
    return []


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

    schedule_map = dataset.get("origin_schedule_map", {})
    schedule = schedule_map.get(origin) or schedule_map.get("*")
    schedule_index = dataset.get("_schedule_indexes", {}).get(schedule or "")
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

    year_index = _offer_schedule_year(as_of_year)
    expression = line.get("annual_rate_expressions", {}).get(str(year_index))
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
