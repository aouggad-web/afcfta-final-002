"""Runtime contracts for special formalities and government-mandated providers."""

import pytest

from routes.regulatory_compliance import router
from services.regulatory_compliance_service import (
    get_country_regulatory_compliance,
    get_supported_regulatory_countries,
)


def _actor(country: str, name_fragment: str):
    compliance = get_country_regulatory_compliance(country)
    assert compliance is not None
    return next(
        actor
        for actor in compliance["mandated_actors"]
        if name_fragment.upper() in actor["actor_name"].upper()
    )


def test_regulatory_runtime_supports_exact_pilot_countries():
    assert get_supported_regulatory_countries() == ["CIV", "COD"]


def test_cod_bivac_is_exposed_as_a_mandated_actor_not_an_authority():
    compliance = get_country_regulatory_compliance("cod")
    assert compliance is not None
    bivac = _actor("COD", "BIVAC")

    assert bivac["actor_type"] == "MANDATED_SERVICE_PROVIDER"
    assert "OCC" in bivac["mandating_authority"].upper()
    assert bivac["regulatory_authority"] != bivac["actor_name"]
    assert bivac["measure_record_id"] == "COD-OCC-CBCA"
    assert bivac["authorized_fees"] is None
    assert bivac["authorized_fees_status"] == "NOT_AVAILABLE"
    assert bivac["mandate_status"] == "CONFIRMED_TIME_LIMITED"
    assert "Attestation de Vérification" in bivac["delivered_document"]
    assert not any(
        "BIVAC" in measure["record_id"].upper() for measure in compliance["measures"]
    )


def test_civ_webb_fontaine_is_exposed_as_terminated_historical_operator():
    webb_fontaine = _actor("CIV", "Webb Fontaine")

    assert webb_fontaine["actor_type"] == "TECHNICAL_OPERATOR"
    assert webb_fontaine["mandate_status"] == "TERMINATED"
    assert webb_fontaine["authorized_fees"] is None
    assert webb_fontaine["authorized_fees_status"] == "NOT_AVAILABLE"
    assert webb_fontaine["measure_record_id"] == "CIV-GUCE-SINGLE-WINDOW"


def test_all_published_measures_and_actors_are_source_bound():
    for country in get_supported_regulatory_countries():
        compliance = get_country_regulatory_compliance(country)
        assert compliance is not None
        for measure in compliance["measures"]:
            assert measure["source_id"]
            assert measure["legal_reference"]
            assert measure["verification_status"]
            assert measure["source_record_path"]
            if measure["fees_status"] == "NOT_AVAILABLE":
                assert measure["fees"] is None
        for actor in compliance["mandated_actors"]:
            assert actor["source_id"]
            assert actor["legal_reference"]
            assert actor["verification_status"]
            assert actor["mandate_status"].casefold() != "active"
            assert actor["mandate_evidence"]
            if actor["authorized_fees_status"] == "NOT_AVAILABLE":
                assert actor["authorized_fees"] is None


def test_runtime_returns_a_deep_copy_of_cached_source_data():
    first = get_country_regulatory_compliance("COD")
    assert first is not None
    first["measures"][0]["measure_name"] = "MUTATED"
    first["mandated_actors"].clear()

    second = get_country_regulatory_compliance("COD")
    assert second is not None
    assert second["measures"][0]["measure_name"] != "MUTATED"
    assert second["mandated_actors"]


def test_unknown_country_remains_unavailable():
    assert get_country_regulatory_compliance("DZA") is None


def test_regulatory_router_declares_country_list_and_detail_paths():
    paths = {route.path for route in router.routes}
    assert "/regulatory-compliance/countries" in paths
    assert "/regulatory-compliance/country/{country_iso3}" in paths


def test_actor_with_bare_active_status_is_rejected(monkeypatch):
    from services import regulatory_compliance_service as service

    source = service._read_json("data/drc/regulatory_measures.json")
    altered = {
        **source,
        "regulatory_measures": [dict(measure) for measure in source["regulatory_measures"]],
    }
    occ = next(
        measure
        for measure in altered["regulatory_measures"]
        if measure["record_id"] == "COD-OCC-CBCA"
    )
    occ["mandated_actors"] = [dict(actor) for actor in occ["mandated_actors"]]
    occ["mandated_actors"][0]["mandate_status"] = "ACTIVE"

    monkeypatch.setattr(service, "_read_json", lambda _path: altered)
    with pytest.raises(ValueError, match="bare ACTIVE"):
        service.get_country_regulatory_compliance("COD")
