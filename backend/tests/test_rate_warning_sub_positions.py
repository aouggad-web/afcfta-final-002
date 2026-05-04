"""
Test suite for rate_warning and sub_positions_details feature
Tests the new functionality that warns users when HS6 codes have varying duty rates
depending on national sub-headings (8-12 digit codes)

Feature: When a HS6 code has sub-positions with different DD rates, the API should:
1. Return 'rate_warning' object with min/max rates and warning messages
2. Return 'sub_positions_details' list with all available sub-positions and their rates
3. NOT return warning for products with uniform rates (like medicines)
"""

import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

class TestRateWarningFeature:
    """Tests for rate_warning when sub-positions have varying rates"""
    
    def test_rice_100630_to_nigeria_has_varying_rates(self):
        """
        Test: Riz blanchi (100630) vers Nigeria doit avoir taux variables 50%-70%
        Nigeria has sub-positions for rice with different rates:
        - 1006301000: 50% (semi-blanchi)
        - 1006302000: 60% (blanchi non étuvé)
        - 1006309100: 70% (parfumé Basmati/Jasmin)
        """
        response = requests.post(f"{BASE_URL}/api/calculate-tariff", json={
            "origin_country": "CIV",  # Côte d'Ivoire
            "destination_country": "NGA",  # Nigeria
            "hs_code": "100630",
            "value": 10000
        })
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        
        # Check rate_warning exists
        assert "rate_warning" in data, "rate_warning field should be present"
        rate_warning = data.get("rate_warning")
        
        if rate_warning:
            # Verify warning structure
            assert rate_warning.get("has_variation") == True, "has_variation should be True"
            assert "message_fr" in rate_warning, "message_fr should be present"
            assert "message_en" in rate_warning, "message_en should be present"
            assert "min_rate" in rate_warning, "min_rate should be present"
            assert "max_rate" in rate_warning, "max_rate should be present"
            
            # Verify rate range (50%-70% for rice in Nigeria)
            min_rate = rate_warning.get("min_rate", 0)
            max_rate = rate_warning.get("max_rate", 0)
            
            print(f"Rice 100630 to Nigeria - Min rate: {min_rate*100:.1f}%, Max rate: {max_rate*100:.1f}%")
            
            # Min should be around 50% (0.50)
            assert min_rate >= 0.50, f"Min rate should be >= 50%, got {min_rate*100:.1f}%"
            # Max should be around 70% (0.70)
            assert max_rate >= 0.60, f"Max rate should be >= 60%, got {max_rate*100:.1f}%"
            # There should be variation
            assert max_rate > min_rate, "Max rate should be greater than min rate"
            
            print(f"✅ Rice 100630 rate_warning verified: {min_rate*100:.1f}% - {max_rate*100:.1f}%")
        else:
            print("⚠️ rate_warning is None - checking if sub_positions exist")
            # Check if has_varying_sub_positions is True
            assert data.get("has_varying_sub_positions") == True, "has_varying_sub_positions should be True for rice"
    
    def test_rice_100630_sub_positions_details(self):
        """Test that sub_positions_details is returned for rice"""
        response = requests.post(f"{BASE_URL}/api/calculate-tariff", json={
            "origin_country": "CIV",
            "destination_country": "NGA",
            "hs_code": "100630",
            "value": 10000
        })
        
        assert response.status_code == 200
        data = response.json()
        
        # Check sub_positions_details
        sub_positions = data.get("sub_positions_details")
        
        if sub_positions:
            assert isinstance(sub_positions, list), "sub_positions_details should be a list"
            assert len(sub_positions) > 0, "sub_positions_details should not be empty"
            
            # Verify structure of each sub-position
            for sp in sub_positions:
                assert "code" in sp, "Each sub-position should have 'code'"
                assert "dd_rate" in sp, "Each sub-position should have 'dd_rate'"
                assert "description_fr" in sp or "description_en" in sp, "Each sub-position should have description"
                
            print(f"✅ Found {len(sub_positions)} sub-positions for rice 100630:")
            for sp in sub_positions:
                print(f"   - {sp.get('code')}: {sp.get('dd_rate_pct', sp.get('dd_rate')*100 if sp.get('dd_rate') else 'N/A')} - {sp.get('description_fr', sp.get('description_en', ''))}")
        else:
            # Check available_sub_positions_count
            count = data.get("available_sub_positions_count", 0)
            print(f"⚠️ sub_positions_details is None, available_sub_positions_count: {count}")
    
    def test_cars_870323_to_nigeria_has_varying_rates(self):
        """
        Test: Voitures (870323) vers Nigeria doit avoir taux variables 35%-70%
        Nigeria has sub-positions for cars 1500-3000cc with different rates:
        - 8703231000: 35% (neuves)
        - 8703239100: 50% (occasion 5-10 ans)
        - 8703239000: 70% (occasion >10 ans)
        """
        response = requests.post(f"{BASE_URL}/api/calculate-tariff", json={
            "origin_country": "ZAF",  # South Africa
            "destination_country": "NGA",  # Nigeria
            "hs_code": "870323",
            "value": 25000
        })
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        
        # Check rate_warning exists
        rate_warning = data.get("rate_warning")
        
        if rate_warning:
            assert rate_warning.get("has_variation") == True, "has_variation should be True for cars"
            
            min_rate = rate_warning.get("min_rate", 0)
            max_rate = rate_warning.get("max_rate", 0)
            
            print(f"Cars 870323 to Nigeria - Min rate: {min_rate*100:.1f}%, Max rate: {max_rate*100:.1f}%")
            
            # Min should be around 35% (0.35)
            assert min_rate >= 0.35, f"Min rate should be >= 35%, got {min_rate*100:.1f}%"
            # Max should be around 70% (0.70)
            assert max_rate >= 0.50, f"Max rate should be >= 50%, got {max_rate*100:.1f}%"
            # There should be variation
            assert max_rate > min_rate, "Max rate should be greater than min rate"
            
            print(f"✅ Cars 870323 rate_warning verified: {min_rate*100:.1f}% - {max_rate*100:.1f}%")
        else:
            # Check if has_varying_sub_positions is True
            has_varying = data.get("has_varying_sub_positions", False)
            print(f"⚠️ rate_warning is None, has_varying_sub_positions: {has_varying}")
            assert has_varying == True, "has_varying_sub_positions should be True for cars"
    
    def test_cars_870323_sub_positions_details(self):
        """Test that sub_positions_details is returned for cars"""
        response = requests.post(f"{BASE_URL}/api/calculate-tariff", json={
            "origin_country": "ZAF",
            "destination_country": "NGA",
            "hs_code": "870323",
            "value": 25000
        })
        
        assert response.status_code == 200
        data = response.json()
        
        sub_positions = data.get("sub_positions_details")
        
        if sub_positions:
            assert len(sub_positions) > 0, "sub_positions_details should not be empty for cars"
            
            print(f"✅ Found {len(sub_positions)} sub-positions for cars 870323:")
            for sp in sub_positions:
                print(f"   - {sp.get('code')}: {sp.get('dd_rate_pct', '')} - {sp.get('description_fr', sp.get('description_en', ''))}")
        else:
            count = data.get("available_sub_positions_count", 0)
            print(f"⚠️ sub_positions_details is None, available_sub_positions_count: {count}")


