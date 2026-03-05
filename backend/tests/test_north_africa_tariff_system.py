"""
Tests for the North African Tariff Intelligence System.

Covers:
- Config loading (DZA, MAR, EGY, TUN)
- Regional config
- EnhancedCalculatorV3
- RegionalIntelligenceService
- NorthAfricaCrossValidator
- Service layer imports
"""

import sys
import os
import pytest

# Ensure backend is in path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


# ==================== Config Tests ====================

class TestCountryConfigs:
    """Tests for country-specific crawler configurations."""

    def test_dza_config_structure(self):
        from config.crawler_configs.dza_config import DZA_CONFIG
        assert DZA_CONFIG["country_iso3"] == "DZA"
        assert "tax_structure" in DZA_CONFIG
        assert "DD" in DZA_CONFIG["tax_structure"]
        assert "TVA" in DZA_CONFIG["tax_structure"]
        assert "crawl_settings" in DZA_CONFIG
        assert DZA_CONFIG["crawl_settings"]["async_enabled"] is True

    def test_mar_config_structure(self):
        from config.crawler_configs.mar_config import MAR_CONFIG
        assert MAR_CONFIG["country_iso3"] == "MAR"
        assert "tax_structure" in MAR_CONFIG
        assert "DD" in MAR_CONFIG["tax_structure"]
        assert "TVA" in MAR_CONFIG["tax_structure"]
        assert MAR_CONFIG["tax_structure"]["TVA"]["standard_rate"] == 20.0
        assert MAR_CONFIG["agricultural_seasonal_variations"] is True

    def test_egy_config_structure(self):
        from config.crawler_configs.egy_config import EGY_CONFIG
        assert EGY_CONFIG["country_iso3"] == "EGY"
        assert "tax_structure" in EGY_CONFIG
        assert "CD" in EGY_CONFIG["tax_structure"]
        assert "VAT" in EGY_CONFIG["tax_structure"]
        assert EGY_CONFIG["tax_structure"]["VAT"]["standard_rate"] == 14.0
        assert "QIZ" in " ".join(EGY_CONFIG.get("preferential_agreements", []))

    def test_tun_config_structure(self):
        from config.crawler_configs.tun_config import TUN_CONFIG
        assert TUN_CONFIG["country_iso3"] == "TUN"
        assert "tax_structure" in TUN_CONFIG
        assert "DD" in TUN_CONFIG["tax_structure"]
        assert "FODEC" in TUN_CONFIG["tax_structure"]
        assert TUN_CONFIG["tax_structure"]["FODEC"]["rate"] == 1.0
        assert "EU Association Agreement" in " ".join(
            TUN_CONFIG.get("preferential_agreements", [])
        )

    def test_all_configs_have_data_paths(self):
        from config.crawler_configs.dza_config import DZA_CONFIG
        from config.crawler_configs.mar_config import MAR_CONFIG
        from config.crawler_configs.egy_config import EGY_CONFIG
        from config.crawler_configs.tun_config import TUN_CONFIG

        for cfg in [DZA_CONFIG, MAR_CONFIG, EGY_CONFIG, TUN_CONFIG]:
            assert "data_paths" in cfg
            assert "raw" in cfg["data_paths"]
            assert "parsed" in cfg["data_paths"]
            assert "published" in cfg["data_paths"]


class TestRegionalConfig:
    """Tests for the regional configuration."""

    def test_north_africa_countries(self):
        from config.regional_config import NORTH_AFRICA_COUNTRIES
        assert set(NORTH_AFRICA_COUNTRIES) == {"DZA", "MAR", "EGY", "TUN"}
        assert len(NORTH_AFRICA_COUNTRIES) == 4

    def test_regional_config_structure(self):
        from config.regional_config import REGIONAL_CONFIG
        assert REGIONAL_CONFIG["region_name"] == "North Africa"
        assert "cross_validation" in REGIONAL_CONFIG
        assert "performance_targets" in REGIONAL_CONFIG
        assert REGIONAL_CONFIG["performance_targets"]["data_freshness_days"] >= 1

    def test_north_africa_vat_rates(self):
        from config.regional_config import NORTH_AFRICA_VAT_RATES
        assert NORTH_AFRICA_VAT_RATES["DZA"] == 19.0
        assert NORTH_AFRICA_VAT_RATES["MAR"] == 20.0
        assert NORTH_AFRICA_VAT_RATES["EGY"] == 14.0
        assert NORTH_AFRICA_VAT_RATES["TUN"] == 19.0


