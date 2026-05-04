"""
Test Multi-Country Comparison Feature
Tests the /api/ai/profile/{country} endpoint used by MultiCountryComparison component
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

class TestAIProfileEndpoint:
    """Tests for /api/ai/profile/{country} endpoint"""
    
    def test_profile_endpoint_returns_200(self):
        """Test that profile endpoint returns 200 for valid country"""
        response = requests.get(f"{BASE_URL}/api/ai/profile/Nigeria?lang=fr", timeout=60)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
    def test_profile_returns_economic_indicators(self):
        """Test that profile returns economic_indicators structure"""
        response = requests.get(f"{BASE_URL}/api/ai/profile/Nigeria?lang=fr", timeout=60)
        assert response.status_code == 200
        data = response.json()
        
        assert "economic_indicators" in data, "Missing economic_indicators"
        eco = data["economic_indicators"]
        
        # Check key economic fields
        assert "gdp_billion_usd" in eco, "Missing gdp_billion_usd"
        assert "gdp_per_capita_usd" in eco, "Missing gdp_per_capita_usd"
        assert "inflation_percent" in eco, "Missing inflation_percent"
        
    def test_profile_returns_trade_summary(self):
        """Test that profile returns trade_summary structure"""
        response = requests.get(f"{BASE_URL}/api/ai/profile/Nigeria?lang=fr", timeout=60)
        assert response.status_code == 200
        data = response.json()
        
        assert "trade_summary" in data, "Missing trade_summary"
        trade = data["trade_summary"]
        
        # Check key trade fields
        assert "total_exports_musd" in trade, "Missing total_exports_musd"
        assert "total_imports_musd" in trade, "Missing total_imports_musd"
        assert "trade_balance_musd" in trade, "Missing trade_balance_musd"
        
    def test_profile_returns_development_indices(self):
        """Test that profile returns development_indices structure"""
        response = requests.get(f"{BASE_URL}/api/ai/profile/Nigeria?lang=fr", timeout=60)
        assert response.status_code == 200
        data = response.json()
        
        assert "development_indices" in data, "Missing development_indices"
        dev = data["development_indices"]
        
        # Check HDI fields
        assert "hdi_score" in dev, "Missing hdi_score"
        assert "hdi_world_rank" in dev, "Missing hdi_world_rank"


class TestCountriesEndpoint:
    """Tests for /api/countries endpoint used by country selector"""
    
    def test_countries_endpoint_returns_200(self):
        """Test that countries endpoint returns 200"""
        response = requests.get(f"{BASE_URL}/api/countries?lang=fr", timeout=30)
        assert response.status_code == 200
        
    def test_countries_returns_list(self):
        """Test that countries returns a list of countries"""
        response = requests.get(f"{BASE_URL}/api/countries?lang=fr", timeout=30)
        assert response.status_code == 200
        data = response.json()
        
        # Should be a list
        assert isinstance(data, list), "Expected list of countries"
        assert len(data) >= 50, f"Expected at least 50 countries, got {len(data)}"
        
    def test_countries_have_required_fields(self):
        """Test that each country has required fields for selector"""
        response = requests.get(f"{BASE_URL}/api/countries?lang=fr", timeout=30)
        assert response.status_code == 200
        data = response.json()
        
        # Check first country has required fields
        country = data[0]
        assert "iso3" in country or "code" in country, "Missing iso3/code field"
        assert "name" in country, "Missing name field"


class TestStatisticsEndpoint:
    """Tests for /api/statistics endpoint used by StatisticsTab"""
    
    def test_statistics_endpoint_returns_200(self):
        """Test that statistics endpoint returns 200"""
        response = requests.get(f"{BASE_URL}/api/statistics", timeout=30)
        assert response.status_code == 200
        
    def test_statistics_returns_top_exporters(self):
        """Test that statistics returns top_exporters_2024"""
        response = requests.get(f"{BASE_URL}/api/statistics", timeout=30)
        assert response.status_code == 200
        data = response.json()
        
        assert "top_exporters_2024" in data, "Missing top_exporters_2024"
        exporters = data["top_exporters_2024"]
        assert isinstance(exporters, list), "top_exporters_2024 should be a list"
        assert len(exporters) >= 10, "Should have at least 10 top exporters"
        
    def test_statistics_returns_top_importers(self):
        """Test that statistics returns top_importers_2024"""
        response = requests.get(f"{BASE_URL}/api/statistics", timeout=30)
        assert response.status_code == 200
        data = response.json()
        
        assert "top_importers_2024" in data, "Missing top_importers_2024"
        importers = data["top_importers_2024"]
        assert isinstance(importers, list), "top_importers_2024 should be a list"
        assert len(importers) >= 10, "Should have at least 10 top importers"


class TestMultipleCountryProfiles:
    """Tests for fetching multiple country profiles (comparison scenario)"""
    
    def test_fetch_two_country_profiles(self):
        """Test fetching profiles for 2 countries (minimum for comparison)"""
        countries = ["Nigeria", "Kenya"]
        profiles = {}
        
        for country in countries:
            response = requests.get(f"{BASE_URL}/api/ai/profile/{country}?lang=fr", timeout=60)
            assert response.status_code == 200, f"Failed to fetch profile for {country}"
            profiles[country] = response.json()
            
        # Verify both have required data
        for country, data in profiles.items():
            assert "economic_indicators" in data, f"{country} missing economic_indicators"
            assert "trade_summary" in data, f"{country} missing trade_summary"
            
    def test_profile_data_is_comparable(self):
        """Test that profile data can be compared (same structure)"""
        response1 = requests.get(f"{BASE_URL}/api/ai/profile/Nigeria?lang=fr", timeout=60)
        response2 = requests.get(f"{BASE_URL}/api/ai/profile/Kenya?lang=fr", timeout=60)
        
        assert response1.status_code == 200
        assert response2.status_code == 200
        
        data1 = response1.json()
        data2 = response2.json()
        
        # Both should have same top-level keys
        keys1 = set(data1.keys())
        keys2 = set(data2.keys())
        
        # Check common required keys exist in both
        required_keys = {"economic_indicators", "trade_summary", "development_indices"}
        assert required_keys.issubset(keys1), f"Nigeria missing keys: {required_keys - keys1}"
        assert required_keys.issubset(keys2), f"Kenya missing keys: {required_keys - keys2}"


class TestProfileEnglishLanguage:
    """Tests for profile endpoint with English language"""
    
    def test_profile_english_returns_200(self):
        """Test profile endpoint with lang=en"""
        response = requests.get(f"{BASE_URL}/api/ai/profile/Nigeria?lang=en", timeout=60)
        assert response.status_code == 200
        
    def test_profile_english_has_data(self):
        """Test profile endpoint returns data in English"""
        response = requests.get(f"{BASE_URL}/api/ai/profile/Nigeria?lang=en", timeout=60)
        assert response.status_code == 200
        data = response.json()
        
        assert "economic_indicators" in data
        assert "trade_summary" in data


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
