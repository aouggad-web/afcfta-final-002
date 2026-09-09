"""Multipays invariants for the shared regional/national calculator.

Rates in these tests are explicitly marked test fixtures; they are not legal
production rates and must never be used as tariff data.
"""

from datetime import date

import pytest

from engine.import_charges import (
    aggregate_overall_status,
    calculate_import_charges,
    validate_quality_dimensions,
)


def membership(bloc, country, start="2020-01-01"):
    return {
        "territory_id": bloc,
        "country_iso3": country,
        "valid_from": start,
        "implementation_status": "ACTIVE",
    }


def override(mid, bloc, kind, rate, start="2020-01-01", end=None):
    return {
        "measure_id": mid,
        "jurisdiction": bloc,
        "measure_type": kind,
        "legal_layer": "REGIONAL_COMMON",
        "regional_bloc": bloc,
        "effective_from": start,
        "effective_to": end,
        "hs_code_from": "010101",
        "hs_code_to": "010101",
        "override_rate": rate,
        "legal_reference": "TEST-FIXTURE",
        "publication_url": "https://example.test/legal.pdf",
        "verification_status": "VERIFIED_TEST_FIXTURE",
        "product_description": "test fixture",
    }


def test_eac_common_layer_and_uganda_national_tax_are_separate():
    result = calculate_import_charges(
        "UGA",
        "KEN",
        "010101",
        customs_value=1000,
        calculation_date=date(2025, 1, 1),
        importer_profile={"base_rate": 10},
        regional_measures=[override("eac-stay", "EAC", "STAY_OF_APPLICATION", 25)],
        national_taxes=[
            {
                "tax_id": "UGA-VAT",
                "country_iso3": "UGA",
                "code": "VAT",
                "rate_pct": 18,
                "sequence": 90,
                "effective_from": "2020-01-01",
                "source_id": "TEST",
            }
        ],
        territory_memberships=[membership("EAC", "UGA")],
        regional_coverage_complete=True,
        national_coverage_complete=True,
    )
    assert result["customs_territory"] == "EAC"
    assert result["applicable_customs_rate"] == 25
    assert result["taxes"][0]["code"] == "VAT"
    assert result["calculation_status"] == "INFORMATIVE_PARTIAL"
    assert result["informational_only"] is True
    assert result["legally_binding"] is False


def test_stay_expires_and_date_changes_result():
    args = dict(
        importing_country="TZA",
        exporting_country="KEN",
        hs6="010101",
        customs_value=1000,
        importer_profile={"base_rate": 10},
        regional_measures=[override("stay", "EAC", "STAY_OF_APPLICATION", 30, end="2024-12-31")],
        territory_memberships=[membership("EAC", "TZA")],
        regional_coverage_complete=True,
        national_coverage_complete=True,
    )
    assert (
        calculate_import_charges(calculation_date=date(2024, 12, 31), **args)[
            "applicable_customs_rate"
        ]
        == 30
    )
    assert (
        calculate_import_charges(calculation_date=date(2025, 1, 1), **args)[
            "applicable_customs_rate"
        ]
        == 10
    )


def test_sacu_common_rate_with_botswana_tax_layer():
    result = calculate_import_charges(
        "BWA",
        "ZAF",
        "010101",
        customs_value=1000,
        calculation_date=date(2025, 1, 1),
        importer_profile={"base_rate": 15},
        national_taxes=[
            {
                "tax_id": "BWA-VAT",
                "country_iso3": "BWA",
                "code": "VAT",
                "rate_pct": 14,
                "sequence": 90,
                "effective_from": "2020-01-01",
                "source_id": "TEST",
            }
        ],
        territory_memberships=[membership("SACU", "BWA")],
        regional_coverage_complete=True,
        national_coverage_complete=True,
    )
    assert result["customs_territory"] == "SACU"
    assert result["applicable_customs_rate"] == 15
    assert result["taxes"][0]["rate"] == 14


def test_cemac_uemoa_and_national_tariff_can_use_same_engine():
    for country, bloc, base in (("CMR", "CEMAC", 20), ("CIV", "UEMOA", 10), ("DZA", None, 5)):
        profile = {"base_rate": base}
        memberships = [] if not bloc else [membership(bloc, country)]
        result = calculate_import_charges(
            country,
            "MAR",
            "010101",
            customs_value=100,
            calculation_date=date(2025, 1, 1),
            importer_profile=profile,
            territory_memberships=memberships,
            regional_coverage_complete=True,
            national_coverage_complete=True,
        )
        assert result["importing_country"] == country
        assert result["applicable_customs_rate"] == base


