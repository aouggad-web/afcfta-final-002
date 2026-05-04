"""
Test Suite for ZLECAf 2024-2025 Data Update
============================================
Tests the updated economic data for the 10 major African economies:
Nigeria, South Africa, Egypt, Algeria, Morocco, Kenya, Ethiopia, Ghana, Côte d'Ivoire, Tanzania

Also tests UNCTAD port statistics (Tanger Med: 10.24M TEU) and LSCI 2024 data.
"""

import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# 10 Major African Economies with expected 2024 data
# ISO2 codes for API calls
MAJOR_ECONOMIES = {
    'NG': {'name': 'Nigeria', 'iso3': 'NGA', 'expected_rank': 1, 'min_gdp_2024': 250},  # CSV has 253B, country_data.py has 334B - DATA DISCREPANCY
    'ZA': {'name': 'South Africa', 'iso3': 'ZAF', 'expected_rank': 2, 'min_gdp_2024': 350},  # ~373B USD
    'EG': {'name': 'Egypt', 'iso3': 'EGY', 'expected_rank': 3, 'min_gdp_2024': 300},  # ~349B USD
    'DZ': {'name': 'Algeria', 'iso3': 'DZA', 'expected_rank': 4, 'min_gdp_2024': 200},  # ~264B USD
    'MA': {'name': 'Morocco', 'iso3': 'MAR', 'expected_rank': 5, 'min_gdp_2024': 140},  # ~154B USD
    'KE': {'name': 'Kenya', 'iso3': 'KEN', 'expected_rank': 6, 'min_gdp_2024': 100},  # ~113B USD
    'ET': {'name': 'Ethiopia', 'iso3': 'ETH', 'expected_rank': 7, 'min_gdp_2024': 130},  # ~150B USD
    'GH': {'name': 'Ghana', 'iso3': 'GHA', 'expected_rank': 8, 'min_gdp_2024': 70},  # ~83B USD
    'CI': {'name': "Côte d'Ivoire", 'iso3': 'CIV', 'expected_rank': 9, 'min_gdp_2024': 70},  # ~87B USD
    'TZ': {'name': 'Tanzania', 'iso3': 'TZA', 'expected_rank': 10, 'min_gdp_2024': 70},  # ~79B USD
}


class TestHealthCheck:
    """Basic health check tests"""
    
    def test_api_health(self):
        """Test API health endpoint"""
        response = requests.get(f"{BASE_URL}/api/health")
        assert response.status_code == 200
        data = response.json()
        assert data['status'] == 'healthy'
        print(f"✅ API Health: {data['status']}")


class TestMajorEconomiesGDP2024:
    """Test GDP 2024 data for 10 major African economies"""
    
    @pytest.mark.parametrize("country_code,expected", [
        ('NG', MAJOR_ECONOMIES['NG']),
        ('ZA', MAJOR_ECONOMIES['ZA']),
        ('EG', MAJOR_ECONOMIES['EG']),
        ('DZ', MAJOR_ECONOMIES['DZ']),
        ('MA', MAJOR_ECONOMIES['MA']),
        ('KE', MAJOR_ECONOMIES['KE']),
        ('ET', MAJOR_ECONOMIES['ET']),
        ('GH', MAJOR_ECONOMIES['GH']),
        ('CI', MAJOR_ECONOMIES['CI']),
        ('TZ', MAJOR_ECONOMIES['TZ']),
    ])
    def test_country_profile_gdp_2024(self, country_code, expected):
        """Test country profile returns valid GDP 2024 data"""
        response = requests.get(f"{BASE_URL}/api/country-profile/{country_code}")
        assert response.status_code == 200, f"Failed to get profile for {country_code}"
        
        data = response.json()
        
        # Verify country name
        assert data['country_name'] is not None
        print(f"\n📊 {expected['name']} ({country_code}):")
        
        # Verify GDP 2024 exists and is reasonable
        gdp_usd = data.get('gdp_usd')
        if gdp_usd:
            gdp_billion = gdp_usd / 1e9
            print(f"   GDP 2024: ${gdp_billion:.2f}B USD")
            assert gdp_billion >= expected['min_gdp_2024'], f"GDP too low for {expected['name']}"
        
        # Verify GDP per capita exists
        gdp_per_capita = data.get('gdp_per_capita')
        if gdp_per_capita:
            print(f"   GDP per capita: ${gdp_per_capita:,.0f}")
            assert gdp_per_capita > 0
        
        # Verify population
        population = data.get('population')
        if population:
            print(f"   Population: {population:,}")
            assert population > 1000000  # At least 1M


