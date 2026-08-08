"""LOT 4 (issue #359) : structuration des formalités CIV/COD en règles exploitables
— portée (générale/sectorielle/conditionnelle), modes de transport, statut des codes
SH, seuils/exclusions et procédure, sans jamais déduire une donnée absente de source.

Ces champs sont additifs et optionnels dans le service (voir
regulatory_compliance_service._validate_structured_scope_fields) : les pays du LOT 3
(CMR/GHA/KEN/NGA) n'en disposent pas encore et continuent de valider sans eux.
"""

import pytest
from services.regulatory_compliance_service import get_country_regulatory_compliance

_STRUCTURED_COUNTRIES = ("CIV", "COD")
_SCOPE_TYPES = {"GENERAL", "SECTORAL", "CONDITIONAL", "NOT_AVAILABLE"}
_TRANSPORT_MODES = {"MARITIME", "AERIEN", "ROUTIER", "FERROVIAIRE", "MULTIMODAL"}


def _measures(country):
    compliance = get_country_regulatory_compliance(country)
    assert compliance is not None
    return compliance["measures"]


def test_lot4_every_civ_cod_measure_has_a_canonical_scope_type():
    for country in _STRUCTURED_COUNTRIES:
        for measure in _measures(country):
            assert measure["scope_type"] in _SCOPE_TYPES, measure["record_id"]


def test_lot4_every_civ_cod_measure_has_canonical_transport_modes():
    for country in _STRUCTURED_COUNTRIES:
        for measure in _measures(country):
            modes = measure["transport_modes"]
            assert modes, measure["record_id"]
            assert set(modes) <= _TRANSPORT_MODES, measure["record_id"]


def test_lot4_maritime_only_measures_are_flagged_conditional_by_transport():
    """BSC (CIV) et FERI (COD) ne s'appliquent qu'au fret maritime : ce ne sont pas
    des mesures multimodales générales, contrairement au guichet unique."""
    civ_bsc = next(m for m in _measures("CIV") if m["record_id"] == "CIV-OIC-BSC")
    cod_feri = next(m for m in _measures("COD") if m["record_id"] == "COD-OGEFREM-FERI")
    assert civ_bsc["transport_modes"] == ["MARITIME"]
    assert cod_feri["transport_modes"] == ["MARITIME"]


def test_lot4_no_hs_code_is_fabricated_when_source_does_not_provide_one():
    """Aucune source CIV/COD collectée ne documente de code SH explicite : le champ
    doit rester NOT_AVAILABLE et hs_codes_explicit vide, jamais une valeur inventée."""
    for country in _STRUCTURED_COUNTRIES:
        for measure in _measures(country):
            assert measure["hs_codes_status"] == "NOT_AVAILABLE", measure["record_id"]
            assert measure["hs_codes_explicit"] == []


def test_lot4_thresholds_and_exclusions_stay_not_available_without_a_source():
    for country in _STRUCTURED_COUNTRIES:
        for measure in _measures(country):
            block = measure["thresholds_and_exclusions"]
            assert block["status"] == "NOT_AVAILABLE", measure["record_id"]
            assert block["text"] is None


def test_lot4_procedure_stays_not_available_without_an_official_delay_source():
    for country in _STRUCTURED_COUNTRIES:
        for measure in _measures(country):
            block = measure["procedure"]
            assert block["status"] == "NOT_AVAILABLE", measure["record_id"]
            assert block["steps"] is None
            assert block["official_delay"] is None


def test_lot4_measure_fees_are_tagged_as_regulatory_not_provider_fees():
    for country in _STRUCTURED_COUNTRIES:
        for measure in _measures(country):
            assert measure["fee_category"] == "REGULATORY_FEE", measure["record_id"]


def test_lot4_mandated_actor_fees_are_tagged_as_provider_not_regulatory_fees():
    """Distingue les honoraires de prestataire (Webb Fontaine, BIVAC) des frais
    réglementaires portés par la mesure elle-même."""
    for country in _STRUCTURED_COUNTRIES:
        compliance = get_country_regulatory_compliance(country)
        for actor in compliance["mandated_actors"]:
            assert actor["fee_category"] == "PROVIDER_FEE", actor["actor_name"]


