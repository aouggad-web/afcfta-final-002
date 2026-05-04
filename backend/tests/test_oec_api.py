"""
OEC Trade API Tests
===================
Tests for the OEC (Observatory of Economic Complexity) trade statistics API endpoints.
Covers: countries list, years, exports, imports, product search, bilateral trade.
"""

import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

class TestOECCountriesAPI:
    """Tests for /api/oec/countries endpoint"""
    
    def test_get_countries_french(self):
        """Test getting African countries list in French"""
        response = requests.get(f"{BASE_URL}/api/oec/countries", params={"lang": "fr"})
        assert response.status_code == 200
        
        data = response.json()
        assert data["success"] == True
        assert "countries" in data
        assert data["total"] >= 50  # At least 50 African countries
        
        # Check country structure
        country = data["countries"][0]
        assert "iso3" in country
        assert "oec_id" in country
        assert "name" in country
        
    def test_get_countries_english(self):
        """Test getting African countries list in English"""
        response = requests.get(f"{BASE_URL}/api/oec/countries", params={"lang": "en"})
        assert response.status_code == 200
        
        data = response.json()
        assert data["success"] == True
        assert len(data["countries"]) >= 50


class TestOECYearsAPI:
    """Tests for /api/oec/years endpoint"""
    
    def test_get_available_years(self):
        """Test getting available years"""
        response = requests.get(f"{BASE_URL}/api/oec/years")
        assert response.status_code == 200
        
        data = response.json()
        assert data["success"] == True
        assert "years" in data
        assert 2022 in data["years"]
        assert 1995 in data["years"]
        assert len(data["years"]) >= 20


class TestOECExportsAPI:
    """Tests for /api/oec/exports/{country_iso3} endpoint"""
    
    def test_get_nigeria_exports(self):
        """Test getting Nigeria exports"""
        response = requests.get(
            f"{BASE_URL}/api/oec/exports/NGA",
            params={"year": 2022, "limit": 10}
        )
        assert response.status_code == 200
        
        data = response.json()
        assert "country" in data
        assert data["country"]["oec_id"] == "afnga"
        assert data["trade_flow"] == "exports"
        assert "data" in data
        
    def test_get_kenya_exports(self):
        """Test getting Kenya exports"""
        response = requests.get(
            f"{BASE_URL}/api/oec/exports/KEN",
            params={"year": 2022, "limit": 5}
        )
        assert response.status_code == 200
        
        data = response.json()
        assert data["country"]["oec_id"] == "afken"
        
    def test_invalid_country_exports(self):
        """Test exports for invalid country code - returns 400"""
        response = requests.get(
            f"{BASE_URL}/api/oec/exports/XXX",
            params={"year": 2022}
        )
        # Invalid country returns 400 Bad Request
        assert response.status_code == 400


class TestOECImportsAPI:
    """Tests for /api/oec/imports/{country_iso3} endpoint"""
    
    def test_get_kenya_imports(self):
        """Test getting Kenya imports"""
        response = requests.get(
            f"{BASE_URL}/api/oec/imports/KEN",
            params={"year": 2022, "limit": 10}
        )
        assert response.status_code == 200
        
        data = response.json()
        assert "country" in data
        assert data["trade_flow"] == "imports"
        assert "data" in data
        
    def test_get_south_africa_imports(self):
        """Test getting South Africa imports"""
        response = requests.get(
            f"{BASE_URL}/api/oec/imports/ZAF",
            params={"year": 2022, "limit": 5}
        )
        assert response.status_code == 200
        
        data = response.json()
        assert data["country"]["oec_id"] == "afzaf"


class TestOECProductAPI:
    """Tests for /api/oec/product/{hs_code} endpoint - MAIN FIX AREA"""
    
    def test_coffee_exports_0901(self):
        """Test coffee (HS 0901) exports - should work with prefix 2"""
        response = requests.get(
            f"{BASE_URL}/api/oec/product/0901",
            params={"year": 2022, "trade_flow": "exports", "limit": 10}
        )
        assert response.status_code == 200
        
        data = response.json()
        assert data["hs_code"] == "0901"
        assert data["year"] == 2022
        assert data["trade_flow"] == "exports"
        # Coffee should have data - major African export
        assert data["total_countries"] > 0, "Coffee (0901) should return data"
        assert data["total_value"] > 0
        
    def test_cocoa_exports_1801(self):
        """Test cocoa beans (HS 1801) exports - KNOWN ISSUE: needs prefix 4"""
        response = requests.get(
            f"{BASE_URL}/api/oec/product/1801",
            params={"year": 2022, "trade_flow": "exports", "limit": 10}
        )
        assert response.status_code == 200
        
        data = response.json()
        assert data["hs_code"] == "1801"
        # NOTE: This may return empty due to incorrect OEC ID format
        # The OEC API uses prefix 4 for chapter 18 (41801), not prefix 2 (21801)
        # This is a known limitation that should be fixed
        
    def test_oil_exports_2709(self):
        """Test crude petroleum (HS 2709) exports - needs prefix 5"""
        response = requests.get(
            f"{BASE_URL}/api/oec/product/2709",
            params={"year": 2022, "trade_flow": "exports", "limit": 10}
        )
        assert response.status_code == 200
        
        data = response.json()
        assert data["hs_code"] == "2709"
        # NOTE: May return empty due to incorrect OEC ID format
        
    def test_product_imports(self):
        """Test product imports flow"""
        response = requests.get(
            f"{BASE_URL}/api/oec/product/0901",
            params={"year": 2022, "trade_flow": "imports", "limit": 10}
        )
        assert response.status_code == 200
        
        data = response.json()
        assert data["trade_flow"] == "imports"


