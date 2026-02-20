"""
Test Suite for Authentic Tariff APIs
Tests the new authentic tariff endpoints with real JSON data from African countries
"""

import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')


class TestAuthenticTariffsCountriesList:
    """Test /api/authentic-tariffs/countries - Liste des pays avec données authentiques"""
    
    def test_countries_list_success(self):
        """Should return list of countries with authentic tariff data"""
        response = requests.get(f"{BASE_URL}/api/authentic-tariffs/countries")
        assert response.status_code == 200
        
        data = response.json()
        assert data["success"] == True
        assert "countries" in data
        assert "total" in data
        assert data["total"] >= 49, f"Expected at least 49 countries, got {data['total']}"
        assert data["data_format"] == "enhanced_v2"
        
    def test_countries_list_structure(self):
        """Each country should have required fields"""
        response = requests.get(f"{BASE_URL}/api/authentic-tariffs/countries")
        data = response.json()
        
        assert len(data["countries"]) >= 49
        
        # Check first country structure
        country = data["countries"][0]
        required_fields = ["iso3", "total_lines", "vat_rate", "data_format"]
        for field in required_fields:
            assert field in country, f"Missing field: {field}"
            
    def test_countries_include_major_african_nations(self):
        """Should include major African nations like MAR, NGA, EGY"""
        response = requests.get(f"{BASE_URL}/api/authentic-tariffs/countries")
        data = response.json()
        
        country_codes = [c["iso3"] for c in data["countries"]]
        major_countries = ["MAR", "NGA", "EGY", "ZAF", "KEN", "GHA", "ETH", "DZA"]
        
        # Note: Some countries might be named differently (ETH might not be in data)
        found_countries = [c for c in major_countries if c in country_codes]
        assert len(found_countries) >= 5, f"Expected at least 5 major countries, found: {found_countries}"


class TestAuthenticTariffsCalculate:
    """Test /api/authentic-tariffs/calculate/{country}/{hs_code} - Calcul détaillé"""
    
    def test_calculate_tariff_mar_cacao(self):
        """Test calculation for Morocco, cacao (HS 180100), value 50000 USD"""
        response = requests.get(
            f"{BASE_URL}/api/authentic-tariffs/calculate/MAR/180100?value=50000&language=fr"
        )
        assert response.status_code == 200
        
        data = response.json()
        # Verify structure
        assert "hs_code" in data
        assert "description" in data
        assert "cif_value" in data
        assert data["cif_value"] == 50000
        
        # Verify NPF calculation
        assert "npf_calculation" in data
        npf = data["npf_calculation"]
        assert "dd" in npf
        assert "vat" in npf
        assert "total_to_pay" in npf
        
        # Verify ZLECAf calculation
        assert "zlecaf_calculation" in data
        zlecaf = data["zlecaf_calculation"]
        assert zlecaf["dd"]["exempt"] == True
        assert zlecaf["dd"]["amount"] == 0
        
        # Verify savings
        assert "savings" in data
        assert data["savings"]["amount"] > 0, "ZLECAf should provide savings"
        
    def test_calculate_tariff_nga(self):
        """Test calculation for Nigeria"""
        response = requests.get(
            f"{BASE_URL}/api/authentic-tariffs/calculate/NGA/870323?value=10000&language=fr"
        )
        assert response.status_code == 200
        
        data = response.json()
        assert data["country_iso3"] == "NGA"
        assert "npf_calculation" in data
        assert "zlecaf_calculation" in data
        
    def test_calculate_tariff_egy(self):
        """Test calculation for Egypt"""
        response = requests.get(
            f"{BASE_URL}/api/authentic-tariffs/calculate/EGY/100199?value=25000&language=en"
        )
        assert response.status_code == 200
        
        data = response.json()
        assert data["country_iso3"] == "EGY"
        assert data["currency"] == "USD"
        
    def test_calculate_tariff_nonexistent_country(self):
        """Should return 404 for non-existent country"""
        response = requests.get(
            f"{BASE_URL}/api/authentic-tariffs/calculate/XXX/180100?value=1000"
        )
        assert response.status_code == 404
        
    def test_calculate_tariff_catch_all_hs_code(self):
        """Code 999999 is valid - it's a catch-all 'Commodities not specified' category"""
        response = requests.get(
            f"{BASE_URL}/api/authentic-tariffs/calculate/MAR/999999?value=1000"
        )
        # 999999 actually exists as a catch-all category
        assert response.status_code == 200
        data = response.json()
        assert "not specified" in data["description"].lower() or "commodities" in data["description"].lower()


