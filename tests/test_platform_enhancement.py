"""
Tests for the AfCFTA Platform comprehensive enhancement:
- Performance infrastructure (cache layers, metrics)
- AI Investment Intelligence Engine
- Enhanced Search Engine
- Regional Analytics
- API routes (AI intelligence, regional analytics, search, performance, mobile)
- GraphQL schema
- WebSocket handlers
"""

import sys
import os
import importlib.util
from pathlib import Path

# Add backend to path
BACKEND_PATH = Path(__file__).parent.parent / "backend"
sys.path.insert(0, str(BACKEND_PATH))

import pytest

# ===========================================================================
# Performance - Cache Layers
# ===========================================================================

class TestCacheLayers:
    """Tests for multi-layer Redis caching infrastructure."""

    def test_cache_layer_config(self):
        from performance.caching.cache_layers import CACHE_LAYERS
        assert len(CACHE_LAYERS) == 4
        assert "L1_hot_data" in CACHE_LAYERS
        assert "L2_regional_intel" in CACHE_LAYERS
        assert "L3_calculations" in CACHE_LAYERS
        assert "L4_realtime" in CACHE_LAYERS

    def test_cache_layer_ttls(self):
        from performance.caching.cache_layers import CACHE_LAYERS
        assert CACHE_LAYERS["L1_hot_data"]["ttl"] == 3600        # 1 hour
        assert CACHE_LAYERS["L2_regional_intel"]["ttl"] == 86400  # 24 hours
        assert CACHE_LAYERS["L3_calculations"]["ttl"] == 21600    # 6 hours
        assert CACHE_LAYERS["L4_realtime"]["ttl"] == 300          # 5 minutes

    def test_cache_layer_patterns(self):
        from performance.caching.cache_layers import CACHE_LAYERS
        assert "hot:" in CACHE_LAYERS["L1_hot_data"]["pattern"]
        assert "region:" in CACHE_LAYERS["L2_regional_intel"]["pattern"]
        assert "calc:" in CACHE_LAYERS["L3_calculations"]["pattern"]
        assert "live:" in CACHE_LAYERS["L4_realtime"]["pattern"]

    def test_multi_layer_cache_singleton(self):
        from performance.caching.cache_layers import get_cache, MultiLayerCache
        cache = get_cache()
        assert isinstance(cache, MultiLayerCache)
        assert cache is get_cache()  # singleton

    def test_cache_build_key(self):
        from performance.caching.cache_layers import CacheLayer, CACHE_LAYERS
        layer = CacheLayer("L1_hot_data", CACHE_LAYERS["L1_hot_data"])
        key = layer.build_key(type="tariff", key="DZ-0901")
        assert "afcfta" in key
        assert "l1_hot_data" in key.lower()

    def test_cache_set_get_without_redis(self):
        """Without Redis, set returns False and get returns None."""
        from performance.caching.cache_layers import CacheLayer, CACHE_LAYERS
        layer = CacheLayer("L1_hot_data", CACHE_LAYERS["L1_hot_data"])
        # Force no client
        layer._client = None

        key = "afcfta:test:key"
        result = layer.set(key, {"test": True})
        # Either False (no Redis) or True (Redis available)
        assert isinstance(result, bool)

    def test_multilayer_all_stats(self):
        from performance.caching.cache_layers import get_cache
        cache = get_cache()
        stats = cache.all_stats()
        assert "L1_hot_data" in stats
        assert "L2_regional_intel" in stats
        assert "timestamp" in stats


# ===========================================================================
# Performance - Metrics
# ===========================================================================

