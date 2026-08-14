#!/usr/bin/env python3
"""Environment-driven smoke tests for the ZLECAf backend API."""

import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

import requests

BACKEND_URL = os.getenv("TEST_BACKEND_URL", "http://localhost:8000/api").rstrip("/")
API_KEY = os.getenv("TEST_API_KEY")
ADMIN_EMAIL = os.getenv("TEST_ADMIN_EMAIL", "admin@afcfta-zlecaf.com")
ADMIN_PASSWORD = os.getenv("TEST_ADMIN_PASSWORD")
BACKEND_LOG = os.getenv("TEST_BACKEND_LOG", "/var/log/supervisor/backend.err.log")
RESULTS_PATH = Path(os.getenv("TEST_RESULTS_PATH", "backend_test_results.json"))
REQUEST_TIMEOUT = float(os.getenv("TEST_REQUEST_TIMEOUT", "15"))

session = requests.Session()
results = {
    "timestamp": datetime.now(timezone.utc).isoformat(),
    "backend_url": BACKEND_URL,
    "tests": [],
}


def env_flag(name, default=False):
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def api_headers(extra=None):
    """Return request headers, adding the API key only when configured."""
    headers = dict(extra or {})
    if API_KEY:
        headers["X-API-Key"] = API_KEY
    return headers


def log_test(name, passed=None, details=None, error=None):
    """Record and print a pass, failure, or explicit skip."""
    status = "skipped" if passed is None else ("passed" if passed else "failed")
    results["tests"].append(
        {
            "test": name,
            "status": status,
            "passed": passed,
            "details": details,
            "error": error,
        }
    )
    label = {"passed": "PASS", "failed": "FAIL", "skipped": "SKIP"}[status]
    print(f"\n{label}: {name}")
    if details:
        print(f"  Details: {details}")
    if error:
        print(f"  Error: {error}")


def response_error(response):
    return f"HTTP {response.status_code}: {response.text[:200]}"


def csrf_headers():
    """Initialize CSRF state on the shared session and return the matching header."""
    response = session.get(
        f"{BACKEND_URL}/health", headers=api_headers(), timeout=REQUEST_TIMEOUT
    )
    response.raise_for_status()
    token = response.headers.get("X-CSRF-Token")
    if not token:
        raise RuntimeError("The health endpoint did not return an X-CSRF-Token header")
    return api_headers({"X-CSRF-Token": token})


def test_health():
    name = "GET /api/health"
    try:
        response = session.get(
            f"{BACKEND_URL}/health", headers=api_headers(), timeout=REQUEST_TIMEOUT
        )
        if response.status_code != 200:
            log_test(name, False, error=response_error(response))
            return
        data = response.json()
        if data.get("status") != "healthy":
            log_test(name, False, error=f"Unexpected status: {data.get('status')}")
            return
        log_test(name, True, f"Status: {data['status']}")
    except Exception as exc:
        log_test(name, False, error=str(exc))


def test_countries():
    name = "GET /api/countries"
    try:
        response = session.get(
            f"{BACKEND_URL}/countries", headers=api_headers(), timeout=REQUEST_TIMEOUT
        )
        if response.status_code != 200:
            log_test(name, False, error=response_error(response))
            return
        data = response.json()
        valid = (
            isinstance(data, list)
            and len(data) == 54
            and all(field in data[0] for field in ("code", "name", "region"))
        )
        if not valid:
            count = len(data) if isinstance(data, list) else "non-list"
            log_test(
                name, False, error=f"Unexpected countries payload (count: {count})"
            )
            return
        log_test(name, True, f"Returned {len(data)} countries")
    except Exception as exc:
        log_test(name, False, error=str(exc))


def test_country_profiles():
    for code in ("KEN", "DZA"):
        name = f"GET /api/country-profile/{code}"
        try:
            response = session.get(
                f"{BACKEND_URL}/country-profile/{code}",
                headers=api_headers(),
                timeout=REQUEST_TIMEOUT,
            )
            if response.status_code != 200:
                log_test(name, False, error=response_error(response))
                continue
            data = response.json()
            if not all(field in data for field in ("country_code", "country_name")):
                log_test(name, False, error="Missing expected fields")
                continue
            log_test(name, True, f"Country: {data['country_name']}")
        except Exception as exc:
            log_test(name, False, error=str(exc))


def test_calculate_tariff():
    name = "POST /api/calculate-tariff"
    payload = {
        "origin_country": "KEN",
        "destination_country": "DZA",
        "hs_code": "080300",
        "value": 10000,
    }
    try:
        response = session.post(
            f"{BACKEND_URL}/calculate-tariff",
            headers=csrf_headers(),
            json=payload,
            timeout=REQUEST_TIMEOUT,
        )
        if response.status_code != 200:
            log_test(name, False, error=response_error(response))
            return
        data = response.json()
        if not all(field in data for field in ("normal_tariff_rate", "hs_code")):
            log_test(name, False, error="Missing expected fields")
            return
        log_test(name, True, f"Tariff calculated for HS {data['hs_code']}")
    except Exception as exc:
        log_test(name, False, error=str(exc))


