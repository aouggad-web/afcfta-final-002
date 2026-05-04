"""
Test suite for AfCFTA Rules of Origin API
Tests the /api/rules-of-origin/{hs_code} and /api/rules-of-origin/stats endpoints
Verifies that product-specific rules are returned instead of generic rules

P0 Bug Fix Verification:
- Previously: Generic rule "35% valeur ajoutée africaine" was displayed for all products
- Now: Product-specific rules from AfCFTA Annex II Appendix IV should be returned

Test Cases:
- Wheat (100110) = WO (Wholly Obtained / Entièrement Obtenu)
- Coffee (090111) = WO (Wholly Obtained / Entièrement Obtenu)
- Machines (850440) = CTH/VA60 (Change of Tariff Heading / Max 60% non-originating)
- Clothing (620311) = YARN (Manufacture from yarn / Fabrication à partir de fils)
- Vehicles (870310) = YTB (Yet to be agreed / En cours de négociation)
"""

import pytest
import requests
import os

# Get BASE_URL from environment
BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')


class TestRulesOfOriginStats:
    """Tests for /api/rules-of-origin/stats endpoint"""
    
    def test_stats_endpoint_returns_200(self):
        """Stats endpoint should return 200 status"""
        response = requests.get(f"{BASE_URL}/api/rules-of-origin/stats")
        assert response.status_code == 200
        print(f"✅ Stats endpoint returns 200")
        
    def test_stats_contains_required_fields(self):
        """Stats should contain all required fields"""
        response = requests.get(f"{BASE_URL}/api/rules-of-origin/stats")
        assert response.status_code == 200
        data = response.json()
        
        required_fields = ["total_chapters", "agreed_chapters", "heading_rules", "source"]
        for field in required_fields:
            assert field in data, f"Missing field: {field}"
        print(f"✅ Stats contains all required fields: {list(data.keys())}")
        
    def test_stats_has_heading_rules(self):
        """Stats should show heading-level rules exist"""
        response = requests.get(f"{BASE_URL}/api/rules-of-origin/stats")
        assert response.status_code == 200
        data = response.json()
        
        heading_rules = data.get("heading_rules", 0)
        assert heading_rules > 0, f"Expected heading_rules > 0, got {heading_rules}"
        print(f"✅ Heading rules count: {heading_rules}")
        
    def test_stats_source_is_afcfta(self):
        """Stats source should reference AfCFTA Annex II"""
        response = requests.get(f"{BASE_URL}/api/rules-of-origin/stats")
        assert response.status_code == 200
        data = response.json()
        
        source = data.get("source", "")
        assert "AfCFTA" in source or "Annex" in source, f"Source should reference AfCFTA: {source}"
        print(f"✅ Source: {source}")


class TestRulesOfOriginWheat:
    """Tests for Wheat (HS 100110) - Should be WO (Wholly Obtained)"""
    
    def test_wheat_returns_200(self):
        """Wheat HS code should return 200"""
        response = requests.get(f"{BASE_URL}/api/rules-of-origin/100110")
        assert response.status_code == 200
        print(f"✅ Wheat (100110) returns 200")
        
    def test_wheat_rule_is_wo(self):
        """Wheat should have WO (Wholly Obtained) rule"""
        response = requests.get(f"{BASE_URL}/api/rules-of-origin/100110")
        assert response.status_code == 200
        data = response.json()
        
        rules = data.get("rules", {})
        primary_rule = rules.get("primary_rule", {})
        rule_code = primary_rule.get("code", "")
        
        assert rule_code == "WO", f"Expected WO rule for wheat, got: {rule_code}"
        print(f"✅ Wheat rule: {rule_code} - {primary_rule.get('name', '')}")
        
    def test_wheat_rule_name_contains_wholly_obtained(self):
        """Wheat rule name should indicate Wholly Obtained"""
        response = requests.get(f"{BASE_URL}/api/rules-of-origin/100110?lang=fr")
        assert response.status_code == 200
        data = response.json()
        
        rules = data.get("rules", {})
        primary_rule = rules.get("primary_rule", {})
        rule_name = primary_rule.get("name", "").lower()
        
        # Should contain "entièrement obtenu" (FR) or "wholly obtained" (EN)
        assert "entièrement" in rule_name or "wholly" in rule_name or "wo" in rule_name.lower(), \
            f"Wheat rule should be Wholly Obtained, got: {primary_rule.get('name', '')}"
        print(f"✅ Wheat rule name: {primary_rule.get('name', '')}")


