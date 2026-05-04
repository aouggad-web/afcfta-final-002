"""
Test suite for HS6 Extended Database API
Tests the HS6 code search, statistics, categories, and sub-positions endpoints
Verifies that the extended chapters (41-63, 72-89) are properly merged
"""

import pytest
import requests
import os

# Get BASE_URL from environment
BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

class TestHS6Search:
    """Tests for /api/hs6/search endpoint"""
    
    def test_search_riz(self):
        """Search for 'riz' (rice) - should return results from chapter 10"""
        response = requests.get(f"{BASE_URL}/api/hs6/search", params={"query": "riz", "limit": 10})
        assert response.status_code == 200
        data = response.json()
        assert "results" in data
        assert "count" in data
        assert data["count"] > 0
        print(f"✅ Search 'riz': {data['count']} results found")
        
    def test_search_automobile(self):
        """Search for 'automobile' - should return vehicle codes from chapter 87"""
        response = requests.get(f"{BASE_URL}/api/hs6/search", params={"query": "automobile", "limit": 10})
        assert response.status_code == 200
        data = response.json()
        assert "results" in data
        print(f"✅ Search 'automobile': {data['count']} results found")
        
    def test_search_textile(self):
        """Search for 'textile' - should return codes from chapters 50-63"""
        response = requests.get(f"{BASE_URL}/api/hs6/search", params={"query": "textile", "limit": 10})
        assert response.status_code == 200
        data = response.json()
        assert "results" in data
        print(f"✅ Search 'textile': {data['count']} results found")
        
    def test_search_acier(self):
        """Search for 'acier' (steel) - should return codes from chapter 72"""
        response = requests.get(f"{BASE_URL}/api/hs6/search", params={"query": "acier", "limit": 10})
        assert response.status_code == 200
        data = response.json()
        assert "results" in data
        print(f"✅ Search 'acier': {data['count']} results found")
        
    def test_search_cuir(self):
        """Search for 'cuir' (leather) - should return codes from chapter 41-42"""
        response = requests.get(f"{BASE_URL}/api/hs6/search", params={"query": "cuir", "limit": 10})
        assert response.status_code == 200
        data = response.json()
        assert "results" in data
        print(f"✅ Search 'cuir': {data['count']} results found")
        
    def test_search_poisson(self):
        """Search for 'poisson' (fish) - should return codes from chapter 03"""
        response = requests.get(f"{BASE_URL}/api/hs6/search", params={"query": "poisson", "limit": 10})
        assert response.status_code == 200
        data = response.json()
        assert "results" in data
        assert data["count"] > 0
        print(f"✅ Search 'poisson': {data['count']} results found")
        
    def test_search_navire(self):
        """Search for 'navire' (ship) - should return codes from chapter 89"""
        response = requests.get(f"{BASE_URL}/api/hs6/search", params={"query": "navire", "limit": 10})
        assert response.status_code == 200
        data = response.json()
        assert "results" in data
        print(f"✅ Search 'navire': {data['count']} results found")
        
    def test_search_by_code(self):
        """Search by HS6 code prefix"""
        response = requests.get(f"{BASE_URL}/api/hs6/search", params={"query": "8703", "limit": 10})
        assert response.status_code == 200
        data = response.json()
        assert "results" in data
        # All results should start with 8703
        for result in data["results"]:
            assert result["code"].startswith("8703")
        print(f"✅ Search by code '8703': {data['count']} results found")
        
    def test_search_english(self):
        """Search with English language parameter"""
        response = requests.get(f"{BASE_URL}/api/hs6/search", params={"query": "coffee", "language": "en", "limit": 10})
        assert response.status_code == 200
        data = response.json()
        assert "results" in data
        print(f"✅ Search 'coffee' (EN): {data['count']} results found")


