"""Regression tests for the real generated DZA tariff calculator path.

These tests deliberately exercise the production calculator chain used by the
frontend: authentic tariff data -> fiscal cascade -> dual-regime breakdown ->
local-currency conversion block. They protect the calculator axis without
introducing another calculation path.
"""

from datetime import datetime, timezone

import exchange_rates as exchange_rates_module
from services import authentic_tariff_service as svc


class _FakeRate:
    rate = 150.0
    source = "test_fixed_fx"
    timestamp = datetime(2026, 1, 1, tzinfo=timezone.utc)


class _FakeFxService:
    def get_rate(self, base, quote):
        assert base == "USD"
        assert quote == "DZD"
        return _FakeRate()


def test_real_dza_tariff_line_cascade_breakdown_and_local_currency(monkeypatch):
    """DZA 0101211100 must keep the authentic calculator as the reference path.

    The current generated DZA dataset has a 15% customs duty, 3% TCS, 19% VAT
    on CIF + DD, and 2% PRCT on CIF + DD + TCS + VAT for this line. For an
    active AfCFTA partner (EGY), DD is eliminated, dependent VAT/PRCT bases are
    recalculated, and local DZD amounts are populated from the FX block.
    """
    monkeypatch.setattr(exchange_rates_module, "get_service", lambda: _FakeFxService())

    result = svc.calculate_import_taxes(
        country_iso3="DZA",
        hs_code="0101211100",
        cif_value=1_000_000.0,
        language="fr",
        origin_country="EGY",
    )

    assert "error" not in result
    assert result["data_source"] == "authentic_tariff"
    assert result["data_format"] == "enhanced_v2"
    assert result["trade_regime"] == "ZLECAF"
    assert result["zlecaf_eligible"] is True
    assert result["zlecaf_preference_applied"] is True

    assert result["rates"]["dd_rate_pct"] == 15.0
    assert result["rates"]["effective_zlecaf_rate_pct"] == 0.0
    assert result["rates"]["tcs_rate_pct"] == 3.0
    assert result["rates"]["prct_rate_pct"] == 2.0
    assert result["rates"]["vat_rate_pct"] == 19.0
    assert result["rates"]["effective_rate_pct"] == 42.65

    by_code = {row["code"]: row for row in result["taxes_breakdown"]}
    assert set(by_code) == {"DD", "TCS", "TVA", "PRCT"}

    assert by_code["DD"]["amount_npf"] == 150_000.0
    assert by_code["DD"]["amount_zlecaf"] == 0.0
    assert by_code["DD"]["affected_by_zlecaf"] is True

    assert by_code["TCS"]["amount_npf"] == 30_000.0
    assert by_code["TCS"]["amount_zlecaf"] == 30_000.0
    assert by_code["TCS"]["affected_by_zlecaf"] is False

    assert by_code["TVA"]["base_expr"] == "CIF + DAPS + DD"
    assert by_code["TVA"]["base_value_npf"] == 1_150_000.0
    assert by_code["TVA"]["base_value_zlecaf"] == 1_000_000.0
    assert by_code["TVA"]["amount_npf"] == 218_500.0
    assert by_code["TVA"]["amount_zlecaf"] == 190_000.0

    assert by_code["PRCT"]["base_expr"] == "CIF + DD + TCS + TVA"
    assert by_code["PRCT"]["base_value_npf"] == 1_398_500.0
    assert by_code["PRCT"]["base_value_zlecaf"] == 1_220_000.0
    assert by_code["PRCT"]["amount_npf"] == 27_970.0
    assert by_code["PRCT"]["amount_zlecaf"] == 24_400.0

    summary = result["taxes_summary"]
    assert summary["npf"]["total_taxes_et_droits"] == 426_470.0
    assert summary["npf"]["cout_total"] == 1_426_470.0
    assert summary["zlecaf"]["total_taxes_et_droits"] == 244_400.0
    assert summary["zlecaf"]["cout_total"] == 1_244_400.0
    assert summary["economie_droits"] == 150_000.0
    assert summary["economie_totale"] == 182_070.0
    assert result["savings"] == {"amount": 182_070.0, "percentage": 12.76}

    currency = result["currency"]
    assert currency["available"] is True
    assert currency["local_code"] == "DZD"
    assert currency["usd_to_local_rate"] == 150.0
    assert currency["value_local"] == 150_000_000.0
    assert by_code["DD"]["amount_npf_local"] == 22_500_000.0
    assert by_code["TVA"]["amount_zlecaf_local"] == 28_500_000.0
    assert currency["summary_local"]["npf"]["cout_total"] == 213_970_500.0
    assert currency["summary_local"]["zlecaf"]["cout_total"] == 186_660_000.0
    assert currency["summary_local"]["economie_totale"] == 27_310_500.0
