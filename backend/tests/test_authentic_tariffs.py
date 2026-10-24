"""
Test Suite for Authentic Tariff APIs
Tests the new authentic tariff endpoints with real JSON data from African countries
"""

import os

import pytest
import requests

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "").rstrip("/")


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
        assert (
            len(found_countries) >= 5
        ), f"Expected at least 5 major countries, found: {found_countries}"


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


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