def test_two_regional_memberships_without_priority_are_not_guessed():
    result = calculate_import_charges(
        "KEN",
        "ZAF",
        "010101",
        customs_value=100,
        calculation_date=date(2025, 1, 1),
        importer_profile={"base_rate": 10},
        territory_memberships=[membership("EAC", "KEN"), membership("COMESA", "KEN")],
        regional_coverage_complete=True,
        national_coverage_complete=True,
    )
    assert result["customs_territory"] is None
    assert result["missing_elements"]
    assert result["calculation_status"] == "INFORMATIVE_PARTIAL"


def test_missing_base_tariff_is_blocked_and_total_is_withheld():
    result = calculate_import_charges(
        importing_country="DZA",
        exporting_country="MAR",
        hs6="010101",
        customs_value=100,
        calculation_date=date(2025, 1, 1),
        regional_coverage_complete=True,
        national_coverage_complete=True,
    )
    assert result["calculation_status"] == "BLOCKED_BASE_TARIFF"
    assert result["verified_total"] is None
    assert result["total_payable"] is None
    assert result["overall_status"] == "CALCULATION_UNAVAILABLE"
    assert result["amount_display_allowed"] is False


def test_present_but_unverified_base_is_simulation_only():
    result = calculate_import_charges(
        importing_country="DZA",
        exporting_country="MAR",
        hs6="010101",
        customs_value=100,
        calculation_date=date(2025, 1, 1),
        base_rate=10,
        base_rate_status="AVAILABLE_UNVERIFIED",
        regional_coverage_complete=True,
        national_coverage_complete=True,
    )
    assert result["calculation_status"] == "UNVERIFIED_SOURCE"
    assert result["base_tariff_verification_status"] == "UNVERIFIED"
    assert result["verified_total"] is None
    assert result["simulated_total"] == 10
    assert result["overall_status"] == "REVIEW_REQUIRED"
    assert result["simulation_only"] is True


def test_verified_base_with_missing_national_layer_is_partial():
    result = calculate_import_charges(
        importing_country="DZA",
        exporting_country="MAR",
        hs6="010101",
        customs_value=100,
        calculation_date=date(2025, 1, 1),
        base_rate=10,
        base_rate_status="SOURCE_ARCHIVED",
        base_source_id="DZA-TARIFF",
        base_hs_version="HS2022",
        base_effective_from="2025-01-01",
        regional_coverage_complete=True,
        national_coverage_complete=False,
    )
    assert result["calculation_status"] == "INFORMATIVE_PARTIAL"
    assert result["verified_total"] == 10
    assert result["component_statuses"]["customs_duty"]["verification_status"] == "VERIFIED"


def test_complete_result_exposes_component_provenance():
    result = calculate_import_charges(
        importing_country="DZA",
        exporting_country="MAR",
        hs6="010101",
        customs_value=100,
        calculation_date=date(2025, 1, 1),
        base_rate=10,
        base_rate_status="SOURCE_ARCHIVED",
        base_source_id="DZA-TARIFF-2025",
        base_source_hash="a" * 64,
        base_hs_version="HS2022",
        base_effective_from="2025-01-01",
        importer_profile={"source_authority": "DGD", "source_title": "Tarif officiel archivé"},
        regional_coverage_complete=True,
        national_coverage_complete=True,
    )
    assert result["calculation_status"] == "INFORMATIVE_COMPLETE"
    assert result["verified_total"] == 10
    assert result["component_statuses"]["base_tariff"]["source_id"] == "DZA-TARIFF-2025"
    assert result["amounts"][0]["effective_from"] == "2025-01-01"


def test_complete_result_is_informative_and_non_binding():
    result = calculate_import_charges(
        importing_country="DZA",
        exporting_country="MAR",
        hs6="010101",
        customs_value=100,
        calculation_date=date(2025, 1, 1),
        base_rate=10,
        base_rate_status="SOURCE_ARCHIVED",
        base_source_id="DZA-TARIFF-2025",
        base_source_hash="a" * 64,
        base_hs_version="HS2022",
        base_effective_from="2025-01-01",
        importer_profile={"source_authority": "DGD", "source_title": "Tarif officiel archivé"},
        regional_coverage_complete=True,
        national_coverage_complete=True,
    )
    assert result["overall_status"] == "INFORMATIVE_COMPLETE"
    assert result["informational_only"] is True
    assert result["legally_binding"] is False
    assert result["disclaimer"]["legally_binding"] is False


