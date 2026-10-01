#!/usr/bin/env python3
"""
Test script for the African customs scraper infrastructure.

This script tests:
1. Registry completeness and data quality

Run with: python test_scraper_infrastructure.py
"""

import asyncio
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent / "backend"))

from crawlers import (
    AFRICAN_COUNTRIES_REGISTRY,
    get_countries_by_region,
    get_country_config,
    get_priority_countries,
)
from crawlers.all_countries_registry import validate_registry


def test_registry():
    """Test the countries registry"""
    print("\n" + "=" * 70)
    print("TEST 1: Countries Registry")
    print("=" * 70)

    # Validate registry
    report = validate_registry()
    print(f"\n✓ Total countries: {report['total_countries']}/54")
    print(f"✓ Registry complete: {report['is_complete']}")

    # Check regions
    print("\nCountries by region:")
    for region, count in report["by_region"].items():
        print(f"  - {region}: {count} countries")

    # Check priorities
    print("\nCountries by priority:")
    for priority, count in report["by_priority"].items():
        print(f"  - {priority}: {count} countries")

    # Check for missing data
    if report["missing_data"]:
        print(f"\n⚠ Warning: {len(report['missing_data'])} missing data fields")
        for issue in report["missing_data"][:5]:
            print(f"  - {issue}")
    else:
        print("\n✓ All required fields present")

    # Sample some countries
    print("\nSample country configurations:")
    for code in ["NGA", "GHA", "KEN", "ZAF", "MAR"]:
        config = get_country_config(code)
        if config:
            print(
                f"  - {code}: {config['name_en']}, VAT: {config['vat_rate']}%, "
                f"Priority: {config['priority'].value}, "
                f"Blocks: {[b.value for b in config['blocks']]}"
            )

    return report["is_complete"]


async def main():
    """Run all tests"""
    print("\n" + "=" * 70)
    print("AFRICAN CUSTOMS SCRAPER INFRASTRUCTURE TEST SUITE")
    print("=" * 70)

    results = []

    # Run tests
    results.append(("Registry Validation", test_registry()))

    # Summary
    print("\n" + "=" * 70)
    print("TEST SUMMARY")
    print("=" * 70)

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for test_name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{status}: {test_name}")

    print(f"\nOverall: {passed}/{total} tests passed ({passed/total*100:.1f}%)")

    if passed == total:
        print("\n🎉 All tests passed! Infrastructure is ready.")
        return 0
    else:
        print(f"\n⚠ {total - passed} test(s) failed.")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