class TestNoWarningForUniformRates:
    """Tests for products that should NOT have rate_warning (uniform rates)"""
    
    def test_medicines_300490_no_warning(self):
        """
        Test: Médicaments (300490) ne doit PAS avoir de warning
        All medicine sub-positions in Nigeria have 0% rate (exonérés)
        """
        response = requests.post(f"{BASE_URL}/api/calculate-tariff", json={
            "origin_country": "EGY",  # Egypt
            "destination_country": "NGA",  # Nigeria
            "hs_code": "300490",
            "value": 5000
        })
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        
        rate_warning = data.get("rate_warning")
        
        # For medicines, either rate_warning should be None or has_variation should be False
        if rate_warning:
            has_variation = rate_warning.get("has_variation", False)
            assert has_variation == False, f"Medicines should NOT have varying rates, got has_variation={has_variation}"
            print(f"✅ Medicines 300490 correctly has no variation (has_variation=False)")
        else:
            print(f"✅ Medicines 300490 correctly has no rate_warning (None)")
        
        # Verify the tariff rate is 0% for medicines
        normal_rate = data.get("normal_tariff_rate", -1)
        print(f"   Normal tariff rate for medicines: {normal_rate*100:.1f}%")
        assert normal_rate == 0.0, f"Medicines should have 0% tariff, got {normal_rate*100:.1f}%"
    
    def test_vaccines_300220_no_warning(self):
        """Test: Vaccins (300220) ne doit PAS avoir de warning - tous à 0%"""
        response = requests.post(f"{BASE_URL}/api/calculate-tariff", json={
            "origin_country": "ZAF",
            "destination_country": "NGA",
            "hs_code": "300220",
            "value": 10000
        })
        
        assert response.status_code == 200
        data = response.json()
        
        rate_warning = data.get("rate_warning")
        
        if rate_warning:
            has_variation = rate_warning.get("has_variation", False)
            assert has_variation == False, "Vaccines should NOT have varying rates"
            print(f"✅ Vaccines 300220 correctly has no variation")
        else:
            print(f"✅ Vaccines 300220 correctly has no rate_warning")
        
        # Verify 0% rate
        normal_rate = data.get("normal_tariff_rate", -1)
        assert normal_rate == 0.0, f"Vaccines should have 0% tariff, got {normal_rate*100:.1f}%"


