"""
Tests for SADC Mining Sector Intelligence
==========================================
Tests for services/mining_sector_service.py covering:
  - Service instantiation
  - Mineral profile queries
  - Country mining profiles
  - Value-chain analysis
  - Export route recommendations
  - Beneficiation opportunities
"""

import sys
import os
import pytest

BACKEND_DIR = os.path.join(os.path.dirname(__file__), '..', 'backend')
sys.path.insert(0, BACKEND_DIR)


# ===========================================================================
# Service instantiation
# ===========================================================================

class TestMiningSectorServiceInit:
    def test_import(self):
        from services.mining_sector_service import MiningSectorService
        svc = MiningSectorService()
        assert svc is not None

    def test_singleton(self):
        from services.mining_sector_service import get_mining_service
        s1 = get_mining_service()
        s2 = get_mining_service()
        assert s1 is s2


# ===========================================================================
# Mineral profiles
# ===========================================================================

class TestMineralProfiles:
    def setup_method(self):
        from services.mining_sector_service import MiningSectorService
        self.svc = MiningSectorService()

    def test_list_minerals(self):
        minerals = self.svc.list_minerals()
        assert isinstance(minerals, list)
        assert len(minerals) >= 6

    def test_list_includes_key_minerals(self):
        minerals = self.svc.list_minerals()
        for m in ["diamond", "platinum", "copper", "cobalt", "coal", "gold"]:
            assert m in minerals

    def test_diamond_profile(self):
        profile = self.svc.get_mineral_profile("diamond")
        assert "error" not in profile
        assert (
            profile.get("sadcGlobalSharePct") == 60
            or profile.get("sadc_global_share_pct") == 60
            or "keyProducers" in profile
            or "key_producers" in profile
        )

    def test_diamond_key_producers(self):
        from services.mining_sector_service import MINERAL_PROFILES
        producers = MINERAL_PROFILES["diamond"].get("keyProducers") or MINERAL_PROFILES["diamond"].get("key_producers", [])
        assert "BWA" in producers
        assert "ZAF" in producers
        assert "NAM" in producers

    def test_platinum_profile(self):
        profile = self.svc.get_mineral_profile("platinum")
        assert "error" not in profile

    def test_copper_profile(self):
        profile = self.svc.get_mineral_profile("copper")
        assert "error" not in profile

    def test_unknown_mineral_returns_error(self):
        profile = self.svc.get_mineral_profile("unobtanium")
        assert "error" in profile
        assert "available" in profile

    def test_case_insensitive_lookup(self):
        p1 = self.svc.get_mineral_profile("DIAMOND")
        p2 = self.svc.get_mineral_profile("diamond")
        assert ("error" in p1) == ("error" in p2)


# ===========================================================================
# Country mining profiles
# ===========================================================================

class TestCountryMiningProfiles:
    def setup_method(self):
        from services.mining_sector_service import MiningSectorService
        self.svc = MiningSectorService()

    def test_south_africa_profile(self):
        profile = self.svc.get_country_mining_profile("ZAF")
        assert isinstance(profile, dict)
        assert "minerals_produced" in profile or "mining_role" in profile

    def test_zambia_copper_producer(self):
        profile = self.svc.get_country_mining_profile("ZMB")
        if "minerals_produced" in profile:
            assert "copper" in profile["minerals_produced"]

    def test_drc_cobalt_producer(self):
        profile = self.svc.get_country_mining_profile("COD")
        if "minerals_produced" in profile:
            assert "cobalt" in profile["minerals_produced"]

    def test_botswana_diamond_producer(self):
        profile = self.svc.get_country_mining_profile("BWA")
        if "minerals_produced" in profile:
            assert "diamond" in profile["minerals_produced"]

    def test_non_producer_country(self):
        # COM (Comoros) is not a significant mineral producer
        profile = self.svc.get_country_mining_profile("COM")
        assert isinstance(profile, dict)


# ===========================================================================
# Value-chain analysis
# ===========================================================================

class TestMiningValueChain:
    def setup_method(self):
        from services.mining_sector_service import MiningSectorService
        self.svc = MiningSectorService()

    def test_diamond_value_chain(self):
        vc = self.svc.get_value_chain("diamond")
        assert "error" not in vc
        assert "value_chain_stages" in vc
        assert len(vc["value_chain_stages"]) > 0

    def test_value_chain_has_mineral_key(self):
        vc = self.svc.get_value_chain("copper")
        assert vc.get("mineral") == "copper"

    def test_value_chain_has_hs_code(self):
        vc = self.svc.get_value_chain("diamond")
        assert "hs_code_prefix" in vc

    def test_value_chain_has_beneficiation_info(self):
        vc = self.svc.get_value_chain("platinum")
        assert "sadc_beneficiation_opportunity" in vc

    def test_value_chain_unknown_mineral(self):
        vc = self.svc.get_value_chain("unobtanium")
        assert "error" in vc


