import json
from pathlib import Path

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
    assert set(get_supported_enrichment_countries()) == EXPECTED_COUNTRIES
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
    for country in EXPECTED_COUNTRIES - {"KEN", "COD"}:
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


def test_unknown_country_has_no_synthetic_enrichment():
    assert get_country_enrichment("XXX") is None