class TestGrowthProjections2025:
    """Test growth projections for 2025"""
    
    @pytest.mark.parametrize("country_code,expected", [
        ('NG', MAJOR_ECONOMIES['NG']),
        ('ZA', MAJOR_ECONOMIES['ZA']),
        ('EG', MAJOR_ECONOMIES['EG']),
        ('DZ', MAJOR_ECONOMIES['DZ']),
        ('MA', MAJOR_ECONOMIES['MA']),
        ('KE', MAJOR_ECONOMIES['KE']),
        ('ET', MAJOR_ECONOMIES['ET']),
        ('GH', MAJOR_ECONOMIES['GH']),
        ('CI', MAJOR_ECONOMIES['CI']),
        ('TZ', MAJOR_ECONOMIES['TZ']),
    ])
    def test_growth_projection_2025(self, country_code, expected):
        """Test country has growth projection for 2025"""
        response = requests.get(f"{BASE_URL}/api/country-profile/{country_code}")
        assert response.status_code == 200
        
        data = response.json()
        projections = data.get('projections', {})
        
        print(f"\n📈 {expected['name']} Growth Projections:")
        
        # Check 2024 growth forecast
        growth_2024 = projections.get('gdp_growth_forecast_2024')
        if growth_2024:
            print(f"   2024 Growth: {growth_2024}")
        
        # Check 2025 growth projection
        growth_2025 = projections.get('gdp_growth_projection_2025')
        if growth_2025:
            print(f"   2025 Projection: {growth_2025}")
            # Verify it's a valid percentage string
            assert '%' in str(growth_2025) or isinstance(growth_2025, (int, float))


class TestAfricanRanking:
    """Test African economic ranking"""
    
    def test_nigeria_rank_1(self):
        """Nigeria should be ranked #1 in Africa by GDP"""
        response = requests.get(f"{BASE_URL}/api/country-profile/NG")
        assert response.status_code == 200
        data = response.json()
        
        projections = data.get('projections', {})
        africa_rank = projections.get('africa_rank')
        
        print(f"\n🏆 Nigeria Africa Rank: #{africa_rank}")
        assert africa_rank == 1, f"Nigeria should be #1, got #{africa_rank}"
    
    def test_south_africa_rank_2(self):
        """South Africa should be ranked #2 in Africa by GDP"""
        response = requests.get(f"{BASE_URL}/api/country-profile/ZA")
        assert response.status_code == 200
        data = response.json()
        
        projections = data.get('projections', {})
        africa_rank = projections.get('africa_rank')
        
        print(f"\n🏆 South Africa Africa Rank: #{africa_rank}")
        assert africa_rank == 2, f"South Africa should be #2, got #{africa_rank}"
    
    def test_egypt_rank_3(self):
        """Egypt should be ranked #3 in Africa by GDP"""
        response = requests.get(f"{BASE_URL}/api/country-profile/EG")
        assert response.status_code == 200
        data = response.json()
        
        projections = data.get('projections', {})
        africa_rank = projections.get('africa_rank')
        
        print(f"\n🏆 Egypt Africa Rank: #{africa_rank}")
        assert africa_rank == 3, f"Egypt should be #3, got #{africa_rank}"


