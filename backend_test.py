"""
Comprehensive Backend API Testing for AFCFTA Trade Intelligence Platform
Tests all major API endpoints to verify functionality after routes registration fix
"""

import requests
import json
import sys
from typing import Dict, List, Tuple

# Backend URL from environment
BACKEND_URL = "https://git-sync-41.preview.emergentagent.com"

# Test results tracking
test_results = {
    "passed": [],
    "failed": [],
    "warnings": []
}

def log_test(endpoint: str, status: str, message: str = ""):
    """Log test result"""
    result = f"{endpoint}: {status}"
    if message:
        result += f" - {message}"
    
    if status == "✅ PASS":
        test_results["passed"].append(result)
        print(f"✅ {endpoint}")
    elif status == "❌ FAIL":
        test_results["failed"].append(result)
        print(f"❌ {endpoint} - {message}")
    else:
        test_results["warnings"].append(result)
        print(f"⚠️  {endpoint} - {message}")

def test_get(endpoint: str, expected_status: int = 200, description: str = "") -> Tuple[bool, dict]:
    """Test GET endpoint"""
    try:
        url = f"{BACKEND_URL}{endpoint}"
        response = requests.get(url, timeout=10)
        
        if response.status_code == expected_status:
            try:
                data = response.json()
                log_test(endpoint, "✅ PASS", description)
                return True, data
            except json.JSONDecodeError:
                log_test(endpoint, "❌ FAIL", f"Invalid JSON response")
                return False, {}
        else:
            log_test(endpoint, "❌ FAIL", f"Expected {expected_status}, got {response.status_code}")
            return False, {}
    except requests.exceptions.Timeout:
        log_test(endpoint, "❌ FAIL", "Request timeout")
        return False, {}
    except Exception as e:
        log_test(endpoint, "❌ FAIL", f"Exception: {str(e)}")
        return False, {}

def test_post(endpoint: str, payload: dict, expected_status: int = 200, description: str = "") -> Tuple[bool, dict]:
    """Test POST endpoint"""
    try:
        url = f"{BACKEND_URL}{endpoint}"
        response = requests.post(url, json=payload, timeout=10)
        
        if response.status_code == expected_status:
            try:
                data = response.json()
                log_test(endpoint, "✅ PASS", description)
                return True, data
            except json.JSONDecodeError:
                log_test(endpoint, "❌ FAIL", f"Invalid JSON response")
                return False, {}
        else:
            log_test(endpoint, "❌ FAIL", f"Expected {expected_status}, got {response.status_code}: {response.text[:200]}")
            return False, {}
    except requests.exceptions.Timeout:
        log_test(endpoint, "❌ FAIL", "Request timeout")
        return False, {}
    except Exception as e:
        log_test(endpoint, "❌ FAIL", f"Exception: {str(e)}")
        return False, {}

