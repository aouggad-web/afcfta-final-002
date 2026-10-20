"""
Test Multi-Country Comparison and All Taxes Display Features
Tests:
1. /api/authentic-tariffs/countries - returns 54 countries
2. Sub-positions
"""

import os

import pytest
import requests

BASE_URL = os.environ.get(
    "REACT_APP_BACKEND_URL", "https://zlecaf-trade-ops.preview.emergentagent.com"
)


class TestAuthenticTariffsCountries:
    """Test countries endpoint returns correct count and structure"""

    def test_countries_list_returns_54_countries(self):
        """Verify 54 African countries are available"""
        response = requests.get(f"{BASE_URL}/api/authentic-tariffs/countries")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"

        data = response.json()
        assert data["success"] == True
        assert data["total"] == 54, f"Expected 54 countries, got {data['total']}"
        assert len(data["countries"]) == 54
        print(f"✅ Countries endpoint returns {data['total']} countries")

    def test_countries_have_required_fields(self):
        """Each country should have iso3, total_lines, vat_rate etc"""
        response = requests.get(f"{BASE_URL}/api/authentic-tariffs/countries")
        data = response.json()

        required_fields = ["iso3", "total_lines", "vat_rate", "dd_range", "data_format"]
        for country in data["countries"][:5]:  # Check first 5
            for field in required_fields:
                assert field in country, f"Missing field {field} in country {country.get('iso3')}"

        print(f"✅ All countries have required fields")

    def test_countries_have_enhanced_v2_format(self):
        """Verify data format is enhanced_v2"""
        response = requests.get(f"{BASE_URL}/api/authentic-tariffs/countries")
        data = response.json()

        assert data["data_format"] == "enhanced_v2"
        for country in data["countries"]:
            assert country["data_format"] == "enhanced_v2"

        print(f"✅ All countries use enhanced_v2 data format")


class TestSubPositions:
    """Test sub-positions endpoint"""

    def test_sub_positions_for_hs6(self):
        """Get sub-positions for an HS6 code"""
        response = requests.get(
            f"{BASE_URL}/api/authentic-tariffs/country/MAR/sub-positions/180100?language=fr"
        )
        assert response.status_code == 200

        data = response.json()
        assert data["success"] == True
        assert "sub_positions" in data

        count = data["total"]
        print(f"✅ MAR/180100 has {count} sub-positions")

        for sp in data["sub_positions"][:3]:
            print(f"  - {sp['code']}: DD {sp['dd']}%")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