def test_rules_of_origin():
    for hs_code in ("080300", "620342"):
        name = f"GET /api/rules-of-origin/{hs_code}"
        try:
            response = session.get(
                f"{BACKEND_URL}/rules-of-origin/{hs_code}",
                headers=api_headers(),
                timeout=REQUEST_TIMEOUT,
            )
            if response.status_code != 200:
                log_test(name, False, error=response_error(response))
                continue
            data = response.json()
            if not all(field in data for field in ("hs_code", "status")):
                log_test(name, False, error="Missing expected fields")
                continue
            log_test(name, True, f"Status: {data['status']}")
        except Exception as exc:
            log_test(name, False, error=str(exc))


def test_statistics():
    name = "GET /api/statistics"
    try:
        response = session.get(
            f"{BACKEND_URL}/statistics", headers=api_headers(), timeout=REQUEST_TIMEOUT
        )
        if response.status_code != 200:
            log_test(name, False, error=response_error(response))
            return
        data = response.json()
        if not all(field in data for field in ("overview", "top_exporters_2024")):
            log_test(name, False, error="Missing expected fields")
            return
        log_test(name, True, "Statistics payload is complete")
    except Exception as exc:
        log_test(name, False, error=str(exc))


def test_admin_login():
    name = "POST /api/auth/login (admin)"
    if not ADMIN_PASSWORD:
        log_test(name, None, details="Set TEST_ADMIN_PASSWORD to enable this test")
        return
    try:
        response = session.post(
            f"{BACKEND_URL}/auth/login",
            headers=csrf_headers(),
            json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD},
            timeout=REQUEST_TIMEOUT,
        )
        if response.status_code != 200:
            log_test(name, False, error=response_error(response))
            return
        data = response.json()
        if data.get("email", "").lower() != ADMIN_EMAIL.lower():
            log_test(name, False, error="Unexpected response structure")
            return
        log_test(name, True, f"Authenticated role: {data.get('role', 'unknown')}")
    except Exception as exc:
        log_test(name, False, error=str(exc))


def check_backend_logs():
    name = "Backend Logs Check"
    if env_flag("TEST_SKIP_LOG_CHECK"):
        log_test(name, None, details="Disabled by TEST_SKIP_LOG_CHECK")
        return
    try:
        completed = subprocess.run(
            ["tail", "-n", "100", BACKEND_LOG],
            capture_output=True,
            text=True,
            timeout=5,
            check=False,
        )
        if completed.returncode != 0:
            message = completed.stderr.strip() or "tail returned a non-zero exit status"
            log_test(
                name, False, error=f"Could not read {BACKEND_LOG}: {message[:200]}"
            )
            return

        keywords = (
            "ModuleNotFoundError",
            "ImportError",
            "500 Internal Server Error",
            "Traceback",
            "ERROR",
        )
        critical_errors = [
            line.strip()
            for line in completed.stdout.splitlines()
            if "WARNING" not in line and any(keyword in line for keyword in keywords)
        ]
        if critical_errors:
            log_test(
                name, False, error=f"Found {len(critical_errors)} potential errors"
            )
            for line in critical_errors[-5:]:
                print(f"    {line}")
            return
        log_test(name, True, "No critical errors found in recent logs")
    except Exception as exc:
        log_test(name, False, error=f"Could not check logs: {exc}")


def save_results():
    RESULTS_PATH.parent.mkdir(parents=True, exist_ok=True)
    RESULTS_PATH.write_text(
        json.dumps(results, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )


def main():
    print("=" * 80)
    print("ZLECAf Trade Calculator - Backend Smoke Test")
    print(f"Backend URL: {BACKEND_URL}")
    print("=" * 80)

    test_health()
    test_countries()
    test_country_profiles()
    test_calculate_tariff()
    test_rules_of_origin()
    test_statistics()
    test_admin_login()
    check_backend_logs()

    save_results()
    counts = {
        status: sum(test["status"] == status for test in results["tests"])
        for status in ("passed", "failed", "skipped")
    }
    print("\n" + "=" * 80)
    print(
        f"Tests: {len(results['tests'])} | Passed: {counts['passed']} | "
        f"Failed: {counts['failed']} | Skipped: {counts['skipped']}"
    )
    print(f"Results: {RESULTS_PATH}")
    return 1 if counts["failed"] else 0


if __name__ == "__main__":
    sys.exit(main())
