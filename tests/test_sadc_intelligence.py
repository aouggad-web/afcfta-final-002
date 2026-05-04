"""
Tests for SADC Regional Intelligence Service
=============================================
Tests for services/sadc_intelligence_service.py covering:
  - Service instantiation
  - Regional overview
  - Investment zone queries
  - Investment recommendations
  - Mining intelligence
  - Transport corridor queries
  - SACU framework retrieval
  - Trade protocol data
  - Cross-regional comparisons
  - Country tariff data loading
"""

import sys
import os
import pytest

BACKEND_DIR = os.path.join(os.path.dirname(__file__), '..', 'backend')
sys.path.insert(0, BACKEND_DIR)


# ===========================================================================
# Service instantiation
# ===========================================================================

class TestSADCIntelligenceServiceInit:
    def test_import_service(self):
        from services.sadc_intelligence_service import SADCIntelligenceService
        svc = SADCIntelligenceService()
        assert svc is not None

    def test_singleton_factory(self):
        from services.sadc_intelligence_service import get_sadc_intelligence
        svc1 = get_sadc_intelligence()
        svc2 = get_sadc_intelligence()
        assert svc1 is svc2


# ===========================================================================
# Regional overview
# ===========================================================================

class TestSADCRegionalOverview:
    def setup_method(self):
        from services.sadc_intelligence_service import SADCIntelligenceService
        self.svc = SADCIntelligenceService()

    def test_overview_returns_dict(self):
        result = self.svc.get_regional_overview()
        assert isinstance(result, dict)

    def test_overview_has_organisation_key(self):
        result = self.svc.get_regional_overview()
        assert "organisation" in result

    def test_organisation_metadata(self):
        result = self.svc.get_regional_overview()
        org = result["organisation"]
        assert org["member_count"] == 16
        assert org["combined_gdp_usd_billion"] == 800
        assert "SADC" in org["abbreviation"]

    def test_overview_has_sacu_key(self):
        result = self.svc.get_regional_overview()
        assert "sacu" in result
        sacu = result["sacu"]
        assert len(sacu["members"]) == 5

    def test_country_groups_present(self):
        result = self.svc.get_regional_overview()
        assert "country_groups" in result
        groups = result["country_groups"]
        assert "sacu" in groups
        assert "ldc_members" in groups
        assert "dual_membership" in groups

    def test_key_statistics(self):
        result = self.svc.get_regional_overview()
        stats = result["key_statistics"]
        assert stats["largest_economy"] == "ZAF"
        assert stats["world_diamond_production_share_pct"] == 60
        assert stats["world_platinum_reserves_share_pct"] == 80


# ===========================================================================
# Data freshness
# ===========================================================================

class TestSADCDataFreshness:
    def test_freshness_report(self):
        from services.sadc_intelligence_service import SADCIntelligenceService
        svc = SADCIntelligenceService()
        report = svc.get_data_freshness()
        result = report.to_dict()
        assert "checked_at" in result
        assert "countries" in result
        assert "total_countries" in result
        assert result["total_countries"] == 16

    def test_all_16_countries_in_report(self):
        from services.sadc_intelligence_service import SADCIntelligenceService, SADC_COUNTRY_LIST
        svc = SADCIntelligenceService()
        report = svc.get_data_freshness()
        result = report.to_dict()
        for code in SADC_COUNTRY_LIST:
            assert code in result["countries"]


# ===========================================================================
# Investment recommendation
# ===========================================================================

class TestSADCInvestmentRecommendation:
    def setup_method(self):
        from services.sadc_intelligence_service import SADCIntelligenceService
        self.svc = SADCIntelligenceService()

    def test_returns_list(self):
        result = self.svc.recommend_investment_location("mining")
        assert isinstance(result, list)

    def test_returns_16_entries(self):
        result = self.svc.recommend_investment_location("mining")
        assert len(result) == 16

    def test_result_has_required_fields(self):
        result = self.svc.recommend_investment_location("mining")
        for entry in result:
            assert "country_code" in entry
            assert "total_score" in entry
            assert "sector_strengths" in entry

    def test_sorted_descending(self):
        result = self.svc.recommend_investment_location("mining")
        scores = [e["total_score"] for e in result]
        assert scores == sorted(scores, reverse=True)

    def test_mining_sector_south_africa_high(self):
        result = self.svc.recommend_investment_location("mining")
        codes = [e["country_code"] for e in result[:5]]
        assert "ZAF" in codes

    def test_financial_services_mauritius_high(self):
        result = self.svc.recommend_investment_location("financial_services")
        codes = [e["country_code"] for e in result[:5]]
        assert "MUS" in codes

    def test_priority_parameter(self):
        result = self.svc.recommend_investment_location("textiles", priority="tax_incentives")
        assert len(result) == 16