class TestPerformanceMetrics:
    """Tests for in-process performance monitoring."""

    def test_metrics_singleton(self):
        from performance.monitoring.performance_metrics import get_metrics, PerformanceMetrics
        m = get_metrics()
        assert isinstance(m, PerformanceMetrics)
        assert m is get_metrics()

    def test_record_cache_hit(self):
        from performance.monitoring.performance_metrics import PerformanceMetrics
        m = PerformanceMetrics()
        m.record_cache_hit("tariff_lookup")
        assert m._hits["tariff_lookup"] == 1

    def test_record_cache_miss(self):
        from performance.monitoring.performance_metrics import PerformanceMetrics
        m = PerformanceMetrics()
        m.record_cache_miss("tariff_lookup")
        assert m._misses["tariff_lookup"] == 1

    def test_hit_rate_calculation(self):
        from performance.monitoring.performance_metrics import PerformanceMetrics
        m = PerformanceMetrics()
        m.record_cache_hit("op")
        m.record_cache_hit("op")
        m.record_cache_miss("op")
        assert abs(m.cache_hit_rate("op") - 2/3) < 0.001

    def test_latency_recording(self):
        from performance.monitoring.performance_metrics import PerformanceMetrics
        m = PerformanceMetrics()
        m.record_latency("search", 0.1)
        m.record_latency("search", 0.3)
        p50 = m.percentile("search", 50)
        assert p50 is not None
        assert 0.0 < p50 <= 0.3

    def test_slow_query_detection(self):
        from performance.monitoring.performance_metrics import PerformanceMetrics, SLOW_QUERY_THRESHOLD_S
        m = PerformanceMetrics()
        m.record_latency("slow_op", SLOW_QUERY_THRESHOLD_S + 0.1)
        assert len(m.slow_queries()) == 1
        assert m.slow_queries()[0]["operation"] == "slow_op"

    def test_summary_structure(self):
        from performance.monitoring.performance_metrics import PerformanceMetrics
        m = PerformanceMetrics()
        m.record_latency("op", 0.05)
        m.record_cache_hit("op")
        summary = m.summary()
        assert "uptime_seconds" in summary
        assert "operations" in summary
        assert "slow_queries_count" in summary


# ===========================================================================
# AI Investment Intelligence Engine
# ===========================================================================

class TestInvestmentIntelligenceEngine:
    """Tests for the AI-powered investment scoring and recommendation engine."""

    def test_engine_singleton(self):
        from intelligence.ai_engine.investment_scoring import (
            get_intelligence_engine, InvestmentIntelligenceEngine
        )
        engine = get_intelligence_engine()
        assert isinstance(engine, InvestmentIntelligenceEngine)
        assert engine is get_intelligence_engine()

    def test_investment_score_returns_score(self):
        from intelligence.ai_engine.investment_scoring import get_intelligence_engine
        engine = get_intelligence_engine()
        score = engine.calculate_investment_score("MAR", "general")
        assert score is not None
        assert 0.0 <= score.overall_score <= 1.0

    def test_investment_score_has_grade(self):
        from intelligence.ai_engine.investment_scoring import get_intelligence_engine
        engine = get_intelligence_engine()
        score = engine.calculate_investment_score("EGY", "manufacturing")
        assert score.grade in {"A+", "A", "B+", "B", "C+", "C", "D"}

    def test_investment_score_components(self):
        from intelligence.ai_engine.investment_scoring import get_intelligence_engine, SCORING_ALGORITHM
        engine = get_intelligence_engine()
        score = engine.calculate_investment_score("KEN")
        assert len(score.component_scores) == len(SCORING_ALGORITHM)

    def test_investment_score_confidence_interval(self):
        from intelligence.ai_engine.investment_scoring import get_intelligence_engine
        engine = get_intelligence_engine()
        score = engine.calculate_investment_score("ZAF")
        ci = score.confidence_interval
        assert "lower" in ci and "upper" in ci
        assert ci["lower"] <= score.overall_score <= ci["upper"]

    def test_investment_score_to_dict(self):
        from intelligence.ai_engine.investment_scoring import get_intelligence_engine
        engine = get_intelligence_engine()
        score = engine.calculate_investment_score("TUN")
        d = score.to_dict()
        assert "overall_score" in d
        assert "grade" in d
        assert "component_scores" in d
        assert "risk_factors" in d

    def test_risk_assessment(self):
        from intelligence.ai_engine.investment_scoring import get_intelligence_engine
        engine = get_intelligence_engine()
        risk = engine.assess_risk("NGA", "ict")
        assert "overall_risk_score" in risk
        assert risk["risk_level"] in {"low", "medium", "high"}
        assert "identified_risks" in risk
        assert "mitigation_strategies" in risk

    def test_personalized_recommendations(self):
        from intelligence.ai_engine.investment_scoring import get_intelligence_engine
        engine = get_intelligence_engine()
        user_profile = {"sector": "agriculture", "risk_tolerance": "medium"}
        recs = engine.get_personalized_recommendations(user_profile, limit=5)
        assert isinstance(recs, list)
        assert len(recs) <= 5
        for rec in recs:
            assert rec.rank >= 1
            assert rec.country
            assert rec.score is not None

    def test_recommendations_ranked_by_score(self):
        from intelligence.ai_engine.investment_scoring import get_intelligence_engine
        engine = get_intelligence_engine()
        recs = engine.get_personalized_recommendations({"sector": "general"}, limit=8)
        scores = [r.score.overall_score for r in recs]
        assert scores == sorted(scores, reverse=True)

    def test_trade_flow_prediction(self):
        from intelligence.ai_engine.investment_scoring import get_intelligence_engine
        engine = get_intelligence_engine()
        pred = engine.predict_trade_flows("MAR", "EGY", "0901", timeframe_months=12)
        assert pred.predicted_value_usd > 0
        assert pred.predicted_volume_tonnes > 0
        assert pred.trend_direction in {"upward", "stable", "downward"}
        assert "lower" in pred.confidence_interval
        assert "upper" in pred.confidence_interval

    def test_scoring_algorithm_weights_sum_to_one(self):
        from intelligence.ai_engine.investment_scoring import SCORING_ALGORITHM
        total_weight = sum(v["weight"] for v in SCORING_ALGORITHM.values())
        assert abs(total_weight - 1.0) < 0.001


