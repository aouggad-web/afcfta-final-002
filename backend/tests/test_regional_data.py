"""
Tests for the Regional Data Inventory — "how many sub-positions by country we get".

Covers:
- /api/regional/sub-positions endpoint
- /api/regional/data-inventory endpoint
- Sub-position counting helpers
- Cross-country format detection
"""

import sys
import os
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

CRAWLED_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "crawled")

# All 54 crawled countries are now enhanced_v2 with real tariff data.
ENHANCED_COUNTRIES = {
    # Originally enhanced_v2 (32)
    "AGO", "BDI", "COD", "COM", "CPV", "DJI", "EGY", "ERI", "ETH",
    "GHA", "GMB", "GNB", "GNQ", "KEN", "LBR", "LBY", "MDG", "MOZ",
    "MRT", "MUS", "MWI", "RWA", "SDN", "SLE", "SOM", "SSD", "STP",
    "SYC", "TZA", "UGA", "ZMB", "ZWE",
    # Migrated from old format to enhanced_v2 (19 with data)
    "BEN", "BFA", "BWA", "CAF", "CIV", "CMR", "COG", "GAB",
    "GIN", "LSO", "MLI", "NAM", "NER", "NGA", "SEN", "SWZ",
    "TCD", "TGO", "ZAF",
    # North Africa — previously empty, now populated from national sources
    "DZA", "MAR", "TUN",
}

# No countries remain empty or in old format
EMPTY_ENHANCED_COUNTRIES: set = set()

# No countries remain in old format
OLD_FORMAT_COUNTRIES: set = set()


# ==================== Helper Tests ====================

class TestRegionalDataHelpers:
    """Tests for the utility helpers in regional_data.py."""

    def test_iter_country_files_yields_countries(self):
        from routes.regional_data import _iter_country_files
        countries = list(_iter_country_files())
        codes = {cc for cc, _ in countries}
        assert len(codes) >= 50, f"Expected ≥50 countries, got {len(codes)}"

    def test_get_lines_tariff_lines_format(self):
        from routes.regional_data import _get_lines
        data = {"tariff_lines": [{"hs6": "010110"}]}
        assert len(_get_lines(data)) == 1

    def test_get_lines_positions_format(self):
        from routes.regional_data import _get_lines
        data = {"positions": [{"code": "0101.10.10"}]}
        assert len(_get_lines(data)) == 1

    def test_get_lines_empty(self):
        from routes.regional_data import _get_lines
        assert _get_lines({}) == []

    def test_count_sub_positions_old_format(self):
        from routes.regional_data import _count_sub_positions
        lines = [{"chapter": "01", "dd_rate": 20.0}]
        assert _count_sub_positions(lines, "old") == 0

    def test_count_sub_positions_enhanced_via_count_field(self):
        from routes.regional_data import _count_sub_positions
        lines = [{"sub_position_count": 3}, {"sub_position_count": 2}]
        assert _count_sub_positions(lines, "enhanced_v2") == 5

    def test_count_sub_positions_enhanced_via_list_field(self):
        from routes.regional_data import _count_sub_positions
        lines = [{"sub_positions": [{"code": "a"}, {"code": "b"}, {"code": "c"}]}]
        assert _count_sub_positions(lines, "enhanced_v2") == 3

    def test_count_sub_positions_enhanced_mixed_fields(self):
        from routes.regional_data import _count_sub_positions
        lines = [
            {"sub_position_count": 4},
            {"sub_positions": [{"code": "x"}, {"code": "y"}]},
            {},  # no sub-positions
        ]
        assert _count_sub_positions(lines, "enhanced_v2") == 6

    def test_build_country_entry_enhanced_v2(self):
        from routes.regional_data import _build_country_entry
        data = {
            "data_format": "enhanced_v2",
            "generated_at": "2026-01-01T00:00:00",
            "summary": {
                "total_tariff_lines": 2,
                "total_sub_positions": 5,
                "lines_with_sub_positions": 1,
                "chapters_covered": 3,
                "dd_rate_range": {},
            },
            "tariff_lines": [
                {"hs6": "010110", "chapter": "01", "sub_position_count": 3,
                 "has_sub_positions": True},
                {"hs6": "010120", "chapter": "01", "sub_position_count": 2,
                 "has_sub_positions": True},
            ],
        }
        entry = _build_country_entry("TST", data)
        assert entry["tariff_lines"] == 2
        assert entry["sub_positions"] == 5
        assert entry["status"] == "available"

    def test_build_country_entry_old_format(self):
        from routes.regional_data import _build_country_entry
        data = {
            "data_format": "old",
            "extracted_at": "2026-01-01T00:00:00",
            "positions": [
                {"code": "0101.10.10", "chapter": "01", "taxes": {"DD": 20}},
            ],
        }
        entry = _build_country_entry("TST", data)
        assert entry["sub_positions"] == 0
        assert entry["tariff_lines"] == 1
        assert entry["status"] == "available"

    def test_build_country_entry_empty(self):
        from routes.regional_data import _build_country_entry
        entry = _build_country_entry("TST", {"data_format": "old", "positions": []})
        assert entry["status"] == "empty"
        assert entry["tariff_lines"] == 0


