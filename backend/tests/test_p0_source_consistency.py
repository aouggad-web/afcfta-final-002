"""Audit regressions using the repository's collected tariff positions."""

import copy
import importlib.util
import json
import sys
from pathlib import Path

import currencies.service as currency_service
import pytest
from services import authentic_tariff_service as svc

ROOT = Path(__file__).resolve().parents[2]
_MODULE_PATH = ROOT / "scripts" / "normalize_crawled.py"
_spec = importlib.util.spec_from_file_location("normalize_crawled", _MODULE_PATH)
_mod = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = _mod
_spec.loader.exec_module(_mod)
normalize_gha_canonical = _mod.normalize_gha_canonical


@pytest.fixture(autouse=True)
def local_sources(monkeypatch):
    monkeypatch.setattr(svc, "_get_postgres_provider", lambda: None)
    monkeypatch.setattr(currency_service, "get_by_country", lambda _: None)


@pytest.mark.parametrize(
    "country,code,duty",
    [
        ("EGY", "0207110000", 30),
        ("TUN", "90031100003", 10),
        ("TUN", "73090090109", 30),
        ("DZA", "2201101100", 30),
    ],
)
def test_collected_duty_agrees_in_listing_rate_and_amount(country, code, duty):
    positions = svc.get_sub_positions(country, code[:6])
    assert next(p for p in positions if p["code"] == code)["dd_rate"] == duty
    result = svc.calculate_import_taxes(country, code, 1000, origin_country="SEN")
    assert "error" not in result, result
    assert result["rates"]["dd_rate_pct"] == duty
    dd = next(t for t in result["taxes_breakdown"] if t["code"] == "DD")
    assert dd["rate_npf_pct"] == duty
    assert dd["amount_npf"] == duty * 10


@pytest.mark.parametrize(
    "country,code",
    [
        ("DZA", "1001110000"),
        ("KEN", "04011000"),
        ("MAR", "0405100010"),
        ("ZAF", "020830"),
        ("ETH", "01013000000"),
        ("TUN", "01012100015"),
    ],
)
def test_missing_or_specific_tax_does_not_produce_complete_total(country, code):
    result = svc.calculate_import_taxes(country, code, 1000, origin_country="SEN")
    assert result["error_detail"]["code"] == "CALCULATION_UNAVAILABLE"
    assert "taxes_summary" not in result
    assert "npf_calculation" not in result


@pytest.mark.parametrize("expression", ["10 USD/kg", "10% or 5 EUR/kg", "-2%", True, float("nan")])
def test_non_ad_valorem_or_invalid_expression_is_not_parsed_as_percent(expression):
    assert svc._parse_crawled_tax_rate(expression) is None


def test_ghana_normalization_preserves_all_national_children_and_zero_duties():
    data = json.loads((ROOT / "backend/data/crawled/GHA_tariffs.json").read_text())
    original = copy.deepcopy(data)
    positions = normalize_gha_canonical(data, "GHA")
    expected = {p["code"]: p for line in data["tariff_lines"] for p in line["sub_positions"]}
    assert len(positions) == len(expected) == 6129
    assert {p["national_code"] for p in positions} == set(expected)
    for position in positions:
        taxes = position["taxes"]
        duty = next(t for t in taxes if t["code"] == "DD")
        assert duty["rate_pct"] == expected[position["national_code"]]["dd"]
        assert sum(t.get("is_vat", False) for t in taxes) == 1
    assert data == original