# ==================== Enhanced Calculator Tests ====================

class TestEnhancedCalculatorV3:
    """Tests for the regional tariff calculator."""

    def setup_method(self):
        from services.enhanced_calculator_v3 import EnhancedCalculatorV3
        self.calculator = EnhancedCalculatorV3()

    def test_calculate_country_taxes_mar(self):
        result = self.calculator.calculate_country_taxes(
            country_code="MAR",
            hs_code="870321",
            cif_value=10000.0,
        )
        assert result["country_code"] == "MAR"
        assert result["cif_value"] == 10000.0
        assert result["vat_rate_pct"] == 20.0
        assert result["total_landed_cost"] > result["cif_value"]
        assert result["dd_amount"] >= 0
        assert result["vat_amount"] >= 0

    def test_calculate_country_taxes_egy(self):
        result = self.calculator.calculate_country_taxes(
            country_code="EGY",
            hs_code="870321",
            cif_value=5000.0,
            dd_rate=20.0,
        )
        assert result["country_code"] == "EGY"
        assert result["dd_rate_pct"] == 20.0
        assert result["vat_rate_pct"] == 14.0
        assert result["dd_amount"] == 1000.0
        assert result["total_taxes"] > 0

    def test_calculate_country_taxes_no_vat(self):
        result = self.calculator.calculate_country_taxes(
            country_code="TUN",
            hs_code="270900",
            cif_value=1000.0,
            dd_rate=0.0,
            apply_vat=False,
        )
        assert result["vat_amount"] == 0
        assert result["total_taxes"] == 0.0
        assert result["total_landed_cost"] == result["cif_value"]

    def test_find_best_route_returns_ranking(self):
        result = self.calculator.find_best_route(
            hs_code="870321",
            cif_value=10000.0,
        )
        assert "rankings" in result
        assert "best_route" in result
        assert len(result["rankings"]) == 4
        # Rankings should be sorted by total landed cost
        costs = [r["total_landed_cost"] for r in result["rankings"]]
        assert costs == sorted(costs)

    def test_find_best_route_with_known_rates(self):
        known_rates = {"DZA": 0.0, "MAR": 2.5, "EGY": 5.0, "TUN": 0.0}
        result = self.calculator.find_best_route(
            hs_code="270900",  # mineral fuels
            cif_value=100000.0,
            dd_rates=known_rates,
        )
        assert result["best_route"] is not None
        # DZA and TUN have 0% DD, so they should be cheapest
        best_dd = result["best_route"]["dd_rate_pct"]
        assert best_dd == 0.0

    def test_analyze_free_zone_arbitrage(self):
        opportunities = self.calculator.analyze_free_zone_arbitrage(
            hs_code="870321",
            cif_value=10000.0,
        )
        assert isinstance(opportunities, list)
        # Morocco and Egypt have free zones
        countries = {o["country"] for o in opportunities}
        assert "MAR" in countries
        assert "EGY" in countries

    def test_get_preferential_rates_eu(self):
        rates = self.calculator.get_preferential_rates(
            hs_code="870321",
            origin_country="MAR",
            destination="EU",
        )
        assert len(rates) > 0
        agreements = [r["agreement"] for r in rates]
        assert any("EU" in a for a in agreements)

    def test_get_preferential_rates_qiz(self):
        rates = self.calculator.get_preferential_rates(
            hs_code="610910",
            origin_country="EGY",
            destination="US",
        )
        assert len(rates) > 0
        agreements = [r["agreement"] for r in rates]
        assert any("QIZ" in a for a in agreements)

    def test_compare_regional_supply_chain(self):
        result = self.calculator.compare_regional_supply_chain(
            hs_codes=["870321", "840810"],
            production_country="MAR",
            unit_value=5000.0,
        )
        assert "total_tax_burden_by_country" in result
        assert "optimal_country" in result
        assert len(result["total_tax_burden_by_country"]) == 4
        assert result["optimal_country"] in ["DZA", "MAR", "EGY", "TUN"]

    def test_singleton_calculator(self):
        from services.enhanced_calculator_v3 import get_enhanced_calculator
        c1 = get_enhanced_calculator()
        c2 = get_enhanced_calculator()
        assert c1 is c2


