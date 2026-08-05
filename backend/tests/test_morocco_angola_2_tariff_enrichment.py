import hashlib
import json
from pathlib import Path

from services.tariff_enrichment_service import (
    get_country_enrichment,
    get_supported_enrichment_countries,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
REGISTRY_PATH = REPO_ROOT / "data" / "morocco-angola-2" / "tariff_enrichment_registry.json"
EXPECTED_COUNTRIES = {"MAR", "AGO"}
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


def test_registry_covers_morocco_and_angola():
    registry = _registry()
    assert set(registry["countries"]) == EXPECTED_COUNTRIES
    assert set(get_supported_enrichment_countries()) >= EXPECTED_COUNTRIES
    assert {
        country for region in registry["regions"].values() for country in region["members"]
    } == EXPECTED_COUNTRIES


def test_registry_dates_remain_scoped_to_their_own_countries():
    """A newer MAR/AGO snapshot must not retimestamp prior country waves."""

    assert get_country_enrichment("MAR")["as_of"] == "2026-08-05"
    assert get_country_enrichment("AGO")["as_of"] == "2026-08-05"
    assert get_country_enrichment("MAR")["consumption_tax"]["as_of"] == "2026-08-05"
    assert get_country_enrichment("AGO")["consumption_tax"]["as_of"] == "2026-08-05"
    assert get_country_enrichment("KEN")["as_of"] == "2026-07-29"
    assert get_country_enrichment("KEN")["consumption_tax"]["as_of"] == "2026-07-29"


def test_statuses_are_canonical_and_missing_preferences_fail_closed():
    for country, configured in _registry()["countries"].items():
        for key, value in configured.items():
            if key.endswith("_status"):
                assert value in CANONICAL_STATUSES, f"{country}.{key}={value}"
        assert configured["afcfta_status"] == "NOT_AVAILABLE"
        assert configured["regulatory_status"] == "NOT_AVAILABLE"
        assert configured["required_documents_status"] == "NOT_AVAILABLE"


def test_registered_line_counts_and_national_depths_match_runtime_data():
    expected = {
        "MAR": (13114, {10}),
        "AGO": (5388, {6}),
    }
    code_field = {"MAR": "code", "AGO": "hs_code"}
    for country, (line_count, digit_depths) in expected.items():
        lines = _tariff_lines(country)
        assert len(lines) == line_count
        actual_depths = {
            len(
                "".join(
                    character for character in str(line[code_field[country]]) if character.isdigit()
                )
            )
            for line in lines
        }
        assert actual_depths == digit_depths


def test_runtime_dataset_hashes_match_the_source_records():
    source_files = {
        "MAR": "data/morocco/legal_sources.json",
        "AGO": "data/angola/legal_sources.json",
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


def test_morocco_national_tariff_is_documented_but_vat_stays_partial():
    """Le tarif national marocain (ADIL, 13 114 positions) est DOCUMENTED,
    mais le taux TVA de 20 % n'est corroboré que par des sources secondaires
    citant le CGI — le texte primaire (tax.gov.ma) n'a pas été atteint ce
    cycle, donc vat_status reste PARTIAL plutôt que DOCUMENTED."""
    enrichment = get_country_enrichment("MAR")
    assert enrichment["tariff"]["status"] == "DOCUMENTED"
    assert enrichment["tariff"]["national_line_digits"] == [10]
    assert enrichment["vat_status"] == "PARTIAL"
    assert enrichment["consumption_tax"]["rates"][0]["rate"] == "20%"
    assert enrichment["consumption_tax"]["rates"][0]["source_id"]
    assert enrichment["consumption_tax"]["rates"][0]["hs_codes_explicit"] == []
    assert enrichment["required_documents"] == []
    assert enrichment["required_documents_status"] == "NOT_AVAILABLE"


def test_angola_hs6_is_not_misrepresented_as_a_national_extension():
    """AGO n'a qu'un référentiel WITS/TRAINS SH6. Le taux général d'IVA à
    14 % est officiellement documenté, mais la couverture TVA globale reste
    PARTIAL tant que le taux territorial de Cabinda et les exonérations
    officielles à l'importation ne sont pas structurés dans le modèle."""
    enrichment = get_country_enrichment("AGO")
    assert enrichment["tariff"]["status"] == "PARTIAL"
    assert enrichment["national_extension_status"] == "NOT_AVAILABLE"
    assert enrichment["tariff"]["national_line_digits"] == [6]
    assert enrichment["vat_status"] == "PARTIAL"
    assert enrichment["consumption_tax"]["rates"][0]["rate"] == "14%"
    assert enrichment["consumption_tax"]["rates"][0]["source_id"]
    assert enrichment["consumption_tax"]["rates"][0]["hs_codes_explicit"] == []


def test_angola_reduced_rates_are_not_fabricated():
    """Le portail officiel confirme 2 % à Cabinda et des exonérations à
    l'importation. Faute de portée géographique et de correspondance SH
    normalisées, elles restent non calculables et le statut global demeure
    PARTIAL plutôt que d'inventer une application nationale ou produit."""
    enrichment = get_country_enrichment("AGO")
    assert enrichment["vat_status"] == "PARTIAL"
    assert [rate["rate"] for rate in enrichment["consumption_tax"]["rates"]] == ["14%"]
    assert enrichment["consumption_tax"]["exemptions"] == []
    assert enrichment["consumption_tax"]["zero_rated"] == []
    assert any("Cabinda" in anomaly for anomaly in enrichment["anomalies"])
    official_sources = [
        source
        for source in enrichment["traceability_sources"]
        if source["source_id"] == "AGO-MINFIN-PORTAL-CONTRIBUINTE-IVA"
    ]
    assert len(official_sources) == 1
    assert "Cabinda" in official_sources[0]["notes"]


def test_morocco_calculation_order_is_documented_from_customs_code():
    """L'ordre de calcul marocain (DD + TPI, puis TVA sur l'assiette
    cumulée) provient directement du Code des Douanes et Impôts Indirects
    (source primaire ADII) : calculation_order_status est DOCUMENTED, à la
    différence de vat_status qui reste PARTIAL (taux non confirmé sur texte
    primaire)."""
    registry = _registry()["countries"]["MAR"]
    assert registry["calculation_order_status"] == "DOCUMENTED"
    assert registry["vat_status"] == "PARTIAL"


def test_all_registered_source_paths_exist_and_traceability_is_exposed():
    for country, configured in _registry()["countries"].items():
        for relative_path in configured["source_paths"]:
            assert (REPO_ROOT / relative_path).is_file(), f"{country}: {relative_path}"
        enrichment = get_country_enrichment(country)
        assert enrichment["traceability_sources"]
        assert all(source["source_id"] for source in enrichment["traceability_sources"])


def test_no_registry_field_carries_a_fabricated_numeric_rate():
    def inspect(value, path="registry"):
        if isinstance(value, dict):
            for key, child in value.items():
                assert not key.endswith("_rate"), f"numeric rate field forbidden: {path}.{key}"
                inspect(child, f"{path}.{key}")
        elif isinstance(value, list):
            for index, child in enumerate(value):
                inspect(child, f"{path}[{index}]")

    inspect(_registry())
