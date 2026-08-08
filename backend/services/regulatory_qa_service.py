"""LOT 6 (issue #361): quality-assurance controls over the regulatory-compliance
data — coverage reporting, source/measure verification-status contradiction
detection, and dataset staleness detection. Read-only aggregation over the
existing source-bound datasets: never fabricates or infers a status, and
never silently drops a country/measure/actor from the counts."""

from collections import Counter
from datetime import date, datetime, timedelta
from typing import Any, Dict, List, Optional

from services.regulatory_compliance_service import (
    COUNTRY_REGULATORY_PATHS,
    get_country_regulatory_compliance,
)
from services.regulatory_master_registry_service import (
    AFRICAN_COUNTRY_ISO3,
    get_regulatory_registry,
)

# Countries whose legal_sources.json uses the shared `verification_status`
# convention. Kenya's legal_sources.json instead tracks `source_status`
# (archival/collection state of the document: COLLECTED/SOURCE_PENDING),
# which is not semantically comparable to a measure's confidence-level
# verification_status — comparing across the two schemas would produce a
# false "contradiction" that isn't real, so Kenya is intentionally excluded
# from this specific check rather than silently misapplied.
_VERIFICATION_STATUS_SCHEMA_COUNTRIES = {"CIV", "COD", "CMR", "GHA", "NGA"}

_VERIFICATION_STRENGTH = {
    "VERIFIED_PRIMARY_TEXT": 4,
    "DOCUMENTED": 3,
    "PARTIAL": 2,
    "UNVERIFIED": 1,
    "PENDING_COLLECTION": 0,
    "NOT_AVAILABLE": 0,
    "REVIEW_REQUIRED": 0,
}

DEFAULT_STALE_THRESHOLD_DAYS = 365


def _load_legal_sources(country_iso3: str) -> List[Dict[str, Any]]:
    from services.regulatory_compliance_service import _read_json

    dataset_path = COUNTRY_REGULATORY_PATHS[country_iso3]
    sources_path = dataset_path.rsplit("/", 1)[0] + "/legal_sources.json"
    return _read_json(sources_path).get("sources", [])


def get_regulatory_coverage_report() -> Dict[str, Any]:
    """Aggregate coverage across all 54 tracked countries: published vs.
    NOT_AVAILABLE, and for published countries, measure/actor counts broken
    down by canonical status. Never masks an unpublished country as covered."""

    registry = get_regulatory_registry()
    published = sorted(COUNTRY_REGULATORY_PATHS)
    not_available = sorted(set(AFRICAN_COUNTRY_ISO3) - set(published))

    per_country: List[Dict[str, Any]] = []
    for iso3 in published:
        compliance = get_country_regulatory_compliance(iso3)
        measure_status_counts = Counter(m["verification_status"] for m in compliance["measures"])
        actor_mandate_status_counts = Counter(
            a["mandate_status"] for a in compliance["mandated_actors"]
        )
        per_country.append(
            {
                "country_iso3": iso3,
                "as_of": compliance.get("as_of"),
                "measure_count": compliance["measure_count"],
                "mandated_actor_count": compliance["mandated_actor_count"],
                "measure_status_counts": dict(measure_status_counts),
                "actor_mandate_status_counts": dict(actor_mandate_status_counts),
                "terminated_actor_count": actor_mandate_status_counts.get("TERMINATED", 0),
            }
        )

    return {
        "total_tracked_countries": len(AFRICAN_COUNTRY_ISO3),
        "published_country_count": len(published),
        "published_countries": published,
        "not_available_country_count": len(not_available),
        "not_available_countries": not_available,
        "countries": per_country,
        "registry_country_count": registry["country_count"],
    }


def find_verification_status_contradictions() -> List[Dict[str, Any]]:
    """Flag any published measure whose verification_status claims *more*
    confidence than the legal source it cites. Restricted to countries whose
    legal_sources.json uses the shared verification_status vocabulary (see
    _VERIFICATION_STATUS_SCHEMA_COUNTRIES)."""

    contradictions: List[Dict[str, Any]] = []
    for iso3 in sorted(_VERIFICATION_STATUS_SCHEMA_COUNTRIES & set(COUNTRY_REGULATORY_PATHS)):
        compliance = get_country_regulatory_compliance(iso3)
        sources_by_id = {s["source_id"]: s for s in _load_legal_sources(iso3)}
        for measure in compliance["measures"]:
            source = sources_by_id.get(measure["source_id"])
            if source is None or "verification_status" not in source:
                continue
            measure_rank = _VERIFICATION_STRENGTH.get(measure["verification_status"])
            source_rank = _VERIFICATION_STRENGTH.get(source["verification_status"])
            if measure_rank is None or source_rank is None:
                continue
            if measure_rank > source_rank:
                contradictions.append(
                    {
                        "country_iso3": iso3,
                        "record_id": measure["record_id"],
                        "measure_verification_status": measure["verification_status"],
                        "source_id": measure["source_id"],
                        "source_verification_status": source["verification_status"],
                    }
                )
    return contradictions


def _parse_iso_date(value: Optional[str]) -> Optional[date]:
    if not value:
        return None
    try:
        return datetime.strptime(value, "%Y-%m-%d").date()
    except ValueError:
        return None


def find_stale_countries(
    reference_date: Optional[date] = None,
    max_age_days: int = DEFAULT_STALE_THRESHOLD_DAYS,
) -> List[Dict[str, Any]]:
    """Flag published countries whose dataset `as_of` is older than
    max_age_days relative to reference_date (defaults to today). Never
    auto-renews a stale dataset's status — this only reports for review."""

    today = reference_date or date.today()
    threshold = today - timedelta(days=max_age_days)
    stale: List[Dict[str, Any]] = []
    for iso3 in sorted(COUNTRY_REGULATORY_PATHS):
        compliance = get_country_regulatory_compliance(iso3)
        as_of = _parse_iso_date(compliance.get("as_of"))
        if as_of is None:
            stale.append(
                {
                    "country_iso3": iso3,
                    "as_of": compliance.get("as_of"),
                    "reason": "unparseable_or_missing_as_of",
                }
            )
        elif as_of < threshold:
            stale.append(
                {
                    "country_iso3": iso3,
                    "as_of": compliance.get("as_of"),
                    "age_days": (today - as_of).days,
                    "reason": "older_than_threshold",
                }
            )
    return stale


def get_regulatory_qa_report() -> Dict[str, Any]:
    """Convenience aggregate of all three QA controls for a single call."""

    return {
        "coverage": get_regulatory_coverage_report(),
        "verification_status_contradictions": find_verification_status_contradictions(),
        "stale_countries": find_stale_countries(),
    }
