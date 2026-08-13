#!/usr/bin/env python3
"""
Backend API Smoke Test for ZLECAf Trade Calculator
Tests core endpoints after fresh import from GitHub
"""

import os
import sys
import requests
import json
from datetime import datetime

# Backend URL from frontend .env
BACKEND_URL = "https://github-dev-sync.preview.emergentagent.com/api"
API_KEY = "zlecaf-frontend-public-key"

# Admin credentials from backend .env
ADMIN_EMAIL = "admin@afcfta-zlecaf.com"
ADMIN_PASSWORD = "P__07Ae3tMFI-wq1sse9ON7X"

# Test results
results = {"timestamp": datetime.now().isoformat(), "backend_url": BACKEND_URL, "tests": []}


def log_test(name, passed, details=None, error=None):
    """Log test result"""
    result = {"test": name, "passed": passed, "details": details, "error": error}
    results["tests"].append(result)

    status = "✅ PASS" if passed else "❌ FAIL"
    print(f"\n{status}: {name}")
    if details:
        print(f"  Details: {details}")
    if error:
        print(f"  Error: {error}")


def test_health():
    """Test GET /api/health"""
    try:
        response = requests.get(f"{BACKEND_URL}/health", timeout=10)

        if response.status_code == 200:
            data = response.json()
            if data.get("status") == "healthy":
                log_test("GET /api/health", True, f"Status: {data.get('status')}")
                return True
            else:
                log_test("GET /api/health", False, error=f"Unexpected status: {data.get('status')}")
                return False
        else:
            log_test(
                "GET /api/health",
                False,
                error=f"HTTP {response.status_code}: {response.text[:200]}",
            )
            return False
    except Exception as e:
        log_test("GET /api/health", False, error=str(e))
        return False


def test_countries():
    """Test GET /api/countries"""
    try:
        response = requests.get(
            f"{BACKEND_URL}/countries", headers={"X-API-Key": API_KEY}, timeout=10
        )

        if response.status_code == 200:
            data = response.json()
            if isinstance(data, list) and len(data) == 54:
                # Check structure of first country
                first = data[0]
                if "code" in first and "name" in first and "region" in first:
                    log_test("GET /api/countries", True, f"Returned {len(data)} countries")
                    return True
                else:
                    log_test(
                        "GET /api/countries", False, error="Missing expected fields in country data"
                    )
                    return False
            else:
                log_test(
                    "GET /api/countries",
                    False,
                    error=f"Expected 54 countries, got {len(data) if isinstance(data, list) else 'non-list'}",
                )
                return False
        else:
            log_test(
                "GET /api/countries",
                False,
                error=f"HTTP {response.status_code}: {response.text[:200]}",
            )
            return False
    except Exception as e:
        log_test("GET /api/countries", False, error=str(e))
        return False


def test_country_profile():
    """Test GET /api/country-profile/{country_code}"""
    test_codes = ["KEN", "DZA"]

    for code in test_codes:
        try:
            response = requests.get(
                f"{BACKEND_URL}/country-profile/{code}", headers={"X-API-Key": API_KEY}, timeout=10
            )

            if response.status_code == 200:
                data = response.json()
                if "country_code" in data and "country_name" in data:
                    log_test(
                        f"GET /api/country-profile/{code}",
                        True,
                        f"Country: {data.get('country_name')}",
                    )
                else:
                    log_test(
                        f"GET /api/country-profile/{code}", False, error="Missing expected fields"
                    )
                    return False
            else:
                log_test(
                    f"GET /api/country-profile/{code}",
                    False,
                    error=f"HTTP {response.status_code}: {response.text[:200]}",
                )
                return False
        except Exception as e:
            log_test(f"GET /api/country-profile/{code}", False, error=str(e))
            return False

    return True


def test_calculate_tariff():
    """Test POST /api/calculate-tariff"""
    try:
        payload = {
            "origin_country": "KEN",
            "destination_country": "DZA",
            "hs_code": "080300",
            "value": 10000,
        }

        response = requests.post(
            f"{BACKEND_URL}/calculate-tariff",
            headers={"X-API-Key": API_KEY, "Content-Type": "application/json"},
            json=payload,
            timeout=15,
        )

        if response.status_code == 200:
            data = response.json()
            if "normal_tariff_rate" in data and "hs_code" in data:
                log_test(
                    "POST /api/calculate-tariff",
                    True,
                    f"Tariff calculated: {data.get('normal_tariff_rate')*100:.2f}% for HS {data.get('hs_code')}",
                )
                return True
            else:
                log_test(
                    "POST /api/calculate-tariff", False, error="Missing expected fields in response"
                )
                return False
        else:
            log_test(
                "POST /api/calculate-tariff",
                False,
                error=f"HTTP {response.status_code}: {response.text[:200]}",
            )
            return False
    except Exception as e:
        log_test("POST /api/calculate-tariff", False, error=str(e))
        return False