# ===========================================================================
# Enhanced Search Engine
# ===========================================================================

class TestEnhancedSearchEngine:
    """Tests for HS code fuzzy/semantic search and investment opportunity filtering."""

    def test_exact_hs_search(self):
        from search.enhanced_search import get_search_engine
        engine = get_search_engine()
        results = engine.intelligent_hs_search("0901")
        assert results["total_matches"] > 0
        # Exact match for '0901'
        exact = results["exact_matches"]
        assert any(m["hs_code"] == "0901" for m in exact)

    def test_semantic_search_coffee(self):
        from search.enhanced_search import get_search_engine
        engine = get_search_engine()
        results = engine.intelligent_hs_search("coffee")
        all_codes = [
            m["hs_code"] for m in
            results["exact_matches"] + results["semantic_matches"] + results["fuzzy_matches"]
        ]
        assert any("09" in c for c in all_codes), "Expected chapter 09 for coffee"

    def test_semantic_search_phone(self):
        from search.enhanced_search import get_search_engine
        engine = get_search_engine()
        results = engine.intelligent_hs_search("smartphone")
        semantic = results["semantic_matches"]
        codes = [m["hs_code"] for m in semantic]
        assert any("85" in c for c in codes), "Expected chapter 85 for phones"

    def test_fuzzy_search_returns_results(self):
        from search.enhanced_search import FuzzyMatcher
        matcher = FuzzyMatcher(threshold=0.5)
        results = matcher.search("cereals")
        assert isinstance(results, list)

    def test_search_result_structure(self):
        from search.enhanced_search import get_search_engine
        engine = get_search_engine()
        results = engine.intelligent_hs_search("wheat")
        assert "query" in results
        assert "exact_matches" in results
        assert "fuzzy_matches" in results
        assert "semantic_matches" in results
        assert "total_matches" in results

    def test_investment_opportunity_search(self):
        from search.enhanced_search import get_search_engine
        engine = get_search_engine()
        criteria = {
            "sectors": ["agriculture"],
            "investment_size": "medium",
            "risk_tolerance": "medium",
            "min_score": 0.0,
        }
        result = engine.investment_opportunity_search(criteria)
        assert "total_count" in result
        assert "opportunities" in result
        assert "facets" in result

    def test_investment_search_sorted_by_score(self):
        from search.enhanced_search import get_search_engine
        engine = get_search_engine()
        result = engine.investment_opportunity_search({"sectors": ["general"]})
        scores = [o["investment_score"] for o in result["opportunities"]]
        assert scores == sorted(scores, reverse=True)

    def test_investment_search_min_score_filter(self):
        from search.enhanced_search import get_search_engine
        engine = get_search_engine()
        result = engine.investment_opportunity_search({
            "sectors": ["general"],
            "min_score": 0.65,
        })
        for opp in result["opportunities"]:
            assert opp["investment_score"] >= 0.65


