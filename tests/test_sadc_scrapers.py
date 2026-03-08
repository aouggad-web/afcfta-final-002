"""
Tests for SADC Scrapers
========================
Unit tests for:
  - south_africa_sadc_scraper (ZAF reference scraper)
  - sadc_member_scraper (all 16 SADC countries)
  - sacu_customs_union (SACU framework and calculations)
"""

import json
import os
import sys
import tempfile
import pytest

# ---------------------------------------------------------------------------
# Path setup
# ---------------------------------------------------------------------------
BACKEND_DIR = os.path.join(os.path.dirname(__file__), '..', 'backend')
sys.path.insert(0, BACKEND_DIR)


# ===========================================================================
# South Africa SADC Scraper
# ===========================================================================

class TestSouthAfricaSADCScraper:
    """Tests for south_africa_sadc_scraper.py"""

    def test_import(self):
        from crawlers.countries.south_africa_sadc_scraper import (
            SOUTH_AFRICA_SADC_TARIFFS,
            HS_CHAPTER_RATES,
            build_positions,
        )
        assert SOUTH_AFRICA_SADC_TARIFFS is not None

    def test_tariff_structure_keys(self):
        from crawlers.countries.south_africa_sadc_scraper import SOUTH_AFRICA_SADC_TARIFFS
        assert "sacu_cet" in SOUTH_AFRICA_SADC_TARIFFS
        assert "sadc_preferences" in SOUTH_AFRICA_SADC_TARIFFS
        assert "additional_duties" in SOUTH_AFRICA_SADC_TARIFFS

    def test_sacu_cet_bands(self):
        from crawlers.countries.south_africa_sadc_scraper import SOUTH_AFRICA_SADC_TARIFFS
        cet = SOUTH_AFRICA_SADC_TARIFFS["sacu_cet"]
        assert cet["raw_materials"] == 0.0
        assert cet["intermediate_goods"] == 5.0
        assert cet["final_goods"] == 15.0
        assert cet["luxury_goods"] == 30.0
        assert cet["automotive"] == 25.0
        assert cet["textiles"] == 22.0

    def test_sadc_preferences(self):
        from crawlers.countries.south_africa_sadc_scraper import SOUTH_AFRICA_SADC_TARIFFS
        prefs = SOUTH_AFRICA_SADC_TARIFFS["sadc_preferences"]
        assert prefs["intra_sadc_reduction"] == 0.85
        assert prefs["ldc_preference"] == 0.70
        assert prefs["sensitive_products"] == 1.0

    def test_build_positions_returns_list(self):
        from crawlers.countries.south_africa_sadc_scraper import build_positions
        positions = build_positions()
        assert isinstance(positions, list)
        assert len(positions) > 0

    def test_position_structure(self):
        from crawlers.countries.south_africa_sadc_scraper import build_positions
        positions = build_positions()
        pos = positions[0]
        assert "code" in pos
        assert "chapter" in pos
        assert "description" in pos
        assert "taxes" in pos
        assert "CET" in pos["taxes"]
        assert "VAT" in pos["taxes"]

    def test_vat_rate(self):
        from crawlers.countries.south_africa_sadc_scraper import build_positions
        positions = build_positions()
        for pos in positions:
            assert pos["taxes"]["VAT"] == 15.0

    def test_chapter_to_section_mapping(self):
        from crawlers.countries.south_africa_sadc_scraper import _chapter_to_section
        assert "Live Animals" in _chapter_to_section("01")
        assert "Vehicles" in _chapter_to_section("87")
        assert "Textiles" in _chapter_to_section("61")

    def test_run_scraper_creates_file(self):
        from crawlers.countries.south_africa_sadc_scraper import run_scraper
        import crawlers.countries.south_africa_sadc_scraper as mod

        with tempfile.TemporaryDirectory() as tmpdir:
            original = mod.OUTPUT_DIR
            mod.OUTPUT_DIR = tmpdir
            try:
                result = run_scraper()
            finally:
                mod.OUTPUT_DIR = original

        assert result["country"] == "ZAF"
        assert "positions" in result
        assert result["stats"]["total_positions"] > 0

    def test_hs_chapter_rates_coverage(self):
        from crawlers.countries.south_africa_sadc_scraper import HS_CHAPTER_RATES
        # Must cover key industries
        assert "87" in HS_CHAPTER_RATES  # Automotive
        assert "61" in HS_CHAPTER_RATES  # Textiles
        assert "84" in HS_CHAPTER_RATES  # Machinery
        assert "71" in HS_CHAPTER_RATES  # Diamonds


# ===========================================================================
# SADC Member Scraper
# ===========================================================================

