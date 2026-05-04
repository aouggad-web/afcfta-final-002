"""
Tests for SACU Customs Union Integration
==========================================
Tests for sacu_customs_union.py covering:
  - Framework data structure
  - Revenue sharing configuration
  - CET rate lookups
  - SADC preferential rate calculations
  - Total landed cost calculations
  - Framework summary generation
"""

import sys
import os
import pytest

BACKEND_DIR = os.path.join(os.path.dirname(__file__), '..', 'backend')
sys.path.insert(0, BACKEND_DIR)


# ===========================================================================
# Framework structure
# ===========================================================================

class TestSACUFrameworkStructure:
    """Validate the SACU framework data structure."""

    def test_import(self):
        from crawlers.countries.sacu_customs_union import SACU_FRAMEWORK
        assert SACU_FRAMEWORK is not None

    def test_framework_keys(self):
        from crawlers.countries.sacu_customs_union import SACU_FRAMEWORK
        assert "name" in SACU_FRAMEWORK
        assert "members" in SACU_FRAMEWORK
        assert "revenue_sharing" in SACU_FRAMEWORK
        assert "harmonised_policies" in SACU_FRAMEWORK
        assert "common_external_tariff" in SACU_FRAMEWORK
        assert "free_internal_trade" in SACU_FRAMEWORK

    def test_five_sacu_members(self):
        from crawlers.countries.sacu_customs_union import SACU_FRAMEWORK
        members = SACU_FRAMEWORK["members"]
        assert len(members) == 5
        for code in ["ZAF", "BWA", "NAM", "LSO", "SWZ"]:
            assert code in members

    def test_common_external_tariff_true(self):
        from crawlers.countries.sacu_customs_union import SACU_FRAMEWORK
        assert SACU_FRAMEWORK["common_external_tariff"] is True

    def test_free_internal_trade_true(self):
        from crawlers.countries.sacu_customs_union import SACU_FRAMEWORK
        assert SACU_FRAMEWORK["free_internal_trade"] is True

    def test_revenue_sharing_components(self):
        from crawlers.countries.sacu_customs_union import SACU_FRAMEWORK
        rs = SACU_FRAMEWORK["revenue_sharing"]
        assert "customs_component" in rs
        assert "excise_component" in rs
        assert "development_component" in rs
        assert "distribution_formula" in rs


# ===========================================================================
# Revenue shares
# ===========================================================================

class TestSACURevenueShares:
    def test_all_five_countries_have_shares(self):
        from crawlers.countries.sacu_customs_union import SACU_REVENUE_SHARES
        for code in ["ZAF", "BWA", "NAM", "LSO", "SWZ"]:
            assert code in SACU_REVENUE_SHARES

    def test_revenue_share_structure(self):
        from crawlers.countries.sacu_customs_union import SACU_REVENUE_SHARES
        for code, shares in SACU_REVENUE_SHARES.items():
            assert "customs_share_pct" in shares
            assert "excise_share_pct" in shares
            assert isinstance(shares["customs_share_pct"], (int, float))

    def test_south_africa_largest_share(self):
        from crawlers.countries.sacu_customs_union import SACU_REVENUE_SHARES
        zaf_share = SACU_REVENUE_SHARES["ZAF"]["customs_share_pct"]
        for code in ["BWA", "NAM", "LSO", "SWZ"]:
            assert zaf_share > SACU_REVENUE_SHARES[code]["customs_share_pct"]

    def test_blns_have_development_component(self):
        from crawlers.countries.sacu_customs_union import SACU_REVENUE_SHARES
        for code in ["BWA", "LSO", "NAM", "SWZ"]:
            assert SACU_REVENUE_SHARES[code].get("development_share_pct", 0) > 0


# ===========================================================================
# CET rate lookups
# ===========================================================================

class TestSACUCETRates:
    def test_automotive_chapter_87(self):
        from crawlers.countries.sacu_customs_union import get_cet_rate
        assert get_cet_rate("87") == 25.0

    def test_textiles_chapter_61(self):
        from crawlers.countries.sacu_customs_union import get_cet_rate
        assert get_cet_rate("61") == 22.0

    def test_tobacco_chapter_24(self):
        from crawlers.countries.sacu_customs_union import get_cet_rate
        assert get_cet_rate("24") == 30.0

    def test_raw_materials_chapter_01(self):
        from crawlers.countries.sacu_customs_union import get_cet_rate
        assert get_cet_rate("01") == 0.0

    def test_pharmaceutical_chapter_30(self):
        from crawlers.countries.sacu_customs_union import get_cet_rate
        assert get_cet_rate("30") == 0.0

    def test_machinery_chapter_84(self):
        from crawlers.countries.sacu_customs_union import get_cet_rate
        assert get_cet_rate("84") == 0.0

    def test_luxury_goods_chapter_42(self):
        from crawlers.countries.sacu_customs_union import get_cet_rate
        assert get_cet_rate("42") == 30.0