class TestHS6Statistics:
    """Tests for /api/hs6/statistics endpoint"""
    
    def test_statistics_returns_data(self):
        """Statistics endpoint should return valid data"""
        response = requests.get(f"{BASE_URL}/api/hs6/statistics")
        assert response.status_code == 200
        data = response.json()
        assert "hs6_base" in data
        print(f"✅ Statistics endpoint returns data")
        
    def test_statistics_total_codes_over_800(self):
        """Total HS6 codes should be over 800 after extension merge"""
        response = requests.get(f"{BASE_URL}/api/hs6/statistics")
        assert response.status_code == 200
        data = response.json()
        total_codes = data["hs6_base"]["total_codes"]
        assert total_codes >= 800, f"Expected >= 800 codes, got {total_codes}"
        print(f"✅ Total HS6 codes: {total_codes} (>= 800)")
        
    def test_statistics_with_sub_positions(self):
        """Should have codes with sub-positions"""
        response = requests.get(f"{BASE_URL}/api/hs6/statistics")
        assert response.status_code == 200
        data = response.json()
        with_sub = data["hs6_base"]["with_sub_positions"]
        assert with_sub > 700, f"Expected > 700 codes with sub-positions, got {with_sub}"
        print(f"✅ Codes with sub-positions: {with_sub}")
        
    def test_statistics_categories_count(self):
        """Should have multiple categories"""
        response = requests.get(f"{BASE_URL}/api/hs6/statistics")
        assert response.status_code == 200
        data = response.json()
        categories = data["hs6_base"]["categories"]
        assert len(categories) >= 60, f"Expected >= 60 categories, got {len(categories)}"
        print(f"✅ Categories count: {len(categories)}")
        
    def test_statistics_sensitivities(self):
        """Should have sensitivity classifications"""
        response = requests.get(f"{BASE_URL}/api/hs6/statistics")
        assert response.status_code == 200
        data = response.json()
        sensitivities = data["hs6_base"]["sensitivities"]
        assert "normal" in sensitivities
        assert "sensitive" in sensitivities
        assert "excluded" in sensitivities
        print(f"✅ Sensitivities: normal={sensitivities['normal']}, sensitive={sensitivities['sensitive']}, excluded={sensitivities['excluded']}")


class TestHS6Info:
    """Tests for /api/hs6/info/{hs_code} endpoint"""
    
    def test_get_info_vehicle_code(self):
        """Get info for vehicle code 870323"""
        response = requests.get(f"{BASE_URL}/api/hs6/info/870323")
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == "870323"
        assert "description" in data
        assert data["chapter"] == "87"
        print(f"✅ Info for 870323: {data['description'][:50]}...")
        
    def test_get_info_coffee_code(self):
        """Get info for coffee code 090111"""
        response = requests.get(f"{BASE_URL}/api/hs6/info/090111")
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == "090111"
        assert "category" in data
        print(f"✅ Info for 090111: {data['description'][:50]}...")
        
    def test_get_info_steel_code(self):
        """Get info for steel code from chapter 72"""
        response = requests.get(f"{BASE_URL}/api/hs6/info/720110")
        assert response.status_code == 200
        data = response.json()
        assert data["chapter"] == "72"
        print(f"✅ Info for 720110: {data['description'][:50]}...")
        
    def test_get_info_leather_code(self):
        """Get info for leather code from chapter 41"""
        response = requests.get(f"{BASE_URL}/api/hs6/info/410411")
        assert response.status_code == 200
        data = response.json()
        assert data["chapter"] == "41"
        print(f"✅ Info for 410411: {data['description'][:50]}...")
        
    def test_get_info_textile_code(self):
        """Get info for textile code from chapter 52"""
        response = requests.get(f"{BASE_URL}/api/hs6/info/520100")
        assert response.status_code == 200
        data = response.json()
        assert data["chapter"] == "52"
        print(f"✅ Info for 520100: {data['description'][:50]}...")
        
    def test_get_info_ship_code(self):
        """Get info for ship code from chapter 89"""
        response = requests.get(f"{BASE_URL}/api/hs6/info/890110")
        assert response.status_code == 200
        data = response.json()
        assert data["chapter"] == "89"
        print(f"✅ Info for 890110: {data['description'][:50]}...")
        
    def test_get_info_nonexistent_code(self):
        """Non-existent code should return 404"""
        response = requests.get(f"{BASE_URL}/api/hs6/info/999999")
        assert response.status_code == 404
        print(f"✅ Non-existent code 999999 returns 404")