class TestUNCTADPortStatistics:
    """Test UNCTAD port statistics - Tanger Med should be 10.24M TEU"""
    
    def test_unctad_ports_endpoint(self):
        """Test UNCTAD ports endpoint returns data"""
        response = requests.get(f"{BASE_URL}/api/statistics/unctad/ports")
        assert response.status_code == 200
        
        data = response.json()
        assert 'top_ports' in data
        print(f"\n🚢 UNCTAD Port Statistics:")
        print(f"   Total African Port Throughput: {data.get('total_african_port_throughput_teu_2024', 'N/A'):,} TEU")
    
    def test_tanger_med_throughput(self):
        """Tanger Med should have ~10.24M TEU throughput (2024)"""
        response = requests.get(f"{BASE_URL}/api/statistics/unctad/ports")
        assert response.status_code == 200
        
        data = response.json()
        top_ports = data.get('top_ports', [])
        
        # Find Tanger Med
        tanger_med = None
        for port in top_ports:
            if 'Tanger' in port.get('port', ''):
                tanger_med = port
                break
        
        assert tanger_med is not None, "Tanger Med not found in top ports"
        
        throughput = tanger_med.get('throughput_teu', 0)
        print(f"\n🚢 Tanger Med Port:")
        print(f"   Throughput: {throughput:,} TEU")
        print(f"   Rank Africa: #{tanger_med.get('rank_africa')}")
        print(f"   Rank Global: #{tanger_med.get('rank_global')}")
        print(f"   Growth Rate: {tanger_med.get('growth_rate')}%")
        
        # Verify Tanger Med is around 10.24M TEU (allow 5% tolerance)
        expected_teu = 10241392
        tolerance = 0.05
        min_teu = expected_teu * (1 - tolerance)
        max_teu = expected_teu * (1 + tolerance)
        
        assert min_teu <= throughput <= max_teu, f"Tanger Med TEU should be ~{expected_teu:,}, got {throughput:,}"
        
        # Verify it's ranked #1 in Africa
        assert tanger_med.get('rank_africa') == 1, "Tanger Med should be #1 in Africa"
    
    def test_top_african_ports_ranking(self):
        """Test top African ports are correctly ranked"""
        response = requests.get(f"{BASE_URL}/api/statistics/unctad/ports")
        assert response.status_code == 200
        
        data = response.json()
        top_ports = data.get('top_ports', [])
        
        print(f"\n🚢 Top 5 African Ports by TEU:")
        for i, port in enumerate(top_ports[:5]):
            print(f"   {i+1}. {port.get('port')} ({port.get('country')}): {port.get('throughput_teu', 0):,} TEU")
        
        # Verify ranking order
        for i in range(len(top_ports) - 1):
            current_teu = top_ports[i].get('throughput_teu', 0)
            next_teu = top_ports[i + 1].get('throughput_teu', 0)
            assert current_teu >= next_teu, f"Ports not sorted correctly: {top_ports[i]['port']} < {top_ports[i+1]['port']}"


class TestUNCTADLSCI:
    """Test UNCTAD Liner Shipping Connectivity Index 2024"""
    
    def test_lsci_endpoint(self):
        """Test LSCI endpoint returns data"""
        response = requests.get(f"{BASE_URL}/api/statistics/unctad/lsci")
        assert response.status_code == 200
        
        data = response.json()
        assert isinstance(data, list)
        assert len(data) > 0
        
        print(f"\n📊 UNCTAD LSCI 2024 - Top 5 African Countries:")
        for country in data[:5]:
            print(f"   {country.get('rank_africa')}. {country.get('country_fr')} - LSCI: {country.get('lsci_2024')} (Global #{country.get('rank_global')})")
    
    def test_morocco_lsci_rank_1(self):
        """Morocco should be #1 in Africa for LSCI"""
        response = requests.get(f"{BASE_URL}/api/statistics/unctad/lsci")
        assert response.status_code == 200
        
        data = response.json()
        
        # Find Morocco
        morocco = None
        for country in data:
            if country.get('country') == 'Morocco' or country.get('country_fr') == 'Maroc':
                morocco = country
                break
        
        assert morocco is not None, "Morocco not found in LSCI data"
        
        print(f"\n📊 Morocco LSCI 2024:")
        print(f"   LSCI Score: {morocco.get('lsci_2024')}")
        print(f"   Africa Rank: #{morocco.get('rank_africa')}")
        print(f"   Global Rank: #{morocco.get('rank_global')}")
        
        assert morocco.get('rank_africa') == 1, f"Morocco should be #1 in Africa LSCI, got #{morocco.get('rank_africa')}"
    
    def test_egypt_lsci_rank_2(self):
        """Egypt should be #2 in Africa for LSCI"""
        response = requests.get(f"{BASE_URL}/api/statistics/unctad/lsci")
        assert response.status_code == 200
        
        data = response.json()
        
        # Find Egypt
        egypt = None
        for country in data:
            if country.get('country') == 'Egypt' or country.get('country_fr') == 'Égypte':
                egypt = country
                break
        
        assert egypt is not None, "Egypt not found in LSCI data"
        
        print(f"\n📊 Egypt LSCI 2024:")
        print(f"   LSCI Score: {egypt.get('lsci_2024')}")
        print(f"   Africa Rank: #{egypt.get('rank_africa')}")
        
        assert egypt.get('rank_africa') == 2, f"Egypt should be #2 in Africa LSCI, got #{egypt.get('rank_africa')}"


