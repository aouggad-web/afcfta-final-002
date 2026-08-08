"""Distinction, pour une mesure, entre « aucun prestataire mandaté confirmé »
(NOT_APPLICABLE), « prestataire non encore documenté » (NOT_AVAILABLE) et
« prestataire mandaté actuellement documenté » (DOCUMENTED) — point de
qualité de données identifié en revue sur les issues #358-#361 : déléguer une
formalité à un opérateur privé mandaté n'est jamais présumé, ni son absence.
mandated_actor_status est un champ requis sur chaque mesure des 6 pays
publiés (voir regulatory_compliance_service._MEASURE_REQUIRED_FIELDS /
_MANDATED_ACTOR_STATUSES).

NOT_APPLICABLE n'est utilisé que lorsque la source confirme explicitement que
l'autorité réglementaire opère la formalité en direct — jamais déduit du
simple constat d'une liste mandated_actors vide, ce qui resterait
NOT_AVAILABLE tant qu'aucune source ne tranche. NGA-NAFDAC-CRIA et
CIV-COMMERCE-VOC, par exemple, décrivent un prestataire non nommé (« agents
accrédités », « organisme mandaté ») et restent donc NOT_AVAILABLE, pas
NOT_APPLICABLE.

La cohérence DOCUMENTED <=> mandated_actors est basée sur les mandats
CONFIRMÉS ACTIFS (_ACTIVE_MANDATE_STATUSES), pas sur la simple présence d'une
entrée dans la liste : un acteur TERMINATED (Webb Fontaine, CIV-GUCE) ou
UNVERIFIED (Intertek, GHA-GSA-EASYPASS après juillet 2026) reste dans
mandated_actors comme historique, sans forcer à lui seul le statut de la
mesure à DOCUMENTED. Revue Copilot/Codex sur PR #372 : GHA-GSA-EASYPASS
(désormais gérée en direct par la GSA depuis le 1er juillet 2026, source
explicite) devait pouvoir rapporter NOT_APPLICABLE tout en conservant
l'historique Bureau Veritas/Intertek — la validation symétrique d'origine
l'en empêchait.
"""

import pytest
from services.regulatory_compliance_service import get_country_regulatory_compliance

_ALL_COUNTRIES = ("CIV", "COD", "CMR", "GHA", "KEN", "NGA")
_STATUSES = {"DOCUMENTED", "NOT_APPLICABLE", "NOT_AVAILABLE"}
_ACTIVE_MANDATE_STATUSES = {"CONFIRMED_TIME_LIMITED", "CONFIRMED_UNDATED_END"}


def _measures(country):
    compliance = get_country_regulatory_compliance(country)
    assert compliance is not None
    return compliance["measures"]


def _has_confirmed_active_actor(measure):
    return any(
        actor.get("mandate_status") in _ACTIVE_MANDATE_STATUSES
        for actor in measure.get("mandated_actors") or []
    )


def test_every_measure_across_all_countries_has_a_canonical_mandated_actor_status():
    for country in _ALL_COUNTRIES:
        for measure in _measures(country):
            assert measure["mandated_actor_status"] in _STATUSES, measure["record_id"]


def test_documented_status_matches_a_confirmed_active_mandated_actor():
    for country in _ALL_COUNTRIES:
        for measure in _measures(country):
            has_active = _has_confirmed_active_actor(measure)
            if measure["mandated_actor_status"] == "DOCUMENTED":
                assert has_active, measure["record_id"]
            else:
                assert not has_active, measure["record_id"]


def test_not_applicable_measures_have_no_confirmed_active_actor():
    """KEN-KRA-ACD (jamais de prestataire) et GHA-GSA-EASYPASS (reprise en
    direct par la GSA depuis juillet 2026) sont les deux seules mesures
    NOT_APPLICABLE sur les 17 : dans les deux cas, aucun acteur documenté
    n'a un mandat confirmé actif."""
    not_applicable = []
    for country in _ALL_COUNTRIES:
        for measure in _measures(country):
            if measure["mandated_actor_status"] == "NOT_APPLICABLE":
                not_applicable.append(measure["record_id"])
                assert not _has_confirmed_active_actor(measure), measure["record_id"]
    assert sorted(not_applicable) == ["GHA-GSA-EASYPASS", "KEN-KRA-ACD"]


def test_gha_easypass_keeps_historical_actors_despite_not_applicable_status():
    """Régression PR #372 (revue codex) : la reprise en gestion directe par
    la GSA ne doit pas effacer l'historique Bureau Veritas (TERMINATED) et
    Intertek (UNVERIFIED) — seulement empêcher qu'ils forcent DOCUMENTED."""
    measure = next(m for m in _measures("GHA") if m["record_id"] == "GHA-GSA-EASYPASS")
    assert measure["mandated_actor_status"] == "NOT_APPLICABLE"
    actor_names = {a["actor_name"] for a in measure["mandated_actors"]}
    assert actor_names == {"Bureau Veritas", "Intertek"}


