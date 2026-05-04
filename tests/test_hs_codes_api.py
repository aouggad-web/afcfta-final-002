"""
Test suite for HS6 Code Selector API endpoints
Tests: /api/hs-codes/search, /api/hs-codes/chapters, /api/hs-codes/chapter/{chapter}, /api/hs-codes/statistics
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')


class TestHSCodesStatistics:
    """Test HS codes statistics endpoint"""
    
    def test_get_statistics(self):
        """Test GET /api/hs-codes/statistics returns correct structure"""
        response = requests.get(f"{BASE_URL}/api/hs-codes/statistics")
        assert response.status_code == 200
        
        data = response.json()
        assert "total_chapters" in data
        assert "total_codes" in data
        assert "top_chapters" in data
        
        # Verify expected counts
        assert data["total_chapters"] == 97
        assert data["total_codes"] == 731
        assert len(data["top_chapters"]) == 10
        
        # Verify top chapter structure
        top_chapter = data["top_chapters"][0]
        assert "chapter" in top_chapter
        assert "chapter_name_fr" in top_chapter
        assert "code_count" in top_chapter


class TestHSCodesChapters:
    """Test HS codes chapters endpoint"""
    
    def test_get_all_chapters(self):
        """Test GET /api/hs-codes/chapters returns all chapters"""
        response = requests.get(f"{BASE_URL}/api/hs-codes/chapters")
        assert response.status_code == 200
        
        data = response.json()
        assert "chapters" in data
        assert "total" in data
        assert data["total"] == 97
        
        # Verify chapter structure (bilingual)
        chapters = data["chapters"]
        assert "01" in chapters
        assert "fr" in chapters["01"]
        assert "en" in chapters["01"]
        assert chapters["01"]["fr"] == "Animaux vivants"
        assert chapters["01"]["en"] == "Live animals"
    
    def test_chapter_18_cacao(self):
        """Test chapter 18 (Cacao) exists with correct labels"""
        response = requests.get(f"{BASE_URL}/api/hs-codes/chapters")
        assert response.status_code == 200
        
        data = response.json()
        chapters = data["chapters"]
        assert "18" in chapters
        assert "Cacao" in chapters["18"]["fr"]
        assert "Cocoa" in chapters["18"]["en"]


class TestHSCodesSearch:
    """Test HS codes search endpoint"""
    
    def test_search_cacao(self):
        """Test search for 'cacao' returns cocoa products"""
        response = requests.get(f"{BASE_URL}/api/hs-codes/search", params={
            "q": "cacao",
            "language": "fr",
            "limit": 15
        })
        assert response.status_code == 200
        
        data = response.json()
        assert "results" in data
        assert "count" in data
        assert data["count"] > 0
        
        # Verify cacao codes are returned
        codes = [r["code"] for r in data["results"]]
        assert "180100" in codes  # Cacao en fèves
        
        # Verify result structure
        result = data["results"][0]
        assert "code" in result
        assert "label" in result
        assert "chapter" in result
        assert "chapter_name" in result
    
    def test_search_coffee_english(self):
        """Test search for 'coffee' in English"""
        response = requests.get(f"{BASE_URL}/api/hs-codes/search", params={
            "q": "coffee",
            "language": "en",
            "limit": 10
        })
        assert response.status_code == 200
        
        data = response.json()
        assert data["count"] >= 6  # At least 6 coffee codes
        
        # Verify English labels
        labels = [r["label"] for r in data["results"]]
        assert any("Coffee" in label for label in labels)
    
    def test_search_poisson(self):
        """Test search for 'poisson' (fish) returns fish products"""
        response = requests.get(f"{BASE_URL}/api/hs-codes/search", params={
            "q": "poisson",
            "language": "fr",
            "limit": 10
        })
        assert response.status_code == 200
        
        data = response.json()
        assert data["count"] > 0
        
        # Verify fish codes are in chapter 03
        for result in data["results"]:
            assert result["chapter"] == "03"
    
    def test_search_by_code(self):
        """Test search by HS code number"""
        response = requests.get(f"{BASE_URL}/api/hs-codes/search", params={
            "q": "0901",
            "language": "fr",
            "limit": 10
        })
        assert response.status_code == 200
        
        data = response.json()
        assert data["count"] > 0
        
        # All results should start with 0901
        for result in data["results"]:
            assert result["code"].startswith("0901")
    
    def test_search_minimum_length(self):
        """Test search requires minimum 2 characters"""
        response = requests.get(f"{BASE_URL}/api/hs-codes/search", params={
            "q": "a",
            "language": "fr"
        })
        # Should return 422 validation error
        assert response.status_code == 422
    
    def test_search_limit_parameter(self):
        """Test search respects limit parameter"""
        response = requests.get(f"{BASE_URL}/api/hs-codes/search", params={
            "q": "huile",
            "language": "fr",
            "limit": 5
        })
        assert response.status_code == 200
        
        data = response.json()
        assert len(data["results"]) <= 5


class TestHSCodesChapterCodes:
    """Test HS codes by chapter endpoint"""
    
    def test_get_chapter_09_codes(self):
        """Test GET /api/hs-codes/chapter/09 returns coffee/tea/spices"""
        response = requests.get(f"{BASE_URL}/api/hs-codes/chapter/09", params={
            "language": "fr"
        })
        assert response.status_code == 200
        
        data = response.json()
        assert data["chapter"] == "09"
        assert "Café" in data["chapter_name_fr"]
        assert "Coffee" in data["chapter_name_en"]
        assert data["count"] == 34
        
        # Verify codes structure
        codes = data["codes"]
        assert len(codes) == 34
        
        # Verify first code is coffee
        first_code = codes[0]
        assert first_code["code"] == "090111"
        assert "Café" in first_code["label"]
    
    def test_get_chapter_18_codes(self):
        """Test GET /api/hs-codes/chapter/18 returns cacao products"""
        response = requests.get(f"{BASE_URL}/api/hs-codes/chapter/18", params={
            "language": "fr"
        })
        assert response.status_code == 200
        
        data = response.json()
        assert data["chapter"] == "18"
        assert "Cacao" in data["chapter_name_fr"]
        
        # Verify cacao codes
        codes = [c["code"] for c in data["codes"]]
        assert "180100" in codes  # Cacao en fèves
        assert "180400" in codes  # Beurre de cacao
    
    def test_get_chapter_03_codes(self):
        """Test GET /api/hs-codes/chapter/03 returns fish products"""
        response = requests.get(f"{BASE_URL}/api/hs-codes/chapter/03", params={
            "language": "fr"
        })
        assert response.status_code == 200
        
        data = response.json()
        assert data["chapter"] == "03"
        assert "Poissons" in data["chapter_name_fr"]
        assert data["count"] == 55
    
    def test_invalid_chapter(self):
        """Test invalid chapter returns 404"""
        response = requests.get(f"{BASE_URL}/api/hs-codes/chapter/XX")
        assert response.status_code == 404
    
    def test_chapter_english_language(self):
        """Test chapter codes in English"""
        response = requests.get(f"{BASE_URL}/api/hs-codes/chapter/09", params={
            "language": "en"
        })
        assert response.status_code == 200
        
        data = response.json()
        # Verify English labels
        first_code = data["codes"][0]
        assert "Coffee" in first_code["label"]


class TestHSCodesSingleCode:
    """Test single HS code endpoint"""
    
    def test_get_code_180100(self):
        """Test GET /api/hs-codes/code/180100 returns cacao beans"""
        response = requests.get(f"{BASE_URL}/api/hs-codes/code/180100", params={
            "language": "fr"
        })
        assert response.status_code == 200
        
        data = response.json()
        assert data["code"] == "180100"
        assert "Cacao" in data["label"]
        assert data["chapter"] == "18"
    
    def test_get_code_english(self):
        """Test single code in English"""
        response = requests.get(f"{BASE_URL}/api/hs-codes/code/090111", params={
            "language": "en"
        })
        assert response.status_code == 200
        
        data = response.json()
        assert "Coffee" in data["label"]
    
    def test_invalid_code(self):
        """Test invalid HS code returns 404"""
        response = requests.get(f"{BASE_URL}/api/hs-codes/code/999999")
        assert response.status_code == 404


class TestRulesOfOriginIntegration:
    """Test rules of origin with HS codes"""
    
    def test_rules_for_cacao(self):
        """Test rules of origin for cacao (chapter 18)"""
        response = requests.get(f"{BASE_URL}/api/rules-of-origin/180100", params={
            "lang": "fr"
        })
        assert response.status_code == 200
        
        data = response.json()
        assert data["hs_code"] == "180100"
        assert data["sector_code"] == "18"
        assert "rules" in data
        assert data["rules"]["regional_content"] == 100  # Wholly obtained
    
    def test_rules_for_coffee(self):
        """Test rules of origin for coffee (chapter 09)"""
        response = requests.get(f"{BASE_URL}/api/rules-of-origin/090111", params={
            "lang": "fr"
        })
        assert response.status_code == 200
        
        data = response.json()
        assert data["sector_code"] == "09"
        assert data["rules"]["regional_content"] == 100  # Wholly obtained
    
    def test_rules_for_fish(self):
        """Test rules of origin for fish (chapter 03)"""
        response = requests.get(f"{BASE_URL}/api/rules-of-origin/030110", params={
            "lang": "en"
        })
        assert response.status_code == 200
        
        data = response.json()
        assert data["sector_code"] == "03"
        assert data["rules"]["regional_content"] == 100  # Wholly obtained


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