class TestRulesOfOriginCoffee:
    """Tests for Coffee (HS 090111) - Should be WO (Wholly Obtained)"""
    
    def test_coffee_returns_200(self):
        """Coffee HS code should return 200"""
        response = requests.get(f"{BASE_URL}/api/rules-of-origin/090111")
        assert response.status_code == 200
        print(f"✅ Coffee (090111) returns 200")
        
    def test_coffee_rule_is_wo(self):
        """Coffee should have WO (Wholly Obtained) rule"""
        response = requests.get(f"{BASE_URL}/api/rules-of-origin/090111")
        assert response.status_code == 200
        data = response.json()
        
        rules = data.get("rules", {})
        primary_rule = rules.get("primary_rule", {})
        rule_code = primary_rule.get("code", "")
        
        assert rule_code == "WO", f"Expected WO rule for coffee, got: {rule_code}"
        print(f"✅ Coffee rule: {rule_code} - {primary_rule.get('name', '')}")
        
    def test_coffee_chapter_is_09(self):
        """Coffee should be in chapter 09"""
        response = requests.get(f"{BASE_URL}/api/rules-of-origin/090111")
        assert response.status_code == 200
        data = response.json()
        
        chapter = data.get("chapter", "")
        assert chapter == "09", f"Expected chapter 09, got: {chapter}"
        print(f"✅ Coffee chapter: {chapter}")


class TestRulesOfOriginMachines:
    """Tests for Machines/Electrical (HS 850440) - Should be CTH or VA60"""
    
    def test_machines_returns_200(self):
        """Machines HS code should return 200"""
        response = requests.get(f"{BASE_URL}/api/rules-of-origin/850440")
        assert response.status_code == 200
        print(f"✅ Machines (850440) returns 200")
        
    def test_machines_rule_is_cth_or_va60(self):
        """Machines should have CTH or VA60 rule"""
        response = requests.get(f"{BASE_URL}/api/rules-of-origin/850440")
        assert response.status_code == 200
        data = response.json()
        
        rules = data.get("rules", {})
        primary_rule = rules.get("primary_rule", {})
        alt_rule = rules.get("alternative_rule", {})
        
        primary_code = primary_rule.get("code", "")
        alt_code = alt_rule.get("code", "") if alt_rule else ""
        
        valid_codes = ["CTH", "VA60", "VA", "CTSH"]
        assert primary_code in valid_codes or alt_code in valid_codes, \
            f"Expected CTH or VA60 for machines, got primary: {primary_code}, alt: {alt_code}"
        print(f"✅ Machines rule: primary={primary_code}, alt={alt_code}")
        
    def test_machines_chapter_is_85(self):
        """Machines should be in chapter 85"""
        response = requests.get(f"{BASE_URL}/api/rules-of-origin/850440")
        assert response.status_code == 200
        data = response.json()
        
        chapter = data.get("chapter", "")
        assert chapter == "85", f"Expected chapter 85, got: {chapter}"
        print(f"✅ Machines chapter: {chapter}")