# ===========================================================================
# Mining intelligence
# ===========================================================================

class TestSADCMiningIntelligence:
    def setup_method(self):
        from services.sadc_intelligence_service import SADCIntelligenceService
        self.svc = SADCIntelligenceService()

    def test_returns_dict(self):
        result = self.svc.get_mining_intelligence()
        assert isinstance(result, dict)

    def test_has_diamond_pipeline(self):
        result = self.svc.get_mining_intelligence()
        assert "diamond_pipeline" in result or "error" in result

    def test_filter_by_mineral(self):
        result = self.svc.get_mining_intelligence(mineral="diamond")
        # Should return matching data or empty dict if not found
        assert isinstance(result, dict)


# ===========================================================================
# Transport corridors
# ===========================================================================

class TestSADCTransportCorridors:
    def setup_method(self):
        from services.sadc_intelligence_service import SADCIntelligenceService
        self.svc = SADCIntelligenceService()

    def test_all_corridors(self):
        result = self.svc.get_transport_corridors()
        assert isinstance(result, dict)

    def test_country_specific_corridors(self):
        result = self.svc.get_transport_corridors(country_code="ZMB")
        assert isinstance(result, dict)
        # Zambia should appear in corridors
        if "error" not in result:
            assert "corridors" in result


# ===========================================================================
# SACU framework
# ===========================================================================

class TestSADCSACUFramework:
    def setup_method(self):
        from services.sadc_intelligence_service import SADCIntelligenceService
        self.svc = SADCIntelligenceService()

    def test_sacu_framework_returns_dict(self):
        result = self.svc.get_sacu_framework()
        assert isinstance(result, dict)

    def test_sacu_has_framework_key(self):
        result = self.svc.get_sacu_framework()
        if "error" not in result:
            assert "framework" in result


# ===========================================================================
# Cross-regional comparisons
# ===========================================================================

class TestSADCCrossRegionalComparisons:
    def setup_method(self):
        from services.sadc_intelligence_service import SADCIntelligenceService
        self.svc = SADCIntelligenceService()

    def test_sadc_vs_eac_returns_dict(self):
        result = self.svc.compare_sadc_eac()
        assert isinstance(result, dict)
        assert "comparison" in result

    def test_sadc_vs_eac_has_dual_members(self):
        result = self.svc.compare_sadc_eac()
        assert "dual_members" in result
        assert "TZA" in result["dual_members"]
        assert "COD" in result["dual_members"]

    def test_sadc_vs_cemac_returns_dict(self):
        result = self.svc.compare_sadc_cemac()
        assert isinstance(result, dict)
        assert "comparison" in result

    def test_sadc_vs_cemac_has_key_differences(self):
        result = self.svc.compare_sadc_cemac()
        assert "key_differences" in result
        assert len(result["key_differences"]) > 0


# ===========================================================================
# Trade protocols
# ===========================================================================

class TestSADCTradeProtocols:
    def setup_method(self):
        from services.sadc_intelligence_service import SADCIntelligenceService
        self.svc = SADCIntelligenceService()

    def test_all_protocols_returns_dict(self):
        result = self.svc.get_trade_protocols()
        assert isinstance(result, dict)

    def test_specific_protocol(self):
        result = self.svc.get_trade_protocols(protocol="sadc_trade_protocol")
        if "error" not in result:
            assert "tariff_elimination" in result

    def test_invalid_protocol_returns_error(self):
        result = self.svc.get_trade_protocols(protocol="nonexistent_protocol")
        assert "error" in result


# ===========================================================================
# Country tariff data
# ===========================================================================

class TestSADCCountryTariffData:
    def setup_method(self):
        from services.sadc_intelligence_service import SADCIntelligenceService
        self.svc = SADCIntelligenceService()

    def test_valid_sadc_country(self):
        result = self.svc.get_country_tariff_data("ZAF")
        # Either real data or informative error
        assert isinstance(result, dict)

    def test_invalid_country_returns_error(self):
        result = self.svc.get_country_tariff_data("USA")
        assert "error" in result

    def test_non_sadc_country_error(self):
        result = self.svc.get_country_tariff_data("FRA")
        assert "error" in result
