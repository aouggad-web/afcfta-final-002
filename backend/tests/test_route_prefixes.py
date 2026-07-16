"""Route topology regression tests."""

from fastapi import APIRouter

from routes.enhanced_calculator import router as enhanced_calculator_router
from routes.regional_calculator import router as regional_calculator_router


def test_enhanced_and_regional_calculators_have_distinct_prefixes():
    """Avoid silently mounting two calculator domains in the same route namespace."""
    assert enhanced_calculator_router.prefix == "/enhanced-calculator"
    assert regional_calculator_router.prefix == "/regional-calculator"


def test_registered_route_prefixes_are_unique_for_calculator_domains():
    routers: list[APIRouter] = [enhanced_calculator_router, regional_calculator_router]
    prefixes = [router.prefix for router in routers]

    assert len(prefixes) == len(set(prefixes))