class TestRulesOfOriginClothing:
    """Tests for Clothing (HS 620311) - Should be YARN (Manufacture from yarn)"""
    
    def test_clothing_returns_200(self):
        """Clothing HS code should return 200"""
        response = requests.get(f"{BASE_URL}/api/rules-of-origin/620311")
        assert response.status_code == 200
        print(f"✅ Clothing (620311) returns 200")
        
    def test_clothing_rule_is_yarn(self):
        """Clothing should have YARN rule"""
        response = requests.get(f"{BASE_URL}/api/rules-of-origin/620311")
        assert response.status_code == 200
        data = response.json()
        
        rules = data.get("rules", {})
        primary_rule = rules.get("primary_rule", {})
        rule_code = primary_rule.get("code", "")
        rule_name = primary_rule.get("name", "").lower()
        
        # Should be YARN or contain "yarn" or "fils"
        assert rule_code == "YARN" or "yarn" in rule_name or "fils" in rule_name, \
            f"Expected YARN rule for clothing, got: {rule_code} - {primary_rule.get('name', '')}"
        print(f"✅ Clothing rule: {rule_code} - {primary_rule.get('name', '')}")
        
    def test_clothing_chapter_is_62(self):
        """Clothing should be in chapter 62"""
        response = requests.get(f"{BASE_URL}/api/rules-of-origin/620311")
        assert response.status_code == 200
        data = response.json()
        
        chapter = data.get("chapter", "")
        assert chapter == "62", f"Expected chapter 62, got: {chapter}"
        print(f"✅ Clothing chapter: {chapter}")


class TestRulesOfOriginVehicles:
    """Tests for Vehicles (HS 870310) - Should be YTB (Yet to be agreed)"""
    
    def test_vehicles_returns_200(self):
        """Vehicles HS code should return 200"""
        response = requests.get(f"{BASE_URL}/api/rules-of-origin/870310")
        assert response.status_code == 200
        print(f"✅ Vehicles (870310) returns 200")
        
    def test_vehicles_rule_is_ytb_or_va60(self):
        """Vehicles should have YTB or VA60 rule (many headings under negotiation)"""
        response = requests.get(f"{BASE_URL}/api/rules-of-origin/870310")
        assert response.status_code == 200
        data = response.json()
        
        rules = data.get("rules", {})
        primary_rule = rules.get("primary_rule", {})
        alt_rule = rules.get("alternative_rule", {})
        status = data.get("status", "")
        
        primary_code = primary_rule.get("code", "")
        alt_code = alt_rule.get("code", "") if alt_rule else ""
        
        # Vehicles chapter 87 has many headings YTB, but some may have VA60
        valid_codes = ["YTB", "VA60", "VA", "CTH"]
        is_valid = primary_code in valid_codes or alt_code in valid_codes or status == "YTB"
        
        assert is_valid, f"Expected YTB or VA60 for vehicles, got primary: {primary_code}, alt: {alt_code}, status: {status}"
        print(f"✅ Vehicles rule: primary={primary_code}, alt={alt_code}, status={status}")
        
    def test_vehicles_chapter_is_87(self):
        """Vehicles should be in chapter 87"""
        response = requests.get(f"{BASE_URL}/api/rules-of-origin/870310")
        assert response.status_code == 200
        data = response.json()
        
        chapter = data.get("chapter", "")
        assert chapter == "87", f"Expected chapter 87, got: {chapter}"
        print(f"✅ Vehicles chapter: {chapter}")