class TestAuthenticTariffsCountrySummary:
    """Test /api/authentic-tariffs/country/{country}/summary - Résumé du pays"""
    
    def test_country_summary_mar(self):
        """Test Morocco summary"""
        response = requests.get(f"{BASE_URL}/api/authentic-tariffs/country/MAR/summary")
        assert response.status_code == 200
        
        data = response.json()
        assert data["success"] == True
        assert data["country_iso3"] == "MAR"
        assert "summary" in data
        
        summary = data["summary"]
        assert "total_tariff_lines" in summary
        assert summary["total_tariff_lines"] > 0
        assert "vat_rate_pct" in summary
        
    def test_country_summary_nga(self):
        """Test Nigeria summary"""
        response = requests.get(f"{BASE_URL}/api/authentic-tariffs/country/NGA/summary")
        assert response.status_code == 200
        
        data = response.json()
        assert data["country_iso3"] == "NGA"
        
    def test_country_summary_nonexistent(self):
        """Should return 404 for non-existent country"""
        response = requests.get(f"{BASE_URL}/api/authentic-tariffs/country/XXX/summary")
        assert response.status_code == 404


class TestAuthenticTariffsSearch:
    """Test /api/authentic-tariffs/search/{country}?q=query - Recherche"""
    
    def test_search_cacao_mar(self):
        """Search for 'cacao' in Morocco tariffs"""
        response = requests.get(
            f"{BASE_URL}/api/authentic-tariffs/search/MAR?q=cacao&language=fr"
        )
        assert response.status_code == 200
        
        data = response.json()
        assert data["success"] == True
        assert data["country_iso3"] == "MAR"
        assert "results" in data
        assert len(data["results"]) > 0, "Should find cacao products"
        
    def test_search_by_hs_code(self):
        """Search by partial HS code"""
        response = requests.get(
            f"{BASE_URL}/api/authentic-tariffs/search/NGA?q=1801&language=en"
        )
        assert response.status_code == 200
        
        data = response.json()
        assert len(data["results"]) > 0
        
    def test_search_min_query_length(self):
        """Query must be at least 2 characters"""
        response = requests.get(
            f"{BASE_URL}/api/authentic-tariffs/search/MAR?q=a"
        )
        # FastAPI validates min_length=2
        assert response.status_code == 422


class TestAuthenticTariffsSubPositions:
    """Test /api/authentic-tariffs/country/{country}/sub-positions/{hs6}"""
    
    def test_get_sub_positions_mar(self):
        """Get sub-positions for HS6 code in Morocco"""
        response = requests.get(
            f"{BASE_URL}/api/authentic-tariffs/country/MAR/sub-positions/180100?language=fr"
        )
        assert response.status_code == 200
        
        data = response.json()
        assert data["success"] == True
        assert data["hs6"] == "180100"
        assert "sub_positions" in data


class TestAuthenticTariffsTaxesDetail:
    """Test /api/authentic-tariffs/country/{country}/taxes/{hs_code}"""
    
    def test_get_taxes_detail(self):
        """Get tax details for a product"""
        response = requests.get(
            f"{BASE_URL}/api/authentic-tariffs/country/NGA/taxes/870323?language=fr"
        )
        assert response.status_code == 200
        
        data = response.json()
        assert data["success"] == True
        assert "taxes" in data


class TestAuthenticTariffsAdvantages:
    """Test /api/authentic-tariffs/country/{country}/advantages/{hs_code}"""
    
    def test_get_fiscal_advantages(self):
        """Get fiscal advantages including ZLECAf for a product"""
        response = requests.get(
            f"{BASE_URL}/api/authentic-tariffs/country/EGY/advantages/180100?language=fr"
        )
        assert response.status_code == 200
        
        data = response.json()
        assert data["success"] == True
        assert "advantages" in data


class TestAuthenticTariffsTariffLine:
    """Test /api/authentic-tariffs/country/{country}/line/{hs_code}"""
    
    def test_get_tariff_line(self):
        """Get complete tariff line with all details"""
        response = requests.get(
            f"{BASE_URL}/api/authentic-tariffs/country/MAR/line/180100?language=fr"
        )
        assert response.status_code == 200
        
        data = response.json()
        assert data["success"] == True
        assert "tariff_line" in data
        
        tariff_line = data["tariff_line"]
        assert "hs6" in tariff_line
        assert "dd_rate" in tariff_line


class TestAuthenticTariffsSavingsCalculation:
    """Test that ZLECAf savings are calculated correctly"""
    
    def test_savings_calculation_correct(self):
        """Verify savings = NPF total - ZLECAf total"""
        response = requests.get(
            f"{BASE_URL}/api/authentic-tariffs/calculate/MAR/180100?value=100000&language=fr"
        )
        assert response.status_code == 200
        
        data = response.json()
        npf_total = data["npf_calculation"]["total_to_pay"]
        zlecaf_total = data["zlecaf_calculation"]["total_to_pay"]
        savings = data["savings"]["amount"]
        
        # Savings should be NPF - ZLECAf
        expected_savings = round(npf_total - zlecaf_total, 2)
        assert abs(savings - expected_savings) < 0.01, f"Savings mismatch: {savings} vs {expected_savings}"
        
    def test_zlecaf_dd_is_zero(self):
        """ZLECAf should exempt customs duties (DD)"""
        response = requests.get(
            f"{BASE_URL}/api/authentic-tariffs/calculate/GHA/870323?value=50000"
        )
        assert response.status_code == 200
        
        data = response.json()
        zlecaf_dd = data["zlecaf_calculation"]["dd"]
        assert zlecaf_dd["exempt"] == True
        assert zlecaf_dd["amount"] == 0


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
