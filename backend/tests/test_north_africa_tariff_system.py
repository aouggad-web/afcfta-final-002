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
        # North Africa countries must all be present
        for code in ["DZA", "MAR", "EGY", "TUN"]:
            assert code in result["countries"]
        # CEMAC countries must also be present
        for code in ["CMR", "CAF", "TCD", "COG", "GNQ", "GAB"]:
            assert code in result["countries"]
        assert len(result["countries"]) >= 4

    def test_investment_map_country_fields(self):
        result = self.intel.build_investment_map()
        total = len(result["countries"])
        for code, profile in result["countries"].items():
            assert "country_name" in profile
            assert "vat_rate" in profile
            assert "investment_score" in profile
            assert "rank" in profile
            assert 1 <= profile["rank"] <= total

    def test_recommend_market_entry_automotive(self):
        result = self.intel.recommend_market_entry(
            sector="automotive",
            priority="eu_access",
        )
        assert "recommendations" in result
        assert "top_recommendation" in result
        assert len(result["recommendations"]) >= 4
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
        # North Africa countries must all be in the matrix
        for code in ["DZA", "MAR", "EGY", "TUN"]:
            assert code in result["matrix"]
        # CEMAC countries must also be in the matrix
        for code in ["CMR", "CAF", "TCD", "COG", "GNQ", "GAB"]:
            assert code in result["matrix"]

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


# ==================== Administrative Formalities Tests ====================

class TestAdministrativeFormalities:
    """
    Tests for the administrative formalities and document requirements
    integrated into MAR and TUN enhanced_v2 tariff data.

    Validates:
    - ETL module functions produce correct formality sets per category
    - MAR and TUN crawled data files have rich multi-document formalities
    - DZA formalities are unchanged (regression)
    - Specific categories produce the expected regulatory documents
    """

    # ---------- ETL module unit tests ----------

    def test_mar_etl_imports_cleanly(self):
        from etl.country_taxes_morocco import (
            MAR_FORMALITIES_BY_CATEGORY,
            get_mar_formality_category,
            get_mar_formalities_for_line,
        )
        assert "animal_products" in MAR_FORMALITIES_BY_CATEGORY
        assert "pharmaceuticals" in MAR_FORMALITIES_BY_CATEGORY
        assert "general" in MAR_FORMALITIES_BY_CATEGORY

    def test_tun_etl_imports_cleanly(self):
        from etl.country_taxes_tunisia import (
            TUN_FORMALITIES_BY_CATEGORY,
            get_tun_formality_category,
            get_tun_formalities_for_line,
        )
        assert "animal_products" in TUN_FORMALITIES_BY_CATEGORY
        assert "pharmaceuticals" in TUN_FORMALITIES_BY_CATEGORY
        assert "general" in TUN_FORMALITIES_BY_CATEGORY

    def test_mar_animal_products_category(self):
        """Livestock/animal products must require veterinary control (C01)."""
        from etl.country_taxes_morocco import get_mar_formalities_for_line
        for cat in ("livestock", "meat", "fish", "dairy", "poultry"):
            forms = get_mar_formalities_for_line(cat, "01")
            codes = {f["code"] for f in forms}
            assert "910" in codes, f"{cat}: missing DUM (910)"
            assert "C01" in codes, f"{cat}: missing veterinary control C01"

    def test_mar_food_agriculture_category(self):
        """Plant/agricultural products must require phytosanitary control (C02)."""
        from etl.country_taxes_morocco import get_mar_formalities_for_line
        for cat in ("vegetables", "fruits", "cereals", "oilseeds"):
            forms = get_mar_formalities_for_line(cat, "07")
            codes = {f["code"] for f in forms}
            assert "C02" in codes, f"{cat}: missing phytosanitary C02"

    def test_mar_pharmaceuticals_category(self):
        """Pharmaceuticals must require Ministry of Health auth (C04, C05)."""
        from etl.country_taxes_morocco import get_mar_formalities_for_line
        forms = get_mar_formalities_for_line("pharmaceuticals", "30")
        codes = {f["code"] for f in forms}
        assert "C04" in codes, "MAR pharma: missing Ministry of Health auth C04"
        assert "C05" in codes, "MAR pharma: missing AMM visa C05"

    def test_mar_vehicles_machinery_category(self):
        """Vehicles/machinery must require IMANOR conformity (C03)."""
        from etl.country_taxes_morocco import get_mar_formalities_for_line
        for cat in ("vehicles", "machinery", "electrical"):
            forms = get_mar_formalities_for_line(cat, "87")
            codes = {f["code"] for f in forms}
            assert "C03" in codes, f"{cat}: missing IMANOR certificate C03"

    def test_mar_chemicals_category(self):
        """Chemicals must require chemical analysis certificate (C11)."""
        from etl.country_taxes_morocco import get_mar_formalities_for_line
        forms = get_mar_formalities_for_line("chemicals", "28")
        codes = {f["code"] for f in forms}
        assert "C11" in codes, "MAR chemicals: missing chemical analysis C11"

    def test_mar_hydrocarbons_category(self):
        """Hydrocarbons must require ONHYM authorization (C09)."""
        from etl.country_taxes_morocco import get_mar_formalities_for_line
        forms = get_mar_formalities_for_line("mineral_fuels", "27")
        codes = {f["code"] for f in forms}
        assert "C09" in codes, "MAR mineral fuels: missing ONHYM auth C09"

    def test_mar_arms_category(self):
        """Arms must require Ministry of Interior authorization (C10)."""
        from etl.country_taxes_morocco import get_mar_formalities_for_line
        forms = get_mar_formalities_for_line("arms", "93")
        codes = {f["code"] for f in forms}
        assert "C10" in codes, "MAR arms: missing Interior Ministry auth C10"

    def test_mar_general_has_only_910(self):
        """General products must have at least DUM (910)."""
        from etl.country_taxes_morocco import get_mar_formalities_for_line
        forms = get_mar_formalities_for_line("general", "49")
        codes = {f["code"] for f in forms}
        assert "910" in codes

    def test_tun_animal_products_category(self):
        """TUN animal products must require veterinary certificate (102)."""
        from etl.country_taxes_tunisia import get_tun_formalities_for_line
        for cat in ("livestock", "meat", "fish", "dairy"):
            forms = get_tun_formalities_for_line(cat, "01")
            codes = {f["code"] for f in forms}
            assert "102" in codes, f"TUN {cat}: missing vet cert 102"

    def test_tun_food_agriculture_category(self):
        """TUN agricultural products must require ONAGRI authorization (101)."""
        from etl.country_taxes_tunisia import get_tun_formalities_for_line
        for cat in ("vegetables", "fruits", "cereals"):
            forms = get_tun_formalities_for_line(cat, "07")
            codes = {f["code"] for f in forms}
            assert "101" in codes, f"TUN {cat}: missing ONAGRI auth 101"

    def test_tun_pharmaceuticals_category(self):
        """TUN pharma must require Ministry of Health authorization (103)."""
        from etl.country_taxes_tunisia import get_tun_formalities_for_line
        forms = get_tun_formalities_for_line("pharmaceuticals", "30")
        codes = {f["code"] for f in forms}
        assert "103" in codes, "TUN pharma: missing Health auth 103"

    def test_tun_vehicles_machinery_category(self):
        """TUN vehicles must require INNORPI conformity (104)."""
        from etl.country_taxes_tunisia import get_tun_formalities_for_line
        for cat in ("vehicles", "machinery", "electrical"):
            forms = get_tun_formalities_for_line(cat, "87")
            codes = {f["code"] for f in forms}
            assert "104" in codes, f"TUN {cat}: missing INNORPI cert 104"

    def test_tun_chemicals_category(self):
        """TUN chemicals must require ANPE environmental declaration (105)."""
        from etl.country_taxes_tunisia import get_tun_formalities_for_line
        forms = get_tun_formalities_for_line("chemicals", "28")
        codes = {f["code"] for f in forms}
        assert "105" in codes, "TUN chemicals: missing ANPE declaration 105"

    def test_tun_hydrocarbons_category(self):
        """TUN hydrocarbons must require STEG/ETAP authorization (108)."""
        from etl.country_taxes_tunisia import get_tun_formalities_for_line
        forms = get_tun_formalities_for_line("mineral_fuels", "27")
        codes = {f["code"] for f in forms}
        assert "108" in codes, "TUN mineral_fuels: missing STEG/ETAP auth 108"

    def test_tun_arms_category(self):
        """TUN arms must require Ministry of Interior authorization (109)."""
        from etl.country_taxes_tunisia import get_tun_formalities_for_line
        forms = get_tun_formalities_for_line("arms", "93")
        codes = {f["code"] for f in forms}
        assert "109" in codes, "TUN arms: missing Interior Ministry auth 109"

    def test_all_formalities_have_required_fields(self):
        """Every formality entry must have code, document_fr, document_en, is_mandatory."""
        from etl.country_taxes_morocco import MAR_FORMALITIES_BY_CATEGORY
        from etl.country_taxes_tunisia import TUN_FORMALITIES_BY_CATEGORY

        required = {"code", "document_fr", "document_en", "is_mandatory"}
        for country, mapping in [("MAR", MAR_FORMALITIES_BY_CATEGORY), ("TUN", TUN_FORMALITIES_BY_CATEGORY)]:
            for bucket, forms in mapping.items():
                for f in forms:
                    missing = required - set(f.keys())
                    assert not missing, (
                        f"{country}/{bucket}: formality {f.get('code','?')} missing fields {missing}"
                    )

    def test_all_formalities_include_910_base(self):
        """Every formality bucket for both countries must include DUM (910) as first entry."""
        from etl.country_taxes_morocco import MAR_FORMALITIES_BY_CATEGORY
        from etl.country_taxes_tunisia import TUN_FORMALITIES_BY_CATEGORY

        for country, mapping in [("MAR", MAR_FORMALITIES_BY_CATEGORY), ("TUN", TUN_FORMALITIES_BY_CATEGORY)]:
            for bucket, forms in mapping.items():
                assert forms, f"{country}/{bucket}: empty formalities list"
                assert forms[0]["code"] == "910", (
                    f"{country}/{bucket}: first formality must be 910 (DUM), got {forms[0]['code']}"
                )

    # ---------- Data file integration tests ----------

    def _load(self, cc: str) -> list:
        import json
        path = os.path.join(
            os.path.dirname(__file__), "..", "data", "crawled", f"{cc}_tariffs.json"
        )
        with open(path, encoding="utf-8") as f:
            d = json.load(f)
        return d["tariff_lines"]

    def test_mar_data_has_multiple_document_types(self):
        """MAR crawled data must use more than just code 910."""
        lines = self._load("MAR")
        distinct_codes = {
            f["code"]
            for line in lines
            for f in line.get("administrative_formalities", [])
        }
        assert len(distinct_codes) >= 5, (
            f"MAR: expected ≥5 distinct document codes, got {sorted(distinct_codes)}"
        )

    def test_tun_data_has_multiple_document_types(self):
        """TUN crawled data must use more than just code 910."""
        lines = self._load("TUN")
        distinct_codes = {
            f["code"]
            for line in lines
            for f in line.get("administrative_formalities", [])
        }
        assert len(distinct_codes) >= 5, (
            f"TUN: expected ≥5 distinct document codes, got {sorted(distinct_codes)}"
        )

    def test_dza_data_formalities_unchanged(self):
        """DZA formalities must still be present and use the expected codes."""
        lines = self._load("DZA")
        distinct_codes = {
            f["code"]
            for line in lines
            for f in line.get("administrative_formalities", [])
        }
        # DZA uses codes 910, 210, 215, 216, 902, 920, 930, 940, 950, 960
        assert "910" in distinct_codes
        assert "216" in distinct_codes, "DZA veterinary cert (216) should still be present"
        assert "920" in distinct_codes, "DZA Ministry of Health auth (920) should still be present"

    def test_mar_livestock_lines_have_veterinary_doc(self):
        """All MAR livestock tariff lines must require veterinary control (C01)."""
        lines = self._load("MAR")
        livestock_lines = [l for l in lines if l.get("category") == "livestock"]
        assert livestock_lines, "Expected some MAR livestock lines"
        for line in livestock_lines:
            codes = {f["code"] for f in line.get("administrative_formalities", [])}
            assert "C01" in codes, (
                f"MAR livestock {line['hs6']}: missing veterinary control C01"
            )

    def test_tun_livestock_lines_have_veterinary_doc(self):
        """All TUN livestock tariff lines must require veterinary certificate (102)."""
        lines = self._load("TUN")
        livestock_lines = [l for l in lines if l.get("category") == "livestock"]
        assert livestock_lines, "Expected some TUN livestock lines"
        for line in livestock_lines:
            codes = {f["code"] for f in line.get("administrative_formalities", [])}
            assert "102" in codes, (
                f"TUN livestock {line['hs6']}: missing veterinary certificate 102"
            )

    def test_mar_pharma_lines_have_health_ministry_doc(self):
        """All MAR pharmaceuticals lines must require Ministry of Health auth (C04)."""
        lines = self._load("MAR")
        pharma_lines = [l for l in lines if l.get("category") in ("pharmaceuticals", "pharma")]
        assert pharma_lines, "Expected some MAR pharma lines"
        for line in pharma_lines:
            codes = {f["code"] for f in line.get("administrative_formalities", [])}
            assert "C04" in codes, (
                f"MAR pharma {line['hs6']}: missing Ministry of Health auth C04"
            )

    def test_tun_pharma_lines_have_health_ministry_doc(self):
        """All TUN pharmaceuticals lines must require DPHM authorization (103)."""
        lines = self._load("TUN")
        pharma_lines = [l for l in lines if l.get("category") in ("pharmaceuticals", "pharma")]
        assert pharma_lines, "Expected some TUN pharma lines"
        for line in pharma_lines:
            codes = {f["code"] for f in line.get("administrative_formalities", [])}
            assert "103" in codes, (
                f"TUN pharma {line['hs6']}: missing DPHM authorization 103"
            )

    def test_every_line_has_at_least_one_formality(self):
        """No tariff line should have an empty formalities list."""
        for cc in ("MAR", "TUN", "DZA"):
            lines = self._load(cc)
            empty = [l["hs6"] for l in lines if not l.get("administrative_formalities")]
            assert not empty, f"{cc}: {len(empty)} tariff lines have empty formalities: {empty[:5]}"

    def test_authentic_tariff_service_returns_formalities_for_mar(self):
        """get_administrative_formalities() must return enriched docs for MAR."""
        from services.authentic_tariff_service import get_administrative_formalities
        # Reload cache by resetting _tariff_cache
        import services.authentic_tariff_service as svc
        svc._tariff_cache.pop("MAR", None)

        # hs6 010110 = livestock → should have C01 (veterinary)
        forms = get_administrative_formalities("MAR", "010110")
        assert forms, "MAR/010110: no formalities returned"
        codes = {f["code"] for f in forms}
        assert "C01" in codes, f"MAR/010110: expected C01, got {sorted(codes)}"

    def test_authentic_tariff_service_returns_formalities_for_tun(self):
        """get_administrative_formalities() must return enriched docs for TUN."""
        from services.authentic_tariff_service import get_administrative_formalities
        import services.authentic_tariff_service as svc
        svc._tariff_cache.pop("TUN", None)

        # hs6 300490 = pharmaceuticals → should have 103 (DPHM)
        forms = get_administrative_formalities("TUN", "300490")
        assert forms, "TUN/300490: no formalities returned"
        codes = {f["code"] for f in forms}
        assert "103" in codes, f"TUN/300490: expected 103, got {sorted(codes)}"


