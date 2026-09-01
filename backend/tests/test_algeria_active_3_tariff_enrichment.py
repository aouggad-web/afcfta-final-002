import hashlib
import json
from pathlib import Path

from services.tariff_enrichment_service import (
    get_country_enrichment,
    get_supported_enrichment_countries,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
REGISTRY_PATH = REPO_ROOT / "data" / "algeria-active-3" / "tariff_enrichment_registry.json"
EXPECTED_COUNTRIES = {"EGY", "MUS", "TUN"}
CANONICAL_STATUSES = {
    "DOCUMENTED",
    "PARTIAL",
    "UNVERIFIED",
    "NOT_AVAILABLE",
    "NOT_APPLICABLE",
}


def _registry():
    return json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))


def _tariff_data(country):
    path = REPO_ROOT / "backend" / "data" / "crawled" / f"{country}_tariffs.json"
    return path, json.loads(path.read_text(encoding="utf-8"))


def _tariff_lines(country):
    _, data = _tariff_data(country)
    for key in ("positions", "sub_positions", "tariff_lines"):
        if key in data:
            return data[key]
    raise AssertionError(f"no tariff-line collection for {country}")


def test_registry_covers_the_three_previously_missing_active_partners():
    registry = _registry()
    assert set(registry["countries"]) == EXPECTED_COUNTRIES
    assert set(get_supported_enrichment_countries()) >= EXPECTED_COUNTRIES
    assert {
        country for region in registry["regions"].values() for country in region["members"]
    } == EXPECTED_COUNTRIES


def test_statuses_are_canonical_and_missing_preferences_fail_closed():
    for country, configured in _registry()["countries"].items():
        for key, value in configured.items():
            if key.endswith("_status"):
                assert value in CANONICAL_STATUSES, f"{country}.{key}={value}"
        assert configured["afcfta_status"] == "NOT_AVAILABLE"


def test_registered_line_counts_and_national_depths_match_runtime_data():
    expected = {
        "EGY": (8746, {10}),
        "MUS": (5619, {6}),
        "TUN": (17512, {10, 11}),
    }
    for country, (line_count, digit_depths) in expected.items():
        lines = _tariff_lines(country)
        assert len(lines) == line_count
        code_field = {
            "EGY": "hs_code",
            "MUS": "hs_code",
            "TUN": "hs_code",
        }[country]
        actual_depths = {
            len("".join(character for character in str(line[code_field]) if character.isdigit()))
            for line in lines
        }
        assert actual_depths == digit_depths


def test_runtime_dataset_hashes_match_the_source_records():
    source_files = {
        "EGY": "data/egypt/legal_sources.json",
        "MUS": "data/mauritius/legal_sources.json",
        "TUN": "data/tunisia/legal_sources.json",
    }
    for country, relative_source_path in source_files.items():
        tariff_path, _ = _tariff_data(country)
        digest = hashlib.sha256(tariff_path.read_bytes()).hexdigest()
        sources = json.loads((REPO_ROOT / relative_source_path).read_text(encoding="utf-8"))[
            "sources"
        ]
        runtime_sources = [
            source
            for source in sources
            if source.get("registry_path") == f"backend/data/crawled/{country}_tariffs.json"
        ]
        assert len(runtime_sources) == 1
        assert runtime_sources[0]["sha256"] == digest


def test_vat_records_are_source_bound_and_never_hs_extrapolated():
    expected_rates = {"EGY": "14%", "MUS": "15%"}
    for country, expected_rate in expected_rates.items():
        enrichment = get_country_enrichment(country)
        tax = enrichment["consumption_tax"]
        assert tax["rates"][0]["rate"] == expected_rate
        assert tax["rates"][0]["source_id"]
        assert tax["rates"][0]["hs_codes_explicit"] == []
        assert enrichment["required_documents"] == []
        assert enrichment["required_documents_status"] == "NOT_AVAILABLE"

    tunisia = get_country_enrichment("TUN")
    assert tunisia["vat_status"] == "NOT_AVAILABLE"
    assert tunisia["consumption_tax"]["rates"] == []


def test_mauritius_hs6_is_not_misrepresented_as_a_national_extension():
    enrichment = get_country_enrichment("MUS")
    assert enrichment["tariff"]["status"] == "PARTIAL"
    assert enrichment["national_extension_status"] == "NOT_AVAILABLE"
    assert enrichment["tariff"]["national_line_digits"] == [6]


def test_tunisia_2025_runtime_is_not_misrepresented_as_current_2026_tariff():
    enrichment = get_country_enrichment("TUN")
    assert enrichment["tariff"]["status"] == "PARTIAL"
    assert any(
        "Tarif Web 2025" in anomaly and "2026" in anomaly for anomaly in enrichment["anomalies"]
    )


def test_egypt_physical_preference_anomaly_remains_explicit():
    enrichment = get_country_enrichment("EGY")
    assert enrichment["afcfta_status"] == "NOT_AVAILABLE"
    assert any("2 276" in anomaly and "53" in anomaly for anomaly in enrichment["anomalies"])


def test_all_registered_source_paths_exist_and_traceability_is_exposed():
    for country, configured in _registry()["countries"].items():
        for relative_path in configured["source_paths"]:
            assert (REPO_ROOT / relative_path).is_file(), f"{country}: {relative_path}"
        enrichment = get_country_enrichment(country)
        assert enrichment["traceability_sources"]
        assert all(source["source_id"] for source in enrichment["traceability_sources"])