class TestUNCTADTradeFlows:
    """Test UNCTAD trade flow statistics"""
    
    def test_trade_flows_endpoint(self):
        """Test trade flows endpoint returns data"""
        response = requests.get(f"{BASE_URL}/api/statistics/unctad/trade-flows")
        assert response.status_code == 200
        
        data = response.json()
        
        print(f"\n📈 UNCTAD Trade Flows 2024:")
        
        intra_african = data.get('intra_african_trade_2024', {})
        if intra_african:
            print(f"   Intra-African Trade: ${intra_african.get('value_billion_usd', 'N/A')}B USD")
            print(f"   Share of Total: {intra_african.get('share_total_african_trade', 'N/A')}%")
            print(f"   Growth Rate: {intra_african.get('growth_rate_2023_2024', 'N/A')}%")
        
        africa_world = data.get('africa_world_trade_2024', {})
        if africa_world:
            print(f"   Total Exports: ${africa_world.get('total_exports_billion_usd', 'N/A')}B USD")
            print(f"   Total Imports: ${africa_world.get('total_imports_billion_usd', 'N/A')}B USD")


class TestAllUNCTADData:
    """Test combined UNCTAD data endpoint"""
    
    def test_all_unctad_endpoint(self):
        """Test all UNCTAD data endpoint"""
        response = requests.get(f"{BASE_URL}/api/statistics/unctad")
        assert response.status_code == 200
        
        data = response.json()
        
        # Verify all sections present
        assert 'port_statistics' in data
        assert 'trade_flows' in data
        assert 'liner_connectivity_index' in data
        
        print(f"\n📊 All UNCTAD Data:")
        print(f"   Source: {data.get('source', 'N/A')}")
        print(f"   Year: {data.get('year', 'N/A')}")
        print(f"   Last Updated: {data.get('last_updated', 'N/A')}")


class TestRiskRatings:
    """Test risk ratings for major economies"""
    
    @pytest.mark.parametrize("country_code,expected", [
        ('NG', MAJOR_ECONOMIES['NG']),
        ('ZA', MAJOR_ECONOMIES['ZA']),
        ('EG', MAJOR_ECONOMIES['EG']),
        ('MA', MAJOR_ECONOMIES['MA']),
    ])
    def test_risk_ratings_present(self, country_code, expected):
        """Test country has risk ratings"""
        response = requests.get(f"{BASE_URL}/api/country-profile/{country_code}")
        assert response.status_code == 200
        
        data = response.json()
        risk_ratings = data.get('risk_ratings', {})
        
        print(f"\n⚠️ {expected['name']} Risk Ratings:")
        print(f"   S&P: {risk_ratings.get('sp', 'N/A')}")
        print(f"   Moody's: {risk_ratings.get('moodys', 'N/A')}")
        print(f"   Fitch: {risk_ratings.get('fitch', 'N/A')}")
        
        # At least one rating should be present
        has_rating = any([
            risk_ratings.get('sp') not in [None, 'NR'],
            risk_ratings.get('moodys') not in [None, 'NR'],
            risk_ratings.get('fitch') not in [None, 'NR']
        ])
        assert has_rating, f"No risk ratings found for {expected['name']}"


# Run tests if executed directly
if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