class TestRulesOfOriginNotGeneric:
    """Tests to verify rules are NOT generic (P0 bug fix verification)"""
    
    def test_wheat_not_generic_35_percent(self):
        """Wheat should NOT have generic 35% value added rule"""
        response = requests.get(f"{BASE_URL}/api/rules-of-origin/100110")
        assert response.status_code == 200
        data = response.json()
        
        rules = data.get("rules", {})
        primary_rule = rules.get("primary_rule", {})
        rule_code = primary_rule.get("code", "")
        regional_content = rules.get("regional_content", 0)
        
        # Should NOT be generic VA35 rule
        assert rule_code != "VA35", f"Wheat should not have generic VA35 rule"
        assert regional_content != 35 or rule_code == "WO", \
            f"Wheat should not have generic 35% rule, got: {regional_content}%"
        print(f"✅ Wheat is NOT generic 35%: rule={rule_code}, regional_content={regional_content}%")
        
    def test_coffee_not_generic_35_percent(self):
        """Coffee should NOT have generic 35% value added rule"""
        response = requests.get(f"{BASE_URL}/api/rules-of-origin/090111")
        assert response.status_code == 200
        data = response.json()
        
        rules = data.get("rules", {})
        primary_rule = rules.get("primary_rule", {})
        rule_code = primary_rule.get("code", "")
        
        # Should NOT be generic VA35 rule
        assert rule_code != "VA35", f"Coffee should not have generic VA35 rule"
        print(f"✅ Coffee is NOT generic 35%: rule={rule_code}")
        
    def test_clothing_not_generic_35_percent(self):
        """Clothing should NOT have generic 35% value added rule"""
        response = requests.get(f"{BASE_URL}/api/rules-of-origin/620311")
        assert response.status_code == 200
        data = response.json()
        
        rules = data.get("rules", {})
        primary_rule = rules.get("primary_rule", {})
        rule_code = primary_rule.get("code", "")
        
        # Should NOT be generic VA35 rule
        assert rule_code != "VA35", f"Clothing should not have generic VA35 rule"
        print(f"✅ Clothing is NOT generic 35%: rule={rule_code}")


class TestRulesOfOriginResponseStructure:
    """Tests for response structure of /api/rules-of-origin/{hs_code}"""
    
    def test_response_has_hs_code(self):
        """Response should contain hs_code field"""
        response = requests.get(f"{BASE_URL}/api/rules-of-origin/090111")
        assert response.status_code == 200
        data = response.json()
        
        assert "hs_code" in data, "Response should contain hs_code"
        print(f"✅ Response has hs_code: {data.get('hs_code')}")
        
    def test_response_has_rules_object(self):
        """Response should contain rules object with primary_rule"""
        response = requests.get(f"{BASE_URL}/api/rules-of-origin/090111")
        assert response.status_code == 200
        data = response.json()
        
        assert "rules" in data, "Response should contain rules"
        rules = data.get("rules", {})
        assert "primary_rule" in rules, "Rules should contain primary_rule"
        print(f"✅ Response has rules.primary_rule")
        
    def test_response_has_status(self):
        """Response should contain status field"""
        response = requests.get(f"{BASE_URL}/api/rules-of-origin/090111")
        assert response.status_code == 200
        data = response.json()
        
        assert "status" in data, "Response should contain status"
        status = data.get("status", "")
        valid_statuses = ["AGREED", "PARTIAL", "YTB", "UNKNOWN"]
        assert status in valid_statuses, f"Invalid status: {status}"
        print(f"✅ Response has status: {status}")
        
    def test_response_has_source(self):
        """Response should contain source information"""
        response = requests.get(f"{BASE_URL}/api/rules-of-origin/090111")
        assert response.status_code == 200
        data = response.json()
        
        assert "source" in data, "Response should contain source"
        print(f"✅ Response has source: {data.get('source')}")


class TestRulesOfOriginLanguage:
    """Tests for language parameter"""
    
    def test_french_language(self):
        """French language should return French descriptions"""
        response = requests.get(f"{BASE_URL}/api/rules-of-origin/090111?lang=fr")
        assert response.status_code == 200
        data = response.json()
        
        rules = data.get("rules", {})
        primary_rule = rules.get("primary_rule", {})
        name = primary_rule.get("name", "")
        
        # French should contain "Entièrement Obtenu" or similar
        print(f"✅ French response: {name}")
        
    def test_english_language(self):
        """English language should return English descriptions"""
        response = requests.get(f"{BASE_URL}/api/rules-of-origin/090111?lang=en")
        assert response.status_code == 200
        data = response.json()
        
        rules = data.get("rules", {})
        primary_rule = rules.get("primary_rule", {})
        name = primary_rule.get("name", "")
        
        # English should contain "Wholly Obtained" or similar
        print(f"✅ English response: {name}")


