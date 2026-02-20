"""
Test for OEC API default year parameter
========================================
This test verifies that all OEC endpoints default to year 2024,
which is the latest available year in the OEC BACI HS17 dataset.
"""

import re
import os


def test_oec_routes_default_year():
    """
    Verify that all OEC API endpoints use year 2024 as the default.
    
    The OEC BACI HS17 dataset has data from 2018-2024.
    Default year should be 2024 (the most recent available year).
    """
    backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    routes_file = os.path.join(backend_dir, "routes", "oec.py")
    
    with open(routes_file, "r") as f:
        source_code = f.read()
    
    pattern = r'year:\s*int\s*=\s*Query\((\d+)\)'
    matches = re.findall(pattern, source_code)
    
    assert len(matches) == 5, f"Expected 5 endpoints with year parameter, found {len(matches)}"
    
    for year in matches:
        assert year == "2024", (
            f"All OEC endpoints should default to year 2024 "
            f"(latest available in OEC BACI), but found year {year}"
        )
    
    print("All OEC endpoints correctly default to year 2024")
    print(f"   Verified {len(matches)} endpoints")


def test_oec_available_years():
    """
    Verify that get_available_years in oec_trade_service returns 2018-2024.
    """
    backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    service_file = os.path.join(backend_dir, "services", "oec_trade_service.py")
    
    with open(service_file, "r") as f:
        content = f.read()
    
    assert "2018-2024" in content, (
        "OEC service should document available years as 2018-2024"
    )
    
    print("OEC service correctly documents 2018-2024 data range")


if __name__ == "__main__":
    import sys
    
    try:
        test_oec_routes_default_year()
        test_oec_available_years()
        print("\nAll tests passed!")
        sys.exit(0)
    except AssertionError as e:
        print(f"\nTest failed: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\nError: {e}")
        sys.exit(1)