# ==================== Africa-wide Administrative Formalities Tests ====================

class TestAllAfricaFormalities:
    """
    Tests for the universal administrative formalities framework
    covering all 54 African countries (etl/africa_formalities.py).

    Validates:
    - Module imports and structure
    - Chapter-to-bucket mapping (used by 19 general-only countries)
    - Category-to-bucket resolution
    - Country-specific authority data present for all 54 countries
    - Per-category document code assertions for key countries in each bloc
    - Data file quality for all 54 countries
    """

    # ---- Module structure ----

    def test_africa_formalities_imports_cleanly(self):
        from etl.africa_formalities import (
            COUNTRY_AUTHORITIES,
            CHAPTER_TO_BUCKET,
            get_formalities_for_line,
        )
        assert COUNTRY_AUTHORITIES
        assert CHAPTER_TO_BUCKET
        assert callable(get_formalities_for_line)

    def test_all_54_countries_have_authority_data(self):
        from etl.africa_formalities import COUNTRY_AUTHORITIES
        # All 54 AU member states
        all_54 = {
            "DZA","EGY","LBY","MAR","MRT","SDN","TUN",        # North Africa
            "BEN","BFA","CIV","GHA","GIN","GMB","GNB","LBR",
            "MLI","NER","NGA","SEN","SLE","TGO",              # ECOWAS
            "CAF","CMR","COG","GAB","GNQ","TCD",              # CEMAC
            "BDI","KEN","RWA","SSD","TZA","UGA",              # EAC
            "AGO","BWA","COM","LSO","MDG","MOZ","MUS","MWI",
            "NAM","SWZ","SYC","ZAF","ZMB","ZWE",             # SADC/COMESA
            "COD","DJI","ERI","ETH","SOM","STP","CPV",       # Others
        }
        missing = all_54 - set(COUNTRY_AUTHORITIES.keys())
        assert not missing, f"Missing authority data for: {sorted(missing)}"

    def test_each_authority_has_required_keys(self):
        from etl.africa_formalities import COUNTRY_AUTHORITIES
        required = {"customs", "veterinary", "phytosanitary", "health",
                    "standards", "environment", "energy", "interior", "agri_inputs"}
        for cc, auth in COUNTRY_AUTHORITIES.items():
            missing = required - set(auth.keys())
            assert not missing, f"{cc}: missing authority keys {missing}"

    def test_no_authority_name_is_empty(self):
        from etl.africa_formalities import COUNTRY_AUTHORITIES
        for cc, auth in COUNTRY_AUTHORITIES.items():
            for role, name in auth.items():
                assert name and name.strip(), f"{cc}/{role}: empty authority name"

    # ---- Chapter mapping ----

    def test_chapter_mapping_covers_all_chapters(self):
        from etl.africa_formalities import CHAPTER_TO_BUCKET
        # All HS chapters that appear in African tariff data (01-99 excluding 77)
        expected_chapters = {f"{i:02d}" for i in range(1, 99) if i != 77}
        missing = expected_chapters - set(CHAPTER_TO_BUCKET.keys())
        assert not missing, f"Missing chapter mappings: {sorted(missing)}"

    def test_chapter_01_is_animal_products(self):
        from etl.africa_formalities import CHAPTER_TO_BUCKET
        assert CHAPTER_TO_BUCKET["01"] == "animal_products"

    def test_chapter_30_is_pharmaceuticals(self):
        from etl.africa_formalities import CHAPTER_TO_BUCKET
        assert CHAPTER_TO_BUCKET["30"] == "pharmaceuticals"

    def test_chapter_27_is_hydrocarbons(self):
        from etl.africa_formalities import CHAPTER_TO_BUCKET
        assert CHAPTER_TO_BUCKET["27"] == "hydrocarbons"

    def test_chapter_87_is_vehicles_machinery(self):
        from etl.africa_formalities import CHAPTER_TO_BUCKET
        assert CHAPTER_TO_BUCKET["87"] == "vehicles_machinery"

    def test_chapter_93_is_arms_security(self):
        from etl.africa_formalities import CHAPTER_TO_BUCKET
        assert CHAPTER_TO_BUCKET["93"] == "arms_security"

    def test_chapter_31_is_agri_inputs(self):
        from etl.africa_formalities import CHAPTER_TO_BUCKET
        assert CHAPTER_TO_BUCKET["31"] == "agri_inputs"

    # ---- Per-country document code assertions ----

    def _forms(self, cc, category, chapter):
        from etl.africa_formalities import get_formalities_for_line
        return get_formalities_for_line(cc, category, chapter)

    def test_nga_pharma_returns_nafdac(self):
        forms = self._forms("NGA", "pharmaceuticals", "30")
        codes = {f["code"] for f in forms}
        assert "PHARMAUTH" in codes
        # Verify NAFDAC appears in authority text
        auth_names = " ".join(f["authority_fr"] for f in forms)
        assert "NAFDAC" in auth_names, "NGA pharma should reference NAFDAC"

    def test_ken_phyto_returns_kephis(self):
        forms = self._forms("KEN", "vegetables", "07")
        auth_names = " ".join(f["authority_fr"] for f in forms)
        assert "KEPHIS" in auth_names, "KEN food/agri should reference KEPHIS"

    def test_zaf_standards_returns_nrcs(self):
        forms = self._forms("ZAF", "vehicles", "87")
        codes = {f["code"] for f in forms}
        assert "STDCERT" in codes
        auth_names = " ".join(f["authority_fr"] for f in forms)
        assert "NRCS" in auth_names or "SABS" in auth_names, \
            "ZAF vehicles should reference NRCS or SABS"

    def test_eth_customs_returns_ecc(self):
        forms = self._forms("ETH", "general", "84")
        auth_names = " ".join(f["authority_fr"] for f in forms)
        assert "ECC" in auth_names or "Ethiopian Customs" in auth_names, \
            "ETH should reference Ethiopian Customs Commission"

    def test_cmr_health_returns_minsante(self):
        forms = self._forms("CMR", "pharmaceuticals", "30")
        auth_names = " ".join(f["authority_fr"] for f in forms)
        assert "MINSANTE" in auth_names, "CMR pharma should reference MINSANTE"

    def test_nga_energy_returns_nnpc(self):
        forms = self._forms("NGA", "mineral_fuels", "27")
        codes = {f["code"] for f in forms}
        assert "ENERGYAUTH" in codes
        auth_names = " ".join(f["authority_fr"] for f in forms)
        assert "NNPC" in auth_names or "DPR" in auth_names, \
            "NGA hydrocarbons should reference NNPC"

    def test_ken_vet_returns_dvs(self):
        forms = self._forms("KEN", "livestock", "01")
        auth_names = " ".join(f["authority_fr"] for f in forms)
        assert "DVS" in auth_names or "Veterinary" in auth_names, \
            "KEN livestock should reference DVS"

    def test_zaf_arms_returns_saps(self):
        forms = self._forms("ZAF", "arms", "93")
        codes = {f["code"] for f in forms}
        assert "ARMAUTH" in codes
        auth_names = " ".join(f["authority_fr"] for f in forms)
        assert "SAPS" in auth_names or "Police" in auth_names or "Interior" in auth_names

    def test_cmr_agri_inputs_returns_minader(self):
        forms = self._forms("CMR", "fertilizers", "31")
        codes = {f["code"] for f in forms}
        assert "AGRIINPUT" in codes
        auth_names = " ".join(f["authority_fr"] for f in forms)
        assert "MINADER" in auth_names or "MINRESI" in auth_names or "protection" in auth_names.lower()

    def test_all_formalities_always_include_impdec(self):
        """Every country/category combination must start with IMPDEC."""
        from etl.africa_formalities import COUNTRY_AUTHORITIES, get_formalities_for_line
        for cc in list(COUNTRY_AUTHORITIES.keys())[:10]:  # sample 10 countries
            for cat, ch in [("general","84"), ("livestock","01"),
                            ("pharmaceuticals","30"), ("arms","93")]:
                forms = get_formalities_for_line(cc, cat, ch)
                assert forms, f"{cc}/{cat}: empty formalities"
                assert forms[0]["code"] == "IMPDEC", \
                    f"{cc}/{cat}: first formality should be IMPDEC, got {forms[0]['code']}"

    def test_all_formalities_have_required_fields_africa(self):
        """Every formality entry must have code, document_fr, document_en, is_mandatory."""
        from etl.africa_formalities import COUNTRY_AUTHORITIES, get_formalities_for_line
        required = {"code", "document_fr", "document_en", "is_mandatory"}
        for cc in COUNTRY_AUTHORITIES:
            for cat, ch in [("general","84"),("livestock","01"),("pharmaceuticals","30")]:
                for fm in get_formalities_for_line(cc, cat, ch):
                    missing = required - set(fm.keys())
                    assert not missing, f"{cc}/{cat}: formality missing {missing}"

    # ---- Data file quality across all 54 countries ----

    def _load(self, cc):
        import json
        path = os.path.join(
            os.path.dirname(__file__), "..", "data", "crawled", f"{cc}_tariffs.json"
        )
        with open(path, encoding="utf-8") as f:
            return json.load(f)["tariff_lines"]

    def test_every_country_has_multi_doc_formalities(self):
        """Every country must have at least some lines with >1 document (not all single-doc)."""
        countries_to_check = [
            "NGA","KEN","ZAF","ETH","GHA","CMR","SEN","TZA","UGA","RWA",
            "AGO","MOZ","ZMB","ZWE","MUS","MDG","COD","BDI","EGY","LBY",
            "MRT","SDN","DJI","ERI","SOM","STP","CPV","BWA","LSO","NAM",
        ]
        for cc in countries_to_check:
            lines = self._load(cc)
            multi = sum(1 for l in lines if len(l.get("administrative_formalities",[])) > 1)
            assert multi > 0, f"{cc}: no lines have more than one formality document"

    def test_pharma_lines_have_pharmauth(self):
        """Pharmaceutical tariff lines (ch30) in key countries must have PHARMAUTH."""
        for cc in ["NGA","KEN","ZAF","ETH","CMR","GHA","SEN","TZA","UGA"]:
            lines = self._load(cc)
            ch30 = [l for l in lines if l.get("chapter") == "30"]
            if not ch30:
                continue
            for l in ch30:
                codes = {f["code"] for f in l.get("administrative_formalities",[])}
                assert "PHARMAUTH" in codes, \
                    f"{cc}/ch30/{l['hs6']}: missing PHARMAUTH"

    def test_animal_lines_have_vetcert(self):
        """Animal product tariff lines (ch01-05) must have VETCERT in key countries."""
        for cc in ["NGA","KEN","ZAF","ETH","CMR","GHA","SEN","TZA"]:
            lines = self._load(cc)
            animal = [l for l in lines if l.get("chapter") in ("01","02","03","04","05")]
            if not animal:
                continue
            for l in animal[:5]:  # sample first 5
                codes = {f["code"] for f in l.get("administrative_formalities",[])}
                assert "VETCERT" in codes, \
                    f"{cc}/ch{l['chapter']}/{l['hs6']}: missing VETCERT"

    def test_food_lines_have_phytocert(self):
        """Plant/food tariff lines (ch07-15) must have PHYTOCERT."""
        for cc in ["NGA","KEN","ZAF","ETH","GHA"]:
            lines = self._load(cc)
            food = [l for l in lines if l.get("chapter") in
                    ("07","08","09","10","11","12","13","14","15")]
            if not food:
                continue
            for l in food[:5]:
                codes = {f["code"] for f in l.get("administrative_formalities",[])}
                assert "PHYTOCERT" in codes, \
                    f"{cc}/ch{l['chapter']}/{l['hs6']}: missing PHYTOCERT"

    def test_hydro_lines_have_energyauth(self):
        """Hydrocarbon tariff lines (ch27) must have ENERGYAUTH."""
        for cc in ["NGA","AGO","GAB","COG","GNQ","LBY","SDN"]:
            lines = self._load(cc)
            hydro = [l for l in lines if l.get("chapter") == "27"]
            if not hydro:
                continue
            for l in hydro[:3]:
                codes = {f["code"] for f in l.get("administrative_formalities",[])}
                assert "ENERGYAUTH" in codes, \
                    f"{cc}/ch27/{l['hs6']}: missing ENERGYAUTH"

    def test_arms_lines_have_armauth(self):
        """Arms tariff lines (ch93) must have ARMAUTH."""
        for cc in ["NGA","KEN","ZAF","GHA","EGY"]:
            lines = self._load(cc)
            arms = [l for l in lines if l.get("chapter") == "93"]
            if not arms:
                continue
            for l in arms[:3]:
                codes = {f["code"] for f in l.get("administrative_formalities",[])}
                assert "ARMAUTH" in codes, \
                    f"{cc}/ch93/{l['hs6']}: missing ARMAUTH"

    def test_no_country_has_empty_formalities(self):
        """No tariff line in any country should have empty formalities."""
        all_countries = [
            "AGO","BDI","BEN","BFA","BWA","CAF","CIV","CMR","COD","COG",
            "COM","CPV","DJI","DZA","EGY","ERI","ETH","GAB","GHA","GIN",
            "GMB","GNB","GNQ","KEN","LBR","LBY","LSO","MAR","MDG","MLI",
            "MOZ","MRT","MUS","MWI","NAM","NER","NGA","RWA","SDN","SEN",
            "SLE","SOM","SSD","STP","SWZ","SYC","TCD","TGO","TUN","TZA",
            "UGA","ZAF","ZMB","ZWE",
        ]
        for cc in all_countries:
            lines = self._load(cc)
            empty = [l["hs6"] for l in lines
                     if not l.get("administrative_formalities")]
            assert not empty, \
                f"{cc}: {len(empty)} tariff lines have empty formalities"

    def test_authority_names_are_country_specific(self):
        """NGA and KEN must have different authority names for the same document."""
        from etl.africa_formalities import get_formalities_for_line
        nga_pharma = get_formalities_for_line("NGA", "pharmaceuticals", "30")
        ken_pharma = get_formalities_for_line("KEN", "pharmaceuticals", "30")
        nga_auth = {f["authority_fr"] for f in nga_pharma}
        ken_auth = {f["authority_fr"] for f in ken_pharma}
        assert nga_auth != ken_auth, \
            "NGA and KEN pharma formalities should have different authority names"

    def test_dza_formalities_preserved(self):
        """DZA must still retain its original code set (910, 210, 215, 216…)."""
        lines = self._load("DZA")
        distinct = {f["code"] for l in lines for f in l.get("administrative_formalities",[])}
        assert "910" in distinct, "DZA: missing 910"
        assert "216" in distinct, "DZA: missing 216 (vet cert)"
        assert "920" in distinct, "DZA: missing 920 (health ministry)"
        # DZA should NOT have been overwritten with IMPDEC scheme
        assert "IMPDEC" not in distinct, "DZA: should keep original code scheme"

    def test_authentic_tariff_service_nga_returns_nafdac(self):
        """Authentic tariff service must return NAFDAC for NGA pharmaceutical lines."""
        from services.authentic_tariff_service import get_administrative_formalities
        import services.authentic_tariff_service as svc
        svc._tariff_cache.pop("NGA", None)
        # hs6 300490 = pharma → ch30
        forms = get_administrative_formalities("NGA", "300490")
        if forms:  # NGA has chapter-based mapping → should work
            codes = {f["code"] for f in forms}
            assert "PHARMAUTH" in codes, f"NGA/300490: expected PHARMAUTH, got {sorted(codes)}"

    def test_authentic_tariff_service_ken_returns_kephis(self):
        """Authentic tariff service must return PHYTOCERT for KEN food lines."""
        from services.authentic_tariff_service import get_administrative_formalities
        import services.authentic_tariff_service as svc
        svc._tariff_cache.pop("KEN", None)
        forms = get_administrative_formalities("KEN", "070190")  # potatoes ch07
        if forms:
            codes = {f["code"] for f in forms}
            assert "PHYTOCERT" in codes, f"KEN/070190: expected PHYTOCERT, got {sorted(codes)}"

    # ---- DRC / COD — OCC-specific tests ----

    def test_cod_occ_authority_has_dedicated_role(self):
        """COD authority entry must have an 'occ' key referencing OCC."""
        from etl.africa_formalities import COUNTRY_AUTHORITIES
        auth = COUNTRY_AUTHORITIES.get("COD", {})
        assert "occ" in auth, "COD authority entry must have an 'occ' role"
        assert "OCC" in auth["occ"], f"COD occ role must reference OCC, got: {auth['occ']}"
        assert "Décret" in auth["occ"] or "Decret" in auth["occ"], \
            "COD occ authority should include legal citation (Décret)"

    def test_cod_all_lines_have_occdecl(self):
        """Every COD tariff line must carry OCCDECL (OCC universal mandate)."""
        lines = self._load("COD")
        assert lines, "COD: no tariff lines found"
        missing = [
            l["hs6"]
            for l in lines
            if not any(f["code"] == "OCCDECL" for f in l.get("administrative_formalities", []))
        ]
        assert not missing, (
            f"COD: {len(missing)} lines missing OCCDECL — "
            f"first 5: {missing[:5]}"
        )

    def test_cod_occdecl_has_correct_authority(self):
        """OCCDECL entries in COD must reference OCC and the Décret."""
        lines = self._load("COD")
        for l in lines[:20]:
            for fm in l.get("administrative_formalities", []):
                if fm["code"] == "OCCDECL":
                    assert "OCC" in fm["authority_fr"], \
                        f"COD OCCDECL authority_fr should mention OCC: {fm['authority_fr']}"
                    assert fm["is_mandatory"] is True, \
                        "COD OCCDECL must be mandatory"
                    assert "1,5" in fm["document_fr"] or "1.5" in fm["document_en"], \
                        "OCCDECL should mention the 1.5% CIF redevance rate"
                    break

    def test_cod_occdecl_is_always_last_formality(self):
        """OCCDECL should be the last formality in every COD line (injected after bucket docs)."""
        lines = self._load("COD")
        for l in lines[:50]:
            forms = l.get("administrative_formalities", [])
            if forms:
                assert forms[-1]["code"] == "OCCDECL", (
                    f"COD {l['hs6']}: OCCDECL should be the last doc, "
                    f"got {forms[-1]['code']}"
                )

    def test_cod_pharma_lines_have_both_pharmauth_and_occdecl(self):
        """COD pharmaceutical lines (ch30) must have PHARMAUTH *and* OCCDECL."""
        lines = self._load("COD")
        ch30 = [l for l in lines if l.get("chapter") == "30"]
        assert ch30, "COD: no chapter 30 lines found"
        for l in ch30:
            codes = {f["code"] for f in l.get("administrative_formalities", [])}
            assert "PHARMAUTH" in codes, f"COD/ch30/{l['hs6']}: missing PHARMAUTH"
            assert "OCCDECL" in codes, f"COD/ch30/{l['hs6']}: missing OCCDECL"

    def test_cod_animal_lines_have_vetcert_and_occdecl(self):
        """COD animal product lines must have VETCERT *and* OCCDECL."""
        lines = self._load("COD")
        animal = [l for l in lines if l.get("chapter") in ("01", "02", "03", "04", "05")]
        assert animal, "COD: no animal product lines found"
        for l in animal[:5]:
            codes = {f["code"] for f in l.get("administrative_formalities", [])}
            assert "VETCERT" in codes, f"COD/{l['chapter']}/{l['hs6']}: missing VETCERT"
            assert "OCCDECL" in codes, f"COD/{l['chapter']}/{l['hs6']}: missing OCCDECL"

    def test_cod_vehicle_lines_have_stdcert_and_occdecl(self):
        """COD vehicle lines (ch87) must have STDCERT (from OCC) *and* OCCDECL."""
        lines = self._load("COD")
        vehicles = [l for l in lines if l.get("chapter") == "87"]
        assert vehicles, "COD: no chapter 87 (vehicle) lines found"
        for l in vehicles[:5]:
            codes = {f["code"] for f in l.get("administrative_formalities", [])}
            assert "STDCERT" in codes, f"COD/ch87/{l['hs6']}: missing STDCERT"
            assert "OCCDECL" in codes, f"COD/ch87/{l['hs6']}: missing OCCDECL"

    def test_cod_general_lines_have_impdec_and_occdecl(self):
        """COD general (mineral) lines must have at minimum IMPDEC and OCCDECL."""
        lines = self._load("COD")
        # ch26 = ores — DRC's most important export category → imports of equipment etc.
        # ch72 = iron and steel = general manufactured goods
        general_chs = [l for l in lines if l.get("chapter") in ("26", "72")]
        if not general_chs:
            general_chs = lines[:5]
        for l in general_chs[:5]:
            codes = {f["code"] for f in l.get("administrative_formalities", [])}
            assert "IMPDEC" in codes, f"COD/{l['hs6']}: missing IMPDEC"
            assert "OCCDECL" in codes, f"COD/{l['hs6']}: missing OCCDECL"

    def test_other_countries_do_not_have_occdecl(self):
        """No country other than COD should have OCCDECL in its tariff data."""
        other_countries = ["NGA", "KEN", "ZAF", "ETH", "CMR", "GHA", "SEN", "TZA"]
        for cc in other_countries:
            lines = self._load(cc)
            occ_lines = [
                l["hs6"]
                for l in lines
                if any(f["code"] == "OCCDECL" for f in l.get("administrative_formalities", []))
            ]
            assert not occ_lines, (
                f"{cc}: should NOT have OCCDECL, but found it in {len(occ_lines)} lines"
            )

    def test_cod_occdecl_from_get_formalities_for_line(self):
        """get_formalities_for_line for COD always injects OCCDECL regardless of bucket."""
        from etl.africa_formalities import get_formalities_for_line
        test_cases = [
            ("livestock",       "01"),
            ("food",            "07"),
            ("pharmaceuticals", "30"),
            ("vehicles",        "87"),
            ("general",         "26"),
            ("chemicals",       "28"),
            ("hydrocarbons",    "27"),
            ("arms",            "93"),
            ("fertilizers",     "31"),
        ]
        for cat, ch in test_cases:
            forms = get_formalities_for_line("COD", cat, ch)
            codes = [f["code"] for f in forms]
            assert "OCCDECL" in codes, \
                f"COD/{cat}/ch{ch}: OCCDECL not in {codes}"
            assert codes[-1] == "OCCDECL", \
                f"COD/{cat}/ch{ch}: OCCDECL should be last, got {codes[-1]}"

    # ---- Para-fiscal analogue systems (NGA FORMM, EGY GOEIC, ETH ETHPERMIT, CEMAC ECTN) ----

    def test_para_fiscal_levies_module_imports_cleanly(self):
        """etl/para_fiscal_levies.py must import without errors."""
        from etl.para_fiscal_levies import (
            LEVY_DESCRIPTIONS,
            COUNTRY_PARA_FISCAL_FORMALITIES,
            enrich_observation,
            get_para_fiscal_formalities,
        )
        assert LEVY_DESCRIPTIONS
        assert COUNTRY_PARA_FISCAL_FORMALITIES
        assert callable(enrich_observation)
        assert callable(get_para_fiscal_formalities)

    def test_levy_descriptions_cover_key_codes(self):
        """LEVY_DESCRIPTIONS must cover all common para-fiscal levy codes."""
        from etl.para_fiscal_levies import LEVY_DESCRIPTIONS
        required = {"CISS", "IDF", "RDL", "GETFUND", "NHIL",
                    "CEDEAO", "PCC", "RS", "PCS", "PUA",
                    "TCI", "CAC", "SUR", "PRCT", "TPI", "IE"}
        missing = required - set(LEVY_DESCRIPTIONS.keys())
        assert not missing, f"LEVY_DESCRIPTIONS missing codes: {missing}"

    def test_enrich_observation_ciss(self):
        """enrich_observation('CISS') must return descriptive text with legal basis."""
        from etl.para_fiscal_levies import enrich_observation
        obs = enrich_observation("CISS")
        assert "1%" in obs, "CISS observation should mention 1% rate"
        assert "Nigeria" in obs, "CISS observation should mention Nigeria"
        assert obs != "CISS", "observation should not just be the code"

    def test_enrich_observation_idf(self):
        from etl.para_fiscal_levies import enrich_observation
        obs = enrich_observation("IDF")
        assert "3.5" in obs, "IDF observation should mention 3.5% rate"
        assert "Kenya" in obs or "KRA" in obs

    def test_enrich_observation_unknown_returns_code(self):
        from etl.para_fiscal_levies import enrich_observation
        obs = enrich_observation("UNKNOWNCODE")
        assert obs == "UNKNOWNCODE"

    def test_nga_all_lines_have_formm(self):
        """Every NGA tariff line must carry FORMM (CBN Form M pre-import authorization)."""
        lines = self._load("NGA")
        assert lines
        missing = [
            l["hs6"] for l in lines
            if not any(f["code"] == "FORMM" for f in l.get("administrative_formalities", []))
        ]
        assert not missing, f"NGA: {len(missing)} lines missing FORMM — first 5: {missing[:5]}"

    def test_nga_formm_authority_is_cbn(self):
        """NGA FORMM must reference the Central Bank of Nigeria."""
        lines = self._load("NGA")
        for l in lines[:20]:
            for fm in l.get("administrative_formalities", []):
                if fm["code"] == "FORMM":
                    assert "CBN" in fm["authority_en"] or "Central Bank" in fm["authority_en"], \
                        f"NGA FORMM authority should reference CBN: {fm['authority_en']}"
                    assert fm["is_mandatory"] is True
                    break

    def test_nga_formm_from_get_formalities(self):
        """get_formalities_for_line('NGA', ...) always produces FORMM for all buckets."""
        from etl.africa_formalities import get_formalities_for_line
        for cat, ch in [("livestock", "01"), ("pharmaceuticals", "30"),
                         ("vehicles", "87"), ("general", "84"),
                         ("hydrocarbons", "27"), ("arms", "93")]:
            forms = get_formalities_for_line("NGA", cat, ch)
            codes = [f["code"] for f in forms]
            assert "FORMM" in codes, f"NGA/{cat}/ch{ch}: FORMM not in {codes}"

    def test_nga_taxes_ciss_has_proper_observation(self):
        """NGA taxes_detail CISS entry must have a descriptive observation (not empty)."""
        lines = self._load("NGA")
        for l in lines:
            for tx in l.get("taxes_detail", []):
                if tx.get("tax") == "CISS":
                    obs = tx.get("observation", "")
                    assert obs and obs != "CISS", \
                        f"NGA CISS observation should be descriptive, got: '{obs}'"
                    assert "1%" in obs or "CISS" in obs, \
                        f"NGA CISS observation should describe the levy"
                    break
            else:
                continue
            break

    def test_nga_other_taxes_rate_reflects_para_fiscal(self):
        """NGA other_taxes_rate must reflect CISS + CEDEAO sum (≥ 1.0%)."""
        lines = self._load("NGA")
        for l in lines:
            rate = l.get("other_taxes_rate", 0.0)
            if rate > 0:
                assert rate >= 1.0, \
                    f"NGA other_taxes_rate should be ≥ 1.0 (CISS 1%), got {rate}"
                break

    def test_egy_manufactured_lines_have_goeic(self):
        """EGY manufactured goods lines (ch84-87) must carry GOEIC."""
        lines = self._load("EGY")
        manufactured = [l for l in lines if l.get("chapter") in ("84", "85", "87")]
        assert manufactured
        for l in manufactured[:5]:
            codes = {f["code"] for f in l.get("administrative_formalities", [])}
            assert "GOEIC" in codes, \
                f"EGY/ch{l['chapter']}/{l['hs6']}: missing GOEIC inspection cert"

    def test_egy_raw_animal_lines_no_goeic(self):
        """EGY ch01 (live animals) must NOT carry GOEIC."""
        lines = self._load("EGY")
        ch01 = [l for l in lines if l.get("chapter") == "01"]
        assert ch01
        for l in ch01[:5]:
            codes = {f["code"] for f in l.get("administrative_formalities", [])}
            assert "GOEIC" not in codes, \
                f"EGY/ch01/{l['hs6']}: GOEIC should not apply to live animals"

    def test_egy_crude_oil_no_goeic(self):
        """EGY ch27 (crude oil/gas) must NOT carry GOEIC."""
        lines = self._load("EGY")
        ch27 = [l for l in lines if l.get("chapter") == "27"]
        if ch27:
            for l in ch27[:3]:
                codes = {f["code"] for f in l.get("administrative_formalities", [])}
                assert "GOEIC" not in codes, \
                    f"EGY/ch27/{l['hs6']}: GOEIC should not apply to crude oil"

    def test_egy_goeic_authority_is_goeic(self):
        """EGY GOEIC formality must reference GOEIC and Decree 991/2015."""
        lines = self._load("EGY")
        for l in lines:
            for fm in l.get("administrative_formalities", []):
                if fm["code"] == "GOEIC":
                    assert "GOEIC" in fm["authority_en"], \
                        f"EGY GOEIC authority must mention GOEIC: {fm['authority_en']}"
                    assert fm["is_mandatory"] is True
                    break
            else:
                continue
            break

    def test_eth_manufactured_lines_have_ethpermit(self):
        """ETH vehicles/machinery lines (ch87) must carry ETHPERMIT."""
        lines = self._load("ETH")
        ch87 = [l for l in lines if l.get("chapter") == "87"]
        assert ch87
        for l in ch87[:5]:
            codes = {f["code"] for f in l.get("administrative_formalities", [])}
            assert "ETHPERMIT" in codes, \
                f"ETH/ch87/{l['hs6']}: missing ETHPERMIT (Ministry of Trade permit)"

    def test_eth_raw_animal_lines_no_ethpermit(self):
        """ETH ch01 (live animals) must NOT carry ETHPERMIT."""
        lines = self._load("ETH")
        ch01 = [l for l in lines if l.get("chapter") == "01"]
        assert ch01
        for l in ch01[:5]:
            codes = {f["code"] for f in l.get("administrative_formalities", [])}
            assert "ETHPERMIT" not in codes, \
                f"ETH/ch01/{l['hs6']}: ETHPERMIT should not apply to live animals"

    def test_eth_processed_food_has_ethpermit(self):
        """ETH processed food (ch16 — meat preparations) must carry ETHPERMIT."""
        lines = self._load("ETH")
        ch16 = [l for l in lines if l.get("chapter") == "16"]
        assert ch16, "ETH should have ch16 lines (processed meat/fish preparations)"
        for l in ch16[:3]:
            codes = {f["code"] for f in l.get("administrative_formalities", [])}
            assert "ETHPERMIT" in codes, \
                f"ETH/ch16/{l['hs6']}: ETHPERMIT should apply to processed food"

    def test_cemac_countries_have_ectn(self):
        """All 6 CEMAC countries must have ECTN on every tariff line."""
        cemac = ["CMR", "CAF", "COG", "GAB", "GNQ", "TCD"]
        for cc in cemac:
            lines = self._load(cc)
            assert lines
            missing = [
                l["hs6"] for l in lines
                if not any(f["code"] == "ECTN" for f in l.get("administrative_formalities", []))
            ]
            assert not missing, (
                f"{cc}: {len(missing)} lines missing ECTN — first 5: {missing[:5]}"
            )

    def test_cemac_ectn_authority_is_national_shippers_council(self):
        """CEMAC ECTN formality must reference the national shippers council."""
        for cc in ["CMR", "CAF", "COG", "GAB", "GNQ", "TCD"]:
            lines = self._load(cc)
            for l in lines[:10]:
                for fm in l.get("administrative_formalities", []):
                    if fm["code"] == "ECTN":
                        assert "Chargeurs" in fm["authority_fr"] or "Shippers" in fm["authority_en"], \
                            f"{cc} ECTN authority should reference Shippers Council: {fm['authority_fr']}"
                        assert fm["is_mandatory"] is True
                        break

    def test_non_cemac_no_ectn(self):
        """Non-CEMAC countries must NOT have ECTN."""
        for cc in ["NGA", "KEN", "ZAF", "GHA", "ETH", "SEN", "BEN"]:
            lines = self._load(cc)
            ectn_lines = [
                l["hs6"] for l in lines
                if any(f["code"] == "ECTN" for f in l.get("administrative_formalities", []))
            ]
            assert not ectn_lines, f"{cc}: should NOT have ECTN, found in {len(ectn_lines)} lines"

    def test_nga_not_in_cemac_ectn(self):
        """NGA gets FORMM (not ECTN)."""
        from etl.africa_formalities import get_formalities_for_line
        forms = get_formalities_for_line("NGA", "general", "84")
        codes = [f["code"] for f in forms]
        assert "FORMM" in codes
        assert "ECTN" not in codes

    def test_ken_idf_observation_descriptive(self):
        """KEN taxes_detail IDF must have a descriptive observation."""
        lines = self._load("KEN")
        for l in lines:
            for tx in l.get("taxes_detail", []):
                if tx.get("tax") == "IDF":
                    obs = tx.get("observation", "")
                    assert obs and obs != "IDF", f"KEN IDF observation should be descriptive, got '{obs}'"
                    assert "3.5" in obs or "Import Declaration" in obs
                    break
            else:
                continue
            break

    def test_gha_getfund_observation_descriptive(self):
        """GHA taxes_detail GETFUND and NHIL must have descriptive observations."""
        lines = self._load("GHA")
        for l in lines:
            taxes = {tx["tax"]: tx["observation"] for tx in l.get("taxes_detail", [])}
            if "GETFUND" in taxes:
                obs = taxes["GETFUND"]
                assert obs and obs != "GETFUND", f"GHA GETFUND observation should be descriptive"
                assert "Ghana" in obs or "Education" in obs or "2.5" in obs
            if "NHIL" in taxes:
                obs = taxes["NHIL"]
                assert obs and obs != "NHIL", f"GHA NHIL observation should be descriptive"
                assert "Health" in obs or "2.5" in obs
            if "GETFUND" in taxes:  # only check when we found the relevant taxes
                break

    def test_nga_other_taxes_rate_non_zero(self):
        """NGA other_taxes_rate must be > 0 (has CISS 1% + CEDEAO 1%)."""
        lines = self._load("NGA")
        zero_count = sum(1 for l in lines if l.get("other_taxes_rate", 0) == 0)
        assert zero_count == 0, \
            f"NGA: {zero_count} lines have other_taxes_rate=0 despite CISS/CEDEAO levies"

    def test_gha_other_taxes_rate_reflects_getfund_nhil(self):
        """GHA other_taxes_rate must reflect GETFUND 2.5% + NHIL 2.5% + CEDEAO 1% = ~6%."""
        lines = self._load("GHA")
        for l in lines:
            rate = l.get("other_taxes_rate", 0)
            if rate > 0:
                assert rate >= 5.0, f"GHA other_taxes_rate expected ≥5% (GETFUND+NHIL+CEDEAO), got {rate}"
                break

    def test_para_fiscal_get_formalities_all_buckets_nga(self):
        """get_para_fiscal_formalities for NGA always returns FORMM regardless of bucket."""
        from etl.para_fiscal_levies import get_para_fiscal_formalities
        for bucket, ch in [("general", "84"), ("animal_products", "01"),
                             ("pharmaceuticals", "30"), ("hydrocarbons", "27"),
                             ("arms_security", "93")]:
            extras = get_para_fiscal_formalities("NGA", bucket, ch)
            codes = [f["code"] for f in extras]
            assert "FORMM" in codes, f"NGA/{bucket}/ch{ch}: FORMM not in {codes}"

    # ─────────────────────────────────────────────────────────────────────────
    # EGY chapter-level GOEIC scoping
    # ─────────────────────────────────────────────────────────────────────────

    def test_egy_goeic_chapter_30_included(self):
        """EGY ch30 (pharmaceuticals) must have GOEIC."""
        from etl.para_fiscal_levies import get_para_fiscal_formalities
        extras = get_para_fiscal_formalities("EGY", "pharmaceuticals", "30")
        codes = [f["code"] for f in extras]
        assert "GOEIC" in codes

    def test_egy_goeic_chapter_87_included(self):
        """EGY ch87 (vehicles) must have GOEIC."""
        from etl.para_fiscal_levies import get_para_fiscal_formalities
        extras = get_para_fiscal_formalities("EGY", "vehicles_machinery", "87")
        codes = [f["code"] for f in extras]
        assert "GOEIC" in codes

    def test_egy_goeic_chapter_27_exempt(self):
        """EGY ch27 (crude oil/gas) is exempt from GOEIC."""
        from etl.para_fiscal_levies import get_para_fiscal_formalities
        extras = get_para_fiscal_formalities("EGY", "hydrocarbons", "27")
        codes = [f["code"] for f in extras]
        assert "GOEIC" not in codes

    def test_egy_goeic_chapter_93_exempt(self):
        """EGY ch93 (arms) is exempt from GOEIC."""
        from etl.para_fiscal_levies import get_para_fiscal_formalities
        extras = get_para_fiscal_formalities("EGY", "arms_security", "93")
        codes = [f["code"] for f in extras]
        assert "GOEIC" not in codes

    def test_egy_goeic_chapter_01_exempt(self):
        """EGY ch01 (live animals) is exempt from GOEIC."""
        from etl.para_fiscal_levies import get_para_fiscal_formalities
        extras = get_para_fiscal_formalities("EGY", "animal_products", "01")
        codes = [f["code"] for f in extras]
        assert "GOEIC" not in codes

    def test_egy_goeic_chapter_10_exempt(self):
        """EGY ch10 (cereals) is exempt from GOEIC."""
        from etl.para_fiscal_levies import get_para_fiscal_formalities
        extras = get_para_fiscal_formalities("EGY", "food_agriculture", "10")
        codes = [f["code"] for f in extras]
        assert "GOEIC" not in codes

    def test_egy_goeic_chapter_84_included(self):
        """EGY ch84 (machinery) must have GOEIC."""
        from etl.para_fiscal_levies import get_para_fiscal_formalities
        extras = get_para_fiscal_formalities("EGY", "general", "84")
        codes = [f["code"] for f in extras]
        assert "GOEIC" in codes

    # ─────────────────────────────────────────────────────────────────────────
    # ETH chapter-level ETHPERMIT scoping
    # ─────────────────────────────────────────────────────────────────────────

    def test_eth_chapter_14_exempt(self):
        """ETH ch14 (vegetable materials) is exempt from ETHPERMIT."""
        from etl.para_fiscal_levies import get_para_fiscal_formalities
        extras = get_para_fiscal_formalities("ETH", "food_agriculture", "14")
        codes = [f["code"] for f in extras]
        assert "ETHPERMIT" not in codes

    def test_eth_chapter_15_has_ethpermit(self):
        """ETH ch15 (animal/vegetable fats) requires ETHPERMIT (boundary chapter)."""
        from etl.para_fiscal_levies import get_para_fiscal_formalities
        extras = get_para_fiscal_formalities("ETH", "food_agriculture", "15")
        codes = [f["code"] for f in extras]
        assert "ETHPERMIT" in codes

    def test_eth_chapter_16_has_ethpermit(self):
        """ETH ch16 (preparations of meat) requires ETHPERMIT (processed food)."""
        from etl.para_fiscal_levies import get_para_fiscal_formalities
        extras = get_para_fiscal_formalities("ETH", "food_agriculture", "16")
        codes = [f["code"] for f in extras]
        assert "ETHPERMIT" in codes

    def test_eth_chapter_84_has_ethpermit(self):
        """ETH ch84 (machinery) requires ETHPERMIT."""
        from etl.para_fiscal_levies import get_para_fiscal_formalities
        extras = get_para_fiscal_formalities("ETH", "general", "84")
        codes = [f["code"] for f in extras]
        assert "ETHPERMIT" in codes

    def test_eth_chapter_01_exempt(self):
        """ETH ch01 (live animals) is exempt from ETHPERMIT."""
        from etl.para_fiscal_levies import get_para_fiscal_formalities
        extras = get_para_fiscal_formalities("ETH", "animal_products", "01")
        codes = [f["code"] for f in extras]
        assert "ETHPERMIT" not in codes

    # ─────────────────────────────────────────────────────────────────────────
    # get_para_fiscal_formalities — CEMAC individual members
    # ─────────────────────────────────────────────────────────────────────────

    def test_cemac_get_formalities_gab(self):
        """get_para_fiscal_formalities for GAB returns ECTN."""
        from etl.para_fiscal_levies import get_para_fiscal_formalities
        extras = get_para_fiscal_formalities("GAB", "general", "84")
        codes = [f["code"] for f in extras]
        assert "ECTN" in codes

    def test_cemac_get_formalities_caf(self):
        """get_para_fiscal_formalities for CAF returns ECTN."""
        from etl.para_fiscal_levies import get_para_fiscal_formalities
        extras = get_para_fiscal_formalities("CAF", "general", "87")
        codes = [f["code"] for f in extras]
        assert "ECTN" in codes

    def test_cemac_get_formalities_cog(self):
        """get_para_fiscal_formalities for COG returns ECTN."""
        from etl.para_fiscal_levies import get_para_fiscal_formalities
        extras = get_para_fiscal_formalities("COG", "food_agriculture", "16")
        codes = [f["code"] for f in extras]
        assert "ECTN" in codes

    def test_cemac_get_formalities_gnq(self):
        """get_para_fiscal_formalities for GNQ returns ECTN."""
        from etl.para_fiscal_levies import get_para_fiscal_formalities
        extras = get_para_fiscal_formalities("GNQ", "pharmaceuticals", "30")
        codes = [f["code"] for f in extras]
        assert "ECTN" in codes

    def test_cemac_get_formalities_tcd(self):
        """get_para_fiscal_formalities for TCD returns ECTN."""
        from etl.para_fiscal_levies import get_para_fiscal_formalities
        extras = get_para_fiscal_formalities("TCD", "general", "84")
        codes = [f["code"] for f in extras]
        assert "ECTN" in codes

    def test_get_formalities_unknown_country_returns_empty(self):
        """get_para_fiscal_formalities for a country with no registration returns []."""
        from etl.para_fiscal_levies import get_para_fiscal_formalities
        extras = get_para_fiscal_formalities("ZZZ", "general", "84")
        assert extras == []

    # ─────────────────────────────────────────────────────────────────────────
    # Data files — individual CEMAC members have ECTN on all lines
    # ─────────────────────────────────────────────────────────────────────────

    def test_gab_all_lines_have_ectn(self):
        """GAB tariff data: all 5831 lines carry ECTN formality."""
        import json, os
        path = os.path.join(os.path.dirname(__file__), "..", "data", "crawled", "GAB_tariffs.json")
        if not os.path.exists(path):
            pytest.skip("GAB_tariffs.json not found")
        with open(path) as f:
            d = json.load(f)
        lines = d["tariff_lines"]
        without = [l["hs_code"] for l in lines
                   if not any(fm["code"] == "ECTN" for fm in l.get("administrative_formalities", []))]
        assert without == [], f"GAB lines without ECTN: {without[:5]}"

    def test_caf_all_lines_have_ectn(self):
        """CAF tariff data: all lines carry ECTN formality."""
        import json, os
        path = os.path.join(os.path.dirname(__file__), "..", "data", "crawled", "CAF_tariffs.json")
        if not os.path.exists(path):
            pytest.skip("CAF_tariffs.json not found")
        with open(path) as f:
            d = json.load(f)
        lines = d["tariff_lines"]
        without = [l["hs_code"] for l in lines
                   if not any(fm["code"] == "ECTN" for fm in l.get("administrative_formalities", []))]
        assert without == [], f"CAF lines without ECTN: {without[:5]}"

    def test_cog_all_lines_have_ectn(self):
        """COG tariff data: all lines carry ECTN formality."""
        import json, os
        path = os.path.join(os.path.dirname(__file__), "..", "data", "crawled", "COG_tariffs.json")
        if not os.path.exists(path):
            pytest.skip("COG_tariffs.json not found")
        with open(path) as f:
            d = json.load(f)
        lines = d["tariff_lines"]
        without = [l["hs_code"] for l in lines
                   if not any(fm["code"] == "ECTN" for fm in l.get("administrative_formalities", []))]
        assert without == [], f"COG lines without ECTN: {without[:5]}"

    def test_gnq_all_lines_have_ectn(self):
        """GNQ tariff data: all lines carry ECTN formality."""
        import json, os
        path = os.path.join(os.path.dirname(__file__), "..", "data", "crawled", "GNQ_tariffs.json")
        if not os.path.exists(path):
            pytest.skip("GNQ_tariffs.json not found")
        with open(path) as f:
            d = json.load(f)
        lines = d["tariff_lines"]
        without = [l["hs_code"] for l in lines
                   if not any(fm["code"] == "ECTN" for fm in l.get("administrative_formalities", []))]
        assert without == [], f"GNQ lines without ECTN: {without[:5]}"

    def test_tcd_all_lines_have_ectn(self):
        """TCD tariff data: all lines carry ECTN formality."""
        import json, os
        path = os.path.join(os.path.dirname(__file__), "..", "data", "crawled", "TCD_tariffs.json")
        if not os.path.exists(path):
            pytest.skip("TCD_tariffs.json not found")
        with open(path) as f:
            d = json.load(f)
        lines = d["tariff_lines"]
        without = [l["hs_code"] for l in lines
                   if not any(fm["code"] == "ECTN" for fm in l.get("administrative_formalities", []))]
        assert without == [], f"TCD lines without ECTN: {without[:5]}"

    def test_cemac_ectn_authorities_country_specific(self):
        """Each CEMAC country has its own shippers council in the ECTN authority."""
        from etl.para_fiscal_levies import COUNTRY_PARA_FISCAL_FORMALITIES
        expected = {
            "CMR": "CNCC",
            "CAF": "CCC",
            "COG": "CCC",
            "GAB": "CGC",
            "GNQ": "CNC-GQ",
            "TCD": "CTC",
        }
        for cc, acronym in expected.items():
            entry = COUNTRY_PARA_FISCAL_FORMALITIES[cc][0]
            auth = entry["authority_en"]
            assert acronym in auth, f"{cc}: expected '{acronym}' in authority '{auth}'"

    # ─────────────────────────────────────────────────────────────────────────
    # enrich_observation — extended code coverage
    # ─────────────────────────────────────────────────────────────────────────

    def test_enrich_observation_getfund(self):
        from etl.para_fiscal_levies import enrich_observation
        obs = enrich_observation("GETFUND")
        assert "Ghana" in obs and "Education" in obs

    def test_enrich_observation_nhil(self):
        from etl.para_fiscal_levies import enrich_observation
        obs = enrich_observation("NHIL")
        assert "Health Insurance" in obs and "Ghana" in obs

    def test_enrich_observation_sur(self):
        from etl.para_fiscal_levies import enrich_observation
        obs = enrich_observation("SUR")
        assert "Ethiopia" in obs and "Surcharge" in obs

    def test_enrich_observation_tci(self):
        from etl.para_fiscal_levies import enrich_observation
        obs = enrich_observation("TCI")
        assert "CEMAC" in obs and "1%" in obs

    def test_enrich_observation_cac(self):
        from etl.para_fiscal_levies import enrich_observation
        obs = enrich_observation("CAC")
        assert "Cameroon" in obs or "Centimes" in obs

    def test_enrich_observation_prct(self):
        from etl.para_fiscal_levies import enrich_observation
        obs = enrich_observation("PRCT")
        assert "Algeria" in obs or "Transport" in obs

    def test_enrich_observation_tpi(self):
        from etl.para_fiscal_levies import enrich_observation
        obs = enrich_observation("TPI")
        assert "Morocco" in obs or "TPI" in obs

    def test_enrich_observation_idf(self):
        from etl.para_fiscal_levies import enrich_observation
        obs = enrich_observation("IDF")
        assert "Kenya" in obs and "3.5" in obs

    def test_enrich_observation_rdl(self):
        from etl.para_fiscal_levies import enrich_observation
        obs = enrich_observation("RDL")
        assert "Railway" in obs and "Kenya" in obs

    def test_enrich_observation_cedeao(self):
        from etl.para_fiscal_levies import enrich_observation
        obs = enrich_observation("CEDEAO")
        assert "ECOWAS" in obs or "CEDEAO" in obs

    def test_enrich_observation_rs(self):
        from etl.para_fiscal_levies import enrich_observation
        obs = enrich_observation("RS")
        assert "Statistical" in obs or "Statistique" in obs or "UEMOA" in obs

    def test_enrich_observation_pcs(self):
        from etl.para_fiscal_levies import enrich_observation
        obs = enrich_observation("PCS")
        assert "UEMOA" in obs or "Solidarity" in obs

    # ─────────────────────────────────────────────────────────────────────────
    # Data-level validation — enriched observations in country files
    # ─────────────────────────────────────────────────────────────────────────

    def test_eth_sur_observation_descriptive(self):
        """ETH SUR tax_detail has a descriptive observation (not empty)."""
        import json, os
        path = os.path.join(os.path.dirname(__file__), "..", "data", "crawled", "ETH_tariffs.json")
        if not os.path.exists(path):
            pytest.skip("ETH_tariffs.json not found")
        with open(path) as f:
            d = json.load(f)
        lines = d["tariff_lines"]
        sur_entry = next(
            (t for l in lines for t in l.get("taxes_detail", []) if t["tax"] == "SUR"),
            None,
        )
        assert sur_entry is not None, "No SUR tax found in ETH"
        obs = sur_entry["observation"]
        assert len(obs) > 20, f"SUR observation too short: '{obs}'"
        assert "Ethiopia" in obs or "Proclamation" in obs

    def test_cmr_tci_observation_descriptive(self):
        """CMR TCI tax_detail has a descriptive observation referencing CEMAC."""
        import json, os
        path = os.path.join(os.path.dirname(__file__), "..", "data", "crawled", "CMR_tariffs.json")
        if not os.path.exists(path):
            pytest.skip("CMR_tariffs.json not found")
        with open(path) as f:
            d = json.load(f)
        lines = d["tariff_lines"]
        tci_entry = next(
            (t for l in lines for t in l.get("taxes_detail", []) if t["tax"] == "TCI"),
            None,
        )
        assert tci_entry is not None, "No TCI tax found in CMR"
        obs = tci_entry["observation"]
        assert "CEMAC" in obs, f"Expected 'CEMAC' in TCI observation: '{obs}'"

    def test_mar_tpi_observation_descriptive(self):
        """MAR TPI tax_detail has a descriptive observation."""
        import json, os
        path = os.path.join(os.path.dirname(__file__), "..", "data", "crawled", "MAR_tariffs.json")
        if not os.path.exists(path):
            pytest.skip("MAR_tariffs.json not found")
        with open(path) as f:
            d = json.load(f)
        lines = d["tariff_lines"]
        tpi_entry = next(
            (t for l in lines for t in l.get("taxes_detail", []) if t["tax"] == "TPI"),
            None,
        )
        assert tpi_entry is not None, "No TPI tax found in MAR"
        obs = tpi_entry["observation"]
        assert len(obs) > 10, f"TPI observation too short: '{obs}'"

    def test_mar_other_taxes_rate_non_zero(self):
        """MAR other_taxes_rate reflects TPI levy."""
        import json, os
        path = os.path.join(os.path.dirname(__file__), "..", "data", "crawled", "MAR_tariffs.json")
        if not os.path.exists(path):
            pytest.skip("MAR_tariffs.json not found")
        with open(path) as f:
            d = json.load(f)
        lines = d["tariff_lines"]
        non_zero = [l for l in lines if l.get("other_taxes_rate", 0) > 0]
        assert len(non_zero) > 0, "MAR other_taxes_rate is always 0"

    def test_ken_other_taxes_rate_reflects_idf(self):
        """KEN other_taxes_rate is 3.5 (IDF) for all lines."""
        import json, os
        path = os.path.join(os.path.dirname(__file__), "..", "data", "crawled", "KEN_tariffs.json")
        if not os.path.exists(path):
            pytest.skip("KEN_tariffs.json not found")
        with open(path) as f:
            d = json.load(f)
        lines = d["tariff_lines"]
        wrong = [l["hs_code"] for l in lines if l.get("other_taxes_rate", 0) != 3.5]
        assert wrong == [], f"KEN lines with wrong other_taxes_rate: {wrong[:5]}"

    def test_eth_sur_rate_is_ten_percent(self):
        """ETH SUR rate is 10% (of customs duty)."""
        import json, os
        path = os.path.join(os.path.dirname(__file__), "..", "data", "crawled", "ETH_tariffs.json")
        if not os.path.exists(path):
            pytest.skip("ETH_tariffs.json not found")
        with open(path) as f:
            d = json.load(f)
        lines = d["tariff_lines"]
        sur_rates = {t["rate"] for l in lines for t in l.get("taxes_detail", []) if t["tax"] == "SUR"}
        assert sur_rates == {10.0}, f"Unexpected SUR rates: {sur_rates}"

    def test_gab_other_taxes_rate_non_zero(self):
        """GAB other_taxes_rate reflects TCI levy (non-zero)."""
        import json, os
        path = os.path.join(os.path.dirname(__file__), "..", "data", "crawled", "GAB_tariffs.json")
        if not os.path.exists(path):
            pytest.skip("GAB_tariffs.json not found")
        with open(path) as f:
            d = json.load(f)
        lines = d["tariff_lines"]
        zero = [l for l in lines if l.get("other_taxes_rate", 0) == 0]
        assert len(zero) == 0, f"GAB has {len(zero)} lines with other_taxes_rate=0"

    # ─────────────────────────────────────────────────────────────────────────
    # LEVY_DESCRIPTIONS — extended coverage checks
    # ─────────────────────────────────────────────────────────────────────────

    def test_levy_descriptions_cemac_codes(self):
        """LEVY_DESCRIPTIONS includes CEMAC-specific codes."""
        from etl.para_fiscal_levies import LEVY_DESCRIPTIONS
        for code in ["TCI", "RI", "CAC"]:
            assert code in LEVY_DESCRIPTIONS, f"Missing CEMAC code: {code}"

    def test_levy_descriptions_ecowas_codes(self):
        """LEVY_DESCRIPTIONS includes ECOWAS/UEMOA community levy codes."""
        from etl.para_fiscal_levies import LEVY_DESCRIPTIONS
        for code in ["CEDEAO", "PCC", "RS", "PCS", "PUA", "ETLS"]:
            assert code in LEVY_DESCRIPTIONS, f"Missing ECOWAS code: {code}"

    def test_levy_descriptions_country_specific_codes(self):
        """LEVY_DESCRIPTIONS covers major country-specific levies."""
        from etl.para_fiscal_levies import LEVY_DESCRIPTIONS
        for code in ["CISS", "GETFUND", "NHIL", "IDF", "RDL", "SUR", "PRCT", "TPI", "IE", "TRA"]:
            assert code in LEVY_DESCRIPTIONS, f"Missing country code: {code}"

    def test_levy_descriptions_entries_have_both_languages(self):
        """Every entry in LEVY_DESCRIPTIONS is a 2-tuple (fr, en)."""
        from etl.para_fiscal_levies import LEVY_DESCRIPTIONS
        for code, val in LEVY_DESCRIPTIONS.items():
            assert isinstance(val, tuple) and len(val) == 2, \
                f"{code}: expected (fr, en) tuple, got {type(val)}"
            assert val[0] and val[1], f"{code}: empty language string"

    def test_ectn_countries_constant(self):
        """ECTN_COUNTRIES set contains all 6 CEMAC members."""
        from etl.para_fiscal_levies import ECTN_COUNTRIES
        expected = {"CMR", "CAF", "COG", "GAB", "GNQ", "TCD"}
        assert ECTN_COUNTRIES == expected


