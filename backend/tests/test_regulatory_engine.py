"""
Test Suite for Regulatory Engine v3 API
Tests the new regulatory engine integration with AfCFTA data for Algeria (DZA)
"""

import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://regulatory-db.preview.emergentagent.com').rstrip('/')


class TestRegulatoryEngineCountries:
    """Tests for /api/regulatory-engine/countries endpoint"""
    
    def test_get_countries_returns_success(self):
        """Verify the countries endpoint returns success"""
        response = requests.get(f"{BASE_URL}/api/regulatory-engine/countries")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] == True
        print(f"✅ Countries endpoint returns success")
    
    def test_get_countries_contains_dza(self):
        """Verify DZA (Algeria) is in the list of available countries"""
        response = requests.get(f"{BASE_URL}/api/regulatory-engine/countries")
        assert response.status_code == 200
        data = response.json()
        assert "countries" in data
        assert "DZA" in data["countries"]
        print(f"✅ DZA is in available countries: {data['countries']}")
    
    def test_get_countries_has_total(self):
        """Verify the total count is returned"""
        response = requests.get(f"{BASE_URL}/api/regulatory-engine/countries")
        assert response.status_code == 200
        data = response.json()
        assert "total" in data
        assert data["total"] >= 1  # At least DZA
        print(f"✅ Total countries: {data['total']}")


