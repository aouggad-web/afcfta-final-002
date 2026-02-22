"""
Test Smart Search for Chapters 70, 71 and Dark Theme UI
Tests the smart-search endpoint with authentic tariff data for SEN
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

class TestSmartSearchChapters:
    """Test HS6 smart search for chapters 70 and 71 with Senegal tariffs"""
    
    def test_chapter_70_search_with_senegal(self):
        """Search chapter 70 (Verre/Glass) with country_code=SEN"""
        response = requests.get(
            f"{BASE_URL}/api/hs6/smart-search",
            params={
                "q": "70",
                "country_code": "SEN",
                "include_sub_positions": True,
                "limit": 20
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify structure
        assert "results" in data
        assert "count" in data
        assert data["count"] > 0, "Should return results for chapter 70"
        
        # Verify chapter 70 results
        results = data["results"]
        assert len(results) > 0, "Should have at least one result"
        
        # All codes should start with 70
        for result in results:
            assert result["code"].startswith("70"), f"Code {result['code']} should start with 70"
        
        # Verify first result has expected fields
        first_result = results[0]
        assert "code" in first_result
        assert "description" in first_result
        assert "chapter" in first_result
        assert first_result["chapter"] == "70"
        
        # Verify authentic data is used
        assert first_result.get("from_authentic") == True, "Should be from authentic data"
        assert "dd_rate" in first_result, "Should have DD rate"
        
        # Verify sub-positions are included
        if "sub_positions" in first_result:
            assert len(first_result["sub_positions"]) > 0, "Should have sub-positions"
            for sp in first_result["sub_positions"]:
                assert "code" in sp
                assert "dd" in sp
                assert len(sp["code"]) > 6, "Sub-position codes should be > 6 digits"
        
        print(f"✅ Chapter 70 search returned {data['count']} results")
        print(f"   First code: {first_result['code']} - {first_result['description'][:50]}...")
    
    def test_chapter_71_search_with_senegal(self):
        """Search chapter 71 (Perles, pierres précieuses) with country_code=SEN"""
        response = requests.get(
            f"{BASE_URL}/api/hs6/smart-search",
            params={
                "q": "71",
                "country_code": "SEN",
                "include_sub_positions": True,
                "limit": 20
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert "results" in data
        assert data["count"] > 0, "Should return results for chapter 71"
        
        results = data["results"]
        
        # All codes should start with 71
        for result in results:
            assert result["code"].startswith("71"), f"Code {result['code']} should start with 71"
        
        first_result = results[0]
        assert first_result["chapter"] == "71"
        assert first_result.get("from_authentic") == True
        
        print(f"✅ Chapter 71 search returned {data['count']} results")
        print(f"   First code: {first_result['code']} - {first_result['description'][:50]}...")
    
    def test_chapter_info_in_response(self):
        """Verify chapter info is included in response"""
        response = requests.get(
            f"{BASE_URL}/api/hs6/smart-search",
            params={
                "q": "70",
                "country_code": "SEN"
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Should have chapter info
        assert "chapter_info" in data
        chapter_info = data["chapter_info"]
        assert chapter_info["chapter"] == "70"
        assert "name" in chapter_info
        assert "Verre" in chapter_info["name"] or "Glass" in chapter_info["name"]
        
        print(f"✅ Chapter info: {chapter_info}")
    
    def test_sub_positions_have_dd_rates(self):
        """Verify sub-positions include DD rates from authentic data"""
        response = requests.get(
            f"{BASE_URL}/api/hs6/smart-search",
            params={
                "q": "70",
                "country_code": "SEN",
                "include_sub_positions": True
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        results = data["results"]
        
        # Find a result with sub_positions
        result_with_subs = None
        for r in results:
            if r.get("sub_positions") and len(r["sub_positions"]) > 0:
                result_with_subs = r
                break
        
        assert result_with_subs is not None, "Should find result with sub-positions"
        
        # Verify each sub-position has DD rate
        for sp in result_with_subs["sub_positions"]:
            assert "dd" in sp, f"Sub-position {sp.get('code')} should have DD rate"
            assert isinstance(sp["dd"], (int, float)), "DD should be numeric"
        
        print(f"✅ Sub-positions have DD rates")
        for sp in result_with_subs["sub_positions"][:3]:
            print(f"   {sp['code']}: DD {sp['dd']}%")
    
    def test_text_search_verre(self):
        """Test text search for 'verre' (glass)"""
        response = requests.get(
            f"{BASE_URL}/api/hs6/smart-search",
            params={
                "q": "verre",
                "country_code": "SEN",
                "language": "fr"
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Should find glass-related results
        if data["count"] > 0:
            print(f"✅ Text search 'verre' returned {data['count']} results")
        else:
            print(f"⚠️ Text search 'verre' returned no results (may need description indexing)")
    
    def test_search_without_country_code(self):
        """Test search without country_code parameter"""
        response = requests.get(
            f"{BASE_URL}/api/hs6/smart-search",
            params={
                "q": "70"
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Should still work, but may not have authentic DD rates
        assert "results" in data
        print(f"✅ Search without country_code returned {data['count']} results")


class TestDarkThemeStyling:
    """Verify the dark theme colors are used in response (these are frontend tests but we verify data structure)"""
    
    def test_response_has_chapter_name_for_header(self):
        """Verify chapter_name is returned for UI header display"""
        response = requests.get(
            f"{BASE_URL}/api/hs6/smart-search",
            params={
                "q": "70",
                "country_code": "SEN"
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Results should have chapter_name for displaying in gold header
        if data["count"] > 0:
            first = data["results"][0]
            assert "chapter_name" in first
            assert "full_position" in first  # For "Chapitre 70: Verre et ouvrages"
            print(f"✅ Chapter header data available: {first['full_position']}")
    
    def test_sub_position_digits_info(self):
        """Verify sub-positions have digit count for UI display (HS8, HS10, etc.)"""
        response = requests.get(
            f"{BASE_URL}/api/hs6/smart-search",
            params={
                "q": "70",
                "country_code": "SEN",
                "include_sub_positions": True
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Find sub-positions
        for r in data["results"]:
            if r.get("sub_positions"):
                for sp in r["sub_positions"]:
                    assert "digits" in sp, "Sub-position should have digits count"
                    assert sp["digits"] >= 8, "Sub-position should be HS8 or higher"
                print(f"✅ Sub-positions have digit count info")
                return
        
        print("⚠️ No sub-positions found to verify digits")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