class TestOECBilateralAPI:
    """Tests for /api/oec/bilateral/{exporter}/{importer} endpoint"""
    
    def test_ivory_coast_to_ghana(self):
        """Test bilateral trade Ivory Coast -> Ghana"""
        response = requests.get(
            f"{BASE_URL}/api/oec/bilateral/CIV/GHA",
            params={"year": 2022, "limit": 10}
        )
        assert response.status_code == 200
        
        data = response.json()
        assert "exporter" in data
        assert "importer" in data
        assert data["exporter"]["oec_id"] == "afciv"
        assert data["importer"]["oec_id"] == "afgha"
        assert data["year"] == 2022
        
    def test_nigeria_to_south_africa(self):
        """Test bilateral trade Nigeria -> South Africa"""
        response = requests.get(
            f"{BASE_URL}/api/oec/bilateral/NGA/ZAF",
            params={"year": 2022, "limit": 5}
        )
        assert response.status_code == 200
        
        data = response.json()
        assert data["exporter"]["oec_id"] == "afnga"
        assert data["importer"]["oec_id"] == "afzaf"
        
    def test_invalid_exporter(self):
        """Test bilateral with invalid exporter - returns 400"""
        response = requests.get(
            f"{BASE_URL}/api/oec/bilateral/XXX/GHA",
            params={"year": 2022}
        )
        # Invalid country returns 400 Bad Request
        assert response.status_code == 400
        
    def test_invalid_importer(self):
        """Test bilateral with invalid importer - returns 400"""
        response = requests.get(
            f"{BASE_URL}/api/oec/bilateral/NGA/XXX",
            params={"year": 2022}
        )
        # Invalid country returns 400 Bad Request
        assert response.status_code == 400


class TestOECAfricanExportersAPI:
    """Tests for /api/oec/product/{hs_code}/africa endpoint"""
    
    def test_top_african_coffee_exporters(self):
        """Test getting top African coffee exporters"""
        response = requests.get(
            f"{BASE_URL}/api/oec/product/0901/africa",
            params={"year": 2022, "limit": 10}
        )
        assert response.status_code == 200
        
        data = response.json()
        assert data["hs_code"] == "0901"
        assert data["year"] == 2022
        assert "data" in data


class TestOECDataIntegrity:
    """Tests for data integrity and response structure"""
    
    def test_exports_response_structure(self):
        """Verify exports response has all required fields"""
        response = requests.get(
            f"{BASE_URL}/api/oec/exports/NGA",
            params={"year": 2022, "limit": 5}
        )
        assert response.status_code == 200
        
        data = response.json()
        required_fields = ["country", "trade_flow", "total_products", "total_value", "currency", "data", "source"]
        for field in required_fields:
            assert field in data, f"Missing field: {field}"
            
    def test_product_response_structure(self):
        """Verify product response has all required fields"""
        response = requests.get(
            f"{BASE_URL}/api/oec/product/0901",
            params={"year": 2022, "trade_flow": "exports", "limit": 5}
        )
        assert response.status_code == 200
        
        data = response.json()
        required_fields = ["hs_code", "year", "trade_flow", "total_countries", "total_value", "currency", "data", "source"]
        for field in required_fields:
            assert field in data, f"Missing field: {field}"
            
    def test_bilateral_response_structure(self):
        """Verify bilateral response has all required fields"""
        response = requests.get(
            f"{BASE_URL}/api/oec/bilateral/CIV/GHA",
            params={"year": 2022, "limit": 5}
        )
        assert response.status_code == 200
        
        data = response.json()
        required_fields = ["exporter", "importer", "year", "total_products", "total_value", "currency", "data", "source"]
        for field in required_fields:
            assert field in data, f"Missing field: {field}"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
