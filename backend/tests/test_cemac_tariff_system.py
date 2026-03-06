"""
Tests for the CEMAC Tariff System — "what data we get now".

Covers:
- CEMAC country configurations (6 member states)
- Data file existence and structure
- Tax structure validation per country
- Route response shapes for /cemac/countries, /cemac/data-summary, /cemac/data/{cc}
"""

import sys
import os
import json
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

DATA_CRAWLED = os.path.join(os.path.dirname(__file__), "..", "data", "crawled")

CEMAC_CODES = ["CMR", "CAF", "COG", "GAB", "GNQ", "TCD"]


# ==================== Country Config Tests ====================

class TestCEMACCountryConfigs:
    """All 6 CEMAC member states must be registered with the required metadata."""

    def _get_cemac_countries(self):
        from routes.cemac_crawlers import CEMAC_COUNTRIES
        return CEMAC_COUNTRIES

    def test_all_six_members_present(self):
        cfg = self._get_cemac_countries()
        assert set(cfg.keys()) == {"CMR", "CAF", "COG", "GAB", "GNQ", "TCD"}

    def test_every_country_has_required_fields(self):
        cfg = self._get_cemac_countries()
        required = {"iso3", "country_name", "country_name_en", "primary_source",
                    "currency", "tva_rate", "national_taxes", "dd_bands"}
        for cc, info in cfg.items():
            missing = required - set(info.keys())
            assert not missing, f"{cc} is missing fields: {missing}"

    def test_all_use_xaf_currency(self):
        cfg = self._get_cemac_countries()
        for cc, info in cfg.items():
            assert "XAF" in info["currency"], f"{cc} should use XAF"

    def test_all_have_cemac_dd_bands(self):
        cfg = self._get_cemac_countries()
        for cc, info in cfg.items():
            assert info["dd_bands"] == [0, 5, 10, 20, 30], f"{cc} DD bands wrong"

    def test_all_have_tci_national_tax(self):
        cfg = self._get_cemac_countries()
        for cc, info in cfg.items():
            assert "TCI" in info["national_taxes"], f"{cc} missing TCI"
            assert info["national_taxes"]["TCI"] == 1.0, f"{cc} TCI must be 1%"

    def test_tva_rates_in_valid_range(self):
        cfg = self._get_cemac_countries()
        for cc, info in cfg.items():
            assert 14.0 <= info["tva_rate"] <= 25.0, f"{cc} TVA rate out of range"

    def test_all_have_afcfta_agreement(self):
        cfg = self._get_cemac_countries()
        for cc, info in cfg.items():
            agreements = " ".join(info.get("preferential_agreements", []))
            assert "AfCFTA" in agreements or "ZLECAf" in agreements, \
                f"{cc} should include AfCFTA/ZLECAf"

    # ---- Country-specific checks ----

    def test_cmr_tva_is_19_25(self):
        cfg = self._get_cemac_countries()
        assert cfg["CMR"]["tva_rate"] == 19.25

    def test_gnq_tva_is_15(self):
        cfg = self._get_cemac_countries()
        assert cfg["GNQ"]["tva_rate"] == 15.0

    def test_gab_and_cog_tva_is_18(self):
        cfg = self._get_cemac_countries()
        assert cfg["GAB"]["tva_rate"] == 18.0
        assert cfg["COG"]["tva_rate"] == 18.0

    def test_tcd_has_ts_national_tax(self):
        cfg = self._get_cemac_countries()
        assert "TS" in cfg["TCD"]["national_taxes"]


# ==================== Data File Tests ====================