def test_civ_guce_terminated_actor_keeps_measure_out_of_documented():
    """Webb Fontaine est confirmé TERMINATED (rachat de sa participation par
    l'État, 2023) et aucune source ne confirme ni n'infirme un rôle technique
    résiduel : la mesure reste NOT_AVAILABLE, pas DOCUMENTED ni NOT_APPLICABLE
    (l'absence totale de prestataire n'est pas confirmée non plus)."""
    measure = next(m for m in _measures("CIV") if m["record_id"] == "CIV-GUCE-SINGLE-WINDOW")
    assert measure["mandated_actor_status"] == "NOT_AVAILABLE"
    assert measure["mandated_actors"][0]["actor_name"] == "Webb Fontaine"


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


def test_mandated_actor_status_documented_without_active_actor_is_rejected(monkeypatch):
    from services import regulatory_compliance_service as service

    source = service._read_json("data/cote-d-ivoire/regulatory_measures.json")
    altered = {
        **source,
        "regulatory_measures": [dict(measure) for measure in source["regulatory_measures"]],
    }
    # CIV-DOUANES-RFCV has no mandated_actors at all.
    altered["regulatory_measures"][1]["mandated_actor_status"] = "DOCUMENTED"

    monkeypatch.setattr(service, "_read_json", lambda _path: altered)
    with pytest.raises(ValueError, match="DOCUMENTED without any confirmed-active"):
        service.get_country_regulatory_compliance("CIV")


def test_mandated_actor_status_documented_with_only_terminated_actor_is_rejected(monkeypatch):
    from services import regulatory_compliance_service as service

    source = service._read_json("data/cote-d-ivoire/regulatory_measures.json")
    altered = {
        **source,
        "regulatory_measures": [dict(measure) for measure in source["regulatory_measures"]],
    }
    # CIV-GUCE-SINGLE-WINDOW's only actor (Webb Fontaine) is TERMINATED.
    altered["regulatory_measures"][0]["mandated_actor_status"] = "DOCUMENTED"

    monkeypatch.setattr(service, "_read_json", lambda _path: altered)
    with pytest.raises(ValueError, match="DOCUMENTED without any confirmed-active"):
        service.get_country_regulatory_compliance("CIV")


def test_mandated_actor_status_not_applicable_with_confirmed_active_actor_is_rejected(
    monkeypatch,
):
    from services import regulatory_compliance_service as service

    source = service._read_json("data/drc/regulatory_measures.json")
    altered = {
        **source,
        "regulatory_measures": [dict(measure) for measure in source["regulatory_measures"]],
    }
    # COD-OCC-CBCA's only actor (BIVAC) is CONFIRMED_TIME_LIMITED — a genuinely
    # active mandate, so downgrading the measure status must be rejected.
    altered["regulatory_measures"][1]["mandated_actor_status"] = "NOT_APPLICABLE"

    monkeypatch.setattr(service, "_read_json", lambda _path: altered)
    with pytest.raises(ValueError, match="not DOCUMENTED"):
        service.get_country_regulatory_compliance("COD")


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


def test_diplomatic_delegation_note_appears_only_when_actors_are_documented():
    """Framing language accompanying documented delegations: presented as a
    punctual, capacity-support arrangement tied to the mandating
    administration's own modernization, never as commentary on its
    competence. Absent from countries/datasets with no documented actor."""
    cmr = get_country_regulatory_compliance("CMR")
    assert cmr["mandated_actor_count"] > 0
    assert "modernisation" in cmr["disclaimer"]

    ken = get_country_regulatory_compliance("KEN")
    assert ken["mandated_actor_count"] > 0
    assert "modernisation" in ken["disclaimer"]


def test_diplomatic_delegation_note_absent_when_no_actor_is_documented():
    """CIV n'a désormais plus aucun mandat confirmé actif (Webb Fontaine est
    TERMINATED) : la note diplomatique, qui n'a de sens qu'en présence d'une
    délégation active, doit être absente — même si mandated_actors conserve
    Webb Fontaine comme entrée historique."""
    civ = get_country_regulatory_compliance("CIV")
    assert all(m["mandated_actor_status"] != "DOCUMENTED" for m in civ["measures"])
    assert "modernisation" not in civ["disclaimer"]


def test_mandated_actors_non_list_value_is_rejected(monkeypatch):
    """A dataset mistake setting mandated_actors to a dict/string must fail
    closed with a clear error, not silently pass has_actors and crash later
    while normalizing actors."""
    from services import regulatory_compliance_service as service

    source = service._read_json("data/cote-d-ivoire/regulatory_measures.json")
    altered_measure = dict(source["regulatory_measures"][1])
    altered_measure["mandated_actors"] = "BIVAC"
    altered = {
        **source,
        "regulatory_measures": [source["regulatory_measures"][0], altered_measure]
        + [dict(measure) for measure in source["regulatory_measures"][2:]],
    }

    monkeypatch.setattr(service, "_read_json", lambda _path: altered)
    with pytest.raises(ValueError, match="non-list mandated_actors"):
        service.get_country_regulatory_compliance("CIV")
