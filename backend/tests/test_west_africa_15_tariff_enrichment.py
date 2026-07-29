import json
from pathlib import Path

import pytest
from services import tariff_enrichment_service
from services.tariff_enrichment_service import (
    get_country_enrichment,
    get_supported_enrichment_countries,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
REGISTRY_PATH = REPO_ROOT / "data" / "west-africa-15" / "tariff_enrichment_registry.json"
WEST_AFRICA_15 = {
    "BEN",
    "BFA",
    "CPV",
    "GHA",
    "GIN",
    "GMB",
    "GNB",
    "LBR",
    "MLI",
    "MRT",
    "NER",
    "NGA",
    "SEN",
    "SLE",
    "TGO",
}
REGIONAL_18 = {
    "BDI",
    "BWA",
    "CAF",
    "CMR",
    "COD",
    "COG",
    "GAB",
    "GNQ",
    "KEN",
    "LSO",
    "NAM",
    "RWA",
    "SSD",
    "SWZ",
    "TCD",
    "TZA",
    "UGA",
    "ZAF",
}
ALGERIA_ACTIVE_3 = {"EGY", "MUS", "TUN"}
CANONICAL_STATUSES = {
    "DOCUMENTED",
    "PARTIAL",
    "UNVERIFIED",
    "NOT_AVAILABLE",
    "NOT_APPLICABLE",
}


def _registry():
    return json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))


def _tariff_lines(country):
    data = json.loads(
        (REPO_ROOT / "backend" / "data" / "crawled" / f"{country}_tariffs.json").read_text(
            encoding="utf-8"
        )
    )
    return next(data[key] for key in ("positions", "sub_positions", "tariff_lines") if key in data)


def test_west_africa_registry_remains_exact_and_combined_api_covers_36_countries():
    assert set(_registry()["countries"]) == WEST_AFRICA_15
    assert set(get_supported_enrichment_countries()) == (
        REGIONAL_18 | WEST_AFRICA_15 | ALGERIA_ACTIVE_3
    )


def test_west_africa_registry_line_counts_match_runtime_files():
    registry = _registry()
    for country, configured in registry["countries"].items():
        tariff = registry["regions"][configured["region"]]["tariff"]
        assert len(_tariff_lines(country)) == tariff["line_count_per_country"], country


def test_west_africa_source_paths_and_statuses_are_valid():
    for country, configured in _registry()["countries"].items():
        for key, value in configured.items():
            if key.endswith("_status"):
                assert value in CANONICAL_STATUSES, f"{country}.{key}={value}"
        for relative_path in configured["source_paths"]:
            assert (REPO_ROOT / relative_path).is_file(), f"{country}: {relative_path}"


def test_vat_records_remain_source_bound_without_numeric_registry_fallback():
    for country in WEST_AFRICA_15:
        enrichment = get_country_enrichment(country)
        assert enrichment["traceability_sources"], country
        assert enrichment["consumption_tax"]["source_record_path"].endswith("vat_measures.json")
        assert enrichment["consumption_tax"]["status"] == enrichment["vat_status"]


def test_known_unsafe_current_rates_are_explicitly_unavailable():
    for country in {"GNB", "TGO"}:
        enrichment = get_country_enrichment(country)
        assert enrichment["vat_status"] == "NOT_AVAILABLE"
        assert enrichment["consumption_tax"]["rates"] == []
        assert enrichment["anomalies"]


def test_no_documents_or_afcfta_preferences_are_invented_for_wave():
    for country in WEST_AFRICA_15:
        enrichment = get_country_enrichment(country)
        assert enrichment["required_documents"] == []
        assert enrichment["required_documents_status"] == "NOT_AVAILABLE"
        assert enrichment["afcfta_status"] == "NOT_AVAILABLE"


def test_registry_loader_fails_clearly_when_no_registry_exists(monkeypatch):
    monkeypatch.setattr(tariff_enrichment_service, "REGISTRY_PATHS", ())
    tariff_enrichment_service._load_registry.cache_clear()
    with pytest.raises(FileNotFoundError, match="No tariff enrichment registry"):
        tariff_enrichment_service._load_registry()
    tariff_enrichment_service._load_registry.cache_clear()


def test_each_country_keeps_its_wave_disclaimer():
    regional = get_country_enrichment("KEN")
    west_africa = get_country_enrichment("GHA")
    assert (
        regional["disclaimer"]
        == json.loads(
            (REPO_ROOT / "data" / "regional-18" / "tariff_enrichment_registry.json").read_text(
                encoding="utf-8"
            )
        )["disclaimer"]
    )
    assert west_africa["disclaimer"] == _registry()["disclaimer"]