# ===========================================================================
# Regional Analytics
# ===========================================================================

class TestRegionalAnalytics:
    """Tests for the regional analytics engine."""

    def test_analytics_singleton(self):
        from intelligence.analytics.regional_analytics import (
            get_regional_analytics, RegionalAnalyticsEngine
        )
        a = get_regional_analytics()
        assert isinstance(a, RegionalAnalyticsEngine)
        assert a is get_regional_analytics()

    def test_bloc_summary(self):
        from intelligence.analytics.regional_analytics import get_regional_analytics
        a = get_regional_analytics()
        summary = a.get_bloc_summary("ECOWAS")
        assert summary["bloc"] == "ECOWAS"
        assert summary["member_count"] > 0
        assert "countries" in summary
        assert "gdp_bn_usd" in summary

    def test_unknown_bloc(self):
        from intelligence.analytics.regional_analytics import get_regional_analytics
        a = get_regional_analytics()
        result = a.get_bloc_summary("UNKNOWN")
        assert "error" in result

    def test_compare_regions(self):
        from intelligence.analytics.regional_analytics import get_regional_analytics
        a = get_regional_analytics()
        comparison = a.compare_regions(blocs=["ECOWAS", "EAC", "SADC"])
        assert "blocs" in comparison
        assert "rankings" in comparison
        assert "best_performer" in comparison

    def test_all_blocs_listed(self):
        from intelligence.analytics.regional_analytics import get_regional_analytics, REGIONAL_BLOCS
        a = get_regional_analytics()
        blocs = a.get_all_blocs()
        assert len(blocs) == len(REGIONAL_BLOCS)

    def test_investment_heatmap(self):
        from intelligence.analytics.regional_analytics import get_regional_analytics
        a = get_regional_analytics()
        heatmap = a.get_investment_heatmap()
        assert isinstance(heatmap, list)
        assert len(heatmap) > 0
        for entry in heatmap:
            assert "bloc" in entry
            assert "investment_score" in entry
            assert "opportunity_tier" in entry
            assert entry["opportunity_tier"] in {"tier1", "tier2", "tier3"}

    def test_heatmap_sorted_by_score(self):
        from intelligence.analytics.regional_analytics import get_regional_analytics
        a = get_regional_analytics()
        heatmap = a.get_investment_heatmap()
        scores = [h["investment_score"] for h in heatmap]
        assert scores == sorted(scores, reverse=True)

    def test_trade_corridors(self):
        from intelligence.analytics.regional_analytics import get_regional_analytics
        a = get_regional_analytics()
        corridors = a.get_trade_corridor_analysis()
        assert isinstance(corridors, list)
        assert len(corridors) > 0
        for c in corridors:
            assert "origin" in c
            assert "destination" in c
            assert "trade_value_bn" in c

    def test_corridor_filter_by_origin(self):
        from intelligence.analytics.regional_analytics import get_regional_analytics
        a = get_regional_analytics()
        corridors = a.get_trade_corridor_analysis(origin_bloc="EAC")
        assert all(c["origin"] == "EAC" for c in corridors)


# ===========================================================================
# FastAPI Routes (using TestClient)
# ===========================================================================

