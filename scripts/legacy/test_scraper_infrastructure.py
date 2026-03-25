#!/usr/bin/env python3
"""
Test script for the African customs scraper infrastructure.

This script tests:
1. Registry completeness and data quality
2. Base scraper functionality
3. Factory pattern implementation
4. Generic scraper operation
5. Integration capabilities

Run with: python test_scraper_infrastructure.py
"""

import asyncio
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent / "backend"))

from crawlers import (
    ScraperFactory,
    AFRICAN_COUNTRIES_REGISTRY,
    get_country_config,
    get_priority_countries,
    get_countries_by_region,
    Priority,
    Region,
)
from crawlers.base_scraper import ScraperConfig
from crawlers.all_countries_registry import validate_registry


def test_registry():
    """Test the countries registry"""
    print("\n" + "="*70)
    print("TEST 1: Countries Registry")
    print("="*70)
    
    # Validate registry
    report = validate_registry()
    print(f"\n✓ Total countries: {report['total_countries']}/54")
    print(f"✓ Registry complete: {report['is_complete']}")
    
    # Check regions
    print("\nCountries by region:")
    for region, count in report['by_region'].items():
        print(f"  - {region}: {count} countries")
    
    # Check priorities
    print("\nCountries by priority:")
    for priority, count in report['by_priority'].items():
        print(f"  - {priority}: {count} countries")
    
    # Check for missing data
    if report['missing_data']:
        print(f"\n⚠ Warning: {len(report['missing_data'])} missing data fields")
        for issue in report['missing_data'][:5]:
            print(f"  - {issue}")
    else:
        print("\n✓ All required fields present")
    
    # Sample some countries
    print("\nSample country configurations:")
    for code in ["NGA", "GHA", "KEN", "ZAF", "MAR"]:
        config = get_country_config(code)
        if config:
            print(f"  - {code}: {config['name_en']}, VAT: {config['vat_rate']}%, "
                  f"Priority: {config['priority'].value}, "
                  f"Blocks: {[b.value for b in config['blocks']]}")
    
    return report['is_complete']