def test_rules_of_origin():
    """Test GET /api/rules-of-origin/{hs_code}"""
    test_codes = ["080300", "620342"]

    for hs_code in test_codes:
        try:
            response = requests.get(
                f"{BACKEND_URL}/rules-of-origin/{hs_code}",
                headers={"X-API-Key": API_KEY},
                timeout=10,
            )

            if response.status_code == 200:
                data = response.json()
                if "hs_code" in data and "status" in data:
                    log_test(
                        f"GET /api/rules-of-origin/{hs_code}",
                        True,
                        f"Status: {data.get('status')}, Chapter: {data.get('chapter')}",
                    )
                else:
                    log_test(
                        f"GET /api/rules-of-origin/{hs_code}",
                        False,
                        error="Missing expected fields",
                    )
                    return False
            else:
                log_test(
                    f"GET /api/rules-of-origin/{hs_code}",
                    False,
                    error=f"HTTP {response.status_code}: {response.text[:200]}",
                )
                return False
        except Exception as e:
            log_test(f"GET /api/rules-of-origin/{hs_code}", False, error=str(e))
            return False

    return True


def test_statistics():
    """Test GET /api/statistics"""
    try:
        response = requests.get(
            f"{BACKEND_URL}/statistics", headers={"X-API-Key": API_KEY}, timeout=10
        )

        if response.status_code == 200:
            data = response.json()
            if "overview" in data and "top_exporters_2024" in data:
                overview = data.get("overview", {})
                log_test(
                    "GET /api/statistics",
                    True,
                    f"African countries: {overview.get('african_countries_members')}, GDP: ${overview.get('estimated_combined_gdp', 0)/1e12:.2f}T",
                )
                return True
            else:
                log_test("GET /api/statistics", False, error="Missing expected fields")
                return False
        else:
            log_test(
                "GET /api/statistics",
                False,
                error=f"HTTP {response.status_code}: {response.text[:200]}",
            )
            return False
    except Exception as e:
        log_test("GET /api/statistics", False, error=str(e))
        return False


def test_admin_login():
    """Test POST /api/auth/login with admin credentials"""
    try:
        # First get CSRF token from health endpoint
        health_response = requests.get(f"{BACKEND_URL}/health", timeout=10)
        csrf_token = health_response.headers.get("X-CSRF-Token")
        cookies = health_response.cookies

        payload = {"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD}

        headers = {"Content-Type": "application/json"}

        if csrf_token:
            headers["X-CSRF-Token"] = csrf_token

        response = requests.post(
            f"{BACKEND_URL}/auth/login", headers=headers, json=payload, cookies=cookies, timeout=10
        )

        if response.status_code == 200:
            data = response.json()
            if "email" in data and data.get("email") == ADMIN_EMAIL.lower():
                log_test(
                    "POST /api/auth/login (admin)",
                    True,
                    f"Admin logged in: {data.get('name')} ({data.get('role')})",
                )
                return True
            else:
                log_test(
                    "POST /api/auth/login (admin)", False, error="Unexpected response structure"
                )
                return False
        else:
            log_test(
                "POST /api/auth/login (admin)",
                False,
                error=f"HTTP {response.status_code}: {response.text[:200]}",
            )
            return False
    except Exception as e:
        log_test("POST /api/auth/login (admin)", False, error=str(e))
        return False


def check_backend_logs():
    """Check backend logs for errors"""
    try:
        import subprocess

        result = subprocess.run(
            ["tail", "-n", "100", "/var/log/supervisor/backend.err.log"],
            capture_output=True,
            text=True,
            timeout=5,
        )

        log_content = result.stdout

        # Check for critical errors
        critical_errors = []
        error_keywords = [
            "ModuleNotFoundError",
            "ImportError",
            "500 Internal Server Error",
            "Traceback",
            "ERROR",
        ]

        for line in log_content.split("\n"):
            for keyword in error_keywords:
                if keyword in line and "WARNING" not in line:
                    critical_errors.append(line.strip())
                    break

        if critical_errors:
            log_test(
                "Backend Logs Check",
                False,
                error=f"Found {len(critical_errors)} potential errors in logs",
            )
            print("\n  Recent errors:")
            for err in critical_errors[-5:]:  # Show last 5 errors
                print(f"    {err}")
            return False
        else:
            log_test("Backend Logs Check", True, "No critical errors found in recent logs")
            return True
    except Exception as e:
        log_test("Backend Logs Check", False, error=f"Could not check logs: {str(e)}")
        return False


def main():
    """Run all smoke tests"""
    print("=" * 80)
    print("ZLECAf Trade Calculator - Backend Smoke Test")
    print("=" * 80)
    print(f"Backend URL: {BACKEND_URL}")
    print(f"Test started: {results['timestamp']}")
    print("=" * 80)

    # Run all tests
    test_health()
    test_countries()
    test_country_profile()
    test_calculate_tariff()
    test_rules_of_origin()
    test_statistics()
    test_admin_login()
    check_backend_logs()

    # Summary
    print("\n" + "=" * 80)
    print("TEST SUMMARY")
    print("=" * 80)

    passed = sum(1 for t in results["tests"] if t["passed"])
    total = len(results["tests"])

    print(f"Total Tests: {total}")
    print(f"Passed: {passed}")
    print(f"Failed: {total - passed}")
    print(f"Success Rate: {(passed/total)*100:.1f}%")

    # List failed tests
    failed_tests = [t for t in results["tests"] if not t["passed"]]
    if failed_tests:
        print("\nFailed Tests:")
        for test in failed_tests:
            print(f"  ❌ {test['test']}")
            if test.get("error"):
                print(f"     Error: {test['error']}")

    print("=" * 80)

    # Save results to file
    with open("/app/backend_test_results.json", "w") as f:
        json.dump(results, f, indent=2)

    print(f"\nDetailed results saved to: /app/backend_test_results.json")

    # Exit with appropriate code
    sys.exit(0 if passed == total else 1)


if __name__ == "__main__":
    main()