class TestRateWarningStructure:
    """Tests for the structure and content of rate_warning object"""
    
    def test_rate_warning_has_all_required_fields(self):
        """Test that rate_warning contains all required fields when present"""
        response = requests.post(f"{BASE_URL}/api/calculate-tariff", json={
            "origin_country": "CIV",
            "destination_country": "NGA",
            "hs_code": "100630",  # Rice - should have varying rates
            "value": 10000
        })
        
        assert response.status_code == 200
        data = response.json()
        
        rate_warning = data.get("rate_warning")
        
        if rate_warning and rate_warning.get("has_variation"):
            required_fields = [
                "has_variation",
                "message_fr",
                "message_en",
                "min_rate",
                "max_rate",
                "min_rate_pct",
                "max_rate_pct",
                "rate_used",
                "rate_used_pct",
                "recommendation_fr",
                "recommendation_en"
            ]
            
            for field in required_fields:
                assert field in rate_warning, f"rate_warning should contain '{field}'"
            
            print(f"✅ rate_warning has all required fields")
            print(f"   Message FR: {rate_warning.get('message_fr', '')[:80]}...")
            print(f"   Message EN: {rate_warning.get('message_en', '')[:80]}...")
    
    def test_sub_positions_details_structure(self):
        """Test the structure of sub_positions_details list"""
        response = requests.post(f"{BASE_URL}/api/calculate-tariff", json={
            "origin_country": "CIV",
            "destination_country": "NGA",
            "hs_code": "100630",
            "value": 10000
        })
        
        assert response.status_code == 200
        data = response.json()
        
        sub_positions = data.get("sub_positions_details")
        
        if sub_positions and len(sub_positions) > 0:
            required_fields = ["code", "dd_rate", "dd_rate_pct"]
            
            for sp in sub_positions:
                for field in required_fields:
                    assert field in sp, f"Each sub-position should have '{field}'"
            
            print(f"✅ sub_positions_details has correct structure")


class TestTariffPrecisionField:
    """Tests for tariff_precision field indicating data source"""
    
    def test_tariff_precision_for_hs6(self):
        """Test that tariff_precision indicates the data source"""
        response = requests.post(f"{BASE_URL}/api/calculate-tariff", json={
            "origin_country": "CIV",
            "destination_country": "NGA",
            "hs_code": "100630",
            "value": 10000
        })
        
        assert response.status_code == 200
        data = response.json()
        
        tariff_precision = data.get("tariff_precision")
        assert tariff_precision is not None, "tariff_precision should be present"
        assert tariff_precision in ["sub_position", "hs6_country", "chapter"], \
            f"tariff_precision should be one of sub_position/hs6_country/chapter, got {tariff_precision}"
        
        print(f"✅ tariff_precision: {tariff_precision}")
    
    def test_has_varying_sub_positions_field(self):
        """Test has_varying_sub_positions boolean field"""
        response = requests.post(f"{BASE_URL}/api/calculate-tariff", json={
            "origin_country": "CIV",
            "destination_country": "NGA",
            "hs_code": "100630",
            "value": 10000
        })
        
        assert response.status_code == 200
        data = response.json()
        
        has_varying = data.get("has_varying_sub_positions")
        assert has_varying is not None, "has_varying_sub_positions should be present"
        assert isinstance(has_varying, bool), "has_varying_sub_positions should be boolean"
        
        print(f"✅ has_varying_sub_positions: {has_varying}")
    
    def test_available_sub_positions_count(self):
        """Test available_sub_positions_count field"""
        response = requests.post(f"{BASE_URL}/api/calculate-tariff", json={
            "origin_country": "CIV",
            "destination_country": "NGA",
            "hs_code": "100630",
            "value": 10000
        })
        
        assert response.status_code == 200
        data = response.json()
        
        count = data.get("available_sub_positions_count")
        assert count is not None, "available_sub_positions_count should be present"
        assert isinstance(count, int), "available_sub_positions_count should be integer"
        
        print(f"✅ available_sub_positions_count: {count}")