# ==================== Regional Intelligence Service Tests ====================

class TestRegionalIntelligenceService:
    """Tests for the regional intelligence service."""

    def setup_method(self):
        from services.regional_intelligence_service import RegionalIntelligenceService
        self.intel = RegionalIntelligenceService()

    def test_get_data_freshness_returns_all_countries(self):
        report = self.intel.get_data_freshness()
        result = report.to_dict()
        assert "countries" in result
        assert "DZA" in result["countries"]
        assert "MAR" in result["countries"]
        assert "EGY" in result["countries"]
        assert "TUN" in result["countries"]

    def test_data_freshness_has_required_fields(self):
        report = self.intel.get_data_freshness()
        result = report.to_dict()
        for country_data in result["countries"].values():
            assert "country_code" in country_data
            assert "is_fresh" in country_data
            assert "record_count" in country_data

    def test_build_investment_map_structure(self):
        result = self.intel.build_investment_map()
        assert "countries" in result
        assert "top_ranked" in result
        assert result["top_ranked"] in ["DZA", "MAR", "EGY", "TUN"]
        assert len(result["countries"]) == 4

    def test_investment_map_country_fields(self):
        result = self.intel.build_investment_map()
        for code, profile in result["countries"].items():
            assert "country_name" in profile
            assert "vat_rate" in profile
            assert "investment_score" in profile
            assert "rank" in profile
            assert 1 <= profile["rank"] <= 4

    def test_recommend_market_entry_automotive(self):
        result = self.intel.recommend_market_entry(
            sector="automotive",
            priority="eu_access",
        )
        assert "recommendations" in result
        assert "top_recommendation" in result
        assert len(result["recommendations"]) == 4
        # Morocco has highest automotive + EU access score
        assert result["top_recommendation"] == "MAR"

    def test_recommend_market_entry_ict(self):
        result = self.intel.recommend_market_entry(
            sector="ict",
            priority="regional_hub",
        )
        assert result["top_recommendation"] in ["DZA", "MAR", "EGY", "TUN"]

    def test_get_preferential_agreements_matrix(self):
        result = self.intel.get_preferential_agreements_matrix()
        assert "matrix" in result
        assert "best_country_by_market" in result
        matrix = result["matrix"]
        assert "DZA" in matrix
        assert "MAR" in matrix
        assert "EGY" in matrix
        assert "TUN" in matrix
        # Morocco should have EU access
        assert matrix["MAR"]["EU"] is True
        # Algeria should NOT have EU access
        assert matrix["DZA"]["EU"] is False
        # Egypt should have QIZ (US market access)
        assert matrix["EGY"]["QIZ"] is True

    def test_agreements_matrix_best_by_market_eu(self):
        result = self.intel.get_preferential_agreements_matrix()
        eu_countries = result["best_country_by_market"]["EU"]
        assert "MAR" in eu_countries
        assert "EGY" in eu_countries
        assert "TUN" in eu_countries
        # Algeria does NOT have EU agreement
        assert "DZA" not in eu_countries

    def test_export_regional_dataset(self):
        result = self.intel.export_regional_dataset()
        assert "countries" in result
        assert "total_records" in result
        assert "exported_at" in result
        assert len(result["countries"]) == 4

    def test_singleton_service(self):
        from services.regional_intelligence_service import get_regional_intelligence
        s1 = get_regional_intelligence()
        s2 = get_regional_intelligence()
        assert s1 is s2


