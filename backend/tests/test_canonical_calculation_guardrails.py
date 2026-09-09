"""Incomplete fiscal inputs must never produce a complete monetary total.

All values below are contract-test sentinels, not official tariff data.
"""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "engine"))
from calculation import CalculationUnavailable, compute_duties
from schemas.canonical_model import (
    CanonicalTariffLine,
    CommodityCode,
    Measure,
    Provenance,
)


def line_with(**updates):
    measure = {
        "country_iso3": "ZZZ",
        "national_code": "00000000",
        "measure_type": "CUSTOMS_DUTY",
        "code": "DD",
        "name_fr": "Contract test sentinel",
        "rate_pct": 0,
    }
    measure.update(updates)
    return CanonicalTariffLine(
        commodity=CommodityCode(
            country_iso3="ZZZ",
            national_code="00000000",
            hs6="000000",
            digits=8,
            description_fr="TEST",
            chapter="00",
        ),
        measures=[Measure(**measure)],
        provenance=Provenance(
            data_status="PARTIAL",
            source_name="Contract fixture only",
            source_url="https://example.invalid/contract-test",
        ),
    )


@pytest.mark.parametrize(
    "updates",
    [
        {"rate_pct": None},
        {"rate_pct": -1},
        {"rate_pct": float("nan")},
        {"rate_pct": float("inf")},
        {"basis": "OTHER"},
        {"basis": "FOB"},
        {"basis": "CIF_PLUS_INCLUDED", "basis_includes": ["missing"]},
        {"basis": "QUANTITY"},
        {"national_code": "00000001"},
    ],
)
def test_invalid_measure_cannot_produce_total(updates):
    with pytest.raises(CalculationUnavailable):
        compute_duties(line_with(**updates), 100)


@pytest.mark.parametrize("value", [0, -1, float("nan"), float("inf")])
def test_invalid_value_rejected(value):
    with pytest.raises(CalculationUnavailable):
        compute_duties(line_with(), value)


@pytest.mark.parametrize("quantity", [None, 0, -1, float("nan"), float("inf")])
def test_specific_duty_requires_valid_quantity(quantity):
    line = line_with(rate_type="SPECIFIC", rate_pct=None, specific_amount=1, specific_unit="DZD/kg")
    with pytest.raises(CalculationUnavailable):
        compute_duties(line, 100, quantity=quantity, currency="DZD")


@pytest.mark.parametrize(
    "updates",
    [
        {"specific_amount": None},
        {"specific_amount": -1},
        {"specific_amount": float("inf")},
        {"specific_unit": None},
        {"specific_unit": "USD/kg"},
    ],
)
def test_specific_duty_requires_amount_and_matching_currency(updates):
    args = {
        "rate_type": "SPECIFIC",
        "rate_pct": None,
        "specific_amount": 1,
        "specific_unit": "DZD/kg",
    }
    args.update(updates)
    with pytest.raises(CalculationUnavailable):
        compute_duties(line_with(**args), 100, quantity=2, currency="DZD")


def test_documented_zero_is_valid():
    result = compute_duties(line_with(), 100)
    assert result.total_duties_taxes == 0
    assert result.landed_cost == 100


@pytest.mark.parametrize("regime", ["NPF", "ZLECAF"])
def test_alternative_rate_is_rejected_even_with_complete_components(regime):
    line = line_with(
        rate_type="ALTERNATIVE", rate_pct=10, specific_amount=1, specific_unit="DZD/kg"
    )
    with pytest.raises(CalculationUnavailable, match="unsupported rate type"):
        compute_duties(line, 100, quantity=2, currency="DZD", regime=regime)


def test_missing_preference_does_not_silently_use_npf():
    with pytest.raises(CalculationUnavailable, match="preferential rate"):
        compute_duties(line_with(is_zlecaf_applicable=True), 100, regime="ZLECAF")


def test_synthetic_and_unattributed_lines_rejected():
    line = line_with()
    line.provenance = Provenance()
    with pytest.raises(CalculationUnavailable, match="synthetic"):
        compute_duties(line, 100)
    line.provenance = Provenance(data_status="VERIFIED")
    with pytest.raises(CalculationUnavailable, match="source"):
        compute_duties(line, 100)


def test_empty_and_duplicate_measures_rejected():
    line = line_with()
    line.measures = []
    with pytest.raises(CalculationUnavailable, match="no documented measures"):
        compute_duties(line, 100)
    line = line_with()
    line.measures.append(line.measures[0].model_copy())
    with pytest.raises(CalculationUnavailable, match="duplicate"):
        compute_duties(line, 100)


def test_specific_and_mixed_arithmetic_with_complete_inputs():
    specific = line_with(
        rate_type="SPECIFIC", rate_pct=None, specific_amount=1, specific_unit="DZD/kg"
    )
    assert compute_duties(specific, 100, quantity=2, currency="DZD").total_duties_taxes == 2
    mixed = line_with(rate_type="MIXED", rate_pct=10, specific_amount=1, specific_unit="DZD/kg")
    assert compute_duties(mixed, 100, quantity=2, currency="DZD").total_duties_taxes == 12


def test_invalid_regime_rejected():
    with pytest.raises(CalculationUnavailable, match="regime"):
        compute_duties(line_with(), 100, regime="unknown")
