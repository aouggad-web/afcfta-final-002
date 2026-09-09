"""LOT 6 (issue #361) — regulatory QA controls: coverage report,
verification-status contradiction detection, dataset staleness detection.

These are governance/regression tests: they assert the current data is
clean (zero contradictions, nothing stale) AND that the detectors actually
catch a synthetic violation when one is injected, so a future data edit
that introduces a real contradiction or lets a dataset go stale cannot pass
silently.
"""

from datetime import date, datetime

import pytest
from services.regulatory_compliance_service import COUNTRY_REGULATORY_PATHS
from services.regulatory_master_registry_service import (
    AFRICAN_COUNTRY_ISO3,
    get_regulatory_registry,
)
from services.regulatory_qa_service import (
    _VERIFICATION_STATUS_SCHEMA_COUNTRIES,
    find_stale_countries,
    find_verification_status_contradictions,
    get_regulatory_coverage_report,
    get_regulatory_qa_report,
)

# Anchored to the master registry's own as_of rather than the wall clock
# (date.today()) so these assertions stay deterministic regardless of when
# CI happens to run — a real "the data is currently clean" check, not one
# that quietly starts failing once enough real time passes.
_REGISTRY_AS_OF = datetime.strptime(get_regulatory_registry()["as_of"], "%Y-%m-%d").date()


def test_coverage_report_accounts_for_every_tracked_country_exactly_once():
    report = get_regulatory_coverage_report()
    assert report["total_tracked_countries"] == 54
    assert report["published_country_count"] + report["not_available_country_count"] == 54
    assert set(report["published_countries"]) == set(COUNTRY_REGULATORY_PATHS)
    assert set(report["not_available_countries"]) == set(AFRICAN_COUNTRY_ISO3) - set(
        COUNTRY_REGULATORY_PATHS
    )
    assert not (set(report["published_countries"]) & set(report["not_available_countries"]))


def test_coverage_report_never_masks_measure_or_actor_counts():
    report = get_regulatory_coverage_report()
    for entry in report["countries"]:
        assert entry["measure_count"] == sum(entry["measure_status_counts"].values())
        assert entry["mandated_actor_count"] == sum(entry["actor_mandate_status_counts"].values())
        assert entry["terminated_actor_count"] == entry["actor_mandate_status_counts"].get(
            "TERMINATED", 0
        )


def test_current_data_has_no_verification_status_contradictions():
    """Every measure's confidence claim is currently backed by an
    equal-or-stronger source claim — this is the expected, curated state."""

    assert find_verification_status_contradictions() == []


def test_kenya_is_excluded_from_the_contradiction_check_by_design():
    """Kenya's legal_sources.json uses source_status (archival state), not
    verification_status (confidence level) — the two schemas are not
    comparable, so Kenya is deliberately out of scope for this check rather
    than silently misapplied."""

    assert "KEN" not in _VERIFICATION_STATUS_SCHEMA_COUNTRIES


def test_contradiction_detector_flags_a_measure_overclaiming_its_source(monkeypatch):
    from services import regulatory_qa_service as qa_service

    def fake_compliance(country_iso3):
        assert country_iso3 == "CIV"
        return {
            "measures": [
                {
                    "record_id": "CIV-FAKE",
                    "source_id": "CIV-FAKE-SOURCE",
                    "verification_status": "DOCUMENTED",
                }
            ],
        }

    def fake_load_sources(country_iso3):
        assert country_iso3 == "CIV"
        return [
            {
                "source_id": "CIV-FAKE-SOURCE",
                "verification_status": "PENDING_COLLECTION",
            }
        ]

    monkeypatch.setattr(qa_service, "_VERIFICATION_STATUS_SCHEMA_COUNTRIES", {"CIV"})
    monkeypatch.setattr(qa_service, "get_country_regulatory_compliance", fake_compliance)
    monkeypatch.setattr(qa_service, "_load_legal_sources", fake_load_sources)
    monkeypatch.setattr(qa_service, "COUNTRY_REGULATORY_PATHS", {"CIV": "unused"})

    contradictions = qa_service.find_verification_status_contradictions()
    assert len(contradictions) == 1
    assert contradictions[0]["record_id"] == "CIV-FAKE"
    assert contradictions[0]["measure_verification_status"] == "DOCUMENTED"
    assert contradictions[0]["source_verification_status"] == "PENDING_COLLECTION"


def test_no_country_is_currently_stale():
    assert find_stale_countries(reference_date=_REGISTRY_AS_OF) == []


def test_staleness_detector_flags_an_old_as_of_date(monkeypatch):
    from services import regulatory_compliance_service as service

    source = service._read_json("data/cote-d-ivoire/regulatory_measures.json")
    altered = {**source, "as_of": "2020-01-01"}
    monkeypatch.setattr(service, "_read_json", lambda _path: altered)

    from services import regulatory_qa_service as qa_service

    monkeypatch.setattr(qa_service, "COUNTRY_REGULATORY_PATHS", {"CIV": "unused"})

    stale = qa_service.find_stale_countries(reference_date=date(2026, 8, 8))
    assert len(stale) == 1
    assert stale[0]["country_iso3"] == "CIV"
    assert stale[0]["reason"] == "older_than_threshold"
    assert stale[0]["age_days"] > qa_service.DEFAULT_STALE_THRESHOLD_DAYS


def test_staleness_detector_flags_an_unparseable_as_of_date(monkeypatch):
    """as_of is required non-empty by the compliance service itself (never
    None in practice) — but its format isn't validated there, so a malformed
    string is the reachable case this branch guards against."""

    from services import regulatory_compliance_service as service

    source = service._read_json("data/cote-d-ivoire/regulatory_measures.json")
    altered = {**source, "as_of": "not-a-date"}
    monkeypatch.setattr(service, "_read_json", lambda _path: altered)

    from services import regulatory_qa_service as qa_service

    monkeypatch.setattr(qa_service, "COUNTRY_REGULATORY_PATHS", {"CIV": "unused"})

    stale = qa_service.find_stale_countries()
    assert len(stale) == 1
    assert stale[0]["reason"] == "unparseable_or_missing_as_of"


def test_full_qa_report_bundles_all_three_controls():
    report = get_regulatory_qa_report(reference_date=_REGISTRY_AS_OF)
    assert set(report.keys()) == {
        "coverage",
        "verification_status_contradictions",
        "stale_countries",
    }
    assert report["verification_status_contradictions"] == []
    assert report["stale_countries"] == []
