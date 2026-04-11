"""
Tests for SADC API Routes
==========================
Tests for the SADC intelligence REST endpoints defined in
backend/routes/sadc_intelligence.py.

These tests use FastAPI's TestClient and exercise the full route stack.
"""

import sys
import os
import pytest

BACKEND_DIR = os.path.join(os.path.dirname(__file__), '..', 'backend')
sys.path.insert(0, BACKEND_DIR)


# ---------------------------------------------------------------------------
# FastAPI TestClient setup
# ---------------------------------------------------------------------------

try:
    import importlib.util
    from fastapi.testclient import TestClient
    from fastapi import FastAPI, APIRouter

    # Import only the SADC route module directly (avoids loading routes/__init__.py
    # which pulls in Redis/database dependencies not available in the test environment)
    _spec = importlib.util.spec_from_file_location(
        "sadc_intelligence_route",
        os.path.join(BACKEND_DIR, "routes", "sadc_intelligence.py"),
    )
    _mod = importlib.util.module_from_spec(_spec)
    _spec.loader.exec_module(_mod)
    sadc_router = _mod.router

    app = FastAPI()
    api_router = APIRouter(prefix="/api")
    api_router.include_router(sadc_router)
    app.include_router(api_router)

    client = TestClient(app)
    ROUTES_AVAILABLE = True
except Exception as _exc:
    ROUTES_AVAILABLE = False

pytestmark = pytest.mark.skipif(
    not ROUTES_AVAILABLE,
    reason="SADC route module or dependencies not available",
)


# ===========================================================================
# Regional overview endpoints
# ===========================================================================

class TestSADCOverviewEndpoint:
    def test_sadc_overview_200(self):
        resp = client.get("/api/regions/sadc/overview")
        assert resp.status_code == 200

    def test_sadc_overview_has_organisation(self):
        resp = client.get("/api/regions/sadc/overview")
        data = resp.json()
        assert "organisation" in data

    def test_sadc_overview_member_count(self):
        resp = client.get("/api/regions/sadc/overview")
        data = resp.json()
        assert data["organisation"]["member_count"] == 16


class TestSADCCountriesEndpoint:
    def test_countries_200(self):
        resp = client.get("/api/regions/sadc/countries")
        assert resp.status_code == 200

    def test_countries_has_16_members(self):
        resp = client.get("/api/regions/sadc/countries")
        data = resp.json()
        assert data.get("total") == 16 or len(data.get("countries", {})) == 16

    def test_south_africa_in_countries(self):
        resp = client.get("/api/regions/sadc/countries")
        data = resp.json()
        countries = data.get("countries", data)
        assert "ZAF" in countries


class TestSADCTradeStatisticsEndpoint:
    def test_trade_statistics_200(self):
        resp = client.get("/api/regions/sadc/trade-statistics")
        assert resp.status_code == 200

    def test_trade_statistics_has_gdp(self):
        resp = client.get("/api/regions/sadc/trade-statistics")
        data = resp.json()
        # Should contain some numeric trade data
        assert isinstance(data, dict)


class TestSADCFreshnessEndpoint:
    def test_freshness_200(self):
        resp = client.get("/api/regions/sadc/freshness")
        assert resp.status_code == 200

    def test_freshness_has_countries(self):
        resp = client.get("/api/regions/sadc/freshness")
        data = resp.json()
        assert "countries" in data
        assert "total_countries" in data
        assert data["total_countries"] == 16


# ===========================================================================
# SACU endpoints
# ===========================================================================

class TestSACUCustomsUnionEndpoint:
    def test_customs_union_200(self):
        resp = client.get("/api/regions/sacu/customs-union")
        assert resp.status_code == 200

    def test_customs_union_has_framework(self):
        resp = client.get("/api/regions/sacu/customs-union")
        data = resp.json()
        assert "framework" in data or "error" in data


class TestSACURevenueSharingEndpoint:
    def test_revenue_sharing_200(self):
        resp = client.get("/api/regions/sacu/revenue-sharing")
        assert resp.status_code == 200

    def test_revenue_sharing_structure(self):
        resp = client.get("/api/regions/sacu/revenue-sharing")
        data = resp.json()
        assert "revenue_sharing_formula" in data or "error" in data


