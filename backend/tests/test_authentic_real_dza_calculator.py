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

    Depuis l'audit P0 du 2026-09-01, DZA n'est plus servi par le dataset
    généré `enhanced_v2` mais par le crawl authentique DGD/conformepro.dz
    (voir `backend/data/archive/superseded/README.md`). Pour cette ligne,
    la source officielle publie : DD 5 %, TCS 3 %, TVA 9 % sur CIF + DAPS
    + DD, PRCT 2 % sur CIF + DD + TCS + TVA. Un partenaire ZLECAf actif
    (EGY) élimine le DD, recalcule les bases dépendantes et alimente les
    montants locaux DZD depuis le bloc FX.
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

    assert result["rates"]["dd_rate_pct"] == 5.0
    assert result["rates"]["effective_zlecaf_rate_pct"] == 0.0
    assert result["rates"]["tcs_rate_pct"] == 3.0
    assert result["rates"]["prct_rate_pct"] == 2.0
    assert result["rates"]["vat_rate_pct"] == 9.0
    assert result["rates"]["effective_rate_pct"] == 19.80

    by_code = {row["code"]: row for row in result["taxes_breakdown"]}
    assert set(by_code) == {"DD", "TCS", "TVA", "PRCT"}

    assert by_code["DD"]["amount_npf"] == 50_000.0
    assert by_code["DD"]["amount_zlecaf"] == 0.0
    assert by_code["DD"]["affected_by_zlecaf"] is True

    assert by_code["TCS"]["amount_npf"] == 30_000.0
    assert by_code["TCS"]["amount_zlecaf"] == 30_000.0
    assert by_code["TCS"]["affected_by_zlecaf"] is False

    assert by_code["TVA"]["base_expr"] == "CIF + DAPS + DD"
    assert by_code["TVA"]["base_value_npf"] == 1_050_000.0
    assert by_code["TVA"]["base_value_zlecaf"] == 1_000_000.0
    assert by_code["TVA"]["amount_npf"] == 94_500.0
    assert by_code["TVA"]["amount_zlecaf"] == 90_000.0

    assert by_code["PRCT"]["base_expr"] == "CIF + DD + TCS + TVA"
    assert by_code["PRCT"]["base_value_npf"] == 1_174_500.0
    assert by_code["PRCT"]["base_value_zlecaf"] == 1_120_000.0
    assert by_code["PRCT"]["amount_npf"] == 23_490.0
    assert by_code["PRCT"]["amount_zlecaf"] == 22_400.0

    summary = result["taxes_summary"]
    assert summary["npf"]["total_taxes_et_droits"] == 197_990.0
    assert summary["npf"]["cout_total"] == 1_197_990.0
    assert summary["zlecaf"]["total_taxes_et_droits"] == 142_400.0
    assert summary["zlecaf"]["cout_total"] == 1_142_400.0
    assert summary["economie_droits"] == 50_000.0
    assert summary["economie_totale"] == 55_590.0
    assert result["savings"] == {"amount": 55_590.0, "percentage": 4.64}

    currency = result["currency"]
    assert currency["available"] is True
    assert currency["local_code"] == "DZD"
    assert currency["usd_to_local_rate"] == 150.0
    assert currency["value_local"] == 150_000_000.0
    assert by_code["DD"]["amount_npf_local"] == 7_500_000.0
    assert by_code["TVA"]["amount_zlecaf_local"] == 13_500_000.0
    assert currency["summary_local"]["npf"]["cout_total"] == 179_698_500.0
    assert currency["summary_local"]["zlecaf"]["cout_total"] == 171_360_000.0
    assert currency["summary_local"]["economie_totale"] == 8_338_500.0