# =============================================================================
# NO MOCKED DATA — Verify every country uses real functional document codes
# =============================================================================

class TestNoMockedData:
    """
    Ensure that no placeholder/mocked formality codes remain in production
    data files or generated data.

    Background:
    - Code "910" is the REAL DGD/ADII/GUCE import declaration code for
      DZA, MAR and TUN (North-Africa national code schemes).  It is legitimate
      only for those three countries.
    - IMPDEC/VETCERT/PHYTOCERT/… are UNCTAD NTM-aligned functional document-type
      codes, NOT ASYCUDA codes.  They are platform-agnostic and apply to all
      countries regardless of which customs software they use (ASYCUDA World,
      GCNET, iCMS, SIMBA, BADR, NICIS, NAFEZA, ECTS, TradeNet, etc.).
    - "910" must NEVER be used as a generic fallback for non-North-Africa countries.
    """

    # Countries where code "910" is a genuine customs code
    _NORTH_AFRICA_910 = {"DZA", "MAR", "TUN"}

    def _crawled_codes(self, cc: str) -> set:
        import json, os
        path = os.path.join(
            os.path.dirname(__file__), "..", "data", "crawled", f"{cc}_tariffs.json"
        )
        if not os.path.exists(path):
            pytest.skip(f"{cc}_tariffs.json not found")
        with open(path) as f:
            d = json.load(f)
        return {
            fm["code"]
            for line in d.get("tariff_lines", [])
            for fm in line.get("administrative_formalities", [])
        }

    def _tariffs_codes(self, cc: str) -> set:
        import json, os
        path = os.path.join(
            os.path.dirname(__file__), "..", "data", "tariffs", f"{cc}_tariffs.json"
        )
        if not os.path.exists(path):
            pytest.skip(f"data/tariffs/{cc}_tariffs.json not found")
        with open(path) as f:
            d = json.load(f)
        return {
            fm["code"]
            for line in d.get("tariff_lines", [])
            for fm in line.get("administrative_formalities", [])
        }

    # ── Crawled data: non-North-Africa countries must not use "910" ──────

    def test_eth_crawled_no_mocked_910(self):
        """ETH crawled data must not use code 910 (placeholder for North Africa only)."""
        codes = self._crawled_codes("ETH")
        assert "910" not in codes, f"ETH has mocked code 910: {codes}"
        assert "IMPDEC" in codes, f"ETH missing real IMPDEC code"

    def test_sdn_crawled_no_mocked_910(self):
        """SDN crawled data must not use code 910."""
        codes = self._crawled_codes("SDN")
        assert "910" not in codes, f"SDN has mocked code 910: {codes}"
        assert "IMPDEC" in codes, f"SDN missing real IMPDEC code"

    def test_som_crawled_no_mocked_910(self):
        """SOM crawled data must not use code 910."""
        codes = self._crawled_codes("SOM")
        assert "910" not in codes, f"SOM has mocked code 910: {codes}"
        assert "IMPDEC" in codes, f"SOM missing real IMPDEC code"

    def test_stp_crawled_no_mocked_910(self):
        """STP crawled data must not use code 910."""
        codes = self._crawled_codes("STP")
        assert "910" not in codes, f"STP has mocked code 910: {codes}"
        assert "IMPDEC" in codes, f"STP missing real IMPDEC code"

    def test_nga_crawled_no_mocked_910(self):
        """NGA crawled data must not use code 910."""
        codes = self._crawled_codes("NGA")
        assert "910" not in codes, f"NGA has mocked code 910"
        assert "IMPDEC" in codes

    def test_ken_crawled_no_mocked_910(self):
        """KEN crawled data must not use code 910."""
        codes = self._crawled_codes("KEN")
        assert "910" not in codes, f"KEN has mocked code 910"
        assert "IMPDEC" in codes

    def test_zaf_crawled_no_mocked_910(self):
        """ZAF crawled data must not use code 910."""
        codes = self._crawled_codes("ZAF")
        assert "910" not in codes, f"ZAF has mocked code 910"
        assert "IMPDEC" in codes

    # ── Crawled data: all 54 countries must have multi-type formalities ───

    def test_all_crawled_countries_have_impdec(self):
        """Every country in data/crawled/ must include IMPDEC functional code,
        except North-African countries that use their own national code schemes
        (DZA/MAR/TUN use their own codes: 910/210/C01-C11/101-109).
        Note: IMPDEC is a UNCTAD NTM functional code — platform-agnostic, NOT
        specific to ASYCUDA. It applies regardless of which customs software
        the country uses (GCNET, iCMS, SIMBA, NAFEZA, NICIS, etc.)."""
        import json, os
        # North-African countries use national code schemes instead of IMPDEC
        _NATIONAL_SCHEME = {"DZA", "MAR", "TUN"}
        crawled_dir = os.path.join(os.path.dirname(__file__), "..", "data", "crawled")
        missing = []
        for fname in sorted(os.listdir(crawled_dir)):
            if not fname.endswith("_tariffs.json"):
                continue
            cc = fname.replace("_tariffs.json", "")
            if cc in _NATIONAL_SCHEME:
                continue  # These use their own national code schemes — skip
            with open(os.path.join(crawled_dir, fname)) as f:
                d = json.load(f)
            codes = {
                fm["code"]
                for line in d.get("tariff_lines", [])
                for fm in line.get("administrative_formalities", [])
            }
            if "IMPDEC" not in codes:
                missing.append(f"{cc}: {sorted(codes)}")
        assert missing == [], (
            f"Countries missing IMPDEC in crawled data:\n" + "\n".join(missing)
        )

    def test_non_north_africa_crawled_no_910(self):
        """Non-North-Africa countries in data/crawled/ must NOT have code 910."""
        import json, os
        crawled_dir = os.path.join(os.path.dirname(__file__), "..", "data", "crawled")
        offenders = []
        for fname in sorted(os.listdir(crawled_dir)):
            if not fname.endswith("_tariffs.json"):
                continue
            cc = fname.replace("_tariffs.json", "")
            if cc in self._NORTH_AFRICA_910:
                continue
            with open(os.path.join(crawled_dir, fname)) as f:
                d = json.load(f)
            codes = {
                fm["code"]
                for line in d.get("tariff_lines", [])
                for fm in line.get("administrative_formalities", [])
            }
            if "910" in codes:
                offenders.append(f"{cc}: {sorted(codes)}")
        assert offenders == [], (
            f"Non-North-Africa countries with mocked code 910:\n" + "\n".join(offenders)
        )

    # ── data/tariffs/ stale files: must now use real codes ───────────────

    def test_eth_tariffs_dir_uses_real_codes(self):
        """data/tariffs/ETH must use real functional codes (not just 910)."""
        codes = self._tariffs_codes("ETH")
        assert "910" not in codes, f"ETH (data/tariffs) still has mocked 910"
        assert "IMPDEC" in codes

    def test_sdn_tariffs_dir_uses_real_codes(self):
        """data/tariffs/SDN must use real functional codes."""
        codes = self._tariffs_codes("SDN")
        assert "910" not in codes, f"SDN (data/tariffs) still has mocked 910"
        assert "IMPDEC" in codes

    def test_som_tariffs_dir_uses_real_codes(self):
        """data/tariffs/SOM must use real functional codes."""
        codes = self._tariffs_codes("SOM")
        assert "910" not in codes, f"SOM (data/tariffs) still has mocked 910"
        assert "IMPDEC" in codes

    def test_stp_tariffs_dir_uses_real_codes(self):
        """data/tariffs/STP must use real functional codes."""
        codes = self._tariffs_codes("STP")
        assert "910" not in codes, f"STP (data/tariffs) still has mocked 910"
        assert "IMPDEC" in codes

    # ── Collector fallback must use IMPDEC, not 910 ──────────────────────

    def test_tariff_collector_fallback_uses_impdec(self):
        """TariffDataCollector fallback formality must use IMPDEC, not code 910."""
        from services.tariff_data_collector import TariffDataCollector
        collector = TariffDataCollector()
        # Use a country not in special-case modules (e.g. GHA which has ECOWAS levies
        # but no dedicated _get_country_taxes module)
        data = collector.collect_country_tariffs("COM")
        # Collect all formality codes from the generated data
        codes = {
            fm["code"]
            for line in data.get("tariff_lines", [])
            for fm in line.get("administrative_formalities", [])
        }
        assert "910" not in codes, (
            f"TariffDataCollector fallback still produces code 910: {sorted(codes)}"
        )

    def test_upgrade_script_default_admin_uses_impdec(self):
        """upgrade_to_enhanced_v2._DEFAULT_ADMIN must use IMPDEC, not code 910."""
        import sys
        import os
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
        from scripts.upgrade_to_enhanced_v2 import _DEFAULT_ADMIN
        codes = {item["code"] for item in _DEFAULT_ADMIN}
        assert "910" not in codes, f"_DEFAULT_ADMIN still has code 910: {_DEFAULT_ADMIN}"
        assert "IMPDEC" in codes, f"_DEFAULT_ADMIN missing IMPDEC: {_DEFAULT_ADMIN}"

    # ── North-Africa codes are STILL real and correct ────────────────────

    def test_dza_910_is_legitimate(self):
        """DZA must still have code 910 (it is the real DGD DUM code)."""
        codes = self._crawled_codes("DZA")
        assert "910" in codes, "DZA lost its real code 910 (DUM)"

    def test_mar_910_is_legitimate(self):
        """MAR must still have code 910 (ADII official code)."""
        codes = self._crawled_codes("MAR")
        assert "910" in codes, "MAR lost its real code 910"

    def test_tun_910_is_legitimate(self):
        """TUN must still have code 910 (GUCE official code)."""
        codes = self._crawled_codes("TUN")
        assert "910" in codes, "TUN lost its real code 910"


