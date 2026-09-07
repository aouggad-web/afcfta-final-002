#!/usr/bin/env python3
"""
AFCFTA Backend API Testing - Post-Merge Regression & New Features
==================================================================
Tests after git merge that:
1. Restored server.py's full router registration (security middlewares, MongoDB indexes)
2. Added UNIDO manufacturing dataset (54 countries) + mining/agriculture data
3. Fixed route double-prefix bug in production.py
4. Added CSRF protection (double-submit cookie pattern)

Test Requirements:
- Use requests.Session() to maintain cookies (CSRF token persistence)
- Test all GET endpoints for 200 OK with real JSON
- Test CSRF protection: POST without token = 403, POST with token = 200
- Verify no double-prefix issues (e.g., /api/api/*)
- Check new UNIDO endpoints
"""

import requests
import json
import sys
from typing import Dict, List, Tuple

# Backend URL from frontend/.env
BASE_URL = "https://git-sync-41.preview.emergentagent.com"

# Test results tracking
test_results = {
    "passed": [],
    "failed": [],
    "total": 0
}


def log_test(name: str, passed: bool, details: str = ""):
    """Log test result"""
    test_results["total"] += 1
    if passed:
        test_results["passed"].append(name)
        print(f"✅ PASS: {name}")
        if details:
            print(f"   {details}")
    else:
        test_results["failed"].append({"name": name, "details": details})
        print(f"❌ FAIL: {name}")
        if details:
            print(f"   {details}")


def test_get_endpoint(session: requests.Session, path: str, name: str, 
                      expected_keys: List[str] = None, min_items: int = None):
    """Test a GET endpoint"""
    try:
        url = f"{BASE_URL}{path}"
        response = session.get(url, timeout=30)
        
        if response.status_code != 200:
            log_test(name, False, f"Status {response.status_code}: {response.text[:200]}")
            return False
        
        # Check if response is JSON
        try:
            data = response.json()
        except json.JSONDecodeError:
            log_test(name, False, f"Response is not JSON: {response.text[:200]}")
            return False
        
        # Check for expected keys
        if expected_keys:
            missing_keys = [k for k in expected_keys if k not in data]
            if missing_keys:
                log_test(name, False, f"Missing keys: {missing_keys}")
                return False
        
        # Check for minimum items (if data is a list or has a list field)
        if min_items is not None:
            if isinstance(data, list):
                if len(data) < min_items:
                    log_test(name, False, f"Expected at least {min_items} items, got {len(data)}")
                    return False
            elif isinstance(data, dict):
                # Check common list fields
                for key in ['countries', 'data', 'sectors', 'ranking', 'products']:
                    if key in data and isinstance(data[key], list):
                        if len(data[key]) < min_items:
                            log_test(name, False, f"Expected at least {min_items} items in '{key}', got {len(data[key])}")
                            return False
                        break
        
        log_test(name, True, f"Status 200, valid JSON")
        return True
        
    except requests.exceptions.RequestException as e:
        log_test(name, False, f"Request error: {str(e)}")
        return False


def test_csrf_protection(session: requests.Session):
    """Test CSRF protection mechanism"""
    print("\n" + "="*80)
    print("CSRF PROTECTION TESTS")
    print("="*80)
    
    # Test 1: POST without CSRF token (should fail with 403)
    try:
        # Create a new session without any prior GET request
        fresh_session = requests.Session()
        url = f"{BASE_URL}/api/contact"
        payload = {
            "name": "Test User",
            "email": "test@example.com",
            "subject": "CSRF Test",
            "message": "Testing CSRF protection without token"
        }
        response = fresh_session.post(url, json=payload, timeout=30)
        
        if response.status_code == 403:
            try:
                error_data = response.json()
                if "CSRF" in error_data.get("detail", "").upper():
                    log_test("CSRF: POST without token returns 403", True, 
                            f"Correctly rejected: {error_data.get('detail')}")
                else:
                    log_test("CSRF: POST without token returns 403", False, 
                            f"403 but wrong error message: {error_data}")
            except:
                log_test("CSRF: POST without token returns 403", True, 
                        "Correctly rejected with 403")
        else:
            log_test("CSRF: POST without token returns 403", False, 
                    f"Expected 403, got {response.status_code}")
    except Exception as e:
        log_test("CSRF: POST without token returns 403", False, f"Error: {str(e)}")
    
    # Test 2: GET to obtain CSRF token, then POST with token (should succeed)
    try:
        # Use the main session that has been making GET requests
        # First, make a GET request to ensure we have a CSRF token
        session.get(f"{BASE_URL}/api/countries", timeout=30)
        
        # Check if we have the CSRF token cookie
        csrf_cookie = session.cookies.get("csrf_token")
        if not csrf_cookie:
            log_test("CSRF: GET request sets csrf_token cookie", False, 
                    "No csrf_token cookie found after GET request")
            return
        
        log_test("CSRF: GET request sets csrf_token cookie", True, 
                f"Cookie value: {csrf_cookie[:20]}...")
        
        # Now POST with the CSRF token in header
        url = f"{BASE_URL}/api/contact"
        payload = {
            "name": "Test User",
            "email": "test@afcfta.com",
            "subject": "CSRF Test with Token",
            "message": "Testing CSRF protection with valid token"
        }
        headers = {
            "X-CSRF-Token": csrf_cookie,
            "Content-Type": "application/json"
        }
        response = session.post(url, json=payload, headers=headers, timeout=30)
        
        if response.status_code == 200:
            log_test("CSRF: POST with valid token succeeds", True, 
                    "Contact form submitted successfully")
        else:
            log_test("CSRF: POST with valid token succeeds", False, 
                    f"Expected 200, got {response.status_code}: {response.text[:200]}")
    except Exception as e:
        log_test("CSRF: POST with valid token succeeds", False, f"Error: {str(e)}")