def main():
    print("=" * 80)
    print("AFCFTA BACKEND API TESTING")
    print("=" * 80)
    print(f"Backend URL: {BACKEND_URL}")
    print("=" * 80)
    print()

    # 1. Health Check (root level, not under /api)
    print("1. HEALTH CHECK")
    print("-" * 80)
    test_get("/health", 200, "Health check endpoint")
    print()

    # 2. Countries Endpoints
    print("2. COUNTRIES ENDPOINTS")
    print("-" * 80)
    success, data = test_get("/api/countries", 200, "List of African countries")
    if success and isinstance(data, list) and len(data) > 0:
        print(f"   → Found {len(data)} countries")
    print()

    # 3. OEC Trade Data Endpoints
    print("3. OEC TRADE DATA ENDPOINTS")
    print("-" * 80)
    test_get("/api/oec/countries", 200, "OEC African countries list")
    test_get("/api/oec/exports/DZA?year=2024&limit=10", 200, "Algeria exports data")
    test_get("/api/oec/imports/MAR?year=2024&limit=10", 200, "Morocco imports data")
    print()

    # 4. Production Endpoints
    print("4. PRODUCTION ENDPOINTS")
    print("-" * 80)
    
    # Test new production statistics endpoint
    success, stats_data = test_get("/api/production/statistics", 200, "Production module statistics")
    if success:
        # Verify structure
        if "years_covered" in stats_data and "dimensions" in stats_data:
            years = stats_data.get("years_covered", [])
            dimensions = stats_data.get("dimensions", {})
            print(f"   → Years covered: {len(years)} years")
            print(f"   → Dimensions: {', '.join(dimensions.keys())}")
            
            # Verify each dimension has years and source
            for dim_name, dim_data in dimensions.items():
                if "years" in dim_data and "source" in dim_data:
                    print(f"   → {dim_name}: {len(dim_data['years'])} years, source: {dim_data['source']}")
                else:
                    log_test(f"/api/production/statistics [{dim_name}]", "❌ FAIL", 
                            f"Missing 'years' or 'source' in dimension {dim_name}")
        else:
            log_test("/api/production/statistics", "❌ FAIL", 
                    "Missing 'years_covered' or 'dimensions' in response")
    
    # Test new macro endpoint with multiple countries
    print("   Testing macro endpoint with multiple countries:")
    test_countries = ["DZA", "MAR", "EGY", "KEN", "ZAF"]
    for country in test_countries:
        success, macro_data = test_get(f"/api/production/macro/{country}", 200, 
                                      f"Macro data for {country}")
        if success:
            # Verify structure
            required_fields = ["country_iso3", "total_records", "years_covered", 
                             "data_by_sector", "source"]
            missing_fields = [f for f in required_fields if f not in macro_data]
            if missing_fields:
                log_test(f"/api/production/macro/{country}", "❌ FAIL", 
                        f"Missing fields: {', '.join(missing_fields)}")
            else:
                sectors = macro_data.get("data_by_sector", {})
                years = macro_data.get("years_covered", [])
                records = macro_data.get("total_records", 0)
                print(f"      → {country}: {len(sectors)} sectors, {len(years)} years, {records} records")
                
                # Verify we have multiple sectors
                if len(sectors) < 3:
                    log_test(f"/api/production/macro/{country}", "⚠️  WARN", 
                            f"Only {len(sectors)} sectors found, expected at least 3")
                
                # Verify GDP growth indicator exists
                has_gdp_growth = False
                for sector_name, sector_records in sectors.items():
                    for record in sector_records:
                        if record.get("indicator_code") == "NY.GDP.MKTP.KD.ZG":
                            has_gdp_growth = True
                            break
                    if has_gdp_growth:
                        break
                
                if not has_gdp_growth:
                    log_test(f"/api/production/macro/{country}", "⚠️  WARN", 
                            "GDP growth indicator (NY.GDP.MKTP.KD.ZG) not found")
    
    # Test invalid country code (should return 404)
    test_get("/api/production/macro/XXX", 404, "Invalid country code (expected 404)")
    
    # Test existing production endpoints (regression check)
    test_get("/api/production/tracked-products", 200, "List of tracked products")
    test_get("/api/production/isic4/countries", 200, "ISIC4 covered countries")
    success, data = test_get("/api/production/isic4/countries", 200, "Get ISIC4 countries")
    if success and data.get("countries"):
        # Test with first available country
        first_country = data["countries"][0]
        test_get(f"/api/production/isic4/{first_country}", 200, f"ISIC4 data for {first_country}")
    print()

    # 5. Tariffs Endpoints
    print("5. TARIFFS ENDPOINTS")
    print("-" * 80)
    test_get("/api/hs6-tariffs/search?q=cafe&limit=5", 200, "Search HS6 tariffs for 'cafe'")
    test_get("/api/hs6-tariffs/code/090111", 200, "Get tariff for HS6 code 090111")
    test_get("/api/hs6-tariffs/chapter/09", 200, "Get tariffs for chapter 09")
    test_get("/api/hs6-tariffs/statistics", 200, "HS6 tariffs statistics")
    test_get("/api/country-tariffs/DZA?hs_code=0901", 200, "Algeria tariffs for HS 0901")
    test_get("/api/country-tariffs-comparison?countries=DZA,MAR,TUN&hs_code=0901", 200, "Compare tariffs")
    test_get("/api/bilateral-tariff/DZA/MAR/090111", 200, "Bilateral tariff DZA-MAR")
    print()

    # 6. HS Codes Endpoints
    print("6. HS CODES ENDPOINTS")
    print("-" * 80)
    test_get("/api/hs-codes/chapters", 200, "List of HS chapters")
    test_get("/api/hs-codes/search?q=coffee&limit=5", 200, "Search HS codes for 'coffee'")
    test_get("/api/hs-codes/code/090111", 200, "Get HS code 090111 details")
    test_get("/api/hs-codes/chapter/09", 200, "Get all codes in chapter 09")
    test_get("/api/hs-codes/statistics", 200, "HS codes statistics")
    print()

    # 7. Rules of Origin Endpoints
    print("7. RULES OF ORIGIN ENDPOINTS")
    print("-" * 80)
    test_get("/api/rules-of-origin/090111", 200, "Rules of origin for HS 090111")
    test_get("/api/rules-of-origin/stats", 200, "Rules of origin statistics")
    print()

    # 8. Statistics Endpoints
    print("8. STATISTICS ENDPOINTS")
    print("-" * 80)
    test_get("/api/statistics", 200, "Main statistics dashboard")
    test_get("/api/statistics/trade-products/summary", 200, "Trade products summary")
    test_get("/api/statistics/trade-products/exports-world", 200, "Africa exports to world")
    test_get("/api/statistics/trade-products/imports-world", 200, "Africa imports from world")
    test_get("/api/statistics/unctad/ports", 200, "UNCTAD port statistics")
    print()

    # 9. Contact Form (POST)
    print("9. CONTACT FORM ENDPOINT")
    print("-" * 80)
    contact_payload = {
        "name": "Test User",
        "email": "test@example.com",
        "message": "This is a test message from automated testing"
    }
    test_post("/api/contact", contact_payload, 200, "Submit contact form")
    print()

    # 10. Auth Endpoint (should return 401 without session)
    print("10. AUTH ENDPOINT (Expected 401)")
    print("-" * 80)
    test_get("/api/auth/me", 401, "Auth check without session (expected 401)")
    print()

    # 11. Currencies, Banking, Insurance
    print("11. FINANCIAL SERVICES ENDPOINTS")
    print("-" * 80)
    test_get("/api/currencies/list", 200, "Currencies list endpoint")
    test_get("/api/banking/countries", 200, "Banking countries list")
    test_get("/api/insurance/countries", 200, "Insurance countries list")
    print()

    # 12. Additional Country Endpoints
    print("12. COUNTRY PROFILE ENDPOINTS")
    print("-" * 80)
    test_get("/api/country-profile/DZA", 200, "Algeria country profile")
    test_get("/api/countries/economic-indicators", 200, "Economic indicators for all countries")
    print()

    # Print Summary
    print()
    print("=" * 80)
    print("TEST SUMMARY")
    print("=" * 80)
    print(f"✅ PASSED: {len(test_results['passed'])}")
    print(f"❌ FAILED: {len(test_results['failed'])}")
    print(f"⚠️  WARNINGS: {len(test_results['warnings'])}")
    print()

    if test_results['failed']:
        print("FAILED TESTS:")
        print("-" * 80)
        for failure in test_results['failed']:
            print(f"  {failure}")
        print()

    if test_results['warnings']:
        print("WARNINGS:")
        print("-" * 80)
        for warning in test_results['warnings']:
            print(f"  {warning}")
        print()

    # Exit with appropriate code
    if test_results['failed']:
        sys.exit(1)
    else:
        print("✅ ALL CRITICAL TESTS PASSED!")
        sys.exit(0)

if __name__ == "__main__":
    main()
