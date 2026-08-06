"""Fail-closed master registry for African regulatory-compliance coverage."""

import copy
import json
from functools import lru_cache
from pathlib import Path
from typing import Any, Dict, List, Optional

REPO_ROOT = Path(__file__).resolve().parents[2]
REGISTRY_PATH = REPO_ROOT / "data" / "regulatory-compliance" / "country_registry.json"

AFRICAN_COUNTRY_ISO3 = (
    "DZA", "AGO", "BEN", "BWA", "BFA", "BDI", "CPV", "CMR", "CAF", "TCD",
    "COM", "COD", "COG", "CIV", "DJI", "EGY", "GNQ", "ERI", "SWZ", "ETH",
    "GAB", "GMB", "GHA", "GIN", "GNB", "KEN", "LSO", "LBR", "LBY", "MDG",
    "MWI", "MLI", "MRT", "MUS", "MAR", "MOZ", "NAM", "NER", "NGA", "RWA",
    "STP", "SEN", "SYC", "SLE", "SOM", "ZAF", "SSD", "SDN", "TZA", "TGO",
    "TUN", "UGA", "ZMB", "ZWE",
)

CANONICAL_STATUSES = {
    "DOCUMENTED", "PARTIAL", "UNVERIFIED", "NOT_AVAILABLE",
    "NOT_APPLICABLE", "REVIEW_REQUIRED",
}

DIMENSION_STATUS_FIELDS = (
    "regulatory_coverage_status", "mandate_status", "fees_status",
    "products_hs_status", "exemptions_status", "transport_status",
    "platform_status", "delivered_document_status",
)


def _validate_country_entry(country: str, entry: Dict[str, Any]) -> None:
    required = set(DIMENSION_STATUS_FIELDS) | {"dataset_path", "source_paths", "notes"}
    missing = sorted(required - set(entry))
    if missing:
        raise ValueError(f"{country} registry entry missing fields: {', '.join(missing)}")

    for field in DIMENSION_STATUS_FIELDS:
        if entry[field] not in CANONICAL_STATUSES:
            raise ValueError(f"{country}.{field} uses non-canonical status {entry[field]}")

    coverage = entry["regulatory_coverage_status"]
    dataset_path = entry["dataset_path"]
    source_paths = entry["source_paths"]
    if coverage == "NOT_AVAILABLE":
        if dataset_path is not None or source_paths:
            raise ValueError(f"{country} publishes paths while coverage is NOT_AVAILABLE")
        return

    if not dataset_path or not source_paths:
        raise ValueError(f"{country} claims coverage without dataset and source paths")
    if not (REPO_ROOT / dataset_path).is_file():
        raise ValueError(f"{country} dataset path does not exist: {dataset_path}")
    for source_path in source_paths:
        if not (REPO_ROOT / source_path).is_file():
            raise ValueError(f"{country} source path does not exist: {source_path}")


@lru_cache(maxsize=1)
def _load_registry() -> Dict[str, Any]:
    registry = json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))
    countries = registry.get("countries", {})
    if registry.get("country_count") != 54:
        raise ValueError("Master registry country_count must remain 54")
    if set(countries) != set(AFRICAN_COUNTRY_ISO3):
        raise ValueError("Master registry must contain exactly the 54 African ISO3 codes")
    for country, entry in countries.items():
        if not isinstance(entry, dict):
            raise ValueError(f"{country} registry entry is not an object")
        _validate_country_entry(country, entry)
    return registry


def get_regulatory_registry() -> Dict[str, Any]:
    return copy.deepcopy(_load_registry())


def get_regulatory_country_entry(country_iso3: str) -> Optional[Dict[str, Any]]:
    entry = _load_registry()["countries"].get(country_iso3.upper())
    return copy.deepcopy(entry) if entry is not None else None


def get_all_regulatory_countries() -> List[str]:
    return list(AFRICAN_COUNTRY_ISO3)


def get_published_regulatory_countries() -> List[str]:
    countries = _load_registry()["countries"]
    return sorted(
        country
        for country, entry in countries.items()
        if entry["regulatory_coverage_status"] != "NOT_AVAILABLE"
    )