class TestCEMACDataFiles:
    """Validate that crawled data files exist and have the required structure."""

    def _load(self, country_code: str) -> dict:
        path = os.path.join(DATA_CRAWLED, f"{country_code}_tariffs.json")
        assert os.path.exists(path), f"Data file missing for {country_code}: {path}"
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)

    def test_all_cemac_data_files_exist(self):
        for cc in CEMAC_CODES:
            path = os.path.join(DATA_CRAWLED, f"{cc}_tariffs.json")
            assert os.path.exists(path), f"Missing data file: {cc}_tariffs.json"

    def test_data_files_have_tariff_lines_or_positions(self):
        for cc in CEMAC_CODES:
            data = self._load(cc)
            has_lines = "tariff_lines" in data or "positions" in data
            assert has_lines, f"{cc}: missing 'tariff_lines' or 'positions' key"

    def test_minimum_tariff_line_count(self):
        for cc in CEMAC_CODES:
            data = self._load(cc)
            lines = data.get("tariff_lines", data.get("positions", []))
            assert len(lines) >= 5000, f"{cc}: only {len(lines)} lines (expected ≥5000)"

    def test_cmr_data_summary_present(self):
        data = self._load("CMR")
        # CMR in crawled/ uses old format — has top-level metadata, no nested summary
        has_metadata = "total_positions" in data or "positions" in data
        assert has_metadata, "CMR data should have positions or total_positions"

    def test_cmr_summary_chapters_covered(self):
        data = self._load("CMR")
        lines = data.get("positions", data.get("tariff_lines", []))
        chapters = {str(p.get("chapter", ""))[:2] for p in lines if p.get("chapter")}
        assert len(chapters) >= 90, f"CMR should cover ≥90 chapters, got {len(chapters)}"

    def test_cmr_summary_dd_rate_range(self):
        data = self._load("CMR")
        lines = data.get("positions", data.get("tariff_lines", []))
        if lines and "taxes" in lines[0]:
            # old format
            dd_rates = [p["taxes"].get("DD", 0) for p in lines if "taxes" in p]
        else:
            # enhanced v2
            dd_rates = [p.get("dd_rate", 0) for p in lines]
        assert min(dd_rates) >= 0
        assert max(dd_rates) <= 30

    def test_tariff_line_has_required_fields(self):
        for cc in CEMAC_CODES:
            data = self._load(cc)
            lines = data.get("tariff_lines", data.get("positions", []))
            assert lines, f"{cc}: no tariff lines"
            sample = lines[0]

            if data.get("data_format") == "enhanced_v2":
                required = {"hs6", "chapter", "dd_rate", "vat_rate", "total_taxes_pct"}
            else:
                required = {"code", "chapter", "taxes", "taxes_detail"}

            missing = required - set(sample.keys())
            assert not missing, f"{cc} sample line missing fields: {missing}"

    def test_enhanced_v2_dd_rate_in_cemac_bands(self):
        """DD rates must be within the CEMAC TEC bands: 0, 5, 10, 20, 30."""
        valid_dd = {0.0, 5.0, 10.0, 20.0, 30.0}
        for cc in CEMAC_CODES:
            data = self._load(cc)
            if data.get("data_format") != "enhanced_v2":
                continue
            lines = data.get("tariff_lines", [])
            for line in lines[:200]:  # sample check
                dd = line.get("dd_rate")
                if dd is not None:
                    assert dd in valid_dd, \
                        f"{cc}: unexpected DD rate {dd} (valid: {valid_dd})"

    def test_old_format_taxes_have_dd_and_tva(self):
        """Old-format files should have DD and TVA in their taxes dict."""
        for cc in CEMAC_CODES:
            data = self._load(cc)
            if data.get("data_format") == "enhanced_v2":
                continue
            lines = data.get("positions", [])
            if not lines:
                continue
            sample_with_taxes = next(
                (ln for ln in lines[:50] if "taxes" in ln), None
            )
            if sample_with_taxes:
                taxes = sample_with_taxes["taxes"]
                assert "DD" in taxes, f"{cc}: missing DD tax"
                assert "TVA" in taxes, f"{cc}: missing TVA tax"

    def test_enhanced_v2_zlecaf_rate_present(self):
        """Enhanced v2 files should include ZLECAf preferential rate."""
        for cc in CEMAC_CODES:
            data = self._load(cc)
            if data.get("data_format") != "enhanced_v2":
                continue
            lines = data.get("tariff_lines", [])
            assert lines
            assert "zlecaf_rate" in lines[0], f"{cc}: missing zlecaf_rate"
            assert "zlecaf_total_taxes" in lines[0], f"{cc}: missing zlecaf_total_taxes"

    def test_enhanced_v2_fiscal_advantages_present(self):
        """Enhanced v2 files should include AfCFTA fiscal advantages."""
        for cc in CEMAC_CODES:
            data = self._load(cc)
            if data.get("data_format") != "enhanced_v2":
                continue
            lines = data.get("tariff_lines", [])
            assert lines
            assert "fiscal_advantages" in lines[0], f"{cc}: missing fiscal_advantages"

    def test_gnq_data_is_enhanced_v2(self):
        """GNQ should be the enhanced v2 format."""
        data = self._load("GNQ")
        assert data.get("data_format") == "enhanced_v2"