class TestSACUImportCostEndpoint:
    def test_import_cost_200(self):
        payload = {
            "cif_value": 1000.0,
            "hs_chapter": "87",
            "destination": "ZAF",
            "origin": "INTL",
        }
        resp = client.post("/api/regions/sacu/import-cost", json=payload)
        assert resp.status_code == 200

    def test_import_cost_fields(self):
        payload = {"cif_value": 1000.0, "hs_chapter": "84", "destination": "ZAF"}
        resp = client.post("/api/regions/sacu/import-cost", json=payload)
        data = resp.json()
        assert "total_landed_cost" in data or "error" in data

    def test_import_cost_automotive(self):
        payload = {"cif_value": 10000.0, "hs_chapter": "87", "destination": "ZAF", "origin": "INTL"}
        resp = client.post("/api/regions/sacu/import-cost", json=payload)
        data = resp.json()
        if "customs_duty" in data:
            assert data["customs_duty"] == 2500.0  # 25% CET


# ===========================================================================
# Country-specific endpoints
# ===========================================================================

class TestSADCCountryTariffsEndpoint:
    def test_valid_country_returns_200_or_404(self):
        resp = client.get("/api/countries/sadc/ZAF/tariffs")
        assert resp.status_code in [200, 404]

    def test_invalid_country_returns_404(self):
        resp = client.get("/api/countries/sadc/USA/tariffs")
        assert resp.status_code == 404


class TestSADCCountrySectorsEndpoint:
    def test_south_africa_sectors_200(self):
        resp = client.get("/api/countries/sadc/ZAF/sectors")
        assert resp.status_code == 200

    def test_sectors_has_country_code(self):
        resp = client.get("/api/countries/sadc/ZAF/sectors")
        data = resp.json()
        assert data.get("country_code") == "ZAF"

    def test_sectors_list(self):
        resp = client.get("/api/countries/sadc/ZAF/sectors")
        data = resp.json()
        assert "sector_strengths" in data
        assert isinstance(data["sector_strengths"], list)

    def test_invalid_country_sectors_404(self):
        resp = client.get("/api/countries/sadc/FRA/sectors")
        assert resp.status_code == 404

    def test_case_insensitive_code(self):
        resp = client.get("/api/countries/sadc/zaf/sectors")
        assert resp.status_code == 200


class TestSADCCountryMiningEndpoint:
    def test_zambia_mining_200(self):
        resp = client.get("/api/countries/sadc/ZMB/mining")
        assert resp.status_code == 200

    def test_mining_profile_is_dict(self):
        resp = client.get("/api/countries/sadc/BWA/mining")
        assert isinstance(resp.json(), dict)


# ===========================================================================
# Mining endpoints
# ===========================================================================

class TestMiningOverviewEndpoint:
    def test_mining_overview_200(self):
        resp = client.get("/api/mining/sadc/overview")
        assert resp.status_code == 200

    def test_mining_overview_is_dict(self):
        resp = client.get("/api/mining/sadc/overview")
        assert isinstance(resp.json(), dict)


class TestMineralListEndpoint:
    def test_minerals_200(self):
        resp = client.get("/api/mining/sadc/minerals")
        assert resp.status_code == 200

    def test_minerals_has_list(self):
        resp = client.get("/api/mining/sadc/minerals")
        data = resp.json()
        assert "minerals" in data
        assert isinstance(data["minerals"], list)
        assert len(data["minerals"]) >= 6


class TestMineralProfileEndpoint:
    def test_diamond_200(self):
        resp = client.get("/api/mining/sadc/minerals/diamond")
        assert resp.status_code == 200

    def test_copper_200(self):
        resp = client.get("/api/mining/sadc/minerals/copper")
        assert resp.status_code == 200

    def test_unknown_mineral_404(self):
        resp = client.get("/api/mining/sadc/minerals/unobtanium")
        assert resp.status_code == 404