class TestSADCMemberScraper:
    """Tests for sadc_member_scraper.py"""

    def test_import(self):
        from crawlers.countries.sadc_member_scraper import COUNTRY_CONFIGS
        assert COUNTRY_CONFIGS is not None

    def test_all_15_non_zaf_countries_configured(self):
        """ZAF is covered by south_africa_sadc_scraper; check remaining 15."""
        from crawlers.countries.sadc_member_scraper import COUNTRY_CONFIGS
        expected = {
            "BWA", "NAM", "LSO", "SWZ",  # SACU
            "AGO", "ZMB", "ZWE", "COD",  # Resource
            "MUS", "SYC", "COM",           # Islands
            "MOZ", "MDG", "MWI", "TZA",   # Emerging
        }
        assert expected.issubset(set(COUNTRY_CONFIGS.keys()))

    def test_sacu_countries_have_cet_flag(self):
        from crawlers.countries.sadc_member_scraper import COUNTRY_CONFIGS
        for code in ["BWA", "NAM", "LSO", "SWZ"]:
            assert COUNTRY_CONFIGS[code]["is_sacu"] is True

    def test_non_sacu_countries_no_cet_flag(self):
        from crawlers.countries.sadc_member_scraper import COUNTRY_CONFIGS
        for code in ["AGO", "ZMB", "MUS", "TZA"]:
            assert COUNTRY_CONFIGS[code]["is_sacu"] is False

    def test_ldc_flags(self):
        from crawlers.countries.sadc_member_scraper import COUNTRY_CONFIGS
        ldc_countries = {"AGO", "ZMB", "COD", "LSO", "MOZ", "MDG", "MWI", "TZA", "COM"}
        for code in ldc_countries:
            assert COUNTRY_CONFIGS[code].get("is_ldc") is True

    def test_build_sacu_country_data(self):
        from crawlers.countries.sadc_member_scraper import build_country_data
        data = build_country_data("BWA")
        assert data is not None
        assert data["country"] == "BWA"
        assert data["is_sacu"] is True
        assert data["vat_rate"] == 12.0
        assert len(data["positions"]) > 0

    def test_build_non_sacu_country_data(self):
        from crawlers.countries.sadc_member_scraper import build_country_data
        data = build_country_data("ZMB")
        assert data is not None
        assert data["country"] == "ZMB"
        assert data["is_sacu"] is False
        assert data["vat_rate"] == 16.0

    def test_position_structure_sacu(self):
        from crawlers.countries.sadc_member_scraper import build_country_data
        data = build_country_data("NAM")
        pos = data["positions"][0]
        assert "code" in pos
        assert "taxes" in pos
        assert "CET" in pos["taxes"]
        assert "VAT" in pos["taxes"]

    def test_position_structure_non_sacu(self):
        from crawlers.countries.sadc_member_scraper import build_country_data
        data = build_country_data("MOZ")
        pos = data["positions"][0]
        assert "code" in pos
        assert "taxes" in pos
        assert "CD" in pos["taxes"] or "DD" in pos["taxes"]

    def test_dual_membership_tza(self):
        from crawlers.countries.sadc_member_scraper import COUNTRY_CONFIGS
        assert "EAC" in COUNTRY_CONFIGS["TZA"]["dual_membership"]

    def test_dual_membership_cod(self):
        from crawlers.countries.sadc_member_scraper import COUNTRY_CONFIGS
        assert "EAC" in COUNTRY_CONFIGS["COD"]["dual_membership"]

    def test_run_all_creates_files(self):
        from crawlers.countries.sadc_member_scraper import run_all
        with tempfile.TemporaryDirectory() as tmpdir:
            results = run_all(countries=["BWA", "NAM"], output_dir=tmpdir)
            assert results["BWA"] is True
            assert results["NAM"] is True
            assert os.path.exists(os.path.join(tmpdir, "BWA_tariffs.json"))

    def test_unknown_country_returns_none(self):
        from crawlers.countries.sadc_member_scraper import build_country_data
        result = build_country_data("XXX")
        assert result is None


# ===========================================================================
# SADC Constants
# ===========================================================================

class TestSADCConstants:
    """Tests for sadc/sadc_constants.py"""

    def test_import(self):
        from crawlers.countries.sadc.sadc_constants import (
            SADC_COUNTRIES, SACU_MEMBERS, LDC_MEMBERS, SADC_ORG, SACU_ORG
        )
        assert SADC_COUNTRIES is not None

    def test_16_member_states(self):
        from crawlers.countries.sadc.sadc_constants import SADC_COUNTRIES
        assert len(SADC_COUNTRIES) == 16

    def test_sacu_has_5_members(self):
        from crawlers.countries.sadc.sadc_constants import SACU_MEMBERS
        assert len(SACU_MEMBERS) == 5
        assert "ZAF" in SACU_MEMBERS

    def test_country_structure(self):
        from crawlers.countries.sadc.sadc_constants import SADC_COUNTRIES
        for code, info in SADC_COUNTRIES.items():
            assert "country_name" in info
            assert "currency" in info
            assert "phase" in info
            assert info["phase"] in [1, 2, 3, 4]

    def test_dual_membership_handling(self):
        from crawlers.countries.sadc.sadc_constants import DUAL_EAC_SADC, SADC_COUNTRIES
        assert "TZA" in DUAL_EAC_SADC
        assert "COD" in DUAL_EAC_SADC
        assert "EAC" in SADC_COUNTRIES["TZA"]["dual_membership"]