def test_scraper_creation():
    """Test scraper factory and creation"""
    print("\n" + "="*70)
    print("TEST 2: Scraper Creation")
    print("="*70)
    
    try:
        # Test single scraper creation
        print("\n✓ Creating scraper for Ghana (GHA)...")
        scraper = ScraperFactory.get_scraper("GHA")
        print(f"  - Class: {scraper.__class__.__name__}")
        print(f"  - Country: {scraper.country_name}")
        print(f"  - Region: {scraper.region}")
        print(f"  - VAT Rate: {scraper.vat_rate}%")
        print(f"  - Source URL: {scraper.source_url}")
        print(f"  - Priority: {scraper.priority}")
        
        # Test with custom config
        print("\n✓ Creating scraper with custom config...")
        config = ScraperConfig(
            country_code="NGA",
            max_retries=5,
            timeout=60.0,
            rate_limit_calls=5
        )
        scraper_ng = ScraperFactory.get_scraper("NGA", config=config)
        print(f"  - Config applied: max_retries={scraper_ng._config.max_retries}")
        
        # Test invalid country code
        print("\n✓ Testing invalid country code handling...")
        try:
            ScraperFactory.get_scraper("XXX")
            print("  ✗ Should have raised ValueError")
            return False
        except ValueError as e:
            print(f"  - Correctly raised ValueError: {str(e)[:60]}...")
        
        return True
        
    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_bulk_operations():
    """Test bulk scraper operations"""
    print("\n" + "="*70)
    print("TEST 3: Bulk Scraper Operations")
    print("="*70)
    
    try:
        # Get high priority scrapers
        print("\n✓ Getting HIGH priority scrapers...")
        high_priority = ScraperFactory.get_priority_scrapers(Priority.HIGH)
        print(f"  - Created {len(high_priority)} scrapers")
        print(f"  - Countries: {[s.country_code for s in high_priority[:5]]}...")
        
        # Get region scrapers
        print("\n✓ Getting West Africa scrapers...")
        west_africa = ScraperFactory.get_region_scrapers(Region.WEST_AFRICA)
        print(f"  - Created {len(west_africa)} scrapers")
        print(f"  - Countries: {[s.country_code for s in west_africa[:5]]}...")
        
        # Get specific countries
        print("\n✓ Getting multiple specific scrapers...")
        countries = ["GHA", "NGA", "KEN", "ZAF", "EGY"]
        scrapers = ScraperFactory.get_multiple_scrapers(countries)
        print(f"  - Created {len(scrapers)} scrapers")
        
        return True
        
    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_generic_scraper():
    """Test the generic scraper functionality"""
    print("\n" + "="*70)
    print("TEST 4: Generic Scraper Functionality")
    print("="*70)
    
    try:
        # Create generic scraper
        print("\n✓ Creating and running generic scraper for Ghana...")
        scraper = ScraperFactory.get_scraper("GHA", force_generic=True)
        
        # Test scrape
        print("\n  Step 1: Scraping...")
        data = await scraper.scrape()
        print(f"    - Scraped data keys: {list(data.keys())}")
        print(f"    - Country: {data.get('country_name')}")
        print(f"    - Type: {data.get('scrape_type')}")
        
        # Test validate
        print("\n  Step 2: Validating...")
        is_valid = await scraper.validate(data)
        print(f"    - Valid: {is_valid}")
        
        # Test full run
        print("\n  Step 3: Running complete pipeline...")
        result = await scraper.run()
        print(f"    - Success: {result.success}")
        print(f"    - Records scraped: {result.records_scraped}")
        print(f"    - Duration: {result.duration_seconds:.2f}s")
        
        # Close scraper
        await scraper.close()
        
        return result.success
        
    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_factory_registry():
    """Test the factory registry"""
    print("\n" + "="*70)
    print("TEST 5: Factory Registry")
    print("="*70)
    
    try:
        # Get registry stats
        stats = ScraperFactory.get_registry_stats()
        print(f"\n✓ Registry Statistics:")
        print(f"  - Total countries: {stats['total_countries']}")
        print(f"  - Specific scrapers: {stats['specific_scrapers']}")
        print(f"  - Using generic: {stats['using_generic']}")
        print(f"  - Coverage: {stats['coverage_percentage']:.1f}%")
        
        # List registered scrapers
        registered = ScraperFactory.list_registered_scrapers()
        if registered:
            print(f"\n✓ Registered country-specific scrapers:")
            for code, name in registered.items():
                print(f"  - {code}: {name}")
        else:
            print("\n  (No country-specific scrapers registered yet - using generic)")
        
        return True
        
    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_scraper_properties():
    """Test scraper properties and methods"""
    print("\n" + "="*70)
    print("TEST 6: Scraper Properties and Methods")
    print("="*70)
    
    try:
        scraper = ScraperFactory.get_scraper("GHA")
        
        print("\n✓ Testing properties:")
        print(f"  - country_code: {scraper.country_code}")
        print(f"  - country_name: {scraper.country_name}")
        print(f"  - country_name_fr: {scraper.country_name_fr}")
        print(f"  - source_url: {scraper.source_url}")
        print(f"  - region: {scraper.region}")
        print(f"  - vat_rate: {scraper.vat_rate}%")
        print(f"  - regional_blocks: {scraper.regional_blocks}")
        print(f"  - priority: {scraper.priority}")
        
        print("\n✓ Testing utility methods:")
        # Test make_absolute_url
        rel_url = "/tariffs/2025"
        abs_url = scraper.make_absolute_url(rel_url)
        print(f"  - make_absolute_url('{rel_url}'): {abs_url}")
        
        # Test get_stats
        stats = scraper.get_stats()
        print(f"  - get_stats(): {list(stats.keys())}")
        
        return True
        
    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """Run all tests"""
    print("\n" + "="*70)
    print("AFRICAN CUSTOMS SCRAPER INFRASTRUCTURE TEST SUITE")
    print("="*70)
    
    results = []
    
    # Run tests
    results.append(("Registry Validation", test_registry()))
    results.append(("Scraper Creation", test_scraper_creation()))
    results.append(("Bulk Operations", test_bulk_operations()))
    results.append(("Generic Scraper", await test_generic_scraper()))
    results.append(("Factory Registry", test_factory_registry()))
    results.append(("Scraper Properties", test_scraper_properties()))
    
    # Summary
    print("\n" + "="*70)
    print("TEST SUMMARY")
    print("="*70)
    
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
