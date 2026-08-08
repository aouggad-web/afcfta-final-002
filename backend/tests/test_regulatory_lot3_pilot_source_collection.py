"""
Vérifications d'intégrité du LOT 3 réglementaire : Cameroun, Ghana, Kenya,
Nigeria — formalités et contrôles obligatoires à l'importation, distincts
des taux fiscaux (vat_measures.json/excise_measures.json).

Recherche effectuée via sources officielles/directement traçables ; les
éléments non confirmés sur source primaire restent PARTIAL/UNVERIFIED et ne
sont jamais présentés comme actifs sans preuve. Aucun frais fabriqué : tous
les montants non officiellement publiés restent null / NOT_AVAILABLE.
"""

import json
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[2]

_CANONICAL_STATUSES = {"DOCUMENTED", "PARTIAL", "UNVERIFIED", "VERIFIED_PRIMARY_TEXT"}
_FORBIDDEN_BARE_STATUS = {"active", "ACTIVE", "Active"}

_COUNTRIES = {
    "CMR": {
        "dir": "cameroon",
        "record_ids": {"CMR-ANOR-PECAE", "CMR-MINFI-PVI", "CMR-CIVIC-VEHICLES", "CMR-CNCC-BESC"},
    },
    "GHA": {
        "dir": "ghana",
        "record_ids": {"GHA-GRA-ICUMS", "GHA-GSA-EASYPASS"},
    },
    "KEN": {
        "dir": "kenya",
        "record_ids": {"KEN-KEBS-PVOC", "KEN-KRA-ACD"},
    },
    "NGA": {
        "dir": "nigeria",
        "record_ids": {"NGA-SON-SONCAP", "NGA-NAFDAC-CRIA"},
    },
}


def _load_measures(iso3: str):
    data_dir = _ROOT / "data" / _COUNTRIES[iso3]["dir"]
    dataset = json.loads((data_dir / "regulatory_measures.json").read_text(encoding="utf-8"))
    assert dataset["country"] == iso3
    return dataset["regulatory_measures"]


def _load_legal_sources(iso3: str):
    data_dir = _ROOT / "data" / _COUNTRIES[iso3]["dir"]
    return json.loads((data_dir / "legal_sources.json").read_text(encoding="utf-8"))["sources"]


def test_lot3_regulatory_measures_present():
    for iso3, meta in _COUNTRIES.items():
        assert {m["record_id"] for m in _load_measures(iso3)} == meta["record_ids"]


def test_lot3_regulatory_measures_use_canonical_statuses():
    for iso3 in _COUNTRIES:
        for m in _load_measures(iso3):
            assert m["verification_status"] in _CANONICAL_STATUSES, f"{iso3}.{m['record_id']}"
            assert m["pending_primary_archive"] is True


def test_lot3_regulatory_fees_are_null_or_documented_not_fabricated():
    for iso3 in _COUNTRIES:
        for m in _load_measures(iso3):
            if m["fees_status"] == "NOT_AVAILABLE":
                assert m["fees"] is None, f"{iso3}.{m['record_id']}"
            else:
                assert m["fees"] is not None, f"{iso3}.{m['record_id']}"


def test_lot3_regulatory_measures_have_required_fields():
    required = {
        "scope",
        "products",
        "transport",
        "conditions",
        "exemptions",
        "documents",
        "authority",
        "platform",
        "source_id",
        "legal_reference",
    }
    for iso3 in _COUNTRIES:
        for m in _load_measures(iso3):
            assert required <= set(m.keys()), f"{iso3}.{m['record_id']}"
            assert m["scope"] and m["authority"] and m["legal_reference"]


_ACTOR_FICHE_FIELDS = {
    "actor_name",
    "actor_type",
    "legal_status",
    "mandating_authority",
    "mission",
    "mandate_basis",
    "mandate_status",
    "mandate_duration",
    "mandate_evidence",
    "authorized_fees",
    "authorized_fees_status",
    "delivered_document",
}


def test_lot3_mandated_actors_never_have_bare_active_status():
    for iso3 in _COUNTRIES:
        for m in _load_measures(iso3):
            for actor in m.get("mandated_actors", []):
                assert _ACTOR_FICHE_FIELDS <= set(actor.keys())
                assert actor["mandate_status"] not in _FORBIDDEN_BARE_STATUS
                assert actor["mandate_evidence"], f"{iso3}: {actor['actor_name']}"
                for ev in actor["mandate_evidence"]:
                    assert {"date", "title", "publisher", "url"} <= set(ev.keys())