# ==================== Sub-Positions Endpoint Tests ====================

class TestRegionalSubPositions:
    """Tests for GET /api/regional/sub-positions."""

    def _call(self, **kwargs):
        from routes.regional_data import _compute_sub_positions as get_regional_sub_positions
        return get_regional_sub_positions(**kwargs)

    def test_returns_expected_keys(self):
        result = self._call()
        assert "totals" in result
        assert "countries" in result
        assert "note" in result

    def test_totals_fields(self):
        result = self._call()
        totals = result["totals"]
        for field in ("total_countries", "countries_with_sub_positions",
                      "total_tariff_lines", "total_sub_positions",
                      "avg_sub_positions_per_line"):
            assert field in totals, f"Missing totals field: {field}"

    def test_at_least_50_countries(self):
        result = self._call()
        assert result["totals"]["total_countries"] >= 50

    def test_total_sub_positions_matches_sum(self):
        result = self._call()
        country_sum = sum(r["sub_positions"] for r in result["countries"])
        assert result["totals"]["total_sub_positions"] == country_sum

    def test_total_lines_matches_sum(self):
        result = self._call()
        line_sum = sum(r["tariff_lines"] for r in result["countries"])
        assert result["totals"]["total_tariff_lines"] == line_sum

    def test_enhanced_countries_have_sub_positions(self):
        result = self._call()
        by_code = {r["iso3"]: r for r in result["countries"]}
        for cc in ENHANCED_COUNTRIES:
            if cc in by_code:
                assert by_code[cc]["sub_positions"] > 0, \
                    f"{cc} (enhanced_v2) should have sub-positions"

    def test_north_africa_countries_have_sub_positions(self):
        """DZA, MAR, TUN are now populated with real tariff data."""
        result = self._call()
        by_code = {r["iso3"]: r for r in result["countries"]}
        for cc in ("DZA", "MAR", "TUN"):
            if cc in by_code:
                assert by_code[cc]["sub_positions"] > 0, \
                    f"{cc} should now have sub-positions from national source data"
                assert by_code[cc]["data_format"] == "enhanced_v2"

    def test_no_old_format_countries_remain(self):
        """After migration all countries are enhanced_v2."""
        result = self._call()
        old_fmt = [r for r in result["countries"] if r.get("data_format") == "old"]
        assert old_fmt == [], f"Unexpected old-format countries: {[r['iso3'] for r in old_fmt]}"

    def test_default_sort_is_descending_by_sub_positions(self):
        result = self._call()
        counts = [r["sub_positions"] for r in result["countries"]]
        assert counts == sorted(counts, reverse=True)

    def test_sort_by_iso3(self):
        result = self._call(sort="iso3")
        codes = [r["iso3"] for r in result["countries"]]
        assert codes == sorted(codes)

    def test_sort_by_tariff_lines(self):
        result = self._call(sort="tariff_lines")
        lines = [r["tariff_lines"] for r in result["countries"]]
        assert lines == sorted(lines, reverse=True)

    def test_min_sub_filter(self):
        result = self._call(min_sub=10000)
        for r in result["countries"]:
            assert r["sub_positions"] >= 10000

    def test_country_entry_required_fields(self):
        result = self._call()
        required = {"iso3", "data_format", "status", "tariff_lines",
                    "sub_positions", "lines_with_sub_positions",
                    "avg_sub_per_line", "chapters_covered"}
        for row in result["countries"]:
            missing = required - set(row.keys())
            assert not missing, f"{row.get('iso3')}: missing {missing}"

    def test_avg_sub_per_line_non_negative(self):
        result = self._call()
        for r in result["countries"]:
            assert r["avg_sub_per_line"] >= 0.0

    def test_enhanced_avg_sub_per_line_reasonable(self):
        """For countries with dense sub-position coverage, avg should be ≥ 1.
        
        Countries migrated from EAC/ECOWAS/NGA 10-digit data have avg ≥ 1 since
        every tariff_line has at least one 10-digit sub-position.
        SADC countries (BWA, LSO, NAM, SWZ, ZAF) may be < 1 because only
        hs6 entries that have 8-digit children yield sub-positions.
        """
        dense_countries = {
            # Originally enhanced_v2
            "AGO", "BDI", "EGY", "ETH", "GNQ", "KEN", "TZA", "UGA",
            # Migrated ECOWAS / NGA — all 10-digit, every line has ≥1 sub
            "BEN", "BFA", "CIV", "GIN", "MLI", "NER", "NGA", "SEN", "TGO",
            # Migrated CEMAC — all 8-digit, every line has ≥1 sub
            "CMR", "CAF", "COG", "GAB", "TCD",
        }
        result = self._call()
        by_code = {r["iso3"]: r for r in result["countries"]}
        for cc in dense_countries:
            if cc in by_code and by_code[cc]["tariff_lines"] > 0:
                avg = by_code[cc]["avg_sub_per_line"]
                assert avg >= 1.0, \
                    f"{cc}: avg sub-positions {avg} should be ≥ 1.0"

    def test_specific_enhanced_country_gnq(self):
        result = self._call()
        gnq = next((r for r in result["countries"] if r["iso3"] == "GNQ"), None)
        assert gnq is not None
        assert gnq["sub_positions"] >= 16000
        assert gnq["data_format"] == "enhanced_v2"

    def test_countries_with_sub_count(self):
        result = self._call()
        actual_with_sub = sum(1 for r in result["countries"] if r["sub_positions"] > 0)
        assert actual_with_sub == result["totals"]["countries_with_sub_positions"]
        # All 54 countries now have real tariff data
        assert actual_with_sub == result["totals"]["total_countries"]


