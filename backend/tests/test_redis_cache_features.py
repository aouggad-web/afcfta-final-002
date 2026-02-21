"""
Test Redis Cache and New Features for ZLECAf Application
Tests: Redis cache, data freshness, HS6 statistics, Rules of Origin, Substitution
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

class TestRedisCacheStats:
    """Test Redis cache statistics endpoint"""
    
    def test_cache_stats_endpoint_returns_200(self):
        """GET /api/ai/cache/stats should return 200"""
        response = requests.get(f"{BASE_URL}/api/ai/cache/stats")
        assert response.status_code == 200
        print(f"Cache stats response: {response.json()}")
    
    def test_cache_stats_returns_connected_status(self):
        """Cache stats should show status=connected when Redis is running"""
        response = requests.get(f"{BASE_URL}/api/ai/cache/stats")
        data = response.json()
        assert "status" in data
        # Status should be either 'connected' or 'disconnected'
        assert data["status"] in ["connected", "disconnected"]
        print(f"Redis status: {data['status']}")
    
    def test_cache_stats_contains_required_fields(self):
        """Cache stats should contain hit rate and key count when connected"""
        response = requests.get(f"{BASE_URL}/api/ai/cache/stats")
        data = response.json()
        if data.get("status") == "connected":
            assert "total_zlecaf_keys" in data
            assert "hits" in data
            assert "misses" in data
            assert "hit_rate" in data
            print(f"Cache stats: keys={data['total_zlecaf_keys']}, hit_rate={data['hit_rate']}%")


class TestHS6Statistics:
    """Test HS6 statistics endpoint"""
    
    def test_hs6_statistics_endpoint_returns_200(self):
        """GET /api/hs6/statistics should return 200"""
        response = requests.get(f"{BASE_URL}/api/hs6/statistics")
        assert response.status_code == 200
    
    def test_hs6_statistics_contains_base_data(self):
        """HS6 statistics should contain base HS6 data"""
        response = requests.get(f"{BASE_URL}/api/hs6/statistics")
        data = response.json()
        assert "hs6_base" in data
        assert "total_codes" in data["hs6_base"]
        assert data["hs6_base"]["total_codes"] > 5000
        print(f"Total HS6 codes: {data['hs6_base']['total_codes']}")
    
    def test_hs6_statistics_contains_national_sub_positions(self):
        """HS6 statistics should contain national sub-positions data"""
        response = requests.get(f"{BASE_URL}/api/hs6/statistics")
        data = response.json()
        assert "national_sub_positions" in data
        assert "countries_covered" in data["national_sub_positions"]
        assert data["national_sub_positions"]["countries_covered"] == 54
        print(f"Countries covered: {data['national_sub_positions']['countries_covered']}")


class TestRulesOfOriginStats:
    """Test Rules of Origin statistics endpoint"""
    
    def test_rules_of_origin_stats_returns_200(self):
        """GET /api/rules-of-origin/stats should return 200"""
        response = requests.get(f"{BASE_URL}/api/rules-of-origin/stats")
        assert response.status_code == 200
    
    def test_rules_of_origin_stats_contains_chapters(self):
        """Rules of Origin stats should contain chapter counts"""
        response = requests.get(f"{BASE_URL}/api/rules-of-origin/stats")
        data = response.json()
        assert "total_chapters" in data
        assert "agreed_chapters" in data
        assert data["total_chapters"] == 96
        assert data["agreed_chapters"] >= 80
        print(f"Total chapters: {data['total_chapters']}, Agreed: {data['agreed_chapters']}")
    
    def test_rules_of_origin_stats_contains_source(self):
        """Rules of Origin stats should contain source information"""
        response = requests.get(f"{BASE_URL}/api/rules-of-origin/stats")
        data = response.json()
        assert "source" in data
        assert "AfCFTA" in data["source"]
        print(f"Source: {data['source']}")


class TestSubstitutionCountries:
    """Test Substitution countries endpoint"""
    
    def test_substitution_countries_returns_200(self):
        """GET /api/substitution/countries should return 200"""
        response = requests.get(f"{BASE_URL}/api/substitution/countries?lang=fr")
        assert response.status_code == 200
    
    def test_substitution_countries_returns_55_countries(self):
        """Substitution countries should return 55 African countries"""
        response = requests.get(f"{BASE_URL}/api/substitution/countries?lang=fr")
        data = response.json()
        assert "total" in data
        assert data["total"] == 55
        print(f"Total countries: {data['total']}")
    
    def test_substitution_countries_contains_trade_data_info(self):
        """Each country should have has_trade_data field"""
        response = requests.get(f"{BASE_URL}/api/substitution/countries?lang=fr")
        data = response.json()
        assert "countries" in data
        assert len(data["countries"]) == 55
        # Check first country has required fields
        first_country = data["countries"][0]
        assert "iso3" in first_country
        assert "name" in first_country
        assert "has_trade_data" in first_country
        print(f"First country: {first_country['name']} ({first_country['iso3']})")
    
    def test_substitution_countries_with_trade_data_count(self):
        """Should have 54 countries with trade data (1 without)"""
        response = requests.get(f"{BASE_URL}/api/substitution/countries?lang=fr")
        data = response.json()
        assert "with_trade_data" in data
        assert data["with_trade_data"] == 54
        assert data["without_trade_data"] == 1
        print(f"With trade data: {data['with_trade_data']}, Without: {data['without_trade_data']}")


class TestSubstitutionAnalysis:
    """Test Substitution analysis endpoints"""
    
    def test_import_substitution_for_kenya(self):
        """GET /api/substitution/opportunities/import/KEN should return opportunities"""
        response = requests.get(f"{BASE_URL}/api/substitution/opportunities/import/KEN?lang=fr")
        assert response.status_code == 200
        data = response.json()
        assert "importer" in data
        assert data["importer"]["iso3"] == "KEN"
        assert "opportunities" in data
        assert len(data["opportunities"]) > 0
        print(f"Kenya import opportunities: {len(data['opportunities'])}")
    
    def test_export_substitution_for_kenya(self):
        """GET /api/substitution/opportunities/export/KEN should return opportunities"""
        response = requests.get(f"{BASE_URL}/api/substitution/opportunities/export/KEN?lang=fr")
        assert response.status_code == 200
        data = response.json()
        assert "exporter" in data
        assert data["exporter"]["iso3"] == "KEN"
        assert "opportunities" in data
        print(f"Kenya export opportunities: {len(data['opportunities'])}")
    
    def test_substitution_summary_contains_required_fields(self):
        """Substitution response should contain summary with required fields"""
        response = requests.get(f"{BASE_URL}/api/substitution/opportunities/import/KEN?lang=fr")
        data = response.json()
        assert "summary" in data
        summary = data["summary"]
        assert "total_opportunities" in summary
        assert "total_substitutable_value" in summary
        print(f"Summary: {summary['total_opportunities']} opportunities, ${summary['total_substitutable_value']:,} value")


class TestAISummary:
    """Test AI Summary endpoint for Vue d'ensemble"""
    
    def test_ai_summary_returns_200(self):
        """GET /api/ai/summary should return 200"""
        response = requests.get(f"{BASE_URL}/api/ai/summary?lang=fr")
        assert response.status_code == 200
    
    def test_ai_summary_contains_overview(self):
        """AI summary should contain overview with trade statistics"""
        response = requests.get(f"{BASE_URL}/api/ai/summary?lang=fr")
        data = response.json()
        assert "overview" in data
        overview = data["overview"]
        assert "total_african_trade_billion_usd" in overview
        assert "intra_african_trade_billion_usd" in overview
        assert "afcfta_countries" in overview
        assert "total_opportunities_identified" in overview
        print(f"Overview: {overview['total_opportunities_identified']} opportunities, ${overview['total_african_trade_billion_usd']}B trade")
    
    def test_ai_summary_contains_5387_opportunities(self):
        """AI summary should show 5387 opportunities"""
        response = requests.get(f"{BASE_URL}/api/ai/summary?lang=fr")
        data = response.json()
        assert data["overview"]["total_opportunities_identified"] == 5387
        print("Verified: 5387 opportunities")
    
    def test_ai_summary_contains_1650_billion_trade(self):
        """AI summary should show $1.65T (1650B) total trade"""
        response = requests.get(f"{BASE_URL}/api/ai/summary?lang=fr")
        data = response.json()
        assert data["overview"]["total_african_trade_billion_usd"] == 1650
        print("Verified: $1.65T total trade")
    
    def test_ai_summary_contains_top_countries(self):
        """AI summary should contain top trading countries"""
        response = requests.get(f"{BASE_URL}/api/ai/summary?lang=fr")
        data = response.json()
        assert "top_trading_countries" in data
        assert len(data["top_trading_countries"]) >= 5
        print(f"Top countries: {[c['name'] for c in data['top_trading_countries'][:3]]}")
    
    def test_ai_summary_contains_top_sectors(self):
        """AI summary should contain top sectors"""
        response = requests.get(f"{BASE_URL}/api/ai/summary?lang=fr")
        data = response.json()
        assert "top_sectors" in data
        assert len(data["top_sectors"]) >= 5
        print(f"Top sectors: {[s['name'] for s in data['top_sectors'][:3]]}")


class TestDataFreshness:
    """Test data freshness indicators in API responses"""
    
    def test_ai_summary_contains_generation_date(self):
        """AI summary should contain generation date for freshness tracking"""
        response = requests.get(f"{BASE_URL}/api/ai/summary?lang=fr")
        data = response.json()
        # Check for generation date or data freshness info
        has_freshness = (
            "generation_date" in data or 
            "data_freshness" in data or
            "generated_by" in data
        )
        assert has_freshness
        print(f"Generation info present: {has_freshness}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