class TestRegulatoryEngineDetails:
    """Tests for /api/regulatory-engine/details endpoint"""
    
    def test_details_with_national_code(self):
        """Test fetching details with national code 0101101000"""
        response = requests.get(
            f"{BASE_URL}/api/regulatory-engine/details",
            params={"country": "DZA", "code": "0101101000"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] == True
        assert data["country_iso3"] == "DZA"
        assert data["code"] == "0101101000"
        assert data["hs6"] == "010110"
        print(f"✅ Successfully fetched details for national code 0101101000")
    
    def test_details_commodity_info(self):
        """Test that commodity info is returned correctly"""
        response = requests.get(
            f"{BASE_URL}/api/regulatory-engine/details",
            params={"country": "DZA", "code": "0101101000"}
        )
        assert response.status_code == 200
        data = response.json()
        commodity = data["commodity"]
        
        # Verify commodity structure
        assert "national_code" in commodity
        assert "hs6" in commodity
        assert "chapter" in commodity
        assert "category" in commodity
        assert "description_fr" in commodity
        
        assert commodity["national_code"] == "0101101000"
        assert commodity["hs6"] == "010110"
        assert commodity["chapter"] == "01"
        print(f"✅ Commodity info verified: {commodity['description_fr']}")
    
    def test_details_measures_structure(self):
        """Test that measures (tariff rates) are returned"""
        response = requests.get(
            f"{BASE_URL}/api/regulatory-engine/details",
            params={"country": "DZA", "code": "0101101000"}
        )
        assert response.status_code == 200
        data = response.json()
        measures = data["measures"]
        
        assert isinstance(measures, list)
        assert len(measures) >= 1  # At least customs duty
        
        # Check for expected measure types
        measure_codes = [m["code"] for m in measures]
        assert "D.D" in measure_codes  # Customs Duty
        assert "T.V.A" in measure_codes  # VAT
        print(f"✅ Measures structure verified: {measure_codes}")
    
    def test_details_measures_have_npf_and_zlecaf_rates(self):
        """Verify measures include both NPF and ZLECAf rates"""
        response = requests.get(
            f"{BASE_URL}/api/regulatory-engine/details",
            params={"country": "DZA", "code": "0101101000"}
        )
        assert response.status_code == 200
        data = response.json()
        
        dd_measure = next((m for m in data["measures"] if m["code"] == "D.D"), None)
        assert dd_measure is not None
        
        assert "rate_pct" in dd_measure  # NPF rate
        assert dd_measure["is_zlecaf_applicable"] == True
        assert "zlecaf_rate_pct" in dd_measure
        assert dd_measure["zlecaf_rate_pct"] == 0  # Duty exemption under AfCFTA
        print(f"✅ D.D rates: NPF={dd_measure['rate_pct']}%, ZLECAf={dd_measure['zlecaf_rate_pct']}%")
    
    def test_details_requirements(self):
        """Test that administrative requirements are returned"""
        response = requests.get(
            f"{BASE_URL}/api/regulatory-engine/details",
            params={"country": "DZA", "code": "0101101000"}
        )
        assert response.status_code == 200
        data = response.json()
        requirements = data["requirements"]
        
        assert isinstance(requirements, list)
        assert len(requirements) >= 1
        
        for req in requirements:
            assert "document_fr" in req
            assert "issuing_authority" in req
            assert "is_mandatory" in req
        
        print(f"✅ Requirements verified: {len(requirements)} documents required")
    
    def test_details_fiscal_advantages(self):
        """Test that fiscal advantages under AfCFTA are returned"""
        response = requests.get(
            f"{BASE_URL}/api/regulatory-engine/details",
            params={"country": "DZA", "code": "0101101000"}
        )
        assert response.status_code == 200
        data = response.json()
        fiscal_advantages = data["fiscal_advantages"]
        
        assert isinstance(fiscal_advantages, list)
        assert len(fiscal_advantages) >= 1
        
        dd_advantage = next((fa for fa in fiscal_advantages if fa["tax_code"] == "D.D"), None)
        assert dd_advantage is not None
        assert dd_advantage["reduced_rate_pct"] == 0
        print(f"✅ Fiscal advantage verified: {dd_advantage['condition_fr']}")
    
    def test_details_totals_and_savings(self):
        """Test that NPF total, ZLECAf total and savings are calculated"""
        response = requests.get(
            f"{BASE_URL}/api/regulatory-engine/details",
            params={"country": "DZA", "code": "0101101000"}
        )
        assert response.status_code == 200
        data = response.json()
        
        assert "total_npf_pct" in data
        assert "total_zlecaf_pct" in data
        assert "savings_pct" in data
        
        assert data["total_npf_pct"] >= 0
        assert data["total_zlecaf_pct"] >= 0
        assert data["savings_pct"] >= 0
        assert data["total_npf_pct"] >= data["total_zlecaf_pct"]  # NPF should be >= ZLECAf
        print(f"✅ Totals: NPF={data['total_npf_pct']}%, ZLECAf={data['total_zlecaf_pct']}%, Savings={data['savings_pct']}%")
    
    def test_details_processing_time(self):
        """Verify processing time is returned and reasonable (<100ms)"""
        response = requests.get(
            f"{BASE_URL}/api/regulatory-engine/details",
            params={"country": "DZA", "code": "0101101000"}
        )
        assert response.status_code == 200
        data = response.json()
        
        assert "processing_time_ms" in data
        assert data["processing_time_ms"] < 100  # Should be fast
        print(f"✅ Processing time: {data['processing_time_ms']}ms")


class TestRegulatoryEngineHS6Search:
    """Tests for HS6 search functionality"""
    
    def test_details_with_hs6_code(self):
        """Test fetching details with HS6 code 010110"""
        response = requests.get(
            f"{BASE_URL}/api/regulatory-engine/details",
            params={"country": "DZA", "code": "010110", "search_type": "hs6"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] == True
        assert data["hs6"] == "010110"
        print(f"✅ HS6 search successful for 010110")
    
    def test_get_all_sub_positions(self):
        """Test fetching all national sub-positions for an HS6"""
        response = requests.get(
            f"{BASE_URL}/api/regulatory-engine/details/all",
            params={"country": "DZA", "hs6": "010110"}
        )
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 1  # At least one sub-position
        print(f"✅ Found {len(data)} sub-positions for HS6 010110")


class TestRegulatoryEngineErrorHandling:
    """Tests for error handling"""
    
    def test_invalid_country(self):
        """Test that invalid country returns proper error"""
        response = requests.get(
            f"{BASE_URL}/api/regulatory-engine/details",
            params={"country": "XXX", "code": "0101101000"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] == False
        assert "error" in data
        print(f"✅ Invalid country handled correctly: {data['error']}")
    
    def test_invalid_code(self):
        """Test that invalid code returns proper error"""
        response = requests.get(
            f"{BASE_URL}/api/regulatory-engine/details",
            params={"country": "DZA", "code": "9999999999"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] == False
        assert "error" in data
        print(f"✅ Invalid code handled correctly: {data['error']}")


class TestRegulatoryEngineSummary:
    """Tests for country summary endpoint"""
    
    def test_country_summary(self):
        """Test fetching country summary for DZA"""
        response = requests.get(f"{BASE_URL}/api/regulatory-engine/summary/DZA")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] == True
        assert data["country_iso3"] == "DZA"
        assert "summary" in data
        print(f"✅ Country summary fetched for DZA")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