# ==================== Route Tests ====================

class TestCEMACRoutes:
    """Validate the cemac_crawlers route helpers and config functions."""

    def test_get_cemac_countries_structure(self):
        from routes.cemac_crawlers import get_cemac_countries
        result = get_cemac_countries()
        assert "region" in result
        assert "total_countries" in result
        assert result["total_countries"] == 6
        assert "countries" in result
        assert len(result["countries"]) == 6

    def test_get_cemac_countries_has_dd_bands(self):
        from routes.cemac_crawlers import get_cemac_countries
        result = get_cemac_countries()
        assert result["dd_bands_pct"] == [0, 5, 10, 20, 30]

    def test_get_cemac_countries_common_tci(self):
        from routes.cemac_crawlers import get_cemac_countries
        result = get_cemac_countries()
        assert "TCI" in result["common_taxes"]

    def test_data_summary_has_all_six_countries(self):
        from routes.cemac_crawlers import get_cemac_data_summary
        result = get_cemac_data_summary()
        assert result["total_countries"] == 6
        assert len(result["countries"]) == 6

    def test_data_summary_countries_have_data(self):
        from routes.cemac_crawlers import get_cemac_data_summary
        result = get_cemac_data_summary()
        available = [c for c in result["countries"] if c["status"] == "available"]
        assert len(available) == 6, \
            f"Expected 6 countries with data, got {len(available)}"

    def test_data_summary_total_lines_positive(self):
        from routes.cemac_crawlers import get_cemac_data_summary
        result = get_cemac_data_summary()
        assert result["total_tariff_lines"] > 0

    def test_data_summary_country_entry_fields(self):
        from routes.cemac_crawlers import get_cemac_data_summary
        result = get_cemac_data_summary()
        required = {"iso3", "status", "tariff_lines", "chapters_covered"}
        for entry in result["countries"]:
            missing = required - set(entry.keys())
            assert not missing, f"{entry.get('iso3')}: missing {missing}"

    def test_data_summary_cmr_has_expected_line_count(self):
        from routes.cemac_crawlers import get_cemac_data_summary
        result = get_cemac_data_summary()
        cmr = next(c for c in result["countries"] if c["iso3"] == "CMR")
        assert cmr["tariff_lines"] >= 5000

    def test_data_summary_has_cemac_tec_note(self):
        from routes.cemac_crawlers import get_cemac_data_summary
        result = get_cemac_data_summary()
        assert "cemac_tec_note" in result

    # ---- country_data_summary helper (low-level) ----

    def test_country_data_summary_cmr(self):
        from routes.cemac_crawlers import _country_data_summary
        entry = _country_data_summary("CMR")
        assert entry["iso3"] == "CMR"
        assert entry["status"] == "available"
        assert entry["tariff_lines"] >= 5000

    def test_country_data_summary_all_available(self):
        from routes.cemac_crawlers import _country_data_summary
        for cc in CEMAC_CODES:
            entry = _country_data_summary(cc)
            assert entry["status"] == "available", f"{cc}: status={entry['status']}"

    def test_country_data_summary_gnq_enhanced(self):
        from routes.cemac_crawlers import _country_data_summary
        entry = _country_data_summary("GNQ")
        assert entry["data_format"] == "enhanced_v2"

    def test_country_data_summary_cmr_chapters(self):
        from routes.cemac_crawlers import _country_data_summary
        entry = _country_data_summary("CMR")
        assert entry["chapters_covered"] >= 90

    def test_country_data_summary_fields_available(self):
        from routes.cemac_crawlers import _country_data_summary
        entry = _country_data_summary("CMR")
        assert "fields_available" in entry
        assert len(entry["fields_available"]) > 0

    def test_load_country_file_all_cemac(self):
        from routes.cemac_crawlers import _load_country_file
        for cc in CEMAC_CODES:
            data = _load_country_file(cc)
            assert data is not None, f"{cc}: _load_country_file returned None"

    def test_load_country_file_unknown_returns_none(self):
        from routes.cemac_crawlers import _load_country_file
        assert _load_country_file("XXX") is None