def test_lot3_actor_fees_are_null_when_status_not_available():
    for iso3 in _COUNTRIES:
        for m in _load_measures(iso3):
            for actor in m.get("mandated_actors", []):
                if actor["authorized_fees_status"] == "NOT_AVAILABLE":
                    assert actor["authorized_fees"] is None


def test_lot3_cameroon_pecae_confirms_three_mandated_providers():
    """PECAE : 3 prestataires confirmés sur source primaire/quasi-primaire
    distincte (Intertek, SGS, TÜV Rheinland), jamais présentés comme
    autorité réglementaire."""
    pecae = next(m for m in _load_measures("CMR") if m["record_id"] == "CMR-ANOR-PECAE")
    actor_names = {a["actor_name"] for a in pecae["mandated_actors"]}
    assert "Intertek International Limited" in actor_names
    assert "SGS S.A. (Société Générale de Surveillance)" in actor_names
    assert "TÜV Rheinland" in actor_names
    for actor in pecae["mandated_actors"]:
        assert actor["actor_type"] == "MANDATED_SERVICE_PROVIDER"
        assert actor["mandating_authority"] != actor["actor_name"]


def test_lot3_ghana_easypass_bureau_veritas_terminated_not_active():
    """Bureau Veritas a perdu son mandat EasyPASS le 1er juillet 2026 : ne
    doit jamais apparaître comme prestataire actif."""
    easypass = next(m for m in _load_measures("GHA") if m["record_id"] == "GHA-GSA-EASYPASS")
    bv = next(a for a in easypass["mandated_actors"] if a["actor_name"] == "Bureau Veritas")
    assert bv["mandate_status"] == "TERMINATED"
    assert bv["actor_type"] == "TECHNICAL_OPERATOR"


def test_lot3_nigeria_ictn_not_included_as_active_measure():
    """L'ICTN nigérian, annoncé depuis 2019 mais non en vigueur au moment de
    la recherche, ne doit apparaître dans aucun record_id de mesure active."""
    record_ids = {m["record_id"] for m in _load_measures("NGA")}
    assert not any("ICTN" in rid or "CTN" in rid for rid in record_ids)


def test_lot3_kenya_pvoc_general_goods_panel_not_fabricated():
    """La liste des 9 prestataires PVoC 'marchandises générales' annoncée en
    presse (source primaire KEBS illisible lors de l'extraction) ne doit pas
    apparaître comme acteurs mandatés confirmés ; seul QISJ (véhicules,
    confirmé sur l'avis KEBS lui-même) doit être listé."""
    pvoc = next(m for m in _load_measures("KEN") if m["record_id"] == "KEN-KEBS-PVOC")
    actor_names = {a["actor_name"] for a in pvoc["mandated_actors"]}
    assert actor_names == {"Quality Inspection Services Inc. (QISJ)"}
    for forbidden in ("Bureau Veritas", "SGS", "Intertek", "Cotecna", "TÜV"):
        assert not any(forbidden in name for name in actor_names)


def test_lot3_source_ids_registered_in_legal_sources():
    for iso3, meta in _COUNTRIES.items():
        sources = _load_legal_sources(iso3)
        registered = {s["source_id"] for s in sources}
        used = {m["source_id"] for m in _load_measures(iso3)}
        assert used <= registered, f"{iso3}: {used - registered}"


def test_lot3_regulatory_work_does_not_add_new_supported_jurisdictions():
    """KEN était déjà une SUPPORTED_JURISDICTION avant ce lot (calcul TVA/accises,
    indépendant des formalités réglementaires) ; CMR/GHA/NGA ne doivent pas être
    ajoutés au calculateur tarifaire par ce lot réglementaire."""
    from services.national_legal_calculation_service import SUPPORTED_JURISDICTIONS

    assert "KEN" in SUPPORTED_JURISDICTIONS
    for iso3 in ("CMR", "GHA", "NGA"):
        assert iso3 not in SUPPORTED_JURISDICTIONS


def test_lot3_has_no_fabricated_afcfta_offer():
    from etl.afcfta_national_offers import NATIONAL_OFFER_REGISTRY, check_conformity

    for iso3 in _COUNTRIES:
        assert iso3 not in NATIONAL_OFFER_REGISTRY
        assert check_conformity(iso3)["status"] == "NO_NATIONAL_OFFER_REGISTERED"