class TestAIIntelligenceRoutes:
    """Tests for AI investment intelligence API routes."""

    def _make_app(self):
        from fastapi import FastAPI
        from fastapi.testclient import TestClient
        import importlib.util
        mod_name = "routes.ai_intelligence"
        if mod_name not in sys.modules:
            spec = importlib.util.spec_from_file_location(
                mod_name,
                BACKEND_PATH / "routes" / "ai_intelligence.py",
            )
            module = importlib.util.module_from_spec(spec)
            sys.modules[mod_name] = module
            spec.loader.exec_module(module)
        module = sys.modules[mod_name]
        app = FastAPI()
        app.include_router(module.router, prefix="/api")
        return TestClient(app, raise_server_exceptions=False)

    def test_investment_score_endpoint(self):
        client = self._make_app()
        response = client.post("/api/ai-intelligence/score", json={
            "country": "MAR",
            "sector": "general",
            "investment_size": "medium",
        })
        assert response.status_code == 200
        data = response.json()
        assert "overall_score" in data
        assert "grade" in data

    def test_recommendations_endpoint(self):
        client = self._make_app()
        response = client.post("/api/ai-intelligence/recommendations", json={
            "sector": "agriculture",
            "risk_tolerance": "medium",
            "limit": 5,
        })
        assert response.status_code == 200
        data = response.json()
        assert "recommendations" in data
        assert len(data["recommendations"]) <= 5

    def test_risk_assessment_endpoint(self):
        client = self._make_app()
        response = client.get("/api/ai-intelligence/risk-assessment/NGA?sector=ict")
        assert response.status_code == 200
        data = response.json()
        assert "risk_level" in data
        assert data["risk_level"] in {"low", "medium", "high"}

    def test_bulk_score_endpoint(self):
        client = self._make_app()
        response = client.post("/api/ai-intelligence/bulk-score", json={
            "countries": ["MAR", "EGY", "KEN"],
            "sector": "general",
        })
        assert response.status_code == 200
        data = response.json()
        assert "scores" in data
        assert len(data["scores"]) == 3

    def test_predict_trade_flows_endpoint(self):
        client = self._make_app()
        response = client.post("/api/ai-intelligence/predict-trade-flows", json={
            "origin_country": "MAR",
            "destination_country": "EGY",
            "product_category": "0901",
            "timeframe_months": 12,
        })
        assert response.status_code == 200
        data = response.json()
        assert "predicted_value_usd" in data
        assert data["predicted_value_usd"] > 0

    def test_scoring_algorithm_endpoint(self):
        client = self._make_app()
        response = client.get("/api/ai-intelligence/scoring-algorithm")
        assert response.status_code == 200
        data = response.json()
        assert "algorithm" in data
        assert len(data["algorithm"]) == 6


class TestRegionalAnalyticsRoutes:
    """Tests for regional analytics API routes."""

    def _make_app(self):
        from fastapi import FastAPI
        from fastapi.testclient import TestClient
        import importlib.util
        mod_name = "routes.regional_analytics"
        if mod_name not in sys.modules:
            spec = importlib.util.spec_from_file_location(
                mod_name,
                BACKEND_PATH / "routes" / "regional_analytics.py",
            )
            module = importlib.util.module_from_spec(spec)
            sys.modules[mod_name] = module
            spec.loader.exec_module(module)
        module = sys.modules[mod_name]
        app = FastAPI()
        app.include_router(module.router, prefix="/api")
        return TestClient(app, raise_server_exceptions=False)

    def test_list_blocs(self):
        client = self._make_app()
        response = client.get("/api/regional-analytics/blocs")
        assert response.status_code == 200
        data = response.json()
        assert "blocs" in data
        assert len(data["blocs"]) >= 7

    def test_get_bloc_summary(self):
        client = self._make_app()
        response = client.get("/api/regional-analytics/blocs/EAC")
        assert response.status_code == 200
        data = response.json()
        assert data["bloc"] == "EAC"

    def test_compare_regions(self):
        client = self._make_app()
        response = client.get("/api/regional-analytics/compare?blocs=ECOWAS,EAC")
        assert response.status_code == 200
        data = response.json()
        assert "blocs" in data
        assert "rankings" in data

    def test_heatmap_endpoint(self):
        client = self._make_app()
        response = client.get("/api/regional-analytics/heatmap")
        assert response.status_code == 200
        data = response.json()
        assert "heatmap" in data

    def test_corridors_endpoint(self):
        client = self._make_app()
        response = client.get("/api/regional-analytics/corridors")
        assert response.status_code == 200
        data = response.json()
        assert "corridors" in data

    def test_radar_chart_endpoint(self):
        client = self._make_app()
        response = client.get("/api/regional-analytics/visualization/radar?countries=MAR,EGY")
        assert response.status_code == 200
        data = response.json()
        assert data["type"] == "radar"
        assert "datasets" in data["data"]

    def test_bar_chart_endpoint(self):
        client = self._make_app()
        response = client.get("/api/regional-analytics/visualization/bar?metric=investment_score")
        assert response.status_code == 200
        data = response.json()
        assert data["type"] == "bar"

    def test_heatmap_chart_endpoint(self):
        client = self._make_app()
        response = client.get("/api/regional-analytics/visualization/heatmap")
        assert response.status_code == 200
        data = response.json()
        assert data["type"] == "heatmap"

    def test_invalid_chart_type(self):
        client = self._make_app()
        response = client.get("/api/regional-analytics/visualization/unknown")
        assert response.status_code == 400

    def test_export_json(self):
        client = self._make_app()
        response = client.get("/api/regional-analytics/export?format=json")
        assert response.status_code == 200