# ==================== Cross Validator Tests ====================

class TestNorthAfricaCrossValidator:
    """Tests for cross-country data validation."""

    def setup_method(self):
        from services.crawlers.cross_validator import NorthAfricaCrossValidator
        self.validator = NorthAfricaCrossValidator()

    def test_validator_init_default_countries(self):
        from config.regional_config import NORTH_AFRICA_COUNTRIES
        assert set(self.validator.countries) == set(NORTH_AFRICA_COUNTRIES)

    def test_validator_custom_countries(self):
        from services.crawlers.cross_validator import NorthAfricaCrossValidator
        v = NorthAfricaCrossValidator(countries=["MAR", "TUN"])
        assert set(v.countries) == {"MAR", "TUN"}

    def test_validate_with_no_data(self):
        result = self.validator.validate()
        assert result is not None
        d = result.to_dict()
        assert "countries_checked" in d
        assert set(d["countries_checked"]) == {"DZA", "MAR", "EGY", "TUN"}
        assert "completeness_scores" in d
        assert "issues" in d

    def test_validate_with_mock_data(self):
        mock_data = {
            "MAR": [
                {
                    "hs_code": "870321",
                    "designation": "Passenger vehicles",
                    "taxes": {"DD": 17.5, "TVA": 20.0},
                    "total_taxes_pct": 37.5,
                }
            ] * 20,
            "TUN": [
                {
                    "hs_code": "870321",
                    "designation": "Véhicules de tourisme",
                    "taxes": {"DD": 30.0, "TVA": 19.0},
                    "total_taxes_pct": 49.0,
                }
            ] * 15,
        }
        result = self.validator.validate(all_data=mock_data)
        d = result.to_dict()
        assert d["completeness_scores"]["MAR"] > 0
        assert d["completeness_scores"]["TUN"] > 0

    def test_check_completeness_good_data(self):
        records = [
            {"hs_code": "870321", "designation": "Vehicles", "taxes": {"DD": 17.5}}
        ] * 50
        score, missing = self.validator.check_completeness(records, "MAR")
        assert score == 100.0
        assert len(missing) == 0

    def test_check_completeness_missing_fields(self):
        records = [{"hs_code": "870321"}] * 50  # missing designation and taxes
        score, missing = self.validator.check_completeness(records, "DZA")
        assert score < 100.0

    def test_check_rate_ranges_valid_data(self):
        records = [
            {
                "hs_code": "870321",
                "taxes": {"DD": 17.5, "TVA": 20.0},
            }
        ] * 20
        anomalies = self.validator.check_rate_ranges(records, "MAR")
        # Normal rates should not trigger anomalies
        vat_anomalies = [a for a in anomalies if "VAT" in a.get("tax", "")]
        assert len(vat_anomalies) == 0

    def test_check_rate_ranges_bad_dd(self):
        records = [
            {
                "hs_code": "870321",
                "taxes": {"DD": 500.0, "TVA": 20.0},  # DD > 200% is anomalous
            }
        ] * 5
        anomalies = self.validator.check_rate_ranges(records, "MAR")
        assert len(anomalies) > 0
        assert any("DD" in a["tax"] for a in anomalies)

    def test_cross_validate_hs_codes_similar_rates(self):
        all_data = {
            "MAR": [
                {
                    "hs_code": "870321",
                    "total_taxes_pct": 37.5,
                }
            ] * 10,
            "TUN": [
                {
                    "hs_code": "870321",
                    "total_taxes_pct": 49.0,  # Significant difference
                }
            ] * 10,
        }
        anomalies = self.validator.cross_validate_hs_codes(all_data)
        assert isinstance(anomalies, list)

    def test_validation_result_to_dict(self):
        from services.crawlers.cross_validator import ValidationResult
        result = ValidationResult()
        result.countries_checked = ["DZA", "MAR"]
        result.add_issue("DZA", "no_data", "No data", severity="warning")
        d = result.to_dict()
        assert "timestamp" in d
        assert "overall_valid" in d
        assert "issues" in d
        assert len(d["issues"]) == 1