# =============================================================================
# CUSTOMS PLATFORM REGISTRY — Verify every country has a real platform entry
# =============================================================================

class TestCustomsPlatform:
    """
    Verify that the CustomsPlatform registry in all_countries_registry.py
    accurately reflects the customs management software used by each of the
    54 African countries.

    Key facts:
    - IMPDEC/VETCERT/… formality codes are UNCTAD NTM functional codes, NOT
      ASYCUDA codes.  They apply regardless of which customs platform is used.
    - Not all African customs administrations use ASYCUDA.  Known non-ASYCUDA:
        GHA → GCNET           NGA → NICIS/CuCMS
        KEN → iCMS            TZA → SIMBA
        ZAF → SARS EDI        EGY → NAFEZA
        MAR → BADR            TUN → SINDA (ASYCUDA-derived, national codes)
        ETH → ECTS            MUS → TradeNet
        SEN → GAINDE          COD → SYDONIA/ASYCUDA (heavily customised)
    """

    def _load_registry(self):
        """Load AFRICAN_COUNTRIES_REGISTRY via direct file import."""
        import importlib.util, os, sys
        reg_path = os.path.join(
            os.path.dirname(__file__), "..", "crawlers", "all_countries_registry.py"
        )
        spec = importlib.util.spec_from_file_location("all_countries_registry", reg_path)
        mod = importlib.util.module_from_spec(spec)
        # Stub out httpx-dependent sub-imports
        sys.modules.setdefault("httpx", type(sys)("httpx"))
        try:
            spec.loader.exec_module(mod)
        except Exception:
            # If crawler imports fail, load just what we need via exec
            with open(reg_path) as f:
                src = f.read()
            ns = {}
            # Strip the import of crawlers submodules that need httpx
            safe_src = "\n".join(
                line for line in src.splitlines()
                if not line.strip().startswith("from .") and not line.strip().startswith("from crawlers.")
            )
            exec(compile(safe_src, reg_path, "exec"), ns)
            return ns["AFRICAN_COUNTRIES_REGISTRY"], ns["CustomsPlatform"], ns["CUSTOMS_PLATFORM_INFO"]
        return mod.AFRICAN_COUNTRIES_REGISTRY, mod.CustomsPlatform, mod.CUSTOMS_PLATFORM_INFO

    def test_all_54_countries_have_customs_platform(self):
        """All 54 countries must have a customs_platform field."""
        registry, _, _ = self._load_registry()
        missing = [cc for cc, data in registry.items() if "customs_platform" not in data]
        assert missing == [], f"Countries missing customs_platform: {missing}"
        assert len(registry) == 54, f"Expected 54 countries, got {len(registry)}"

    def test_customs_platform_values_are_valid_enum_members(self):
        """customs_platform values must be valid CustomsPlatform enum members."""
        registry, CustomsPlatform, _ = self._load_registry()
        valid_values = {p.value for p in CustomsPlatform}
        invalid = []
        for cc, data in registry.items():
            p = data.get("customs_platform")
            if p is not None and p.value not in valid_values:
                invalid.append(f"{cc}: {p!r}")
        assert invalid == [], f"Invalid platform values: {invalid}"

    def test_non_asycuda_countries_identified(self):
        """Key non-ASYCUDA countries must NOT be mapped to ASYCUDA_WORLD."""
        registry, CustomsPlatform, _ = self._load_registry()
        # These countries are definitively NOT standard ASYCUDA World
        non_asycuda = {
            "GHA": "GCNET",
            "NGA": "NICIS",
            "KEN": "ICMS",
            "TZA": "SIMBA",
            "ZAF": "SARS_EDI",
            "EGY": "NAFEZA",
            "MAR": "BADR",
            "TUN": "SINDA",
            "ETH": "ECTS",
            "MUS": "TRADENET",
        }
        for cc, expected_attr in non_asycuda.items():
            data = registry.get(cc, {})
            platform = data.get("customs_platform")
            assert platform is not None, f"{cc}: missing customs_platform"
            expected = getattr(CustomsPlatform, expected_attr)
            assert platform == expected, (
                f"{cc}: expected platform {expected.value!r}, got {platform.value!r}"
            )

    # Minimum number of African countries expected to use ASYCUDA World
    _MIN_ASYCUDA_WORLD_COUNTRIES = 30

    def test_asycuda_world_is_most_common_platform(self):
        """ASYCUDA World should be the majority platform (≥30 countries)."""
        registry, CustomsPlatform, _ = self._load_registry()
        asycuda_count = sum(
            1 for data in registry.values()
            if data.get("customs_platform") == CustomsPlatform.ASYCUDA_WORLD
        )
        assert asycuda_count >= self._MIN_ASYCUDA_WORLD_COUNTRIES, (
            f"Expected ≥{self._MIN_ASYCUDA_WORLD_COUNTRIES} ASYCUDA World countries, got {asycuda_count}"
        )

    def test_dza_uses_asycuda_world(self):
        """DZA must use ASYCUDA World (national code scheme uses numeric codes like 910)."""
        registry, CustomsPlatform, _ = self._load_registry()
        platform = registry["DZA"]["customs_platform"]
        assert platform == CustomsPlatform.ASYCUDA_WORLD

    def test_mar_uses_badr(self):
        """MAR must use BADR (Morocco's fully national system, not ASYCUDA)."""
        registry, CustomsPlatform, _ = self._load_registry()
        platform = registry["MAR"]["customs_platform"]
        assert platform == CustomsPlatform.BADR

    def test_ken_uses_icms(self):
        """KEN must use iCMS (KRA's national system, replaced SIMBA in 2022)."""
        registry, CustomsPlatform, _ = self._load_registry()
        platform = registry["KEN"]["customs_platform"]
        assert platform == CustomsPlatform.ICMS

    def test_tza_uses_simba(self):
        """TZA must use SIMBA (TRA system, not ASYCUDA)."""
        registry, CustomsPlatform, _ = self._load_registry()
        platform = registry["TZA"]["customs_platform"]
        assert platform == CustomsPlatform.SIMBA

    def test_gha_uses_gcnet(self):
        """GHA must use GCNET (Ghana Revenue Authority, not ASYCUDA)."""
        registry, CustomsPlatform, _ = self._load_registry()
        platform = registry["GHA"]["customs_platform"]
        assert platform == CustomsPlatform.GCNET

    def test_cod_uses_sydonia(self):
        """COD must use SYDONIA/ASYCUDA (DRC's ASYCUDA-derived system)."""
        registry, CustomsPlatform, _ = self._load_registry()
        platform = registry["COD"]["customs_platform"]
        assert platform == CustomsPlatform.SYDONIA

    def test_customs_platform_info_covers_all_enum_members(self):
        """CUSTOMS_PLATFORM_INFO dict must have an entry for every CustomsPlatform value."""
        _, CustomsPlatform, CUSTOMS_PLATFORM_INFO = self._load_registry()
        missing = []
        for p in CustomsPlatform:
            if p.value not in CUSTOMS_PLATFORM_INFO:
                missing.append(p.value)
        assert missing == [], f"CustomsPlatform values not in CUSTOMS_PLATFORM_INFO: {missing}"

    def test_customs_platform_info_has_required_keys(self):
        """Every entry in CUSTOMS_PLATFORM_INFO must have vendor and notes."""
        _, _, CUSTOMS_PLATFORM_INFO = self._load_registry()
        for platform, info in CUSTOMS_PLATFORM_INFO.items():
            assert "vendor" in info, f"{platform}: missing 'vendor'"
            assert "notes" in info, f"{platform}: missing 'notes'"
            assert "url" in info, f"{platform}: missing 'url'"
            assert info["vendor"], f"{platform}: empty vendor"

    def test_formality_codes_are_platform_agnostic(self):
        """IMPDEC formality code must appear for non-ASYCUDA countries (GHA, NGA, KEN, TZA, ZAF).

        This confirms IMPDEC is a functional code, not an ASYCUDA-specific code.
        If IMPDEC were ASYCUDA-only, these countries' crawled data would be wrong.
        """
        import json, os
        non_asycuda_with_impdec = ["GHA", "NGA", "KEN", "TZA", "ZAF"]
        crawled_dir = os.path.join(os.path.dirname(__file__), "..", "data", "crawled")
        for cc in non_asycuda_with_impdec:
            path = os.path.join(crawled_dir, f"{cc}_tariffs.json")
            if not os.path.exists(path):
                continue
            with open(path) as f:
                d = json.load(f)
            codes = {
                fm["code"]
                for line in d.get("tariff_lines", [])
                for fm in line.get("administrative_formalities", [])
            }
            assert "IMPDEC" in codes, (
                f"{cc} (non-ASYCUDA platform) is missing IMPDEC — "
                f"this should NOT happen since IMPDEC is platform-agnostic. "
                f"Got codes: {sorted(codes)}"
            )


