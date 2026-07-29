import json
from pathlib import Path

import pytest
import services.tariff_enrichment_service as enrichment_service
from services.tariff_enrichment_service import (
    get_country_enrichment,
    get_supported_enrichment_countries,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
REGISTRY_PATH = REPO_ROOT / "data" / "regional-18" / "tariff_enrichment_registry.json"
EXPECTED_COUNTRIES = {
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
    for key in ("positions", "sub_positions", "tariff_lines"):
        if key in data:
            return data[key]
    raise AssertionError(f"no tariff-line collection for {country}")


def test_registry_covers_exactly_the_regional_18():
    registry = _registry()
    assert set(registry["countries"]) == EXPECTED_COUNTRIES
    assert EXPECTED_COUNTRIES < set(get_supported_enrichment_countries())
    assert {
        country for region in registry["regions"].values() for country in region["members"]
    } == EXPECTED_COUNTRIES


def test_all_country_statuses_use_the_canonical_vocabulary():
    registry = _registry()
    for country, configured in registry["countries"].items():
        for key, value in configured.items():
            if key.endswith("_status"):
                assert value in CANONICAL_STATUSES, f"{country}.{key}={value}"


def test_registered_tariff_files_and_line_counts_match_the_runtime_data():
    registry = _registry()
    for country, configured in registry["countries"].items():
        expected = registry["regions"][configured["region"]]["tariff"]["line_count_per_country"]
        assert len(_tariff_lines(country)) == expected, country


def test_all_registered_source_paths_exist():
    for country, configured in _registry()["countries"].items():
        for relative_path in configured["source_paths"]:
            assert (REPO_ROOT / relative_path).is_file(), f"{country}: {relative_path}"


def test_registry_contains_no_numeric_tax_or_preference_rate_fallback():
    def inspect(value, path="registry"):
        if isinstance(value, dict):
            for key, child in value.items():
                assert not key.endswith("_rate"), f"numeric rate field forbidden: {path}.{key}"
                inspect(child, f"{path}.{key}")
        elif isinstance(value, list):
            for index, child in enumerate(value):
                inspect(child, f"{path}[{index}]")

    inspect(_registry())


def test_only_source_bound_countries_expose_required_documents():
    source_bound = {"KEN", "COD", "SSD", "BWA", "LSO", "NAM", "SWZ"}
    for country in EXPECTED_COUNTRIES - source_bound:
        enrichment = get_country_enrichment(country)
        assert enrichment["required_documents"] == []
        assert enrichment["required_documents_status"] == "NOT_AVAILABLE"


def test_kenya_and_cod_documents_remain_source_bound_and_scope_aware():
    kenya = get_country_enrichment("KEN")
    assert {item["document_id"] for item in kenya["required_documents"]} == {
        "FORM-TPA-44A",
        "FORM-KRA-CLEARANCE-DOCS",
    }
    assert all(item["source_id"] for item in kenya["required_documents"])
    assert kenya["required_documents_are_hs_specific"] is False

    cod = get_country_enrichment("COD")
    assert len(cod["required_documents"]) == 9
    assert all(item["source_id"] for item in cod["required_documents"])
    assert all(item["issuer"] is None for item in cod["required_documents"])
    assert cod["required_documents_are_hs_specific"] is False


def test_known_data_conflicts_are_exposed_not_silently_resolved():
    registry = _registry()["countries"]
    for country in {"BDI", "SSD", "UGA", "TCD", "GAB", "GNQ"}:
        assert registry[country]["anomalies"], country


def test_priority_08_consumption_taxes_are_country_specific_and_fail_closed():
    expected_vat = {
        "BDI": 18.0,
        "BWA": 14.0,
        "LSO": 15.0,
        "NAM": 15.0,
        "SWZ": 15.0,
        "CAF": 19.0,
        "GNQ": 15.0,
    }
    for country, expected_rate in expected_vat.items():
        enrichment = get_country_enrichment(country)
        assert enrichment["consumption_tax"]["tax_type"] == "VAT"
        assert enrichment["consumption_tax"]["standard_rate"] == expected_rate
        assert enrichment["traceability_sources"]

    south_sudan = get_country_enrichment("SSD")["consumption_tax"]
    assert south_sudan["tax_type"] == "IMPORT_SALES_TAX"
    assert south_sudan["status"] == "NOT_AVAILABLE"
    assert south_sudan["standard_rate"] is None
    assert south_sudan["historical_record"]["rate"] == 20.0
    assert south_sudan["historical_record"]["status"] == "HISTORICAL_NOT_CURRENT"


def test_unmapped_reduced_rates_are_not_presented_as_hs_specific():
    for country in {"CAF", "GNQ"}:
        tax = get_country_enrichment(country)["consumption_tax"]
        assert tax["status"] == "PARTIAL"
        assert all(item["hs_mapping_status"] == "NOT_AVAILABLE" for item in tax["reduced_rates"])


def test_no_priority_08_country_invents_pre_shipment_inspection():
    for country in {"BDI", "SSD", "BWA", "LSO", "NAM", "SWZ", "CAF", "GNQ"}:
        inspection = get_country_enrichment(country)["inspection_before_shipment"]
        assert inspection == {"status": "NOT_AVAILABLE"}


def test_priority_08_documents_are_general_or_conditionally_scoped_not_hs_mapped():
    for country in {"SSD", "BWA", "LSO", "NAM", "SWZ"}:
        enrichment = get_country_enrichment(country)
        assert enrichment["required_documents"]
        assert enrichment["required_documents_are_hs_specific"] is False
        assert all(
            item["source_id"] and item["status"] == "DOCUMENTED"
            for item in enrichment["required_documents"]
        )


def test_unknown_country_has_no_synthetic_enrichment():
    assert get_country_enrichment("XXX") is None


def test_static_source_json_is_cached_on_hot_api_paths():
    enrichment_service._read_json.cache_clear()
    get_country_enrichment("KEN")
    first = enrichment_service._read_json.cache_info()
    get_country_enrichment("KEN")
    second = enrichment_service._read_json.cache_info()
    assert second.hits > first.hits


def test_source_path_traversal_is_rejected():
    enrichment_service._read_json.cache_clear()
    with pytest.raises(ValueError, match="outside repository"):
        enrichment_service._read_json("../outside.json")


def test_kenya_document_registry_drift_fails_fast(monkeypatch):
    monkeypatch.setattr(
        enrichment_service,
        "_read_json",
        lambda _path: {"administrative_formalities": []},
    )
    with pytest.raises(ValueError, match="FORM-TPA-44A"):
        enrichment_service._kenya_required_documents(["FORM-TPA-44A"])


def test_drc_document_registry_drift_fails_fast(monkeypatch):
    monkeypatch.setattr(
        enrichment_service,
        "_read_json",
        lambda _path: {"regulatory_measures": []},
    )
    with pytest.raises(ValueError, match="COD-OCC-CBCA"):
        enrichment_service._cod_required_documents(["COD-OCC-CBCA"])
