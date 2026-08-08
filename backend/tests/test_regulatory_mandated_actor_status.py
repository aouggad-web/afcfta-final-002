"""Distinction, pour une mesure sans mandated_actors, entre « aucun prestataire
mandaté confirmé » (NOT_APPLICABLE) et « prestataire non encore documenté »
(NOT_AVAILABLE) — point de qualité de données identifié en revue sur les
issues #358-#361 : déléguer une formalité à un opérateur privé mandaté n'est
jamais présumé, ni son absence. mandated_actor_status est un champ requis sur
chaque mesure des 6 pays publiés (voir
regulatory_compliance_service._MEASURE_REQUIRED_FIELDS /
_MANDATED_ACTOR_STATUSES).

NOT_APPLICABLE n'est utilisé que lorsque la source confirme explicitement que
l'autorité réglementaire opère la formalité en direct — jamais déduit du
simple constat d'une liste mandated_actors vide, ce qui resterait
NOT_AVAILABLE tant qu'aucune source ne tranche. Sur les 17 mesures publiées,
seule KEN-KRA-ACD (« Plateforme opérée directement par la Kenya Revenue
Authority ») remplit ce critère ; NGA-NAFDAC-CRIA et CIV-COMMERCE-VOC, par
exemple, décrivent un prestataire non nommé (« agents accrédités »,
« organisme mandaté ») et restent donc NOT_AVAILABLE, pas NOT_APPLICABLE.
"""

import pytest
from services.regulatory_compliance_service import get_country_regulatory_compliance

_ALL_COUNTRIES = ("CIV", "COD", "CMR", "GHA", "KEN", "NGA")
_STATUSES = {"DOCUMENTED", "NOT_APPLICABLE", "NOT_AVAILABLE"}


def _measures(country):
    compliance = get_country_regulatory_compliance(country)
    assert compliance is not None
    return compliance["measures"]


def test_every_measure_across_all_countries_has_a_canonical_mandated_actor_status():
    for country in _ALL_COUNTRIES:
        for measure in _measures(country):
            assert measure["mandated_actor_status"] in _STATUSES, measure["record_id"]


def test_documented_status_matches_a_non_empty_mandated_actors_list():
    for country in _ALL_COUNTRIES:
        for measure in _measures(country):
            has_actors = bool(measure.get("mandated_actors"))
            if measure["mandated_actor_status"] == "DOCUMENTED":
                assert has_actors, measure["record_id"]
            else:
                assert not has_actors, measure["record_id"]


def test_ken_kra_acd_is_the_only_not_applicable_measure():
    """Seule mesure sur les 17 pour laquelle la source confirme explicitement
    une exploitation directe par l'autorité, sans aucun prestataire mandaté :
    toute autre mesure avec mandated_actors vide reste NOT_AVAILABLE, jamais
    NOT_APPLICABLE par défaut."""
    not_applicable = []
    for country in _ALL_COUNTRIES:
        for measure in _measures(country):
            if measure["mandated_actor_status"] == "NOT_APPLICABLE":
                not_applicable.append(measure["record_id"])
    assert not_applicable == ["KEN-KRA-ACD"]


def test_measures_with_an_implied_but_unnamed_provider_stay_not_available():
    """NGA-NAFDAC-CRIA (agents accrédités non nommés) et CIV-COMMERCE-VOC
    (organisme mandaté non nommé) ne sont jamais requalifiées en
    NOT_APPLICABLE : un prestataire est évoqué par la source, seule son
    identité manque."""
    nga_cria = next(m for m in _measures("NGA") if m["record_id"] == "NGA-NAFDAC-CRIA")
    civ_voc = next(m for m in _measures("CIV") if m["record_id"] == "CIV-COMMERCE-VOC")
    assert nga_cria["mandated_actor_status"] == "NOT_AVAILABLE"
    assert civ_voc["mandated_actor_status"] == "NOT_AVAILABLE"


def test_mandated_actor_status_invalid_value_is_rejected(monkeypatch):
    from services import regulatory_compliance_service as service

    source = service._read_json("data/cote-d-ivoire/regulatory_measures.json")
    altered = {
        **source,
        "regulatory_measures": [dict(measure) for measure in source["regulatory_measures"]],
    }
    altered["regulatory_measures"][1]["mandated_actor_status"] = "PROBABLY_NONE"

    monkeypatch.setattr(service, "_read_json", lambda _path: altered)
    with pytest.raises(ValueError, match="non-canonical mandated_actor_status"):
        service.get_country_regulatory_compliance("CIV")


def test_mandated_actor_status_documented_without_actors_is_rejected(monkeypatch):
    from services import regulatory_compliance_service as service

    source = service._read_json("data/cote-d-ivoire/regulatory_measures.json")
    altered = {
        **source,
        "regulatory_measures": [dict(measure) for measure in source["regulatory_measures"]],
    }
    altered["regulatory_measures"][1]["mandated_actor_status"] = "DOCUMENTED"

    monkeypatch.setattr(service, "_read_json", lambda _path: altered)
    with pytest.raises(ValueError, match="DOCUMENTED without any mandated_actors"):
        service.get_country_regulatory_compliance("CIV")


def test_mandated_actor_status_not_applicable_with_actors_present_is_rejected(monkeypatch):
    from services import regulatory_compliance_service as service

    source = service._read_json("data/cote-d-ivoire/regulatory_measures.json")
    altered = {
        **source,
        "regulatory_measures": [dict(measure) for measure in source["regulatory_measures"]],
    }
    altered["regulatory_measures"][0]["mandated_actor_status"] = "NOT_APPLICABLE"

    monkeypatch.setattr(service, "_read_json", lambda _path: altered)
    with pytest.raises(ValueError, match="not DOCUMENTED"):
        service.get_country_regulatory_compliance("CIV")


def test_mandated_actor_status_is_required_on_every_measure(monkeypatch):
    from services import regulatory_compliance_service as service

    source = service._read_json("data/cote-d-ivoire/regulatory_measures.json")
    altered_measure = dict(source["regulatory_measures"][0])
    del altered_measure["mandated_actor_status"]
    altered = {
        **source,
        "regulatory_measures": [altered_measure]
        + [dict(measure) for measure in source["regulatory_measures"][1:]],
    }

    monkeypatch.setattr(service, "_read_json", lambda _path: altered)
    with pytest.raises(ValueError, match="missing required fields"):
        service.get_country_regulatory_compliance("CIV")
