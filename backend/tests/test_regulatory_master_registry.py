"""Contracts for the 54-country regulatory-compliance master registry."""

import json
from pathlib import Path

from services.regulatory_master_registry_service import (
    AFRICAN_COUNTRY_ISO3,
    CANONICAL_STATUSES,
    DIMENSION_STATUS_FIELDS,
    get_all_regulatory_countries,
    get_published_regulatory_countries,
    get_regulatory_country_entry,
    get_regulatory_registry,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
SCHEMA_PATH = REPO_ROOT / "data" / "regulatory-compliance" / "regulatory_registry.schema.json"


def test_master_registry_contains_exactly_54_african_countries():
    registry = get_regulatory_registry()
    assert registry["country_count"] == 54
    assert len(AFRICAN_COUNTRY_ISO3) == len(set(AFRICAN_COUNTRY_ISO3)) == 54
    assert set(registry["countries"]) == set(AFRICAN_COUNTRY_ISO3)
    assert get_all_regulatory_countries() == list(AFRICAN_COUNTRY_ISO3)


def test_initial_published_coverage_is_exactly_the_two_source_bound_pilots():
    assert get_published_regulatory_countries() == ["CIV", "COD"]
    for country in ("CIV", "COD"):
        entry = get_regulatory_country_entry(country)
        assert entry["regulatory_coverage_status"] == "PARTIAL"
        assert entry["dataset_path"] and entry["source_paths"]


def test_other_52_countries_fail_closed_without_paths_or_claimed_coverage():
    registry = get_regulatory_registry()
    unavailable = set(AFRICAN_COUNTRY_ISO3) - {"CIV", "COD"}
    assert len(unavailable) == 52
    for country in unavailable:
        entry = registry["countries"][country]
        assert entry["dataset_path"] is None
        assert entry["source_paths"] == []
        assert all(entry[field] == "NOT_AVAILABLE" for field in DIMENSION_STATUS_FIELDS)


def test_every_dimension_uses_a_canonical_status():
    for country, entry in get_regulatory_registry()["countries"].items():
        for field in DIMENSION_STATUS_FIELDS:
            assert entry[field] in CANONICAL_STATUSES, f"{country}.{field}"


def test_published_dataset_and_source_paths_exist():
    registry = get_regulatory_registry()
    for country in get_published_regulatory_countries():
        entry = registry["countries"][country]
        assert (REPO_ROOT / entry["dataset_path"]).is_file()
        for source_path in entry["source_paths"]:
            assert (REPO_ROOT / source_path).is_file(), f"{country}: {source_path}"


def test_schema_status_enum_matches_runtime_contract():
    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    assert set(schema["$defs"]["status"]["enum"]) == CANONICAL_STATUSES


def test_registry_does_not_publish_numeric_rates_or_fees():
    forbidden = {"rate", "fee", "fees", "authorized_fees"}

    def inspect(value, path="registry"):
        if isinstance(value, dict):
            for key, child in value.items():
                assert key not in forbidden, f"forbidden field: {path}.{key}"
                assert not key.endswith(("_rate", "_amount")), f"forbidden field: {path}.{key}"
                inspect(child, f"{path}.{key}")
        elif isinstance(value, list):
            for index, child in enumerate(value):
                inspect(child, f"{path}[{index}]")

    inspect(get_regulatory_registry())


def test_registry_service_returns_defensive_copies():
    first = get_regulatory_registry()
    first["countries"]["CIV"]["notes"].append("MUTATED")
    assert "MUTATED" not in get_regulatory_registry()["countries"]["CIV"]["notes"]


def test_unknown_country_remains_unavailable():
    assert get_regulatory_country_entry("FRA") is None