# ==================== Regional Orchestrator Tests ====================

class TestNorthAfricaOrchestrator:
    """Tests for the North Africa crawl orchestrator."""

    def setup_method(self):
        from services.crawlers.regional_orchestrator import NorthAfricaOrchestrator
        self.orchestrator = NorthAfricaOrchestrator(max_concurrency=2)

    def test_orchestrator_supported_countries(self):
        from config.regional_config import NORTH_AFRICA_COUNTRIES
        assert set(self.orchestrator.SUPPORTED_COUNTRIES) == set(NORTH_AFRICA_COUNTRIES)

    def test_orchestrator_regional_status(self):
        status = self.orchestrator.get_regional_status()
        assert "supported_countries" in status
        assert "total_jobs" in status
        assert "max_concurrency" in status
        assert status["max_concurrency"] == 2

    def test_orchestrator_list_jobs_empty(self):
        jobs = self.orchestrator.list_jobs()
        assert isinstance(jobs, list)
        assert len(jobs) == 0

    def test_orchestrator_cancel_nonexistent_job(self):
        result = self.orchestrator.cancel_job("nonexistent_id")
        assert result is False

    def test_orchestrator_get_nonexistent_job(self):
        result = self.orchestrator.get_job("nonexistent_id")
        assert result is None

    @pytest.mark.asyncio
    async def test_start_crawl_invalid_country(self):
        with pytest.raises(ValueError, match="Unsupported countries"):
            await self.orchestrator.start_regional_crawl(countries=["XXX"])

    def test_orchestrator_singleton(self):
        from services.crawlers.regional_orchestrator import (
            get_north_africa_orchestrator,
            init_north_africa_orchestrator,
        )
        # Re-initialize to get a fresh singleton
        o1 = init_north_africa_orchestrator()
        o2 = get_north_africa_orchestrator()
        assert o1 is o2


# ==================== Base Crawler Tests ====================

class TestNorthAfricaCrawlerBase:
    """Tests for the NorthAfricaCrawlerBase utility methods."""

    def _get_concrete_class(self):
        """Return a minimal concrete subclass for testing base methods."""
        from services.crawlers.base_north_africa_crawler import NorthAfricaCrawlerBase

        class ConcreteCrawler(NorthAfricaCrawlerBase):
            _country_code = "MAR"

            async def scrape(self):
                return {"records": []}

            async def parse_taxes(self, html, country_config):
                return []

            async def validate_data(self, tariff_lines):
                return True

            async def save_to_db(self, data):
                return 0

        return ConcreteCrawler

    def test_normalize_hs_code(self):
        cls = self._get_concrete_class()
        instance = cls.__new__(cls)
        instance._country_code = "MAR"

        # 6-digit -> padded to 10
        assert instance.normalize_hs_code("870321") == "8703210000"
        # 10-digit unchanged
        assert instance.normalize_hs_code("8703210000") == "8703210000"
        # With dots
        assert instance.normalize_hs_code("87.03.21") == "8703210000"

    def test_normalize_rate(self):
        cls = self._get_concrete_class()
        instance = cls.__new__(cls)
        instance._country_code = "MAR"

        assert instance.normalize_rate("17.5 %") == 17.5
        assert instance.normalize_rate(20) == 20.0
        assert instance.normalize_rate(None) is None
        assert instance.normalize_rate("0 %") == 0.0
        assert instance.normalize_rate("free") is None

    def test_build_canonical_record(self):
        cls = self._get_concrete_class()
        instance = cls.__new__(cls)
        instance._country_code = "MAR"

        record = instance.build_canonical_record(
            hs_code="8703210000",
            designation="Passenger cars",
            taxes={"DD": 17.5, "TVA": 20.0},
            source="douane.gov.ma",
        )

        assert record["country_code"] == "MAR"
        assert record["hs_code"] == "8703210000"
        assert record["designation"] == "Passenger cars"
        assert record["taxes"]["DD"] == 17.5
        assert record["taxes"]["TVA"] == 20.0
        assert record["total_taxes_pct"] == pytest.approx(37.5)
        assert "scraped_at" in record