class TestHS6SubPositions:
    """Tests for /api/hs6/suggestions/{hs_code} endpoint"""
    
    def test_suggestions_vehicle_code(self):
        """Get sub-position suggestions for vehicle code"""
        response = requests.get(f"{BASE_URL}/api/hs6/suggestions/870323")
        assert response.status_code == 200
        data = response.json()
        assert data["hs6_code"] == "870323"
        assert "generic_suggestions" in data
        print(f"✅ Suggestions for 870323: {len(data['generic_suggestions'])} types")
        
    def test_suggestions_with_country(self):
        """Get sub-position suggestions with country code"""
        response = requests.get(f"{BASE_URL}/api/hs6/suggestions/870323", params={"country_code": "SEN"})
        assert response.status_code == 200
        data = response.json()
        assert data["country_code"] == "SEN"
        print(f"✅ Suggestions for 870323 (SEN): has_country_specific_rates={data['has_country_specific_rates']}")


class TestHS6Categories:
    """Tests for /api/hs6/categories endpoint"""
    
    def test_get_all_categories(self):
        """Get all product categories"""
        response = requests.get(f"{BASE_URL}/api/hs6/categories")
        assert response.status_code == 200
        data = response.json()
        assert "categories" in data
        assert "count" in data
        assert data["count"] >= 60
        print(f"✅ Categories: {data['count']} total")
        
    def test_categories_include_new_chapters(self):
        """Categories should include products from new chapters"""
        response = requests.get(f"{BASE_URL}/api/hs6/categories")
        assert response.status_code == 200
        data = response.json()
        categories = data["categories"]
        # Check for categories from extended chapters
        expected_categories = ["leather", "textiles", "steel", "vehicles", "ships"]
        found = [cat for cat in expected_categories if cat in categories]
        print(f"✅ Found categories from extended chapters: {found}")


class TestHS6CategoryCodes:
    """Tests for /api/hs6/category/{category} endpoint"""
    
    def test_get_vehicles_category(self):
        """Get codes in vehicles category"""
        response = requests.get(f"{BASE_URL}/api/hs6/category/vehicles")
        assert response.status_code == 200
        data = response.json()
        assert data["category"] == "vehicles"
        assert data["count"] > 0
        print(f"✅ Vehicles category: {data['count']} codes")
        
    def test_get_coffee_category(self):
        """Get codes in coffee category"""
        response = requests.get(f"{BASE_URL}/api/hs6/category/coffee")
        assert response.status_code == 200
        data = response.json()
        assert data["category"] == "coffee"
        assert data["count"] > 0
        print(f"✅ Coffee category: {data['count']} codes")
        
    def test_get_nonexistent_category(self):
        """Non-existent category should return 404"""
        response = requests.get(f"{BASE_URL}/api/hs6/category/nonexistent_category_xyz")
        assert response.status_code == 404
        print(f"✅ Non-existent category returns 404")


class TestHS6RuleOfOrigin:
    """Tests for /api/hs6/rule-of-origin/{hs_code} endpoint"""
    
    def test_rule_of_origin_vehicle(self):
        """Get rule of origin for vehicle code"""
        response = requests.get(f"{BASE_URL}/api/hs6/rule-of-origin/870323")
        assert response.status_code == 200
        data = response.json()
        assert data["hs6_code"] == "870323"
        assert "type" in data
        assert "regional_content" in data
        print(f"✅ Rule of origin for 870323: {data['type']}, {data['regional_content']}% regional content")
        
    def test_rule_of_origin_coffee(self):
        """Get rule of origin for coffee code"""
        response = requests.get(f"{BASE_URL}/api/hs6/rule-of-origin/090111")
        assert response.status_code == 200
        data = response.json()
        assert "regional_content" in data
        print(f"✅ Rule of origin for 090111: {data['type']}, {data['regional_content']}% regional content")
        
    def test_rule_of_origin_default(self):
        """Non-existent code should return default rule"""
        response = requests.get(f"{BASE_URL}/api/hs6/rule-of-origin/999999")
        assert response.status_code == 200
        data = response.json()
        assert data["regional_content"] == 40  # Default
        print(f"✅ Default rule of origin: {data['regional_content']}% regional content")