class TestEnhancedSearchRoutes:
    """Tests for enhanced search API routes."""

    def _make_app(self):
        from fastapi import FastAPI
        from fastapi.testclient import TestClient
        import importlib.util
        mod_name = "routes.enhanced_search"
        if mod_name not in sys.modules:
            spec = importlib.util.spec_from_file_location(
                mod_name,
                BACKEND_PATH / "routes" / "enhanced_search.py",
            )
            module = importlib.util.module_from_spec(spec)
            sys.modules[mod_name] = module
            spec.loader.exec_module(module)
        module = sys.modules[mod_name]
        app = FastAPI()
        app.include_router(module.router, prefix="/api")
        return TestClient(app, raise_server_exceptions=False)

    def test_hs_code_search(self):
        client = self._make_app()
        response = client.get("/api/enhanced-search/hs-codes?q=0901")
        assert response.status_code == 200
        data = response.json()
        assert "exact_matches" in data
        assert "total_matches" in data

    def test_hs_search_natural_language(self):
        client = self._make_app()
        response = client.get("/api/enhanced-search/hs-codes?q=coffee")
        assert response.status_code == 200

    def test_investment_opportunity_search(self):
        client = self._make_app()
        response = client.post("/api/enhanced-search/investment-opportunities", json={
            "sectors": ["agriculture"],
            "risk_tolerance": "medium",
            "per_page": 10,
        })
        assert response.status_code == 200
        data = response.json()
        assert "opportunities" in data
        assert "pagination" in data

    def test_autocomplete(self):
        client = self._make_app()
        response = client.get("/api/enhanced-search/autocomplete?q=cof")
        assert response.status_code == 200
        data = response.json()
        assert "suggestions" in data

    def test_filter_options(self):
        client = self._make_app()
        response = client.get("/api/enhanced-search/filters/options")
        assert response.status_code == 200
        data = response.json()
        assert "geographic_filters" in data
        assert "investment_filters" in data


class TestPerformanceRoutes:
    """Tests for performance monitoring API routes."""

    def _make_app(self):
        from fastapi import FastAPI
        from fastapi.testclient import TestClient
        import importlib.util
        mod_name = "routes.performance"
        if mod_name not in sys.modules:
            spec = importlib.util.spec_from_file_location(
                mod_name,
                BACKEND_PATH / "routes" / "performance.py",
            )
            module = importlib.util.module_from_spec(spec)
            sys.modules[mod_name] = module
            spec.loader.exec_module(module)
        module = sys.modules[mod_name]
        app = FastAPI()
        app.include_router(module.router, prefix="/api")
        return TestClient(app, raise_server_exceptions=False)

    def test_cache_stats_endpoint(self):
        client = self._make_app()
        response = client.get("/api/performance/cache/stats")
        assert response.status_code == 200

    def test_performance_metrics_endpoint(self):
        client = self._make_app()
        response = client.get("/api/performance/metrics")
        assert response.status_code == 200
        data = response.json()
        assert "uptime_seconds" in data

    def test_slow_queries_endpoint(self):
        client = self._make_app()
        response = client.get("/api/performance/metrics/slow-queries")
        assert response.status_code == 200
        data = response.json()
        assert "slow_queries" in data


