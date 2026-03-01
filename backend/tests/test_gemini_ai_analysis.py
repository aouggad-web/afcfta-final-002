"""
Test suite for Gemini AI Trade Analysis APIs
Tests /api/ai/* endpoints for trade opportunity analysis
"""
import pytest
import requests
import os

# Get BASE_URL from environment
BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')
if not BASE_URL:
    BASE_URL = "https://afcfta-tools.preview.emergentagent.com"


class TestAIHealthEndpoint:
    """Test /api/ai/health endpoint"""
    
    def test_ai_health_returns_200(self):
        """Health endpoint should return 200"""
        response = requests.get(f"{BASE_URL}/api/ai/health")
        assert response.status_code == 200
        print(f"SUCCESS: AI health endpoint returned 200")
    
    def test_ai_health_shows_operational(self):
        """Health endpoint should show operational status"""
        response = requests.get(f"{BASE_URL}/api/ai/health")
        data = response.json()
        
        assert "status" in data
        assert data["status"] == "operational"
        assert data["api_key_configured"] == True
        assert data["model"] == "gemini-3-flash-preview"
        print(f"SUCCESS: AI service is operational with model {data['model']}")
    
    def test_ai_health_response_structure(self):
        """Health endpoint should have correct structure"""
        response = requests.get(f"{BASE_URL}/api/ai/health")
        data = response.json()
        
        required_fields = ["status", "api_key_configured", "model", "provider"]
        for field in required_fields:
            assert field in data, f"Missing field: {field}"
        print(f"SUCCESS: Health response has all required fields")


class TestAIOpportunitiesExportMode:
    """Test /api/ai/opportunities/{country} - Export mode"""
    
    def test_kenya_export_opportunities(self):
        """Test export opportunities for Kenya"""
        response = requests.get(
            f"{BASE_URL}/api/ai/opportunities/Kenya",
            params={"mode": "export", "lang": "fr"},
            timeout=60
        )
        assert response.status_code == 200
        data = response.json()
        
        # Check response structure
        assert "opportunities" in data
        assert "country" in data
        assert data["country"] == "Kenya"
        assert data["mode"] == "export"
        assert "generated_by" in data
        print(f"SUCCESS: Kenya export analysis returned {len(data['opportunities'])} opportunities")
    
    def test_export_opportunities_have_required_fields(self):
        """Export opportunities should have required fields"""
        response = requests.get(
            f"{BASE_URL}/api/ai/opportunities/Kenya",
            params={"mode": "export", "lang": "fr"},
            timeout=60
        )
        data = response.json()
        
        if data.get("opportunities"):
            opp = data["opportunities"][0]
            required_fields = ["product_name", "hs_code", "potential_partner", "rationale"]
            for field in required_fields:
                assert field in opp, f"Missing field in opportunity: {field}"
            print(f"SUCCESS: Export opportunities have all required fields")
    
    def test_export_opportunities_have_estimation_flag(self):
        """Export opportunities should have is_estimation flag"""
        response = requests.get(
            f"{BASE_URL}/api/ai/opportunities/Kenya",
            params={"mode": "export", "lang": "fr"},
            timeout=60
        )
        data = response.json()
        
        if data.get("opportunities"):
            # Check that at least some opportunities have is_estimation field
            has_estimation_field = any("is_estimation" in opp for opp in data["opportunities"])
            assert has_estimation_field, "No opportunities have is_estimation field"
            print(f"SUCCESS: Export opportunities include is_estimation flag")
    
    def test_morocco_export_opportunities(self):
        """Test export opportunities for Morocco"""
        response = requests.get(
            f"{BASE_URL}/api/ai/opportunities/Morocco",
            params={"mode": "export", "lang": "fr"},
            timeout=60
        )
        assert response.status_code == 200
        data = response.json()
        
        assert "opportunities" in data
        assert len(data["opportunities"]) > 0
        print(f"SUCCESS: Morocco export analysis returned {len(data['opportunities'])} opportunities")


