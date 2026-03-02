"""
Backend API tests for ZLECAf Dashboard Dynamic Widgets
Tests all API endpoints used by the dashboard widgets for real-time data
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://afcfta-trade-calc.preview.emergentagent.com')

class TestHealthEndpoints:
    """Health check endpoint tests"""
    
    def test_health_check(self):
        """Test basic health endpoint"""
        response = requests.get(f"{BASE_URL}/api/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "timestamp" in data
        print(f"✓ Health check passed: {data['status']}")
    
    def test_detailed_health_status(self):
        """Test detailed health status endpoint"""
        response = requests.get(f"{BASE_URL}/api/health/status")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "checks" in data
        print(f"✓ Detailed health check passed: {data['status']}")


class TestStatisticsEndpoint:
    """Tests for /api/statistics - Used by LiveTradeWidget and AfCFTAProgressWidget"""
    
    def test_statistics_endpoint_returns_200(self):
        """Test statistics endpoint returns 200"""
        response = requests.get(f"{BASE_URL}/api/statistics")
        assert response.status_code == 200
        print("✓ Statistics endpoint returns 200")
    
    def test_statistics_trade_evolution_data(self):
        """Test trade evolution data structure and values"""
        response = requests.get(f"{BASE_URL}/api/statistics")
        assert response.status_code == 200
        data = response.json()
        
        # Verify trade_evolution exists
        assert "trade_evolution" in data
        trade_evo = data["trade_evolution"]
        
        # Verify expected values from requirements
        assert trade_evo.get("intra_african_trade_2024") == 218.7, f"Expected 218.7, got {trade_evo.get('intra_african_trade_2024')}"
        assert trade_evo.get("total_exports_2024") == 553.7, f"Expected 553.7, got {trade_evo.get('total_exports_2024')}"
        print(f"✓ Trade evolution data verified: Intra-African=${trade_evo['intra_african_trade_2024']}B, Total Exports=${trade_evo['total_exports_2024']}B")
    
    def test_statistics_top_exporters(self):
        """Test top exporters data"""
        response = requests.get(f"{BASE_URL}/api/statistics")
        assert response.status_code == 200
        data = response.json()
        
        assert "top_exporters_2024" in data
        exporters = data["top_exporters_2024"]
        assert len(exporters) >= 5, f"Expected at least 5 exporters, got {len(exporters)}"
        
        # Verify structure of first exporter
        first_exporter = exporters[0]
        assert "country" in first_exporter
        assert "name" in first_exporter
        assert "share_pct" in first_exporter
        print(f"✓ Top exporters verified: {len(exporters)} countries, top is {first_exporter['name']}")
    
    def test_statistics_top_importers(self):
        """Test top importers data"""
        response = requests.get(f"{BASE_URL}/api/statistics")
        assert response.status_code == 200
        data = response.json()
        
        assert "top_importers_2024" in data
        importers = data["top_importers_2024"]
        assert len(importers) >= 5, f"Expected at least 5 importers, got {len(importers)}"
        print(f"✓ Top importers verified: {len(importers)} countries")
    
    def test_statistics_zlecaf_impact_metrics(self):
        """Test ZLECAf impact metrics for AfCFTAProgressWidget"""
        response = requests.get(f"{BASE_URL}/api/statistics")
        assert response.status_code == 200
        data = response.json()
        
        assert "zlecaf_impact_metrics" in data or "zlecaf_impact" in data
        print("✓ ZLECAf impact metrics present")


class TestUNCTADPortsEndpoint:
    """Tests for /api/statistics/unctad/ports - Used by LivePortsWidget"""
    
    def test_ports_endpoint_returns_200(self):
        """Test UNCTAD ports endpoint returns 200"""
        response = requests.get(f"{BASE_URL}/api/statistics/unctad/ports")
        assert response.status_code == 200
        print("✓ UNCTAD ports endpoint returns 200")
    
    def test_ports_total_throughput(self):
        """Test port throughput data - Expected 28.5M TEU"""
        response = requests.get(f"{BASE_URL}/api/statistics/unctad/ports")
        assert response.status_code == 200
        data = response.json()
        
        assert "total_african_port_throughput_teu_2023" in data
        throughput = data["total_african_port_throughput_teu_2023"]
        # Expected ~28.5M TEU (28,500,000)
        assert throughput >= 25000000, f"Expected throughput >= 25M TEU, got {throughput}"
        print(f"✓ Port throughput verified: {throughput/1000000:.1f}M TEU")
    
    def test_ports_growth_rate(self):
        """Test port growth rate data"""
        response = requests.get(f"{BASE_URL}/api/statistics/unctad/ports")
        assert response.status_code == 200
        data = response.json()
        
        assert "growth_rate_2022_2023" in data
        growth = data["growth_rate_2022_2023"]
        assert isinstance(growth, (int, float))
        print(f"✓ Port growth rate verified: {growth}%")
    
    def test_ports_top_ports_list(self):
        """Test top ports list"""
        response = requests.get(f"{BASE_URL}/api/statistics/unctad/ports")
        assert response.status_code == 200
        data = response.json()
        
        assert "top_ports" in data
        ports = data["top_ports"]
        assert len(ports) >= 6, f"Expected at least 6 ports, got {len(ports)}"
        
        # Verify port structure
        first_port = ports[0]
        assert "port" in first_port
        assert "throughput_teu" in first_port
        print(f"✓ Top ports verified: {len(ports)} ports, top is {first_port['port']}")


class TestUNCTADLSCIEndpoint:
    """Tests for /api/statistics/unctad/lsci - Used by LSCIChartWidget"""
    
    def test_lsci_endpoint_returns_200(self):
        """Test LSCI endpoint returns 200"""
        response = requests.get(f"{BASE_URL}/api/statistics/unctad/lsci")
        assert response.status_code == 200
        print("✓ LSCI endpoint returns 200")
    
    def test_lsci_data_structure(self):
        """Test LSCI data structure - Expected 8 African countries"""
        response = requests.get(f"{BASE_URL}/api/statistics/unctad/lsci")
        assert response.status_code == 200
        data = response.json()
        
        assert isinstance(data, list)
        assert len(data) >= 8, f"Expected at least 8 countries, got {len(data)}"
        
        # Verify structure
        first_country = data[0]
        assert "country" in first_country
        assert "country_fr" in first_country
        assert "lsci_2023" in first_country
        assert "rank_africa" in first_country
        print(f"✓ LSCI data verified: {len(data)} countries")
    
    def test_lsci_top_countries(self):
        """Test LSCI top countries - Morocco should be #1 in Africa"""
        response = requests.get(f"{BASE_URL}/api/statistics/unctad/lsci")
        assert response.status_code == 200
        data = response.json()
        
        # Find Morocco
        morocco = next((c for c in data if c["country"] == "Morocco"), None)
        assert morocco is not None, "Morocco should be in LSCI data"
        assert morocco["rank_africa"] == 1, f"Morocco should be rank 1 in Africa, got {morocco['rank_africa']}"
        print(f"✓ LSCI top country verified: Morocco with LSCI {morocco['lsci_2023']}")


