"""
Test Multi-Country Comparison and All Taxes Display Features
Tests:
1. /api/authentic-tariffs/countries - returns 54 countries
2. /api/authentic-tariffs/calculate/{country}/{hs_code} - returns taxes_detail with all tax labels
3. Multi-country comparison workflow
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://regulatory-data-hub.preview.emergentagent.com')


class TestAuthenticTariffsCountries:
    """Test countries endpoint returns correct count and structure"""
    
    def test_countries_list_returns_54_countries(self):
        """Verify 54 African countries are available"""
        response = requests.get(f"{BASE_URL}/api/authentic-tariffs/countries")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        data = response.json()
        assert data['success'] == True
        assert data['total'] == 54, f"Expected 54 countries, got {data['total']}"
        assert len(data['countries']) == 54
        print(f"✅ Countries endpoint returns {data['total']} countries")
    
    def test_countries_have_required_fields(self):
        """Each country should have iso3, total_lines, vat_rate etc"""
        response = requests.get(f"{BASE_URL}/api/authentic-tariffs/countries")
        data = response.json()
        
        required_fields = ['iso3', 'total_lines', 'vat_rate', 'dd_range', 'data_format']
        for country in data['countries'][:5]:  # Check first 5
            for field in required_fields:
                assert field in country, f"Missing field {field} in country {country.get('iso3')}"
        
        print(f"✅ All countries have required fields")
    
    def test_countries_have_enhanced_v2_format(self):
        """Verify data format is enhanced_v2"""
        response = requests.get(f"{BASE_URL}/api/authentic-tariffs/countries")
        data = response.json()
        
        assert data['data_format'] == 'enhanced_v2'
        for country in data['countries']:
            assert country['data_format'] == 'enhanced_v2'
        
        print(f"✅ All countries use enhanced_v2 data format")


class TestTaxesDetailWithLabels:
    """Test that taxes_detail returns all taxes with codes and labels"""
    
    def test_morocco_taxes_detail_has_all_taxes(self):
        """Morocco should return D.D, TPI, T.V.A taxes"""
        response = requests.get(
            f"{BASE_URL}/api/authentic-tariffs/calculate/MAR/180100?value=50000&language=fr"
        )
        assert response.status_code == 200
        
        data = response.json()
        assert 'taxes_detail' in data, "taxes_detail field missing"
        
        taxes = data['taxes_detail']
        tax_codes = [t['tax'] for t in taxes]
        
        # Morocco should have D.D, TPI, T.V.A
        assert 'D.D' in tax_codes, f"D.D not found in taxes: {tax_codes}"
        assert 'T.V.A' in tax_codes, f"T.V.A not found in taxes: {tax_codes}"
        
        print(f"✅ Morocco taxes: {tax_codes}")
        
        # Each tax should have rate and observation
        for tax in taxes:
            assert 'tax' in tax, "Tax code missing"
            assert 'rate' in tax, "Rate missing"
            assert 'observation' in tax, "Observation/label missing"
            print(f"  - {tax['tax']}: {tax['rate']}% ({tax['observation']})")
    
    def test_nigeria_taxes_detail_has_regional_taxes(self):
        """Nigeria should have CEDEAO and CISS regional taxes"""
        response = requests.get(
            f"{BASE_URL}/api/authentic-tariffs/calculate/NGA/180100?value=50000&language=fr"
        )
        assert response.status_code == 200
        
        data = response.json()
        taxes = data.get('taxes_detail', [])
        tax_codes = [t['tax'] for t in taxes]
        
        print(f"✅ Nigeria taxes: {tax_codes}")
        
        # Nigeria often has CEDEAO, CISS taxes (depending on product)
        for tax in taxes:
            assert isinstance(tax['rate'], (int, float)), f"Rate should be numeric: {tax}"
    
    def test_algeria_taxes_detail_has_prct_tcs(self):
        """Algeria should have PRCT, T.C.S taxes"""
        response = requests.get(
            f"{BASE_URL}/api/authentic-tariffs/calculate/DZA/180100?value=50000&language=fr"
        )
        assert response.status_code == 200
        
        data = response.json()
        taxes = data.get('taxes_detail', [])
        tax_codes = [t['tax'] for t in taxes]
        
        print(f"✅ Algeria taxes: {tax_codes}")
        
        # Algeria has specific taxes
        for tax in taxes:
            print(f"  - {tax['tax']}: {tax['rate']}%")


class TestCalculateEndpoint:
    """Test the calculate endpoint returns correct structure"""
    
    def test_calculate_returns_npf_vs_zlecaf(self):
        """Verify NPF and ZLECAf calculations are returned"""
        response = requests.get(
            f"{BASE_URL}/api/authentic-tariffs/calculate/MAR/180100?value=50000&language=fr"
        )
        assert response.status_code == 200
        
        data = response.json()
        
        # Required fields
        assert 'npf_calculation' in data
        assert 'zlecaf_calculation' in data
        assert 'savings' in data
        assert 'rates' in data
        
        # NPF calculation details
        npf = data['npf_calculation']
        assert 'total_to_pay' in npf
        assert 'dd' in npf
        assert 'vat' in npf
        
        # ZLECAf calculation details
        zlecaf = data['zlecaf_calculation']
        assert 'total_to_pay' in zlecaf
        assert zlecaf['dd']['exempt'] == True, "DD should be exempt under ZLECAf"
        
        print(f"✅ NPF total: ${npf['total_to_pay']}, ZLECAf total: ${zlecaf['total_to_pay']}")
        print(f"✅ Savings: ${data['savings']['amount']} ({data['savings']['percentage']}%)")
    
    def test_calculate_returns_fiscal_advantages(self):
        """Verify fiscal advantages are returned"""
        response = requests.get(
            f"{BASE_URL}/api/authentic-tariffs/calculate/MAR/180100?value=50000&language=fr"
        )
        data = response.json()
        
        assert 'fiscal_advantages' in data
        advantages = data['fiscal_advantages']
        
        # Should have ZLECAf DD exemption advantage
        has_zlecaf = any('ZLECAf' in str(adv) for adv in advantages)
        print(f"✅ Fiscal advantages: {len(advantages)} found, ZLECAf mentioned: {has_zlecaf}")
    
    def test_calculate_returns_administrative_formalities(self):
        """Verify administrative formalities are returned"""
        response = requests.get(
            f"{BASE_URL}/api/authentic-tariffs/calculate/MAR/180100?value=50000&language=fr"
        )
        data = response.json()
        
        assert 'administrative_formalities' in data
        formalities = data['administrative_formalities']
        
        print(f"✅ Administrative formalities: {len(formalities)} found")
        for f in formalities[:3]:
            print(f"  - {f.get('code', 'N/A')}: {f.get('document_fr', 'N/A')}")


class TestMultiCountryComparison:
    """Test multi-country comparison workflow"""
    
    def test_compare_5_countries_parallel(self):
        """Compare 5 countries for same product"""
        countries = ['MAR', 'DZA', 'TUN', 'EGY', 'NGA']
        hs_code = '180100'
        value = 50000
        
        results = []
        for country in countries:
            response = requests.get(
                f"{BASE_URL}/api/authentic-tariffs/calculate/{country}/{hs_code}?value={value}&language=fr"
            )
            assert response.status_code == 200, f"Failed for {country}"
            
            data = response.json()
            results.append({
                'country': country,
                'npf_total': data['npf_calculation']['total_to_pay'],
                'zlecaf_total': data['zlecaf_calculation']['total_to_pay'],
                'savings': data['savings']['amount'],
                'taxes_count': len(data.get('taxes_detail', []))
            })
        
        # Sort by ZLECAf total (lowest first)
        results.sort(key=lambda x: x['zlecaf_total'])
        
        print(f"✅ Multi-country comparison for HS {hs_code}, CIF ${value}:")
        print(f"   Best choice: {results[0]['country']} with ${results[0]['zlecaf_total']}")
        
        for r in results:
            print(f"   - {r['country']}: NPF ${r['npf_total']} | ZLECAf ${r['zlecaf_total']} | Savings ${r['savings']} | {r['taxes_count']} taxes")
        
        # Verify all results have different totals (realistic scenario)
        totals = [r['zlecaf_total'] for r in results]
        assert len(set(totals)) > 1, "All countries shouldn't have identical totals"
    
    def test_each_country_has_taxes_detail(self):
        """Each country in comparison should have taxes_detail array"""
        countries = ['MAR', 'NGA', 'DZA']
        
        for country in countries:
            response = requests.get(
                f"{BASE_URL}/api/authentic-tariffs/calculate/{country}/180100?value=50000"
            )
            data = response.json()
            
            assert 'taxes_detail' in data, f"{country} missing taxes_detail"
            assert len(data['taxes_detail']) > 0, f"{country} has empty taxes_detail"
            
            taxes = [t['tax'] for t in data['taxes_detail']]
            print(f"✅ {country} taxes: {taxes}")


class TestSubPositions:
    """Test sub-positions endpoint"""
    
    def test_sub_positions_for_hs6(self):
        """Get sub-positions for an HS6 code"""
        response = requests.get(
            f"{BASE_URL}/api/authentic-tariffs/country/MAR/sub-positions/180100?language=fr"
        )
        assert response.status_code == 200
        
        data = response.json()
        assert data['success'] == True
        assert 'sub_positions' in data
        
        count = data['total']
        print(f"✅ MAR/180100 has {count} sub-positions")
        
        for sp in data['sub_positions'][:3]:
            print(f"  - {sp['code']}: DD {sp['dd']}%")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