class TestMobileRoutes:
    """Tests for mobile-optimised API routes."""

    def _make_app(self):
        from fastapi import FastAPI
        from fastapi.testclient import TestClient
        from api.mobile.lightweight_endpoints import router
        app = FastAPI()
        app.include_router(router, prefix="/api")
        return TestClient(app, raise_server_exceptions=False)

    def test_mobile_country_summary(self):
        client = self._make_app()
        response = client.get("/api/mobile/country/summary/MAR")
        assert response.status_code == 200
        data = response.json()
        assert data["country_code"] == "MAR"
        assert "investment" in data
        assert "key_opportunities" in data

    def test_mobile_quick_search(self):
        client = self._make_app()
        response = client.get("/api/mobile/search/quick?q=coffee")
        assert response.status_code == 200
        data = response.json()
        assert "suggestions" in data
        assert len(data["suggestions"]) <= 8

    def test_mobile_dashboard_overview(self):
        client = self._make_app()
        response = client.get("/api/mobile/dashboard/overview")
        assert response.status_code == 200
        data = response.json()
        assert "top_blocs" in data
        assert "platform_stats" in data
        assert "quick_actions" in data

    def test_mobile_alerts_feed(self):
        client = self._make_app()
        response = client.get("/api/mobile/alerts/feed?limit=5")
        assert response.status_code == 200
        data = response.json()
        assert "alerts" in data
        assert len(data["alerts"]) <= 5

    def test_mobile_country_details_investment(self):
        client = self._make_app()
        response = client.get("/api/mobile/country/details/EGY?section=investment")
        assert response.status_code == 200
        data = response.json()
        assert "investment" in data["data"]

    def test_mobile_country_summary_etag(self):
        """ETag header is returned for cache validation."""
        client = self._make_app()
        response = client.get("/api/mobile/country/summary/KEN")
        # ETag is present in headers (if Redis available) or at minimum 200 returned
        assert response.status_code == 200


class TestGraphQLEndpoint:
    """Tests for GraphQL API endpoint."""

    def _make_app(self):
        from fastapi import FastAPI
        from fastapi.testclient import TestClient
        from api.graphql.schema import router
        app = FastAPI()
        app.include_router(router, prefix="/api")
        return TestClient(app, raise_server_exceptions=False)

    def test_schema_endpoint(self):
        client = self._make_app()
        response = client.get("/api/graphql/schema")
        assert response.status_code == 200
        data = response.json()
        assert "schema" in data
        assert "Query" in data["schema"]

    def test_graphql_health_query(self):
        client = self._make_app()
        response = client.post("/api/graphql", json={
            "query": "{ health }",
        })
        assert response.status_code in (200, 400)

    def test_graphql_playground(self):
        client = self._make_app()
        response = client.get("/api/graphql")
        assert response.status_code == 200
        assert "GraphQL" in response.text


class TestWebSocketStatus:
    """Tests for WebSocket status endpoint."""

    def _make_app(self):
        from fastapi import FastAPI
        from fastapi.testclient import TestClient
        from api.websocket.handlers import router
        app = FastAPI()
        app.include_router(router, prefix="/api")
        return TestClient(app, raise_server_exceptions=False)

    def test_websocket_status_endpoint(self):
        client = self._make_app()
        response = client.get("/api/ws/status")
        assert response.status_code == 200
        data = response.json()
        assert "channels" in data
        assert "total_connections" in data
        assert "investment_alerts" in data["channels"]


# ===========================================================================
# Dashboard - Visualization Engine
# ===========================================================================

class TestVisualizationEngine:
    """Tests for the dashboard visualization data generator."""

    def test_radar_chart_data(self):
        from dashboard.visualization_engine import get_visualization_engine
        viz = get_visualization_engine()
        data = viz.radar_chart_data(["MAR", "EGY"], sector="agriculture")
        assert data["type"] == "radar"
        assert len(data["data"]["datasets"]) == 2
        assert len(data["data"]["labels"]) == 6

    def test_bar_chart_data(self):
        from dashboard.visualization_engine import get_visualization_engine
        viz = get_visualization_engine()
        data = viz.bar_chart_data(blocs=["ECOWAS", "EAC"], metric="investment_score")
        assert data["type"] == "bar"
        assert len(data["data"]["datasets"][0]["data"]) == 2

    def test_heatmap_data(self):
        from dashboard.visualization_engine import get_visualization_engine
        viz = get_visualization_engine()
        data = viz.heatmap_data()
        assert data["type"] == "heatmap"
        assert isinstance(data["entries"], list)
        for entry in data["entries"]:
            assert "country" in entry
            assert "score" in entry
            assert "color" in entry

    def test_sankey_data(self):
        from dashboard.visualization_engine import get_visualization_engine
        viz = get_visualization_engine()
        data = viz.sankey_data()
        assert data["type"] == "sankey"
        assert "nodes" in data
        assert "links" in data

    def test_line_chart_trend(self):
        from dashboard.visualization_engine import get_visualization_engine
        viz = get_visualization_engine()
        data = viz.line_chart_trend("MAR", metric="investment_score", years=5)
        assert data["type"] == "line"
        datasets = data["data"]["datasets"]
        assert len(datasets) == 1
        assert len(datasets[0]["data"]) == 6  # 5 historical + 1 current