class TestCountryProfileEndpoint:
    """Tests for /api/country-profile/{code} - Used by CountryProfileWidget"""
    
    def test_country_profile_dz_returns_200(self):
        """Test Algeria country profile returns 200"""
        response = requests.get(f"{BASE_URL}/api/country-profile/DZ")
        assert response.status_code == 200
        print("✓ Country profile DZ returns 200")
    
    def test_country_profile_dz_data(self):
        """Test Algeria country profile data structure"""
        response = requests.get(f"{BASE_URL}/api/country-profile/DZ")
        assert response.status_code == 200
        data = response.json()
        
        # Verify basic fields
        assert data["country_name"] == "Algérie"
        assert data["country_code"] == "DZ"
        assert "gdp_usd" in data
        assert "population" in data
        
        # Verify GDP is reasonable (Algeria ~$266B)
        gdp = data["gdp_usd"]
        assert gdp > 200000000000, f"Expected GDP > $200B, got {gdp}"
        
        # Verify population is reasonable (Algeria ~47M)
        pop = data["population"]
        assert pop > 40000000, f"Expected population > 40M, got {pop}"
        
        print(f"✓ Country profile DZ verified: {data['country_name']}, GDP=${gdp/1e9:.1f}B, Pop={pop/1e6:.1f}M")
    
    def test_country_profile_dz_projections(self):
        """Test Algeria country profile projections data"""
        response = requests.get(f"{BASE_URL}/api/country-profile/DZ")
        assert response.status_code == 200
        data = response.json()
        
        assert "projections" in data
        projections = data["projections"]
        
        # Verify exports data
        assert "exports_2024_billion_usd" in projections
        exports = projections["exports_2024_billion_usd"]
        assert exports > 30, f"Expected exports > $30B, got {exports}"
        print(f"✓ Country profile projections verified: Exports=${exports}B")
    
    def test_country_profile_invalid_code(self):
        """Test invalid country code returns 404"""
        response = requests.get(f"{BASE_URL}/api/country-profile/XX")
        assert response.status_code == 404
        print("✓ Invalid country code returns 404")


class TestCountriesEndpoint:
    """Tests for /api/countries endpoint"""
    
    def test_countries_endpoint_returns_200(self):
        """Test countries endpoint returns 200"""
        response = requests.get(f"{BASE_URL}/api/countries")
        assert response.status_code == 200
        print("✓ Countries endpoint returns 200")
    
    def test_countries_count(self):
        """Test 54 African countries are returned"""
        response = requests.get(f"{BASE_URL}/api/countries")
        assert response.status_code == 200
        data = response.json()
        
        assert len(data) == 54, f"Expected 54 countries, got {len(data)}"
        print(f"✓ Countries count verified: {len(data)} countries")
    
    def test_countries_language_fr(self):
        """Test French language translations"""
        response = requests.get(f"{BASE_URL}/api/countries?lang=fr")
        assert response.status_code == 200
        data = response.json()
        
        # Find Algeria
        algeria = next((c for c in data if c["code"] == "DZ"), None)
        assert algeria is not None
        assert algeria["name"] == "Algérie"
        print(f"✓ French translation verified: {algeria['name']}")
    
    def test_countries_language_en(self):
        """Test English language translations"""
        response = requests.get(f"{BASE_URL}/api/countries?lang=en")
        assert response.status_code == 200
        data = response.json()
        
        # Find Algeria
        algeria = next((c for c in data if c["code"] == "DZ"), None)
        assert algeria is not None
        assert algeria["name"] == "Algeria"
        print(f"✓ English translation verified: {algeria['name']}")


class TestRulesOfOriginEndpoint:
    """Tests for /api/rules-of-origin/{hs_code} endpoint"""
    
    def test_rules_of_origin_returns_200(self):
        """Test rules of origin endpoint returns 200"""
        response = requests.get(f"{BASE_URL}/api/rules-of-origin/0901")
        assert response.status_code == 200
        print("✓ Rules of origin endpoint returns 200")
    
    def test_rules_of_origin_data_structure(self):
        """Test rules of origin data structure"""
        response = requests.get(f"{BASE_URL}/api/rules-of-origin/0901")
        assert response.status_code == 200
        data = response.json()
        
        assert "hs_code" in data
        assert "rules" in data
        assert "explanation" in data
        print(f"✓ Rules of origin structure verified for HS code {data['hs_code']}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
