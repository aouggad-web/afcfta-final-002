"""API routes for regulatory-compliance QA controls (LOT 6, issue #361):
coverage reporting, verification-status contradiction detection, and dataset
staleness detection."""

from fastapi import APIRouter
from services.regulatory_qa_service import (
    find_stale_countries,
    find_verification_status_contradictions,
    get_regulatory_coverage_report,
)

router = APIRouter(prefix="/regulatory-qa")


@router.get("/coverage-report")
def get_coverage_report_endpoint():
    """54-country coverage summary: published vs. NOT_AVAILABLE, and
    per-published-country measure/actor status breakdowns."""

    return {"success": True, "report": get_regulatory_coverage_report()}


@router.get("/contradictions")
def get_contradictions_endpoint():
    """Measures whose verification_status claims more confidence than the
    legal source they cite. Should always be empty for correctly curated
    data — a non-empty result flags a real data-quality issue to fix."""

    contradictions = find_verification_status_contradictions()
    return {
        "success": True,
        "total": len(contradictions),
        "contradictions": contradictions,
    }


@router.get("/stale-countries")
def get_stale_countries_endpoint():
    """Published countries whose dataset `as_of` is older than the default
    staleness threshold — flagged for re-verification, never auto-renewed."""

    stale = find_stale_countries()
    return {"success": True, "total": len(stale), "stale_countries": stale}