def main():
    """Run all backend tests"""
    print("="*80)
    print("AFCFTA BACKEND API TESTING - POST-MERGE REGRESSION & NEW FEATURES")
    print("="*80)
    print(f"Base URL: {BASE_URL}")
    print(f"Testing Date: 2026-09-07")
    print("="*80)
    
    # Create a session to maintain cookies (for CSRF)
    session = requests.Session()
    
    # =========================================================================
    # 1. HEALTH CHECK
    # =========================================================================
    print("\n" + "="*80)
    print("1. HEALTH CHECK")
    print("="*80)
    
    test_get_endpoint(session, "/health", "GET /health", 
                     expected_keys=None)  # May return HTML or JSON
    
    # =========================================================================
    # 2. COUNTRIES & PROFILES
    # =========================================================================
    print("\n" + "="*80)
    print("2. COUNTRIES & PROFILES")
    print("="*80)
    
    test_get_endpoint(session, "/api/countries", "GET /api/countries", 
                     min_items=50)
    
    # =========================================================================
    # 3. OEC TRADE DATA
    # =========================================================================
    print("\n" + "="*80)
    print("3. OEC TRADE DATA")
    print("="*80)
    
    test_get_endpoint(session, "/api/oec/countries", "GET /api/oec/countries", 
                     min_items=50)
    
    # =========================================================================
    # 4. PRODUCTION DATA - ISIC4
    # =========================================================================
    print("\n" + "="*80)
    print("4. PRODUCTION DATA - ISIC4")
    print("="*80)
    
    test_get_endpoint(session, "/api/production/isic4/countries", 
                     "GET /api/production/isic4/countries", 
                     expected_keys=["countries", "count"])
    
    test_get_endpoint(session, "/api/production/isic4/MAR", 
                     "GET /api/production/isic4/MAR", 
                     expected_keys=["country_iso3", "sectors"])
    
    test_get_endpoint(session, "/api/production/isic4/MAR/1010", 
                     "GET /api/production/isic4/MAR/1010 (timeseries)", 
                     expected_keys=["country_iso3", "isic4"])
    
    # =========================================================================
    # 5. PRODUCTION DATA - UNIDO (NEW)
    # =========================================================================
    print("\n" + "="*80)
    print("5. PRODUCTION DATA - UNIDO (NEW)")
    print("="*80)
    
    test_get_endpoint(session, "/api/production/unido/MAR", 
                     "GET /api/production/unido/MAR", 
                     expected_keys=["country_iso3"])
    
    test_get_endpoint(session, "/api/production/unido/statistics", 
                     "GET /api/production/unido/statistics", 
                     expected_keys=["total_countries", "total_mva_mln_usd"])
    
    test_get_endpoint(session, "/api/production/unido/ranking", 
                     "GET /api/production/unido/ranking", 
                     expected_keys=["ranking"], min_items=50)
    
    test_get_endpoint(session, "/api/production/unido/isic4/MAR", 
                     "GET /api/production/unido/isic4/MAR", 
                     expected_keys=["country_iso3"])
    
    # =========================================================================
    # 6. PRODUCTION DATA - MINING (NEW)
    # =========================================================================
    print("\n" + "="*80)
    print("6. PRODUCTION DATA - MINING (NEW)")
    print("="*80)
    
    test_get_endpoint(session, "/api/production/mining/ZAF", 
                     "GET /api/production/mining/ZAF", 
                     expected_keys=["country_iso3"])
    
    # =========================================================================
    # 7. PRODUCTION DATA - MACRO & STATISTICS (RESTORED)
    # =========================================================================
    print("\n" + "="*80)
    print("7. PRODUCTION DATA - MACRO & STATISTICS (RESTORED)")
    print("="*80)
    
    test_get_endpoint(session, "/api/production/statistics", 
                     "GET /api/production/statistics", 
                     expected_keys=["years_covered"])
    
    test_get_endpoint(session, "/api/production/macro/DZA", 
                     "GET /api/production/macro/DZA", 
                     expected_keys=["country_iso3", "data_by_sector"])
    
    # =========================================================================
    # 8. TARIFFS
    # =========================================================================
    print("\n" + "="*80)
    print("8. TARIFFS")
    print("="*80)
    
    test_get_endpoint(session, "/api/tariffs", "GET /api/tariffs")
    
    # =========================================================================
    # 9. RULES OF ORIGIN
    # =========================================================================
    print("\n" + "="*80)
    print("9. RULES OF ORIGIN")
    print("="*80)
    
    test_get_endpoint(session, "/api/rules-of-origin/chapters", 
                     "GET /api/rules-of-origin/chapters", 
                     min_items=90)
    
    # =========================================================================
    # 10. TRACKED PRODUCTS & CAPACITY
    # =========================================================================
    print("\n" + "="*80)
    print("10. TRACKED PRODUCTS & CAPACITY")
    print("="*80)
    
    test_get_endpoint(session, "/api/production/tracked-products", 
                     "GET /api/production/tracked-products", 
                     expected_keys=["products", "total"])
    
    # Test capacity endpoint (if available)
    try:
        url = f"{BASE_URL}/api/production/capacity/0901"
        response = session.get(url, timeout=30)
        if response.status_code == 200:
            log_test("GET /api/production/capacity/0901", True, "Capacity endpoint available")
        elif response.status_code == 503:
            log_test("GET /api/production/capacity/0901", True, 
                    "Capacity service unavailable (expected if data files missing)")
        else:
            log_test("GET /api/production/capacity/0901", False, 
                    f"Unexpected status: {response.status_code}")
    except Exception as e:
        log_test("GET /api/production/capacity/0901", False, f"Error: {str(e)}")
    
    # =========================================================================
    # 11. CSRF PROTECTION TESTS
    # =========================================================================
    test_csrf_protection(session)
    
    # =========================================================================
    # 12. CHECK FOR DOUBLE-PREFIX BUGS
    # =========================================================================
    print("\n" + "="*80)
    print("12. DOUBLE-PREFIX BUG CHECK")
    print("="*80)
    
    # Test that /api/api/* paths don't exist (should be 404 or redirect)
    try:
        url = f"{BASE_URL}/api/api/production/unido/MAR"
        response = session.get(url, timeout=30)
        if response.status_code == 404:
            log_test("No double-prefix bug: /api/api/* returns 404", True, 
                    "Correctly returns 404 for double-prefix path")
        elif response.status_code == 200:
            log_test("No double-prefix bug: /api/api/* returns 404", False, 
                    "WARNING: Double-prefix path still works! This indicates a bug.")
        else:
            log_test("No double-prefix bug: /api/api/* returns 404", True, 
                    f"Returns {response.status_code} (not 200, so no double-prefix)")
    except Exception as e:
        log_test("No double-prefix bug: /api/api/* returns 404", False, f"Error: {str(e)}")
    
    # =========================================================================
    # SUMMARY
    # =========================================================================
    print("\n" + "="*80)
    print("TEST SUMMARY")
    print("="*80)
    print(f"Total Tests: {test_results['total']}")
    print(f"Passed: {len(test_results['passed'])} ({len(test_results['passed'])/test_results['total']*100:.1f}%)")
    print(f"Failed: {len(test_results['failed'])} ({len(test_results['failed'])/test_results['total']*100:.1f}%)")
    
    if test_results['failed']:
        print("\n" + "="*80)
        print("FAILED TESTS DETAILS")
        print("="*80)
        for failure in test_results['failed']:
            print(f"\n❌ {failure['name']}")
            print(f"   {failure['details']}")
    
    print("\n" + "="*80)
    print("TESTING COMPLETE")
    print("="*80)
    
    # Return exit code based on results
    return 0 if len(test_results['failed']) == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