class TestAIOpportunitiesImportMode:
    """Test /api/ai/opportunities/{country} - Import mode"""
    
    def test_morocco_import_opportunities(self):
        """Test import substitution opportunities for Morocco"""
        response = requests.get(
            f"{BASE_URL}/api/ai/opportunities/Morocco",
            params={"mode": "import", "lang": "fr"},
            timeout=60
        )
        assert response.status_code == 200
        data = response.json()
        
        assert "opportunities" in data
        assert data["mode"] == "import"
        print(f"SUCCESS: Morocco import analysis returned {len(data['opportunities'])} opportunities")
    
    def test_import_opportunities_have_substitution_fields(self):
        """Import opportunities should have substitution-specific fields"""
        response = requests.get(
            f"{BASE_URL}/api/ai/opportunities/Morocco",
            params={"mode": "import", "lang": "fr"},
            timeout=60
        )
        data = response.json()
        
        if data.get("opportunities"):
            opp = data["opportunities"][0]
            # Import mode should have potential_supplier instead of potential_partner
            assert "potential_supplier" in opp or "current_source" in opp
            print(f"SUCCESS: Import opportunities have substitution-specific fields")
    
    def test_import_opportunities_have_estimation_flag(self):
        """Import opportunities should have is_estimation flag"""
        response = requests.get(
            f"{BASE_URL}/api/ai/opportunities/Morocco",
            params={"mode": "import", "lang": "fr"},
            timeout=60
        )
        data = response.json()
        
        if data.get("opportunities"):
            has_estimation_field = any("is_estimation" in opp for opp in data["opportunities"])
            assert has_estimation_field, "No import opportunities have is_estimation field"
            print(f"SUCCESS: Import opportunities include is_estimation flag")


class TestAIOpportunitiesIndustrialMode:
    """Test /api/ai/opportunities/{country} - Industrial/Value Chain mode"""
    
    def test_nigeria_industrial_opportunities(self):
        """Test industrial value chain opportunities for Nigeria"""
        response = requests.get(
            f"{BASE_URL}/api/ai/opportunities/Nigeria",
            params={"mode": "industrial", "lang": "fr"},
            timeout=60
        )
        assert response.status_code == 200
        data = response.json()
        
        assert "opportunities" in data
        assert data["mode"] == "industrial"
        print(f"SUCCESS: Nigeria industrial analysis returned {len(data['opportunities'])} opportunities")
    
    def test_industrial_opportunities_have_value_chain_fields(self):
        """Industrial opportunities should have input/output product fields"""
        response = requests.get(
            f"{BASE_URL}/api/ai/opportunities/Nigeria",
            params={"mode": "industrial", "lang": "fr"},
            timeout=60
        )
        data = response.json()
        
        if data.get("opportunities"):
            opp = data["opportunities"][0]
            # Industrial mode should have input_product and output_product
            value_chain_fields = ["input_product", "output_product", "target_markets"]
            has_value_chain = any(field in opp for field in value_chain_fields)
            assert has_value_chain, "Industrial opportunities missing value chain fields"
            print(f"SUCCESS: Industrial opportunities have value chain fields")
    
    def test_industrial_opportunities_have_estimation_flag(self):
        """Industrial opportunities should have is_estimation flag"""
        response = requests.get(
            f"{BASE_URL}/api/ai/opportunities/Nigeria",
            params={"mode": "industrial", "lang": "fr"},
            timeout=60
        )
        data = response.json()
        
        if data.get("opportunities"):
            has_estimation_field = any("is_estimation" in opp for opp in data["opportunities"])
            assert has_estimation_field, "No industrial opportunities have is_estimation field"
            print(f"SUCCESS: Industrial opportunities include is_estimation flag")


