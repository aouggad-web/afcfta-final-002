"""Multipays invariants for the shared regional/national calculator.

Rates in these tests are explicitly marked test fixtures; they are not legal
production rates and must never be used as tariff data.
"""
from datetime import date

from engine.import_charges import calculate_import_charges


def membership(bloc, country, start="2020-01-01"):
    return {"territory_id": bloc, "country_iso3": country, "valid_from": start, "implementation_status": "ACTIVE"}


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
        "UGA", "KEN", "010101", customs_value=1000, calculation_date=date(2025, 1, 1),
        importer_profile={"base_rate": 10},
        regional_measures=[override("eac-stay", "EAC", "STAY_OF_APPLICATION", 25)],
        national_taxes=[{"tax_id": "UGA-VAT", "country_iso3": "UGA", "code": "VAT", "rate_pct": 18, "sequence": 90, "effective_from": "2020-01-01", "source_id": "TEST"}],
        territory_memberships=[membership("EAC", "UGA")],
        regional_coverage_complete=True, national_coverage_complete=True,
    )
    assert result["customs_territory"] == "EAC"
    assert result["applicable_customs_rate"] == 25
    assert result["taxes"][0]["code"] == "VAT"
    assert result["calculation_status"] == "VERIFIED_COMPLETE"


def test_stay_expires_and_date_changes_result():
    args = dict(importing_country="TZA", exporting_country="KEN", hs6="010101", customs_value=1000,
                importer_profile={"base_rate": 10}, regional_measures=[override("stay", "EAC", "STAY_OF_APPLICATION", 30, end="2024-12-31")],
                territory_memberships=[membership("EAC", "TZA")], regional_coverage_complete=True, national_coverage_complete=True)
    assert calculate_import_charges(calculation_date=date(2024, 12, 31), **args)["applicable_customs_rate"] == 30
    assert calculate_import_charges(calculation_date=date(2025, 1, 1), **args)["applicable_customs_rate"] == 10


def test_sacu_common_rate_with_botswana_tax_layer():
    result = calculate_import_charges(
        "BWA", "ZAF", "010101", customs_value=1000, calculation_date=date(2025, 1, 1),
        importer_profile={"base_rate": 15}, national_taxes=[{"tax_id": "BWA-VAT", "country_iso3": "BWA", "code": "VAT", "rate_pct": 14, "sequence": 90, "effective_from": "2020-01-01", "source_id": "TEST"}],
        territory_memberships=[membership("SACU", "BWA")], regional_coverage_complete=True, national_coverage_complete=True,
    )
    assert result["customs_territory"] == "SACU"
    assert result["applicable_customs_rate"] == 15
    assert result["taxes"][0]["rate"] == 14


def test_cemac_uemoa_and_national_tariff_can_use_same_engine():
    for country, bloc, base in (("CMR", "CEMAC", 20), ("CIV", "UEMOA", 10), ("DZA", None, 5)):
        profile = {"base_rate": base}
        memberships = [] if not bloc else [membership(bloc, country)]
        result = calculate_import_charges(country, "MAR", "010101", customs_value=100,
            calculation_date=date(2025, 1, 1), importer_profile=profile,
            territory_memberships=memberships, regional_coverage_complete=True,
            national_coverage_complete=True)
        assert result["importing_country"] == country
        assert result["applicable_customs_rate"] == base


def test_two_regional_memberships_without_priority_are_not_guessed():
    result = calculate_import_charges("KEN", "ZAF", "010101", customs_value=100,
        calculation_date=date(2025, 1, 1), importer_profile={"base_rate": 10},
        territory_memberships=[membership("EAC", "KEN"), membership("COMESA", "KEN")],
        regional_coverage_complete=True, national_coverage_complete=True)
    assert result["customs_territory"] is None
    assert result["missing_elements"]
    assert result["calculation_status"] == "VERIFIED_PARTIAL"