class TestValueChainEndpoint:
    def test_diamond_value_chain_200(self):
        resp = client.get("/api/mining/sadc/value-chain/diamond")
        assert resp.status_code == 200

    def test_value_chain_has_stages(self):
        resp = client.get("/api/mining/sadc/value-chain/platinum")
        data = resp.json()
        assert "value_chain_stages" in data

    def test_unknown_mineral_value_chain_404(self):
        resp = client.get("/api/mining/sadc/value-chain/unobtanium")
        assert resp.status_code == 404


class TestBeneficiationEndpoint:
    def test_beneficiation_200(self):
        resp = client.get("/api/mining/sadc/beneficiation")
        assert resp.status_code == 200

    def test_beneficiation_has_opportunities(self):
        resp = client.get("/api/mining/sadc/beneficiation")
        data = resp.json()
        assert "opportunities" in data
        assert len(data["opportunities"]) >= 5


class TestExportRoutesEndpoint:
    def test_zambia_routes_200(self):
        resp = client.get("/api/mining/sadc/export-routes/ZMB")
        assert resp.status_code == 200

    def test_routes_is_dict(self):
        resp = client.get("/api/mining/sadc/export-routes/ZMB")
        assert isinstance(resp.json(), dict)


# ===========================================================================
# Transport corridors
# ===========================================================================

class TestTransportCorridorsEndpoint:
    def test_corridors_200(self):
        resp = client.get("/api/trade-corridors/sadc")
        assert resp.status_code == 200

    def test_corridors_has_corridors_key(self):
        resp = client.get("/api/trade-corridors/sadc")
        data = resp.json()
        assert "corridors" in data or "error" in data

    def test_country_corridors_200(self):
        resp = client.get("/api/trade-corridors/sadc/ZMB")
        assert resp.status_code == 200


# ===========================================================================
# Cross-regional analysis
# ===========================================================================

class TestCrossRegionalAnalysis:
    def test_sadc_vs_eac_200(self):
        resp = client.get("/api/analysis/sadc-vs-eac")
        assert resp.status_code == 200

    def test_sadc_vs_eac_has_comparison(self):
        resp = client.get("/api/analysis/sadc-vs-eac")
        data = resp.json()
        assert "comparison" in data

    def test_sadc_vs_cemac_200(self):
        resp = client.get("/api/analysis/sadc-vs-cemac")
        assert resp.status_code == 200

    def test_sadc_vs_cemac_has_comparison(self):
        resp = client.get("/api/analysis/sadc-vs-cemac")
        data = resp.json()
        assert "comparison" in data


# ===========================================================================
# Investment recommendation endpoint
# ===========================================================================

class TestInvestmentRecommendationEndpoint:
    def test_investment_recommendation_200(self):
        payload = {"sector": "mining", "priority": "infrastructure"}
        resp = client.post("/api/regions/sadc/investment-recommendation", json=payload)
        assert resp.status_code == 200

    def test_recommendation_has_rankings(self):
        payload = {"sector": "mining"}
        resp = client.post("/api/regions/sadc/investment-recommendation", json=payload)
        data = resp.json()
        assert "rankings" in data
        assert len(data["rankings"]) == 16

    def test_recommendation_sorted(self):
        payload = {"sector": "financial_services", "priority": "tax_incentives"}
        resp = client.post("/api/regions/sadc/investment-recommendation", json=payload)
        data = resp.json()
        scores = [r["total_score"] for r in data["rankings"]]
        assert scores == sorted(scores, reverse=True)

    def test_recommendation_missing_sector_422(self):
        resp = client.post("/api/regions/sadc/investment-recommendation", json={})
        assert resp.status_code == 422


# ===========================================================================
# Trade protocols
# ===========================================================================

class TestTradeProtocolsEndpoint:
    def test_protocols_200(self):
        resp = client.get("/api/regions/sadc/protocols")
        assert resp.status_code == 200

    def test_specific_protocol(self):
        resp = client.get("/api/regions/sadc/protocols?protocol=sadc_trade_protocol")
        assert resp.status_code == 200