# =============================================================================
# CUSTOMS PLATFORM UTILITY FUNCTIONS
# =============================================================================

class TestCustomsPlatformUtilityFunctions:
    """
    Verify the new utility functions added to all_countries_registry.py:
      - get_country_platform()
      - get_country_declaration_form()
      - get_countries_by_platform()
    And that validate_registry() now requires customs_platform.
    """

    def _load_registry_module(self):
        """Load the registry module via exec to bypass httpx dependency."""
        import importlib.util, os, sys
        reg_path = os.path.join(
            os.path.dirname(__file__), "..", "crawlers", "all_countries_registry.py"
        )
        sys.modules.setdefault("httpx", type(sys)("httpx"))
        ns = {}
        with open(reg_path) as f:
            src = f.read()
        safe_src = "\n".join(
            line for line in src.splitlines()
            if not line.strip().startswith("from .") and not line.strip().startswith("from crawlers.")
        )
        exec(compile(safe_src, reg_path, "exec"), ns)
        return ns

    # ── get_country_platform ─────────────────────────────────────────────────

    def test_get_country_platform_gcnet(self):
        """GHA → GCNET."""
        ns = self._load_registry_module()
        p = ns["get_country_platform"]("GHA")
        assert p == ns["CustomsPlatform"].GCNET

    def test_get_country_platform_icms(self):
        """KEN → iCMS."""
        ns = self._load_registry_module()
        assert ns["get_country_platform"]("KEN") == ns["CustomsPlatform"].ICMS

    def test_get_country_platform_simba(self):
        """TZA → SIMBA."""
        ns = self._load_registry_module()
        assert ns["get_country_platform"]("TZA") == ns["CustomsPlatform"].SIMBA

    def test_get_country_platform_sars_edi(self):
        """ZAF → SARS EDI."""
        ns = self._load_registry_module()
        assert ns["get_country_platform"]("ZAF") == ns["CustomsPlatform"].SARS_EDI

    def test_get_country_platform_nicis(self):
        """NGA → NICIS/CuCMS."""
        ns = self._load_registry_module()
        assert ns["get_country_platform"]("NGA") == ns["CustomsPlatform"].NICIS

    def test_get_country_platform_nafeza(self):
        """EGY → NAFEZA."""
        ns = self._load_registry_module()
        assert ns["get_country_platform"]("EGY") == ns["CustomsPlatform"].NAFEZA

    def test_get_country_platform_asycuda_world(self):
        """DZA → ASYCUDA World."""
        ns = self._load_registry_module()
        assert ns["get_country_platform"]("DZA") == ns["CustomsPlatform"].ASYCUDA_WORLD

    def test_get_country_platform_case_insensitive(self):
        """Country code lookup should be case-insensitive."""
        ns = self._load_registry_module()
        assert ns["get_country_platform"]("gha") == ns["CustomsPlatform"].GCNET

    def test_get_country_platform_unknown_country(self):
        """Unknown country code should return None."""
        ns = self._load_registry_module()
        assert ns["get_country_platform"]("XYZ") is None

    # ── get_country_declaration_form ─────────────────────────────────────────

    def test_declaration_form_kenya_en(self):
        """Kenya uses 'Import Declaration Form (IDF)' not generic 'Import Declaration'."""
        ns = self._load_registry_module()
        form = ns["get_country_declaration_form"]("KEN", lang="en")
        assert "IDF" in form, f"KEN EN form: {form}"

    def test_declaration_form_ghana_en(self):
        """Ghana uses 'CUSDEC' not generic 'Import Declaration'."""
        ns = self._load_registry_module()
        form = ns["get_country_declaration_form"]("GHA", lang="en")
        assert "CUSDEC" in form, f"GHA EN form: {form}"

    def test_declaration_form_nigeria_en(self):
        """Nigeria uses 'Single Goods Declaration (SGD)'."""
        ns = self._load_registry_module()
        form = ns["get_country_declaration_form"]("NGA", lang="en")
        assert "SGD" in form, f"NGA EN form: {form}"

    def test_declaration_form_south_africa_en(self):
        """South Africa uses 'Bill of Entry (DA 306)'."""
        ns = self._load_registry_module()
        form = ns["get_country_declaration_form"]("ZAF", lang="en")
        assert "DA 306" in form, f"ZAF EN form: {form}"

    def test_declaration_form_egypt_en(self):
        """Egypt uses 'Electronic Import Notice (EIN)'."""
        ns = self._load_registry_module()
        form = ns["get_country_declaration_form"]("EGY", lang="en")
        assert "EIN" in form, f"EGY EN form: {form}"

    def test_declaration_form_french(self):
        """French form name should differ from English for non-generic platforms."""
        ns = self._load_registry_module()
        en = ns["get_country_declaration_form"]("KEN", lang="en")
        fr = ns["get_country_declaration_form"]("KEN", lang="fr")
        assert en != fr, "French and English form names should differ"
        assert "IDF" in fr, f"KEN FR form: {fr}"

    def test_declaration_form_asycuda_is_sad(self):
        """ASYCUDA World countries use SAD (Single Administrative Document)."""
        ns = self._load_registry_module()
        form = ns["get_country_declaration_form"]("BWA", lang="en")
        assert "SAD" in form, f"BWA EN form (ASYCUDA): {form}"

    def test_declaration_form_unknown_country_fallback(self):
        """Unknown country falls back to generic 'Import Declaration'."""
        ns = self._load_registry_module()
        form = ns["get_country_declaration_form"]("XYZ", lang="en")
        assert form == "Import Declaration"

    # ── get_countries_by_platform ─────────────────────────────────────────────

    def test_get_countries_by_platform_gcnet(self):
        """Only GHA uses GCNET."""
        ns = self._load_registry_module()
        countries = ns["get_countries_by_platform"](ns["CustomsPlatform"].GCNET)
        assert countries == ["GHA"]

    def test_get_countries_by_platform_simba(self):
        """Only TZA uses SIMBA."""
        ns = self._load_registry_module()
        countries = ns["get_countries_by_platform"](ns["CustomsPlatform"].SIMBA)
        assert countries == ["TZA"]

    def test_get_countries_by_platform_sars_edi(self):
        """Only ZAF uses SARS EDI."""
        ns = self._load_registry_module()
        countries = ns["get_countries_by_platform"](ns["CustomsPlatform"].SARS_EDI)
        assert countries == ["ZAF"]

    def test_get_countries_by_platform_asycuda_world_count(self):
        """42 countries should use ASYCUDA World."""
        ns = self._load_registry_module()
        countries = ns["get_countries_by_platform"](ns["CustomsPlatform"].ASYCUDA_WORLD)
        assert len(countries) >= 30, f"Expected ≥30 ASYCUDA World countries, got {len(countries)}"
        assert "GHA" not in countries
        assert "NGA" not in countries
        assert "KEN" not in countries
        assert "TZA" not in countries
        assert "ZAF" not in countries

    def test_get_countries_by_platform_results_are_sorted(self):
        """Results from get_countries_by_platform must be sorted."""
        ns = self._load_registry_module()
        countries = ns["get_countries_by_platform"](ns["CustomsPlatform"].ASYCUDA_WORLD)
        assert countries == sorted(countries)

    # ── validate_registry includes customs_platform ─────────────────────────

    def test_validate_registry_includes_customs_platform(self):
        """validate_registry() must flag countries missing customs_platform."""
        ns = self._load_registry_module()
        # Tamper with one entry by temporarily removing customs_platform
        reg = ns["AFRICAN_COUNTRIES_REGISTRY"]
        original = reg["AGO"].pop("customs_platform")
        try:
            report = ns["validate_registry"]()
            assert any("customs_platform" in item for item in report["missing_data"]), (
                "validate_registry() should flag missing customs_platform"
            )
        finally:
            reg["AGO"]["customs_platform"] = original

    def test_validate_registry_passes_with_all_platforms(self):
        """validate_registry() should report no missing_data for the full registry."""
        ns = self._load_registry_module()
        report = ns["validate_registry"]()
        assert report["missing_data"] == [], (
            f"Registry has missing data: {report['missing_data']}"
        )

    # ── Platform-specific names propagate through get_formalities_for_line ───

    def test_formality_impdec_uses_platform_name_kenya(self):
        """get_formalities_for_line('KEN', ...) IMPDEC document_en must be IDF, not generic."""
        import sys
        import os
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
        try:
            from etl.africa_formalities import get_formalities_for_line
        except ImportError:
            import pytest
            pytest.skip("africa_formalities import failed")
        forms = get_formalities_for_line("KEN", "general", "87")
        impdec = next((f for f in forms if f["code"] == "IMPDEC"), None)
        assert impdec is not None, "KEN: no IMPDEC formality found"
        assert "IDF" in impdec["document_en"], (
            f"KEN IMPDEC document_en should contain 'IDF', got: {impdec['document_en']}"
        )

    def test_formality_impdec_uses_platform_name_ghana(self):
        """get_formalities_for_line('GHA', ...) IMPDEC document_en must be CUSDEC."""
        import sys
        import os
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
        try:
            from etl.africa_formalities import get_formalities_for_line
        except ImportError:
            import pytest
            pytest.skip("africa_formalities import failed")
        forms = get_formalities_for_line("GHA", "general", "87")
        impdec = next((f for f in forms if f["code"] == "IMPDEC"), None)
        assert impdec is not None, "GHA: no IMPDEC formality found"
        assert "CUSDEC" in impdec["document_en"], (
            f"GHA IMPDEC document_en should contain 'CUSDEC', got: {impdec['document_en']}"
        )

    def test_formality_impdec_uses_platform_name_south_africa(self):
        """get_formalities_for_line('ZAF', ...) IMPDEC must show Bill of Entry DA 306."""
        import sys
        import os
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
        try:
            from etl.africa_formalities import get_formalities_for_line
        except ImportError:
            import pytest
            pytest.skip("africa_formalities import failed")
        forms = get_formalities_for_line("ZAF", "general", "87")
        impdec = next((f for f in forms if f["code"] == "IMPDEC"), None)
        assert impdec is not None, "ZAF: no IMPDEC formality found"
        assert "DA 306" in impdec["document_en"], (
            f"ZAF IMPDEC document_en should contain 'DA 306', got: {impdec['document_en']}"
        )

    def test_formality_impdec_uses_platform_name_nigeria(self):
        """get_formalities_for_line('NGA', ...) IMPDEC must show SGD."""
        import sys
        import os
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
        try:
            from etl.africa_formalities import get_formalities_for_line
        except ImportError:
            import pytest
            pytest.skip("africa_formalities import failed")
        forms = get_formalities_for_line("NGA", "general", "87")
        impdec = next((f for f in forms if f["code"] == "IMPDEC"), None)
        assert impdec is not None, "NGA: no IMPDEC formality found"
        assert "SGD" in impdec["document_en"], (
            f"NGA IMPDEC document_en should contain 'SGD', got: {impdec['document_en']}"
        )

    def test_formality_impdec_asycuda_uses_sad(self):
        """ASYCUDA World countries should show SAD in IMPDEC document_en."""
        import sys
        import os
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
        try:
            from etl.africa_formalities import get_formalities_for_line
        except ImportError:
            import pytest
            pytest.skip("africa_formalities import failed")
        forms = get_formalities_for_line("BWA", "general", "87")
        impdec = next((f for f in forms if f["code"] == "IMPDEC"), None)
        assert impdec is not None, "BWA: no IMPDEC formality found"
        assert "SAD" in impdec["document_en"], (
            f"BWA (ASYCUDA World) IMPDEC document_en should contain 'SAD', got: {impdec['document_en']}"
        )
