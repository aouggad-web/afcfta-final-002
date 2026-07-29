"""
Vérifications d'intégrité du premier lot réglementaire RDC : formalités et
contrôles obligatoires à l'importation (SEGUCE, OCC/CBCA, FERI/FERE),
distincts des taux fiscaux (vat_measures.json).

Aucune mesure de ce lot n'a pu être archivée sur texte primaire : les
portails officiels renvoient HTTP 403. Statuts canoniques : PARTIAL,
pending_primary_archive=true. Tous les frais restent null (NOT_AVAILABLE).
BIVAC (Bureau Veritas) figure comme opérateur mandaté sous la mesure
OCC/CBCA, pas comme mesure réglementaire autonome.
"""

import csv
import json
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[2]
_DATA_DIR = _ROOT / "data" / "drc"
_SOURCES_DIR = _ROOT / "data" / "sources" / "drc"

_CANONICAL_STATUSES = {"PARTIAL", "UNVERIFIED", "VERIFIED_PRIMARY_TEXT"}
_EXPECTED_RECORD_IDS = {
    "COD-SEGUCE-SINGLE-WINDOW",
    "COD-OCC-CBCA",
    "COD-OGEFREM-FERI",
}


def _load_measures():
    return json.loads((_DATA_DIR / "regulatory_measures.json").read_text(encoding="utf-8"))[
        "regulatory_measures"
    ]


def test_cod_regulatory_measures_present():
    measures = _load_measures()
    assert {m["record_id"] for m in measures} == _EXPECTED_RECORD_IDS


def test_cod_regulatory_measures_use_canonical_statuses():
    for m in _load_measures():
        assert m["verification_status"] in _CANONICAL_STATUSES
        assert m["verification_status"] == "PARTIAL"
        assert m["pending_primary_archive"] is True


def test_cod_regulatory_fees_are_null_not_fabricated():
    for m in _load_measures():
        assert m["fees"] is None
        assert m["fees_status"] == "NOT_AVAILABLE"


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

_FORBIDDEN_BARE_STATUS = {"active", "ACTIVE", "Active"}


def test_cod_bivac_is_mandated_actor_not_standalone_measure():
    """BIVAC ne doit PAS avoir son propre record_id : il figure comme
    MANDATED_SERVICE_PROVIDER, avec sa propre fiche d'acteur, sous la
    mesure OCC/CBCA."""
    measures = _load_measures()
    record_ids = {m["record_id"] for m in measures}
    # aucun enregistrement autonome BIVAC
    assert not any("BIVAC" in rid.upper() for rid in record_ids)
    # BIVAC présent comme acteur mandaté sous OCC, avec fiche complète
    occ = next(m for m in measures if m["record_id"] == "COD-OCC-CBCA")
    actors = occ.get("mandated_actors", [])
    bivac = next(a for a in actors if "BIVAC" in a["actor_name"].upper())
    assert bivac["actor_type"] == "MANDATED_SERVICE_PROVIDER"
    assert bivac["mandating_authority"] and "OCC" in bivac["mandating_authority"].upper()
    assert _ACTOR_FICHE_FIELDS <= set(bivac.keys())
    assert bivac["authorized_fees"] is None
    assert bivac["authorized_fees_status"] == "NOT_AVAILABLE"
    # les autres mesures ne portent pas d'acteur BIVAC
    for m in measures:
        if m["record_id"] == "COD-OCC-CBCA":
            continue
        assert not any(
            "BIVAC" in a.get("actor_name", "").upper() for a in m.get("mandated_actors", [])
        )


def test_cod_bivac_mandate_status_never_bare_active():
    """Le mandat BIVAC est daté et prouvé, mais explicitement limité dans le
    temps (échéance rapportée nov. 2026, appel d'offres concurrentiel) :
    jamais un statut 'active' nu, toujours accompagné de dates et preuves."""
    occ = next(m for m in _load_measures() if m["record_id"] == "COD-OCC-CBCA")
    bivac = next(a for a in occ["mandated_actors"] if "BIVAC" in a["actor_name"].upper())
    assert bivac["mandate_status"] not in _FORBIDDEN_BARE_STATUS
    assert len(bivac["mandate_evidence"]) >= 1
    for ev in bivac["mandate_evidence"]:
        assert {"date", "title", "publisher", "url"} <= set(ev.keys())


def test_cod_bivac_delivered_document_is_precise():
    """Le document délivré par BIVAC doit être distingué précisément :
    Attestation de Vérification (programme VOC), pas un terme ambigu
    mêlant Attestation de Vérification et Certificat de Conformité."""
    occ = next(m for m in _load_measures() if m["record_id"] == "COD-OCC-CBCA")
    bivac = next(a for a in occ["mandated_actors"] if "BIVAC" in a["actor_name"].upper())
    assert "Attestation de Vérification" in bivac["delivered_document"]
    # distinction explicite du Certificat de Conformité (programme différent)
    assert "Certificat de Conformité" in bivac["delivered_document"]
    assert (
        "Distincte" in bivac["delivered_document"]
        or "distinct" in bivac["delivered_document"].lower()
    )


def test_cod_regulatory_measures_have_required_fields():
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
    for m in _load_measures():
        assert required <= set(m.keys())
        assert m["scope"] and m["authority"] and m["legal_reference"]


def test_cod_regulatory_source_ids_registered():
    sources = json.loads((_DATA_DIR / "legal_sources.json").read_text(encoding="utf-8"))["sources"]
    registered = {s["source_id"] for s in sources}
    used = {m["source_id"] for m in _load_measures()}
    assert used <= registered


def test_cod_partial_sources_have_no_fabricated_archive():
    sources = json.loads((_DATA_DIR / "legal_sources.json").read_text(encoding="utf-8"))["sources"]
    used = {m["source_id"] for m in _load_measures()}
    for s in sources:
        if s["source_id"] in used:
            assert s["verification_status"] == "PARTIAL"
            assert s.get("pending_primary_archive") is True
            assert s["local_file"] is None
            assert s["sha256"] is None


def test_cod_inventory_lists_regulatory_sources():
    with open(_SOURCES_DIR / "inventory.csv", encoding="utf-8", newline="") as f:
        rows = list(csv.DictReader(f))
    ids = {r["id"] for r in rows}
    used = {m["source_id"] for m in _load_measures()}
    assert used <= ids


def test_cod_readme_documents_403_and_bivac():
    readme = (_SOURCES_DIR / "README.md").read_text(encoding="utf-8")
    assert "403" in readme
    assert "PARTIAL" in readme
    assert "BIVAC" in readme


def test_cod_not_registered_as_supported_jurisdiction():
    from services.national_legal_calculation_service import SUPPORTED_JURISDICTIONS

    assert "COD" not in SUPPORTED_JURISDICTIONS


def test_cod_has_no_fabricated_afcfta_offer():
    from etl.afcfta_national_offers import NATIONAL_OFFER_REGISTRY, check_conformity

    assert "COD" not in NATIONAL_OFFER_REGISTRY
    assert check_conformity("COD")["status"] == "NO_NATIONAL_OFFER_REGISTERED"