# ===========================================================================
# SADC preferential rates
# ===========================================================================

class TestSACUPreferentialRates:
    def test_sacu_member_gets_zero(self):
        from crawlers.countries.sacu_customs_union import get_sadc_preferential_rate
        rate = get_sadc_preferential_rate(20.0, "BWA")
        assert rate == 0.0

    def test_ldc_gets_30_percent_reduction(self):
        from crawlers.countries.sacu_customs_union import get_sadc_preferential_rate
        rate = get_sadc_preferential_rate(20.0, "ZMB")
        assert rate == 14.0  # 20 * 0.70

    def test_non_ldc_non_sacu_gets_15_percent_reduction(self):
        from crawlers.countries.sacu_customs_union import get_sadc_preferential_rate
        rate = get_sadc_preferential_rate(20.0, "ZWE")
        assert rate == 17.0  # 20 * 0.85

    def test_mauritius_non_sacu_non_ldc(self):
        from crawlers.countries.sacu_customs_union import get_sadc_preferential_rate
        rate = get_sadc_preferential_rate(10.0, "MUS")
        assert rate == 8.5  # 10 * 0.85


# ===========================================================================
# Import cost calculation
# ===========================================================================

class TestSACUImportCost:
    def test_basic_calculation_returns_dict(self):
        from crawlers.countries.sacu_customs_union import calculate_total_import_cost
        result = calculate_total_import_cost(1000.0, "87", "ZAF", "INTL")
        assert isinstance(result, dict)

    def test_required_keys_present(self):
        from crawlers.countries.sacu_customs_union import calculate_total_import_cost
        result = calculate_total_import_cost(1000.0, "87", "ZAF", "INTL")
        for key in ["cif_value", "customs_duty", "vat", "total_landed_cost", "effective_rate_pct"]:
            assert key in result

    def test_sacu_origin_zero_duty(self):
        from crawlers.countries.sacu_customs_union import calculate_total_import_cost
        result = calculate_total_import_cost(1000.0, "87", "ZAF", "BWA")
        assert result["customs_duty"] == 0.0
        assert result["applied_duty_rate_pct"] == 0.0

    def test_intl_origin_full_cet(self):
        from crawlers.countries.sacu_customs_union import calculate_total_import_cost
        result = calculate_total_import_cost(1000.0, "87", "ZAF", "INTL")
        assert result["cet_rate_pct"] == 25.0
        assert result["customs_duty"] == 250.0

    def test_vat_applied_on_cif_plus_duty(self):
        from crawlers.countries.sacu_customs_union import calculate_total_import_cost
        result = calculate_total_import_cost(1000.0, "87", "ZAF", "INTL")
        expected_vat = (1000.0 + 250.0) * 0.15
        assert abs(result["vat"] - expected_vat) < 0.01

    def test_total_is_cif_plus_duty_plus_vat(self):
        from crawlers.countries.sacu_customs_union import calculate_total_import_cost
        result = calculate_total_import_cost(1000.0, "84", "ZAF", "INTL")
        expected_total = result["cif_value"] + result["customs_duty"] + result["vat"]
        assert abs(result["total_landed_cost"] - expected_total) < 0.01

    def test_zero_rate_raw_material(self):
        from crawlers.countries.sacu_customs_union import calculate_total_import_cost
        result = calculate_total_import_cost(1000.0, "84", "ZAF", "INTL")
        assert result["customs_duty"] == 0.0

    def test_effective_rate_positive(self):
        from crawlers.countries.sacu_customs_union import calculate_total_import_cost
        result = calculate_total_import_cost(1000.0, "87", "ZAF", "INTL")
        assert result["effective_rate_pct"] > 0


# ===========================================================================
# Summary generation
# ===========================================================================

class TestSACUSummary:
    def test_generate_summary(self):
        from crawlers.countries.sacu_customs_union import generate_sacu_summary
        summary = generate_sacu_summary()
        assert "framework" in summary
        assert "revenue_shares" in summary
        assert "cet_bands" in summary
        assert "generated_at" in summary

    def test_run_scraper_returns_dict(self):
        import tempfile
        from crawlers.countries import sacu_customs_union as mod
        from crawlers.countries.sacu_customs_union import run_scraper

        with tempfile.TemporaryDirectory() as tmpdir:
            original = mod.OUTPUT_DIR
            mod.OUTPUT_DIR = tmpdir
            try:
                result = run_scraper()
            finally:
                mod.OUTPUT_DIR = original

        assert "framework" in result
        assert result["framework"]["member_count"] == 5
