import sys
import os
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from services.tariff_data_collector import TariffDataCollector, get_collector


class TestTariffDataCollector:
    def setup_method(self):
        self.collector = TariffDataCollector()

    def test_collector_initialization(self):
        assert self.collector._loaded is False
        assert self.collector._hs6_db is None

    def test_load_modules(self):
        self.collector._load_modules()
        assert self.collector._loaded is True
        assert self.collector._hs6_db is not None
        assert self.collector._hs6_csv_db is not None
        assert self.collector._country_tariffs_map is not None
        assert self.collector._vat_rates is not None
        assert self.collector._other_taxes is not None
        assert self.collector._hs6_detailed is not None
        assert self.collector._sub_position_types is not None

    def test_collect_country_returns_data(self):
        data = self.collector.collect_country_tariffs("NGA")
        assert data["country_code"] == "NGA"
        assert "tariff_lines" in data
        assert "summary" in data
        assert len(data["tariff_lines"]) > 5000

    def test_summary_fields(self):
        data = self.collector.collect_country_tariffs("DZA")
        summary = data["summary"]
        assert "total_tariff_lines" in summary
        assert "total_sub_positions" in summary
        assert "total_positions" in summary
        assert "lines_with_sub_positions" in summary
        assert "vat_rate_pct" in summary
        assert "dd_rate_range" in summary
        assert "chapters_covered" in summary
        assert summary["total_tariff_lines"] > 5000
        assert summary["total_sub_positions"] > 0
        assert summary["total_positions"] > summary["total_tariff_lines"]

    def test_tariff_line_structure(self):
        data = self.collector.collect_country_tariffs("CIV")
        line = data["tariff_lines"][0]
        required_fields = [
            "hs6", "chapter", "description_fr", "description_en",
            "category", "sensitivity", "dd_rate", "dd_source",
            "zlecaf_rate", "zlecaf_source", "vat_rate", "other_taxes_rate",
            "total_import_taxes", "zlecaf_total_taxes", "has_sub_positions",
            "sub_position_count"
        ]
        for field in required_fields:
            assert field in line, f"Missing field: {field}"

    def test_sub_positions_generated(self):
        data = self.collector.collect_country_tariffs("NGA")
        lines_with_subs = [l for l in data["tariff_lines"] if l["has_sub_positions"]]
        assert len(lines_with_subs) > 1000

        for line in lines_with_subs[:10]:
            for sp in line["sub_positions"]:
                assert "code" in sp
                assert "digits" in sp
                assert "dd" in sp
                assert "description_fr" in sp
                assert len(sp["code"]) > 6

    def test_sub_position_digits(self):
        data = self.collector.collect_country_tariffs("KEN")
        all_digits = set()
        for line in data["tariff_lines"]:
            if line["has_sub_positions"]:
                for sp in line["sub_positions"]:
                    all_digits.add(sp["digits"])
        assert any(d >= 8 for d in all_digits), f"No HS8+ sub-positions found. Digits: {all_digits}"

    def test_detailed_sub_positions_priority(self):
        data = self.collector.collect_country_tariffs("NGA")
        vehicle_line = next((l for l in data["tariff_lines"] if l["hs6"] == "870321"), None)
        if vehicle_line and vehicle_line["has_sub_positions"]:
            sources = [sp.get("source", "") for sp in vehicle_line["sub_positions"]]
            assert any("national" in s.lower() or "détaillé" in s.lower() for s in sources)

    def test_iso2_to_iso3_conversion(self):
        data = self.collector.collect_country_tariffs("NG")
        assert data["country_code"] == "NGA"

    def test_vat_rate_accuracy(self):
        data = self.collector.collect_country_tariffs("NGA")
        assert data["summary"]["vat_rate_pct"] == 7.5

        data_dza = self.collector.collect_country_tariffs("DZA")
        assert data_dza["summary"]["vat_rate_pct"] == 19.0

    def test_54_countries_available(self):
        self.collector._load_modules()
        available = list(self.collector._country_tariffs_map.keys())
        assert len(available) == 54

    def test_chapters_coverage(self):
        data = self.collector.collect_country_tariffs("ZAF")
        assert data["summary"]["chapters_covered"] >= 90

    def test_dd_rates_reasonable(self):
        data = self.collector.collect_country_tariffs("MAR")
        for line in data["tariff_lines"]:
            assert 0 <= line["dd_rate"] <= 100, f"DD rate out of range: {line['dd_rate']} for {line['hs6']}"
            assert 0 <= line["zlecaf_rate"] <= 100
            assert 0 <= line["vat_rate"] <= 50

    def test_get_collector_singleton(self):
        c1 = get_collector()
        c2 = get_collector()
        assert c1 is c2

    def test_save_and_load(self, tmp_path):
        import services.tariff_data_collector as module
        original_dir = module.DATA_DIR
        module.DATA_DIR = tmp_path

        try:
            data = self.collector.collect_country_tariffs("SEN")
            path = self.collector.save_country_tariffs("SEN", data)
            assert os.path.exists(path)

            loaded = self.collector.load_country_tariffs("SEN")
            assert loaded is not None
            assert loaded["country_code"] == "SEN"
            assert len(loaded["tariff_lines"]) == len(data["tariff_lines"])
        finally:
            module.DATA_DIR = original_dir

    def test_available_countries_list(self):
        countries = self.collector.get_available_countries()
        assert isinstance(countries, list)


class TestMiddlewares:
    def test_security_headers_import(self):
        from middlewares.security_headers import SecurityHeadersMiddleware
        assert SecurityHeadersMiddleware is not None

    def test_csrf_import(self):
        from middlewares.csrf_protection import CSRFMiddleware
        assert CSRFMiddleware is not None

    def test_rate_limiter_import(self):
        from middlewares.rate_limiter import RateLimitMiddleware
        assert RateLimitMiddleware is not None

    def test_rate_limiter_cleanup(self):
        import time
        from unittest.mock import MagicMock
        from middlewares.rate_limiter import RateLimitMiddleware

        app = MagicMock()
        limiter = RateLimitMiddleware.__new__(RateLimitMiddleware)
        limiter.requests_per_minute = 60
        limiter.burst_limit = 10
        limiter.exempt_paths = []
        from collections import defaultdict
        limiter._buckets = defaultdict(list)
        limiter._last_cleanup = 0

        now = time.time()
        limiter._buckets["old_key"] = [now - 120]
        limiter._buckets["new_key"] = [now - 10]
        limiter._cleanup_old_entries(now)

        assert "old_key" not in limiter._buckets
        assert "new_key" in limiter._buckets