def test_missing_effective_date_is_partial_temporality():
    result = calculate_import_charges(
        importing_country="DZA",
        exporting_country="MAR",
        hs6="010101",
        customs_value=100,
        base_rate=10,
        base_rate_status="SOURCE_ARCHIVED",
        base_source_id="DZA-TARIFF",
        base_source_hash="a" * 64,
        base_hs_version="HS2022",
        regional_coverage_complete=True,
        national_coverage_complete=True,
    )
    assert result["quality_dimensions"]["temporal_validity"] == "PARTIAL"
    assert result["calculation_status"] == "UNVERIFIED_SOURCE"


def test_internal_source_id_alone_is_not_documented():
    result = calculate_import_charges(
        importing_country="DZA",
        exporting_country="MAR",
        hs6="010101",
        customs_value=100,
        base_rate=10,
        base_rate_status="SOURCE_ARCHIVED",
        base_source_id="INTERNAL-TARIFF",
        base_hs_version="HS2022",
        base_effective_from="2025-01-01",
        regional_coverage_complete=True,
        national_coverage_complete=True,
    )
    assert result["quality_dimensions"]["source"] != "DOCUMENTED"
    assert result["calculation_status"] == "INFORMATIVE_PARTIAL"


def test_missing_fiscal_component_prevents_informative_complete():
    result = calculate_import_charges(
        importing_country="DZA",
        exporting_country="MAR",
        hs6="010101",
        customs_value=100,
        base_rate=10,
        base_rate_status="SOURCE_ARCHIVED",
        base_source_id="DZA-TARIFF-2025",
        base_source_hash="a" * 64,
        base_hs_version="HS2022",
        base_effective_from="2025-01-01",
        regional_coverage_complete=True,
        national_coverage_complete=True,
        national_taxes=[
            {
                "country_iso3": "DZA",
                "code": "VAT",
                "rate_pct": 19,
                "effective_from": "2025-01-01",
                "source_id": "VAT-1",
                "verification_status": "SOURCE_PENDING",
            }
        ],
    )
    assert result["quality_dimensions"]["taxes_and_levies"] == "PARTIAL"
    assert result["calculation_status"] == "INFORMATIVE_PARTIAL"
    assert result["overall_status"] == "REVIEW_REQUIRED"
    assert result["simulation_only"] is True


QUALITY_DIMENSIONS = {
    "source": "DOCUMENTED",
    "temporal_validity": "DOCUMENTED",
    "classification": "DOCUMENTED",
    "taxes_and_levies": "DOCUMENTED",
    "preference_and_origin": "NOT_APPLICABLE",
    "formalities": "NOT_APPLICABLE",
}


def test_quality_dimensions_reject_sixth_value():
    invalid = {**QUALITY_DIMENSIONS, "source": "UNKNOWN"}
    with pytest.raises(ValueError):
        validate_quality_dimensions(invalid, require_all=True)


def test_overall_status_complete_allows_documented_and_not_applicable():
    assert aggregate_overall_status(QUALITY_DIMENSIONS) == "INFORMATIVE_COMPLETE"


def test_overall_status_partial_does_not_average_dimensions():
    partial = {**QUALITY_DIMENSIONS, "taxes_and_levies": "PARTIAL"}
    assert aggregate_overall_status(partial) == "INFORMATIVE_PARTIAL"


def test_overall_status_review_for_determinant_unverified():
    review = {**QUALITY_DIMENSIONS, "classification": "UNVERIFIED"}
    assert aggregate_overall_status(review, determinant_unverified=True) == "REVIEW_REQUIRED"


def test_overall_status_unavailable_for_missing_base_or_indispensable_dimension():
    assert (
        aggregate_overall_status(QUALITY_DIMENSIONS, base_available=False)
        == "CALCULATION_UNAVAILABLE"
    )
    unavailable = {**QUALITY_DIMENSIONS, "taxes_and_levies": "NOT_AVAILABLE"}
    assert aggregate_overall_status(unavailable) == "CALCULATION_UNAVAILABLE"