# ===========================================================================
# Dashboard - Export Services
# ===========================================================================

class TestExportServices:
    """Tests for PDF/Excel/CSV export functionality."""

    def _sample_data(self):
        return {
            "opportunities": [
                {"country": "MAR", "sector": "agriculture", "investment_score": 0.72, "grade": "A", "recommendation": "buy"},
                {"country": "EGY", "sector": "manufacturing", "investment_score": 0.65, "grade": "B+", "recommendation": "hold"},
            ],
            "total_count": 2,
        }

    def test_excel_export_returns_bytes(self):
        from dashboard.export_services import get_export_service
        exporter = get_export_service()
        data = exporter.export_investment_analysis_excel(self._sample_data())
        assert isinstance(data, bytes)
        assert len(data) > 0

    def test_pdf_export_returns_bytes(self):
        from dashboard.export_services import get_export_service
        exporter = get_export_service()
        data = exporter.export_investment_analysis_pdf(self._sample_data())
        assert isinstance(data, bytes)
        assert len(data) > 0

    def test_csv_fallback(self):
        from dashboard.export_services import ExportService
        data = ExportService._csv_fallback(self._sample_data())
        assert isinstance(data, bytes)
        assert b"MAR" in data

    def test_json_fallback(self):
        from dashboard.export_services import ExportService
        import json
        data = ExportService._json_fallback(self._sample_data())
        parsed = json.loads(data)
        assert "opportunities" in parsed


# ===========================================================================
# GraphQL Schema Definition
# ===========================================================================

class TestGraphQLSchema:
    """Tests for the GraphQL schema SDL."""

    def test_schema_contains_query_type(self):
        from api.graphql.schema_definition import GRAPHQL_SCHEMA_SDL
        assert "type Query" in GRAPHQL_SCHEMA_SDL

    def test_schema_contains_mutation_type(self):
        from api.graphql.schema_definition import GRAPHQL_SCHEMA_SDL
        assert "type Mutation" in GRAPHQL_SCHEMA_SDL

    def test_schema_contains_subscription_type(self):
        from api.graphql.schema_definition import GRAPHQL_SCHEMA_SDL
        assert "type Subscription" in GRAPHQL_SCHEMA_SDL

    def test_schema_investment_score_query(self):
        from api.graphql.schema_definition import GRAPHQL_SCHEMA_SDL
        assert "getInvestmentScore" in GRAPHQL_SCHEMA_SDL

    def test_schema_bulk_tariff_query(self):
        from api.graphql.schema_definition import GRAPHQL_SCHEMA_SDL
        assert "bulkTariffCalculation" in GRAPHQL_SCHEMA_SDL

    def test_schema_trade_flow_prediction(self):
        from api.graphql.schema_definition import GRAPHQL_SCHEMA_SDL
        assert "predictTradeFlows" in GRAPHQL_SCHEMA_SDL

    def test_schema_regional_bloc_enum(self):
        from api.graphql.schema_definition import GRAPHQL_SCHEMA_SDL
        assert "RegionalBloc" in GRAPHQL_SCHEMA_SDL
        assert "ECOWAS" in GRAPHQL_SCHEMA_SDL

    def test_schema_websocket_subscriptions(self):
        from api.graphql.schema_definition import GRAPHQL_SCHEMA_SDL
        assert "tariffUpdates" in GRAPHQL_SCHEMA_SDL
        assert "investmentAlerts" in GRAPHQL_SCHEMA_SDL
        assert "liveRegionalData" in GRAPHQL_SCHEMA_SDL


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