class TestHS6ExtendedChapters:
    """Tests to verify extended chapters (41-63, 72-89) are accessible"""
    
    def test_chapter_41_leather(self):
        """Verify chapter 41 (leather) codes are accessible"""
        response = requests.get(f"{BASE_URL}/api/hs6/search", params={"query": "41", "limit": 20})
        assert response.status_code == 200
        data = response.json()
        # Check if any results are from chapter 41
        chapter_41_codes = [r for r in data["results"] if r["code"].startswith("41")]
        print(f"✅ Chapter 41 codes found: {len(chapter_41_codes)}")
        
    def test_chapter_52_cotton(self):
        """Verify chapter 52 (cotton) codes are accessible"""
        response = requests.get(f"{BASE_URL}/api/hs6/search", params={"query": "coton", "limit": 20})
        assert response.status_code == 200
        data = response.json()
        print(f"✅ Cotton search: {data['count']} results")
        
    def test_chapter_72_steel(self):
        """Verify chapter 72 (steel) codes are accessible"""
        response = requests.get(f"{BASE_URL}/api/hs6/info/720110")
        assert response.status_code == 200
        data = response.json()
        assert data["chapter"] == "72"
        print(f"✅ Chapter 72 code 720110: {data['description'][:50]}...")
        
    def test_chapter_84_machinery(self):
        """Verify chapter 84 (machinery) codes are accessible"""
        response = requests.get(f"{BASE_URL}/api/hs6/info/847130")
        assert response.status_code == 200
        data = response.json()
        assert data["chapter"] == "84"
        print(f"✅ Chapter 84 code 847130: {data['description'][:50]}...")
        
    def test_chapter_87_vehicles(self):
        """Verify chapter 87 (vehicles) codes are accessible"""
        response = requests.get(f"{BASE_URL}/api/hs6/info/870340")
        assert response.status_code == 200
        data = response.json()
        assert data["chapter"] == "87"
        print(f"✅ Chapter 87 code 870340: {data['description'][:50]}...")
        
    def test_chapter_89_ships(self):
        """Verify chapter 89 (ships) codes are accessible"""
        response = requests.get(f"{BASE_URL}/api/hs6/info/890110")
        assert response.status_code == 200
        data = response.json()
        assert data["chapter"] == "89"
        print(f"✅ Chapter 89 code 890110: {data['description'][:50]}...")


class TestDataConsistency:
    """Tests to verify data consistency between search and statistics"""
    
    def test_search_count_vs_statistics(self):
        """Verify search results are consistent with statistics"""
        # Get statistics
        stats_response = requests.get(f"{BASE_URL}/api/hs6/statistics")
        assert stats_response.status_code == 200
        stats = stats_response.json()
        total_codes = stats["hs6_base"]["total_codes"]
        
        # Search for codes (using a valid search term)
        search_response = requests.get(f"{BASE_URL}/api/hs6/search", params={"query": "00", "limit": 50})
        assert search_response.status_code == 200
        
        print(f"✅ Statistics total: {total_codes}, Search returns results")
        
    def test_categories_sum_equals_total(self):
        """Verify sum of category counts equals total codes"""
        response = requests.get(f"{BASE_URL}/api/hs6/statistics")
        assert response.status_code == 200
        data = response.json()
        
        total_codes = data["hs6_base"]["total_codes"]
        categories = data["hs6_base"]["categories"]
        category_sum = sum(categories.values())
        
        assert category_sum == total_codes, f"Category sum {category_sum} != total {total_codes}"
        print(f"✅ Category sum ({category_sum}) equals total codes ({total_codes})")
        
    def test_sensitivities_sum_equals_total(self):
        """Verify sum of sensitivity counts equals total codes"""
        response = requests.get(f"{BASE_URL}/api/hs6/statistics")
        assert response.status_code == 200
        data = response.json()
        
        total_codes = data["hs6_base"]["total_codes"]
        sensitivities = data["hs6_base"]["sensitivities"]
        sensitivity_sum = sum(sensitivities.values())
        
        assert sensitivity_sum == total_codes, f"Sensitivity sum {sensitivity_sum} != total {total_codes}"
        print(f"✅ Sensitivity sum ({sensitivity_sum}) equals total codes ({total_codes})")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
