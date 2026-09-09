"""Arithmetic contract fixtures only; no customs rates are added to production."""

from copy import deepcopy

import pytest

from services.tax_computation import compute_dual_breakdown


def _lines():
    return [
        {"code": "DD", "name": "DD", "rate_pct": 10, "base": "CIF"},
        {"code": "DAPS", "name": "DAPS", "rate_pct": 20, "base": "CIF"},
        {"code": "TVA", "name": "TVA", "rate_pct": 10, "base": "CIF + DD + DAPS"},
    ]


def test_daps_exemption_preserves_npf_and_recomputes_preferential_vat():
    lines = _lines()
    original = deepcopy(lines)
    dual = compute_dual_breakdown(100, lines, 10, 0, zlecaf_exempt_codes={"DAPS"})
    assert lines == original
    by_code = {row["code"]: row for row in dual["breakdown"]}
    assert by_code["DAPS"]["amount_npf"] == 20
    assert by_code["DAPS"]["amount_zlecaf"] == 0
    assert by_code["DAPS"]["rate_npf_pct"] == 20
    assert by_code["DAPS"]["rate_zlecaf_pct"] == 0
    assert by_code["DAPS"]["exempt_zlecaf"] is True
    assert by_code["TVA"]["base_value_npf"] == 130
    assert by_code["TVA"]["base_value_zlecaf"] == 100
    assert dual["summary"]["npf"]["total_taxes_et_droits"] == 43
    assert dual["summary"]["zlecaf"]["total_taxes_et_droits"] == 10
    assert dual["summary"]["economie_totale"] == 33


@pytest.mark.parametrize("exemptions", [None, set(), {"UNRELATED"}])
def test_no_documented_exemption_keeps_daps_in_both_regimes(exemptions):
    dual = compute_dual_breakdown(100, _lines(), 10, 0, zlecaf_exempt_codes=exemptions)
    daps = next(row for row in dual["breakdown"] if row["code"] == "DAPS")
    assert daps["amount_npf"] == daps["amount_zlecaf"] == 20
    assert dual["summary"]["zlecaf"]["total_taxes_et_droits"] == 32


def test_exemption_keeps_npf_cap_and_normalizes_codes():
    dual = compute_dual_breakdown(
        100, _lines(), 10, 0, caps={"DAPS": 15}, zlecaf_exempt_codes={" daps "}
    )
    daps = next(row for row in dual["breakdown"] if row["code"] == "DAPS")
    assert daps["amount_npf"] == 15
    assert daps["amount_zlecaf"] == 0


def test_customs_duty_uses_explicit_rate_parameter():
    with pytest.raises(ValueError, match="zlecaf_dd_rate_pct"):
        compute_dual_breakdown(100, _lines(), 10, 5, zlecaf_exempt_codes={"DD"})