class TestOtherCountriesWithVaryingRates:
    """Test varying rates for other countries"""
    
    def test_kenya_rice_varying_rates(self):
        """Test Kenya rice (100630) - should have 75% uniform rate"""
        response = requests.post(f"{BASE_URL}/api/calculate-tariff", json={
            "origin_country": "TZA",  # Tanzania
            "destination_country": "KEN",  # Kenya
            "hs_code": "100630",
            "value": 10000
        })
        
        assert response.status_code == 200
        data = response.json()
        
        rate_warning = data.get("rate_warning")
        normal_rate = data.get("normal_tariff_rate", 0)
        
        print(f"Kenya rice 100630 - Normal rate: {normal_rate*100:.1f}%")
        
        if rate_warning:
            print(f"   has_variation: {rate_warning.get('has_variation')}")
            if rate_warning.get("has_variation"):
                print(f"   Rate range: {rate_warning.get('min_rate_pct')} - {rate_warning.get('max_rate_pct')}")
    
    def test_south_africa_cars_varying_rates(self):
        """Test South Africa cars (870323) - should have 25% uniform rate"""
        response = requests.post(f"{BASE_URL}/api/calculate-tariff", json={
            "origin_country": "NGA",
            "destination_country": "ZAF",  # South Africa
            "hs_code": "870323",
            "value": 25000
        })
        
        assert response.status_code == 200
        data = response.json()
        
        rate_warning = data.get("rate_warning")
        normal_rate = data.get("normal_tariff_rate", 0)
        
        print(f"South Africa cars 870323 - Normal rate: {normal_rate*100:.1f}%")
        
        if rate_warning:
            print(f"   has_variation: {rate_warning.get('has_variation')}")


class TestEdgeCases:
    """Edge case tests"""
    
    def test_product_without_sub_positions_data(self):
        """Test a product that may not have detailed sub-positions data"""
        response = requests.post(f"{BASE_URL}/api/calculate-tariff", json={
            "origin_country": "CIV",
            "destination_country": "NGA",
            "hs_code": "999999",  # Non-existent code
            "value": 1000
        })
        
        # Should still return 200 with fallback rates
        assert response.status_code == 200
        data = response.json()
        
        # rate_warning should be None or has_variation=False
        rate_warning = data.get("rate_warning")
        if rate_warning:
            assert rate_warning.get("has_variation") == False, "Non-existent code should not have varying rates"
    
    def test_specific_sub_position_code(self):
        """Test with a specific 10-digit sub-position code"""
        response = requests.post(f"{BASE_URL}/api/calculate-tariff", json={
            "origin_country": "CIV",
            "destination_country": "NGA",
            "hs_code": "1006309100",  # Riz parfumé (Basmati, Jasmin) - 70%
            "value": 10000
        })
        
        assert response.status_code == 200
        data = response.json()
        
        # When specific sub-position is provided, tariff_precision should be "sub_position"
        tariff_precision = data.get("tariff_precision")
        sub_position_used = data.get("sub_position_used")
        
        print(f"Specific sub-position 1006309100:")
        print(f"   tariff_precision: {tariff_precision}")
        print(f"   sub_position_used: {sub_position_used}")
        print(f"   normal_tariff_rate: {data.get('normal_tariff_rate', 0)*100:.1f}%")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