def test_lot4_general_scope_measures_confirmed_by_existing_scope_text():
    """Le guichet unique (CIV/COD) est explicitement décrit comme s'appliquant à
    'toutes marchandises... sans restriction sectorielle' : GENERAL, pas SECTORAL."""
    civ_guce = next(m for m in _measures("CIV") if m["record_id"] == "CIV-GUCE-SINGLE-WINDOW")
    cod_seguce = next(m for m in _measures("COD") if m["record_id"] == "COD-SEGUCE-SINGLE-WINDOW")
    assert civ_guce["scope_type"] == "GENERAL"
    assert cod_seguce["scope_type"] == "GENERAL"


def test_lot4_sectoral_conformity_measures_are_not_overclaimed_as_general():
    """VOC (CIV) et OCC/CBCA (COD) ne visent que les 'produits réglementés' / une
    liste non confirmée de marchandises soumises au contrôle qualité : SECTORAL,
    jamais GENERAL malgré l'absence de liste précise."""
    civ_voc = next(m for m in _measures("CIV") if m["record_id"] == "CIV-COMMERCE-VOC")
    cod_occ = next(m for m in _measures("COD") if m["record_id"] == "COD-OCC-CBCA")
    assert civ_voc["scope_type"] == "SECTORAL"
    assert cod_occ["scope_type"] == "SECTORAL"


def test_lot4_lot3_countries_remain_unaffected_by_optional_structured_fields():
    """CMR/GHA/KEN/NGA n'ont pas encore été enrichis par ce lot : ils continuent de
    valider et de fonctionner sans scope_type/transport_modes/hs_codes_status."""
    for country in ("CMR", "GHA", "KEN", "NGA"):
        compliance = get_country_regulatory_compliance(country)
        assert compliance is not None
        for measure in compliance["measures"]:
            assert "scope_type" not in measure
            assert "transport_modes" not in measure


def test_lot4_invalid_scope_type_is_rejected(monkeypatch):
    from services import regulatory_compliance_service as service

    source = service._read_json("data/cote-d-ivoire/regulatory_measures.json")
    altered = {
        **source,
        "regulatory_measures": [dict(measure) for measure in source["regulatory_measures"]],
    }
    altered["regulatory_measures"][0]["scope_type"] = "NATIONWIDE"

    monkeypatch.setattr(service, "_read_json", lambda _path: altered)
    with pytest.raises(ValueError, match="non-canonical scope_type"):
        service.get_country_regulatory_compliance("CIV")


def test_lot4_hs_codes_documented_without_explicit_codes_is_rejected(monkeypatch):
    from services import regulatory_compliance_service as service

    source = service._read_json("data/cote-d-ivoire/regulatory_measures.json")
    altered = {
        **source,
        "regulatory_measures": [dict(measure) for measure in source["regulatory_measures"]],
    }
    altered["regulatory_measures"][0]["hs_codes_status"] = "DOCUMENTED"

    monkeypatch.setattr(service, "_read_json", lambda _path: altered)
    with pytest.raises(ValueError, match="DOCUMENTED without hs_codes_explicit"):
        service.get_country_regulatory_compliance("CIV")


def test_lot4_fee_category_on_measure_rejects_non_regulatory_value(monkeypatch):
    from services import regulatory_compliance_service as service

    source = service._read_json("data/cote-d-ivoire/regulatory_measures.json")
    altered = {
        **source,
        "regulatory_measures": [dict(measure) for measure in source["regulatory_measures"]],
    }
    altered["regulatory_measures"][0]["fee_category"] = "PROVIDER_FEE"

    monkeypatch.setattr(service, "_read_json", lambda _path: altered)
    with pytest.raises(ValueError, match="fee_category must be REGULATORY_FEE"):
        service.get_country_regulatory_compliance("CIV")