class TestAITradeBalance:
    """Test /api/ai/balance/{country} endpoint"""
    
    def test_kenya_trade_balance(self):
        """Test trade balance history for Kenya"""
        response = requests.get(
            f"{BASE_URL}/api/ai/balance/Kenya",
            params={"lang": "fr"},
            timeout=60
        )
        assert response.status_code == 200
        data = response.json()
        
        assert "trade_balance_history" in data
        assert "country" in data
        assert data["country"] == "Kenya"
        print(f"SUCCESS: Kenya trade balance returned {len(data.get('trade_balance_history', []))} years of data")
    
    def test_trade_balance_has_yearly_data(self):
        """Trade balance should have yearly data from 2020-2024"""
        response = requests.get(
            f"{BASE_URL}/api/ai/balance/Kenya",
            params={"lang": "fr"},
            timeout=60
        )
        data = response.json()
        
        if data.get("trade_balance_history"):
            years = [item["year"] for item in data["trade_balance_history"]]
            assert 2020 in years or 2021 in years, "Missing recent year data"
            print(f"SUCCESS: Trade balance includes years: {years}")
    
    def test_trade_balance_has_analysis(self):
        """Trade balance should include trend analysis"""
        response = requests.get(
            f"{BASE_URL}/api/ai/balance/Kenya",
            params={"lang": "fr"},
            timeout=60
        )
        data = response.json()
        
        if "analysis" in data:
            analysis = data["analysis"]
            assert "trend" in analysis, "Missing trend in analysis"
            print(f"SUCCESS: Trade balance includes analysis with trend: {analysis.get('trend')}")
    
    def test_trade_balance_estimation_flags(self):
        """Trade balance should mark estimations for recent years"""
        response = requests.get(
            f"{BASE_URL}/api/ai/balance/Kenya",
            params={"lang": "fr"},
            timeout=60
        )
        data = response.json()
        
        if data.get("trade_balance_history"):
            # Check if 2024 data is marked as estimation
            for item in data["trade_balance_history"]:
                if item.get("year") == 2024:
                    assert "is_estimation" in item, "2024 data should have is_estimation field"
                    print(f"SUCCESS: 2024 data has is_estimation={item.get('is_estimation')}")
                    break


class TestAIInvalidInputs:
    """Test error handling for invalid inputs"""
    
    def test_invalid_mode_returns_400(self):
        """Invalid mode should return 400 error"""
        response = requests.get(
            f"{BASE_URL}/api/ai/opportunities/Kenya",
            params={"mode": "invalid_mode", "lang": "fr"},
            timeout=30
        )
        assert response.status_code == 400
        print(f"SUCCESS: Invalid mode correctly returns 400")
    
    def test_valid_modes_accepted(self):
        """Valid modes (export, import, industrial) should be accepted"""
        valid_modes = ["export", "import", "industrial"]
        for mode in valid_modes:
            response = requests.get(
                f"{BASE_URL}/api/ai/opportunities/Kenya",
                params={"mode": mode, "lang": "fr"},
                timeout=60
            )
            assert response.status_code == 200, f"Mode {mode} should return 200"
        print(f"SUCCESS: All valid modes accepted")


class TestAILanguageSupport:
    """Test language support (fr/en)"""
    
    def test_french_language_response(self):
        """French language should return French content"""
        response = requests.get(
            f"{BASE_URL}/api/ai/opportunities/Kenya",
            params={"mode": "export", "lang": "fr"},
            timeout=60
        )
        data = response.json()
        # Just verify the request succeeds with French
        assert response.status_code == 200
        print(f"SUCCESS: French language request successful")
    
    def test_english_language_response(self):
        """English language should return English content"""
        response = requests.get(
            f"{BASE_URL}/api/ai/opportunities/Kenya",
            params={"mode": "export", "lang": "en"},
            timeout=60
        )
        data = response.json()
        assert response.status_code == 200
        print(f"SUCCESS: English language request successful")


class TestAISources:
    """Test that AI responses include source information"""
    
    def test_opportunities_include_sources(self):
        """AI opportunities should include data sources"""
        response = requests.get(
            f"{BASE_URL}/api/ai/opportunities/Kenya",
            params={"mode": "export", "lang": "fr"},
            timeout=60
        )
        data = response.json()
        
        # Check for sources field
        if "sources" in data:
            assert len(data["sources"]) > 0, "Sources list should not be empty"
            print(f"SUCCESS: Response includes sources: {data['sources'][:3]}")
        else:
            print(f"INFO: No sources field in response (may be in individual opportunities)")
    
    def test_opportunities_include_generated_by(self):
        """AI opportunities should indicate they were generated by Gemini"""
        response = requests.get(
            f"{BASE_URL}/api/ai/opportunities/Kenya",
            params={"mode": "export", "lang": "fr"},
            timeout=60
        )
        data = response.json()
        
        assert "generated_by" in data
        assert "Gemini" in data["generated_by"]
        print(f"SUCCESS: Response indicates generated by: {data['generated_by']}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