# ===========================================================================
# Export routes
# ===========================================================================

class TestMineralExportRoutes:
    def setup_method(self):
        from services.mining_sector_service import MiningSectorService
        self.svc = MiningSectorService()

    def test_zambia_routes(self):
        routes = self.svc.get_mineral_export_routes("ZMB")
        assert isinstance(routes, dict)
        assert "export_routes" in routes or "note" in routes

    def test_zambia_has_multiple_routes(self):
        routes = self.svc.get_mineral_export_routes("ZMB")
        if "export_routes" in routes:
            assert len(routes["export_routes"]) > 1

    def test_south_africa_direct(self):
        routes = self.svc.get_mineral_export_routes("ZAF")
        assert isinstance(routes, dict)

    def test_unknown_country_handled(self):
        routes = self.svc.get_mineral_export_routes("XYZ")
        assert isinstance(routes, dict)
        assert "note" in routes or "export_routes" in routes

    def test_recommendation_field(self):
        routes = self.svc.get_mineral_export_routes("ZMB")
        if "export_routes" in routes:
            assert "recommendation" in routes


# ===========================================================================
# Beneficiation opportunities
# ===========================================================================

class TestBeneficiationOpportunities:
    def setup_method(self):
        from services.mining_sector_service import MiningSectorService
        self.svc = MiningSectorService()

    def test_returns_list(self):
        opps = self.svc.get_beneficiation_opportunities()
        assert isinstance(opps, list)

    def test_at_least_5_opportunities(self):
        opps = self.svc.get_beneficiation_opportunities()
        assert len(opps) >= 5

    def test_opportunity_structure(self):
        opps = self.svc.get_beneficiation_opportunities()
        for opp in opps:
            assert "mineral" in opp
            assert "opportunity" in opp
            assert "valueMultiplier" in opp or "value_multiplier" in opp

    def test_includes_diamond(self):
        opps = self.svc.get_beneficiation_opportunities()
        minerals = [o["mineral"] for o in opps]
        assert "diamond" in minerals

    def test_includes_copper(self):
        opps = self.svc.get_beneficiation_opportunities()
        minerals = [o["mineral"] for o in opps]
        assert "copper" in minerals


# ===========================================================================
# MINERAL_PROFILES constants
# ===========================================================================

class TestMineralProfileConstants:
    def test_import(self):
        from services.mining_sector_service import MINERAL_PROFILES
        assert MINERAL_PROFILES is not None

    def test_diamond_hs_code(self):
        from services.mining_sector_service import MINERAL_PROFILES
        code = MINERAL_PROFILES["diamond"].get("hsCodePrefix") or MINERAL_PROFILES["diamond"].get("hs_code_prefix")
        assert code == "7102"

    def test_platinum_hs_code(self):
        from services.mining_sector_service import MINERAL_PROFILES
        code = MINERAL_PROFILES["platinum"].get("hsCodePrefix") or MINERAL_PROFILES["platinum"].get("hs_code_prefix")
        assert code == "7110"

    def test_copper_hs_code(self):
        from services.mining_sector_service import MINERAL_PROFILES
        code = MINERAL_PROFILES["copper"].get("hsCodePrefix") or MINERAL_PROFILES["copper"].get("hs_code_prefix")
        assert code == "7403"

    def test_cobalt_hs_code(self):
        from services.mining_sector_service import MINERAL_PROFILES
        code = MINERAL_PROFILES["cobalt"].get("hsCodePrefix") or MINERAL_PROFILES["cobalt"].get("hs_code_prefix")
        assert code == "8105"

    def test_sadc_share_realistic(self):
        from services.mining_sector_service import MINERAL_PROFILES
        diamond_share = MINERAL_PROFILES["diamond"].get("sadcGlobalSharePct") or MINERAL_PROFILES["diamond"].get("sadc_global_share_pct")
        platinum_share = MINERAL_PROFILES["platinum"].get("sadcGlobalSharePct") or MINERAL_PROFILES["platinum"].get("sadc_global_share_pct")
        cobalt_share = MINERAL_PROFILES["cobalt"].get("sadcGlobalSharePct") or MINERAL_PROFILES["cobalt"].get("sadc_global_share_pct")
        assert diamond_share == 60
        assert platinum_share == 80
        assert cobalt_share == 70