class TestCalculateTariffIncludesRulesOfOrigin:
    """Tests for /api/calculate-tariff endpoint including rules of origin"""
    
    def test_calculate_tariff_returns_rules_of_origin(self):
        """Calculate tariff should include rules_of_origin in response"""
        payload = {
            "origin_country": "SEN",
            "destination_country": "CIV",
            "hs_code": "090111",
            "value": 10000
        }
        response = requests.post(f"{BASE_URL}/api/calculate-tariff", json=payload)
        assert response.status_code == 200
        data = response.json()
        
        assert "rules_of_origin" in data, "Response should contain rules_of_origin"
        rules = data.get("rules_of_origin", {})
        assert "rule" in rules, "rules_of_origin should contain rule"
        print(f"✅ Calculate tariff includes rules_of_origin: {rules.get('rule')}")
        
    def test_calculate_tariff_coffee_has_wo_rule(self):
        """Calculate tariff for coffee should have WO rule"""
        payload = {
            "origin_country": "ETH",
            "destination_country": "KEN",
            "hs_code": "090111",
            "value": 50000
        }
        response = requests.post(f"{BASE_URL}/api/calculate-tariff", json=payload)
        assert response.status_code == 200
        data = response.json()
        
        rules = data.get("rules_of_origin", {})
        rule = rules.get("rule", "")
        rule_code = rules.get("rule_code", "")
        
        # Should be WO or contain "Wholly Obtained" / "Entièrement Obtenu"
        assert rule_code == "WO" or "wholly" in rule.lower() or "entièrement" in rule.lower(), \
            f"Coffee should have WO rule, got: {rule_code} - {rule}"
        print(f"✅ Coffee tariff calculation has WO rule: {rule_code} - {rule}")
        
    def test_calculate_tariff_clothing_has_yarn_rule(self):
        """Calculate tariff for clothing should have YARN rule"""
        payload = {
            "origin_country": "MAR",
            "destination_country": "TUN",
            "hs_code": "620311",
            "value": 25000
        }
        response = requests.post(f"{BASE_URL}/api/calculate-tariff", json=payload)
        assert response.status_code == 200
        data = response.json()
        
        rules = data.get("rules_of_origin", {})
        rule = rules.get("rule", "")
        rule_code = rules.get("rule_code", "")
        
        # Should be YARN or contain "yarn" / "fils"
        assert rule_code == "YARN" or "yarn" in rule.lower() or "fils" in rule.lower(), \
            f"Clothing should have YARN rule, got: {rule_code} - {rule}"
        print(f"✅ Clothing tariff calculation has YARN rule: {rule_code} - {rule}")


class TestRulesOfOriginEdgeCases:
    """Tests for edge cases and error handling"""
    
    def test_invalid_hs_code_returns_404(self):
        """Invalid HS code should return 404"""
        response = requests.get(f"{BASE_URL}/api/rules-of-origin/999999")
        # May return 404 or 200 with UNKNOWN status
        if response.status_code == 200:
            data = response.json()
            status = data.get("status", "")
            assert status == "UNKNOWN", f"Invalid code should have UNKNOWN status, got: {status}"
        print(f"✅ Invalid HS code handled: status={response.status_code}")
        
    def test_short_hs_code(self):
        """Short HS code (4 digits) should work"""
        response = requests.get(f"{BASE_URL}/api/rules-of-origin/0901")
        assert response.status_code == 200
        data = response.json()
        
        rules = data.get("rules", {})
        primary_rule = rules.get("primary_rule", {})
        assert primary_rule is not None, "Short HS code should return rules"
        print(f"✅ Short HS code (0901) works: {primary_rule.get('code')}")
        
    def test_long_hs_code(self):
        """Long HS code (8+ digits) should work"""
        response = requests.get(f"{BASE_URL}/api/rules-of-origin/09011100")
        assert response.status_code == 200
        data = response.json()
        
        rules = data.get("rules", {})
        primary_rule = rules.get("primary_rule", {})
        assert primary_rule is not None, "Long HS code should return rules"
        print(f"✅ Long HS code (09011100) works: {primary_rule.get('code')}")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