# ==================== Data Inventory Endpoint Tests ====================

class TestRegionalDataInventory:
    """Tests for GET /api/regional/data-inventory."""

    def _call(self, **kwargs):
        from routes.regional_data import _compute_data_inventory as get_regional_data_inventory
        return get_regional_data_inventory(**kwargs)

    def test_returns_expected_keys(self):
        result = self._call()
        assert "summary" in result
        assert "countries" in result

    def test_summary_fields(self):
        result = self._call()
        summary = result["summary"]
        for field in ("total_countries", "enhanced_v2_countries",
                      "old_format_countries", "total_tariff_lines",
                      "total_sub_positions"):
            assert field in summary, f"Missing summary field: {field}"

    def test_total_countries_count(self):
        result = self._call()
        assert result["summary"]["total_countries"] >= 50

    def test_enhanced_v2_countries_count(self):
        """After migration all 54 countries are enhanced_v2."""
        result = self._call()
        assert result["summary"]["enhanced_v2_countries"] == result["summary"]["total_countries"]

    def test_format_counts_sum_to_total(self):
        result = self._call()
        s = result["summary"]
        assert s["enhanced_v2_countries"] + s["old_format_countries"] == s["total_countries"]

    def test_countries_sorted_by_iso3(self):
        result = self._call()
        codes = [r["iso3"] for r in result["countries"]]
        assert codes == sorted(codes)

    def test_format_filter_enhanced_v2(self):
        result = self._call(format_filter="enhanced_v2")
        for r in result["countries"]:
            assert r["data_format"] == "enhanced_v2"

    def test_format_filter_old_returns_empty(self):
        """After migration no countries remain in old format."""
        result = self._call(format_filter="old")
        assert result["countries"] == [], \
            f"Expected 0 old-format countries, got: {[r['iso3'] for r in result['countries']]}"

    def test_country_entry_has_all_fields(self):
        result = self._call()
        required = {"iso3", "data_format", "status", "tariff_lines",
                    "sub_positions", "chapters_covered"}
        for row in result["countries"]:
            missing = required - set(row.keys())
            assert not missing, f"{row.get('iso3')}: missing {missing}"

    def test_total_lines_matches_sum(self):
        result = self._call()
        line_sum = sum(r["tariff_lines"] for r in result["countries"])
        assert result["summary"]["total_tariff_lines"] == line_sum

    def test_total_sub_matches_sum(self):
        result = self._call()
        sub_sum = sum(r["sub_positions"] for r in result["countries"])
        assert result["summary"]["total_sub_positions"] == sub_sum
