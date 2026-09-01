"""Fail-closed master registry for African regulatory-compliance coverage."""

import copy
import json
from functools import lru_cache
from pathlib import Path
from typing import Any, Dict, List, Optional

REPO_ROOT = Path(__file__).resolve().parents[2]
RESOLVED_REPO_ROOT = REPO_ROOT.resolve()
REGISTRY_PATH = REPO_ROOT / "data" / "regulatory-compliance" / "country_registry.json"

AFRICAN_COUNTRY_ISO3 = (
    "DZA",
    "AGO",
    "BEN",
    "BWA",
    "BFA",
    "BDI",
    "CPV",
    "CMR",
    "CAF",
    "TCD",
    "COM",
    "COD",
    "COG",
    "CIV",
    "DJI",
    "EGY",
    "GNQ",
    "ERI",
    "SWZ",
    "ETH",
    "GAB",
    "GMB",
    "GHA",
    "GIN",
    "GNB",
    "KEN",
    "LSO",
    "LBR",
    "LBY",
    "MDG",
    "MWI",
    "MLI",
    "MRT",
    "MUS",
    "MAR",
    "MOZ",
    "NAM",
    "NER",
    "NGA",
    "RWA",
    "STP",
    "SEN",
    "SYC",
    "SLE",
    "SOM",
    "ZAF",
    "SSD",
    "SDN",
    "TZA",
    "TGO",
    "TUN",
    "UGA",
    "ZMB",
    "ZWE",
)

CANONICAL_STATUSES = {
    "DOCUMENTED",
    "PARTIAL",
    "UNVERIFIED",
    "NOT_AVAILABLE",
    "NOT_APPLICABLE",
    "REVIEW_REQUIRED",
}

DIMENSION_STATUS_FIELDS = (
    "regulatory_coverage_status",
    "mandate_status",
    "fees_status",
    "products_hs_status",
    "exemptions_status",
    "transport_status",
    "platform_status",
    "delivered_document_status",
)


def _resolve_repo_path(country: str, label: str, relative_path: str) -> Path:
    """Resolve a registry-declared path, rejecting absolute paths and traversal outside the repo."""

    resolved = (REPO_ROOT / relative_path).resolve()
    try:
        resolved.relative_to(RESOLVED_REPO_ROOT)
    except ValueError as exc:
        raise ValueError(f"{country} {label} resolves outside repository: {relative_path}") from exc
    return resolved


def _check_path_country_field(country: str, label: str, resolved_path: Path) -> None:
    """Reject a source-bound JSON file whose own 'country' field mismatches the registry key."""

    if resolved_path.suffix != ".json":
        return
    try:
        payload = json.loads(resolved_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f"{country} {label} {resolved_path} is not readable JSON") from exc
    declared_country = payload.get("country") if isinstance(payload, dict) else None
    if declared_country is not None and declared_country != country:
        raise ValueError(
            f"{country} {label} {resolved_path} belongs to {declared_country}, not {country}"
        )


def _validate_country_entry(country: str, entry: Dict[str, Any]) -> None:
    required = set(DIMENSION_STATUS_FIELDS) | {"dataset_path", "source_paths", "notes"}
    missing = sorted(required - set(entry))
    if missing:
        raise ValueError(f"{country} registry entry missing fields: {', '.join(missing)}")
    extra = sorted(set(entry) - required)
    if extra:
        raise ValueError(f"{country} registry entry has unexpected fields: {', '.join(extra)}")

    for field in DIMENSION_STATUS_FIELDS:
        if entry[field] not in CANONICAL_STATUSES:
            raise ValueError(f"{country}.{field} uses non-canonical status {entry[field]}")

    dataset_path = entry["dataset_path"]
    source_paths = entry["source_paths"]
    notes = entry["notes"]
    if dataset_path is not None and not isinstance(dataset_path, str):
        raise ValueError(f"{country}.dataset_path must be a string or null")
    if not isinstance(source_paths, list) or not all(
        isinstance(item, str) for item in source_paths
    ):
        raise ValueError(f"{country}.source_paths must be a list of strings")
    if not isinstance(notes, list) or not all(isinstance(item, str) for item in notes):
        raise ValueError(f"{country}.notes must be a list of strings")

    coverage = entry["regulatory_coverage_status"]
    if coverage == "NOT_AVAILABLE":
        if dataset_path is not None or source_paths:
            raise ValueError(f"{country} publishes paths while coverage is NOT_AVAILABLE")
        undocumented = [
            field for field in DIMENSION_STATUS_FIELDS if entry[field] != "NOT_AVAILABLE"
        ]
        if undocumented:
            raise ValueError(
                f"{country} claims {', '.join(undocumented)} while overall coverage is "
                "NOT_AVAILABLE"
            )
        return

    if not dataset_path or not source_paths:
        raise ValueError(f"{country} claims coverage without dataset and source paths")
    resolved_dataset_path = _resolve_repo_path(country, "dataset_path", dataset_path)
    if not resolved_dataset_path.is_file():
        raise ValueError(f"{country} dataset path does not exist: {dataset_path}")
    _check_path_country_field(country, "dataset_path", resolved_dataset_path)
    for source_path in source_paths:
        resolved_source_path = _resolve_repo_path(country, "source_path", source_path)
        if not resolved_source_path.is_file():
            raise ValueError(f"{country} source path does not exist: {source_path}")
        _check_path_country_field(country, "source_path", resolved_source_path)


def _require_non_empty_string(registry: Dict[str, Any], field: str) -> None:
    value = registry.get(field)
    if not isinstance(value, str) or not value:
        raise ValueError(f"Master registry {field} must be a non-empty string")


@lru_cache(maxsize=1)
def _load_registry() -> Dict[str, Any]:
    registry = json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))
    if registry.get("schema_version") != "1.0":
        raise ValueError("Master registry schema_version must be '1.0'")
    _require_non_empty_string(registry, "as_of")
    _require_non_empty_string(registry, "disclaimer")
    if registry.get("country_count") != 54:
        raise ValueError("Master registry country_count must remain 54")
    countries = registry.get("countries")
    if not isinstance(countries, dict):
        raise ValueError("Master registry countries must be an object")
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
