"""Regression coverage for country-specific calculator methods from tariffs.

The generated tariff files use source-native tax codes. These tests make sure
those codes are canonicalized before the country cascade profile is applied, so
VAT and levies use the method declared for each destination country.
"""

import currencies.service as currency_service
from services import authentic_tariff_service as svc


def _calc(monkeypatch, country, hs_code):
    monkeypatch.setattr(currency_service, "get_by_country", lambda code: None)
    return svc.calculate_import_taxes(country, hs_code, 1_000.0, language="fr")


def test_kenya_eac_tariff_codes_use_eac_cascade(monkeypatch):
    result = _calc(monkeypatch, "KEN", "010129")
    by_code = {row["code"]: row for row in result["taxes_breakdown"]}

    assert set(by_code) == {"DD", "IDF", "RDL", "TVA"}
    assert by_code["DD"]["amount_npf"] == 250.0
    assert by_code["IDF"]["amount_npf"] == 35.0
    assert by_code["RDL"]["amount_npf"] == 20.0
    assert by_code["TVA"]["base_expr"] == "CIF + DD"
    assert by_code["TVA"]["base_value_npf"] == 1_250.0
    assert by_code["TVA"]["amount_npf"] == 200.0
    assert result["taxes_summary"]["npf"]["total_taxes_et_droits"] == 505.0


def test_ghana_tariff_codes_use_ghana_vat_and_levy_bases(monkeypatch):
    result = _calc(monkeypatch, "GHA", "010121")
    by_code = {row["code"]: row for row in result["taxes_breakdown"]}

    assert set(by_code) == {"DD", "TVA", "NHIL", "GETFUND"}
    assert by_code["DD"]["amount_npf"] == 50.0
    assert by_code["TVA"]["base_expr"] == "CIF + DD + CEDEAO"
    assert by_code["TVA"]["base_value_npf"] == 1_050.0
    assert by_code["TVA"]["amount_npf"] == 157.5
    assert by_code["NHIL"]["base_value_npf"] == 1_050.0
    assert by_code["GETFUND"]["base_value_npf"] == 1_050.0
    assert result["taxes_summary"]["npf"]["total_taxes_et_droits"] == 260.0


def test_ethiopia_tariff_codes_use_surtax_then_vat_cascade(monkeypatch):
    result = _calc(monkeypatch, "ETH", "020110")
    by_code = {row["code"]: row for row in result["taxes_breakdown"]}

    assert {"DD", "SUR", "TVA", "WHR"} <= set(by_code)
    assert by_code["DD"]["amount_npf"] == 350.0
    assert by_code["SUR"]["base_expr"] == "CIF + DD"
    assert by_code["SUR"]["base_value_npf"] == 1_350.0
    assert by_code["SUR"]["amount_npf"] == 135.0
    assert by_code["TVA"]["base_expr"] == "CIF + DD + SUR"
    assert by_code["TVA"]["base_value_npf"] == 1_485.0
    assert by_code["TVA"]["amount_npf"] == 222.75
    assert by_code["WHR"]["amount_npf"] == 30.0
    assert result["taxes_summary"]["npf"]["total_taxes_et_droits"] == 737.75


def test_cemac_tariff_codes_use_cemac_tva_base_and_keep_ri(monkeypatch):
    result = _calc(monkeypatch, "CMR", "010110")
    by_code = {row["code"]: row for row in result["taxes_breakdown"]}

    assert {"DD", "TCI", "TVA", "RI"} <= set(by_code)
    assert by_code["DD"]["amount_npf"] == 50.0
    assert by_code["TCI"]["amount_npf"] == 10.0
    assert by_code["TVA"]["base_expr"] == "CIF + DD + TCI"
    assert by_code["TVA"]["base_value_npf"] == 1_060.0
    assert by_code["TVA"]["amount_npf"] == 204.05
    assert by_code["RI"]["base_expr"] == "CIF"
    assert by_code["RI"]["amount_npf"] == 4.5
    assert result["taxes_summary"]["npf"]["total_taxes_et_droits"] == 268.55


def test_tunisia_tariff_codes_normalize_duty_and_import_levy(monkeypatch):
    result = _calc(monkeypatch, "TUN", "010121")
    by_code = {row["code"]: row for row in result["taxes_breakdown"]}

    assert set(by_code) == {"DD", "TCL"}
    assert by_code["DD"]["amount_npf"] == 360.0
    assert by_code["TCL"]["base_expr"] == "CIF"
    assert by_code["TCL"]["amount_npf"] == 30.0
    assert result["taxes_summary"]["npf"]["total_taxes_et_droits"] == 390.0
