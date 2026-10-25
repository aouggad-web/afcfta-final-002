"""
Tests for SACU Customs Union Integration
==========================================
Tests for sacu_customs_union.py covering:
  - Framework data structure
  - Revenue sharing configuration
  - Framework summary generation
"""

import os
import sys

import pytest

BACKEND_DIR = os.path.join(os.path.dirname(__file__), "..", "backend")
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
# Summary generation
# ===========================================================================


class TestSACUSummary:
    def test_generate_summary(self):
        from crawlers.countries.sacu_customs_union import generate_sacu_summary

        summary = generate_sacu_summary()
        assert "framework" in summary
        assert "revenue_shares" in summary
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