# ==================== Advanced Regional Intelligence Tests ====================

class TestRegionalIntelligenceAdvanced:
    """Tests for the new advanced regional intelligence methods."""

    def setup_method(self):
        from services.regional_intelligence_service import RegionalIntelligenceService
        self.intel = RegionalIntelligenceService()

    # ---------- optimal_trade_route ----------

    def test_optimal_route_returns_all_countries(self):
        result = self.intel.optimal_trade_route(
            hs_code="870321",
            origin_region="sub_saharan_africa",
            target_market="europe",
        )
        assert "routes" in result
        assert len(result["routes"]) == 4
        codes = {r["country_code"] for r in result["routes"]}
        assert codes == {"DZA", "MAR", "EGY", "TUN"}

    def test_optimal_route_has_required_fields(self):
        result = self.intel.optimal_trade_route(
            hs_code="870321",
            origin_region="sub_saharan_africa",
            target_market="europe",
        )
        assert "optimal_route" in result
        assert result["optimal_route"] is not None
        route = result["optimal_route"]
        assert "combined_score" in route
        assert "clearance_days_avg" in route
        assert "dd_rate_typical_pct" in route
        assert "annual_duty_estimate_usd" in route

    def test_optimal_route_for_eu_favors_eu_countries(self):
        result = self.intel.optimal_trade_route(
            hs_code="610910",
            origin_region="sub_saharan_africa",
            target_market="europe",
            preferences=["lowest_cost", "most_reliable"],
        )
        # Countries with EU agreements should rank better for EU target
        top = result["optimal_route"]["country_code"]
        eu_countries = {"MAR", "EGY", "TUN"}
        assert top in eu_countries

    def test_optimal_route_annual_duty_positive(self):
        result = self.intel.optimal_trade_route(
            hs_code="870321",
            origin_region="asia",
            target_market="mena",
            annual_volume=5_000_000,
        )
        for route in result["routes"]:
            assert route["annual_duty_estimate_usd"] >= 0

    def test_optimal_route_sorted_by_score(self):
        result = self.intel.optimal_trade_route(
            hs_code="840710",
            origin_region="americas",
            target_market="africa",
        )
        scores = [r["combined_score"] for r in result["routes"]]
        assert scores == sorted(scores, reverse=True)

    def test_optimal_route_metadata(self):
        result = self.intel.optimal_trade_route(
            hs_code="270900",
            origin_region="sub_saharan_africa",
            target_market="europe",
            annual_volume=10_000_000,
            preferences=["fastest_clearance"],
        )
        assert result["hs_code"] == "270900"
        assert result["origin_region"] == "sub_saharan_africa"
        assert result["target_market"] == "europe"
        assert result["annual_volume_usd"] == 10_000_000
        assert "generated_at" in result

    # ---------- investment_analysis ----------

    def test_investment_analysis_returns_all_countries(self):
        result = self.intel.investment_analysis(industry="automotive")
        assert "recommendations" in result
        assert len(result["recommendations"]) == 4
        codes = {r["country_code"] for r in result["recommendations"]}
        assert codes == {"DZA", "MAR", "EGY", "TUN"}

    def test_investment_analysis_has_required_fields(self):
        result = self.intel.investment_analysis(
            industry="textile",
            target_markets=["eu"],
            investment_size=20_000_000,
            employment_target=500,
        )
        assert result["industry"] == "textile"
        assert result["investment_size_usd"] == 20_000_000
        assert result["employment_target"] == 500
        assert "top_recommendation" in result
        assert "size_note" in result
        assert "generated_at" in result

    def test_investment_analysis_automotive_eu_recommends_mar(self):
        result = self.intel.investment_analysis(
            industry="automotive",
            target_markets=["eu"],
        )
        # Morocco is the regional automotive + EU leader
        assert result["top_recommendation"] == "MAR"

    def test_investment_analysis_textile_us_includes_egy(self):
        result = self.intel.investment_analysis(
            industry="textile",
            target_markets=["us"],
        )
        # Egypt QIZ gives US access for textiles; should rank high
        us_accessible = [
            r for r in result["recommendations"]
            if "US" in r["markets_accessible"]
        ]
        assert any(r["country_code"] == "EGY" for r in us_accessible)

    def test_investment_analysis_rank_field(self):
        result = self.intel.investment_analysis(industry="ict")
        ranks = [r["rank"] for r in result["recommendations"]]
        assert sorted(ranks) == [1, 2, 3, 4]

    def test_investment_analysis_large_investment_note(self):
        result = self.intel.investment_analysis(
            industry="automotive",
            investment_size=100_000_000,
        )
        assert "Large-scale" in result["size_note"]

    def test_investment_analysis_small_investment_note(self):
        result = self.intel.investment_analysis(
            industry="ict",
            investment_size=500_000,
        )
        assert "Smaller" in result["size_note"]

    # ---------- get_preferential_matrix_by_hs ----------

    def test_preferential_matrix_structure(self):
        result = self.intel.get_preferential_matrix_by_hs(hs_code="870321")
        assert "hs_code" in result
        assert "matrix" in result
        assert set(result["matrix"].keys()) == {"DZA", "MAR", "EGY", "TUN"}

    def test_preferential_matrix_hs_chapter_detection(self):
        result = self.intel.get_preferential_matrix_by_hs(hs_code="870321")
        assert result["hs_chapter"] == "87"
        assert result["product_category"] == "vehicles_transport"

    def test_preferential_matrix_agricultural_chapter(self):
        result = self.intel.get_preferential_matrix_by_hs(hs_code="100190")
        assert result["product_category"] == "agricultural"

    def test_preferential_matrix_machinery_chapter(self):
        result = self.intel.get_preferential_matrix_by_hs(hs_code="841431")
        assert result["product_category"] == "machinery_electronics"

    def test_preferential_matrix_invalid_hs_too_short(self):
        with pytest.raises(ValueError, match="Invalid HS code"):
            self.intel.get_preferential_matrix_by_hs(hs_code="8")

    def test_preferential_matrix_invalid_hs_non_numeric(self):
        with pytest.raises(ValueError, match="Invalid HS code"):
            self.intel.get_preferential_matrix_by_hs(hs_code="XY1234")

    def test_preferential_matrix_eu_access_countries(self):
        result = self.intel.get_preferential_matrix_by_hs(hs_code="610910")
        eu_countries = result["best_for_eu_access"]
        assert "MAR" in eu_countries
        assert "EGY" in eu_countries
        assert "TUN" in eu_countries
        # Algeria does NOT have EU agreement
        assert "DZA" not in eu_countries

    def test_preferential_matrix_us_access_countries(self):
        result = self.intel.get_preferential_matrix_by_hs(hs_code="870321")
        us_countries = result["best_for_us_access"]
        # MAR has US FTA, EGY has QIZ
        assert "MAR" in us_countries
        assert "EGY" in us_countries

    def test_preferential_matrix_afcfta_universal(self):
        result = self.intel.get_preferential_matrix_by_hs(hs_code="270900")
        for country_data in result["matrix"].values():
            agreements = [a["agreement"] for a in country_data["applicable_agreements"]]
            assert any("AfCFTA" in ag for ag in agreements)

    def test_preferential_matrix_qiz_egypt_only(self):
        result = self.intel.get_preferential_matrix_by_hs(hs_code="610910")
        egy_agreements = [
            a["agreement"]
            for a in result["matrix"]["EGY"]["applicable_agreements"]
        ]
        assert any("QIZ" in ag for ag in egy_agreements)
        # Other countries should NOT have QIZ
        for country_code in ["DZA", "MAR", "TUN"]:
            agreements = [
                a["agreement"]
                for a in result["matrix"][country_code]["applicable_agreements"]
            ]
            assert not any("QIZ" in ag for ag in agreements)

    def test_preferential_matrix_generated_at(self):
        result = self.intel.get_preferential_matrix_by_hs(hs_code="840710")
        assert "generated_at" in result

    # ---------- get_trade_flows ----------

    def test_trade_flows_structure(self):
        result = self.intel.get_trade_flows()
        assert "intra_regional" in result
        assert "eu_access" in result
        assert "mena_hub" in result
        assert "africa_gateway" in result
        assert "generated_at" in result

    def test_trade_flows_intra_regional_pairs(self):
        result = self.intel.get_trade_flows()
        intra = result["intra_regional"]
        expected_pairs = {"dza_mar", "dza_tun", "egy_tun", "mar_tun", "mar_egy"}
        assert set(intra.keys()) == expected_pairs

    def test_trade_flows_eu_access_countries(self):
        result = self.intel.get_trade_flows()
        eu = result["eu_access"]
        countries = {v["country"] for v in eu.values()}
        # MAR and TUN are EU-focused in the model
        assert "MAR" in countries
        assert "TUN" in countries

    def test_trade_flows_suez_canal_egypt(self):
        result = self.intel.get_trade_flows()
        mena = result["mena_hub"]
        egy_position = mena.get("egy_position", {})
        assert egy_position.get("country") == "EGY"
        assert "Suez Canal" in str(egy_position.get("strategic_assets", []))

    def test_trade_flows_africa_gateway(self):
        result = self.intel.get_trade_flows()
        gateway = result["africa_gateway"]
        countries = {v["country"] for v in gateway.values()}
        # All North African countries should feature
        assert len(countries) >= 2

    # ---------- get_opportunity_map ----------

    def test_opportunity_map_default_sectors(self):
        result = self.intel.get_opportunity_map()
        assert "opportunity_map" in result
        assert "overall_ranking" in result
        assert "best_overall" in result
        # Default 4 sectors
        assert len(result["opportunity_map"]) >= 4

    def test_opportunity_map_custom_sectors(self):
        result = self.intel.get_opportunity_map(sectors=["automotive", "ict"])
        assert set(result["opportunity_map"].keys()) == {"automotive", "ict"}

    def test_opportunity_map_rankings_structure(self):
        result = self.intel.get_opportunity_map(sectors=["automotive"])
        auto = result["opportunity_map"]["automotive"]
        assert "rankings" in auto
        assert "top_country" in auto
        assert len(auto["rankings"]) == 4

    def test_opportunity_map_automotive_top_mar(self):
        result = self.intel.get_opportunity_map(sectors=["automotive"])
        top = result["opportunity_map"]["automotive"]["top_country"]
        # Morocco is the clear automotive leader
        assert top == "MAR"

    def test_opportunity_map_overall_ranking_all_countries(self):
        result = self.intel.get_opportunity_map()
        codes = {r["country_code"] for r in result["overall_ranking"]}
        assert codes == {"DZA", "MAR", "EGY", "TUN"}

    def test_opportunity_map_score_fields(self):
        result = self.intel.get_opportunity_map(sectors=["textile"])
        rankings = result["opportunity_map"]["textile"]["rankings"]
        for r in rankings:
            assert "combined_score" in r
            assert "cost_structure" in r
            assert "market_access" in r
            assert "regulatory_environment" in r
            assert "infrastructure_quality" in r

    def test_opportunity_map_generated_at(self):
        result = self.intel.get_opportunity_map(sectors=["agriculture"])
        assert "generated_at" in result
