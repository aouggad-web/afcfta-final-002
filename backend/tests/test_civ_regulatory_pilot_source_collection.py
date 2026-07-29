"""
Vérifications d'intégrité du premier lot réglementaire Côte d'Ivoire :
formalités et contrôles obligatoires à l'importation (GUCE, RFCV, BSC,
VOC/PVoC), distincts des taux fiscaux (vat_measures.json).

Aucune mesure de ce lot n'a pu être archivée sur texte primaire : les
portails officiels renvoient HTTP 403 sur récupération automatique. Statuts
canoniques : PARTIAL (source officielle identifiable, non archivée),
pending_primary_archive=true. Tous les frais restent null (NOT_AVAILABLE) :
aucun montant secondaire n'entre dans le calculateur.
"""

import csv
import json
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[2]
_DATA_DIR = _ROOT / "data" / "cote-d-ivoire"
_SOURCES_DIR = _ROOT / "data" / "sources" / "cote-d-ivoire"

_CANONICAL_STATUSES = {"PARTIAL", "UNVERIFIED", "VERIFIED_PRIMARY_TEXT"}
_EXPECTED_RECORD_IDS = {
    "CIV-GUCE-SINGLE-WINDOW",
    "CIV-DOUANES-RFCV",
    "CIV-OIC-BSC",
    "CIV-COMMERCE-VOC",
}


def _load_measures():
    return json.loads(
        (_DATA_DIR / "regulatory_measures.json").read_text(encoding="utf-8")
    )["regulatory_measures"]


def test_civ_regulatory_measures_present():
    measures = _load_measures()
    assert {m["record_id"] for m in measures} == _EXPECTED_RECORD_IDS


def test_civ_regulatory_measures_use_canonical_statuses():
    for m in _load_measures():
        assert m["verification_status"] in _CANONICAL_STATUSES
        # aucune mesure archivée ce cycle : toutes en attente d'archive primaire
        assert m["verification_status"] == "PARTIAL"
        assert m["pending_primary_archive"] is True


def test_civ_regulatory_fees_are_null_not_fabricated():
    """Aucun frais issu de source secondaire : fees=null, statut NOT_AVAILABLE."""
    for m in _load_measures():
        assert m["fees"] is None
        assert m["fees_status"] == "NOT_AVAILABLE"


def test_civ_regulatory_measures_have_required_fields():
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


def test_civ_webb_fontaine_classified_with_actor_fiche():
    """Webb Fontaine est rattaché à GUCE-CI avec une fiche d'acteur complète,
    classé selon son rôle exact (opérateur technique, pas prestataire
    mandaté en exercice faute de confirmation post-2023)."""
    guce = next(
        m for m in _load_measures() if m["record_id"] == "CIV-GUCE-SINGLE-WINDOW"
    )
    actors = guce.get("mandated_actors", [])
    wf = next(a for a in actors if "WEBB FONTAINE" in a["actor_name"].upper())
    assert wf["actor_type"] in {"TECHNICAL_OPERATOR", "MANDATED_SERVICE_PROVIDER"}
    assert _ACTOR_FICHE_FIELDS <= set(wf.keys())
    assert wf["authorized_fees"] is None
    assert wf["authorized_fees_status"] == "NOT_AVAILABLE"
    # mandat post-2023 non confirmé : jamais "active" nu, statut explicite
    assert wf["mandate_status"] not in _FORBIDDEN_BARE_STATUS
    assert wf["mandate_status"] == "TERMINATED"
    assert len(wf["mandate_evidence"]) >= 1
    for ev in wf["mandate_evidence"]:
        assert {"date", "title", "publisher", "url"} <= set(ev.keys())


def test_civ_regulatory_source_ids_registered():
    """Chaque source_id cité doit exister dans legal_sources.json."""
    sources = json.loads(
        (_DATA_DIR / "legal_sources.json").read_text(encoding="utf-8")
    )["sources"]
    registered = {s["source_id"] for s in sources}
    used = {m["source_id"] for m in _load_measures()}
    assert used <= registered


def test_civ_partial_sources_have_no_fabricated_archive():
    """Une source PARTIAL non archivée ne doit pas prétendre un fichier local
    ou un SHA-256 : local_file et sha256 restent null."""
    sources = json.loads(
        (_DATA_DIR / "legal_sources.json").read_text(encoding="utf-8")
    )["sources"]
    used = {m["source_id"] for m in _load_measures()}
    for s in sources:
        if s["source_id"] in used:
            assert s["verification_status"] == "PARTIAL"
            assert s.get("pending_primary_archive") is True
            assert s["local_file"] is None
            assert s["sha256"] is None


def test_civ_inventory_lists_regulatory_sources():
    with open(_SOURCES_DIR / "inventory.csv", encoding="utf-8", newline="") as f:
        rows = list(csv.DictReader(f))
    ids = {r["id"] for r in rows}
    used = {m["source_id"] for m in _load_measures()}
    assert used <= ids


def test_civ_readme_documents_403_and_partial():
    readme = (_SOURCES_DIR / "README.md").read_text(encoding="utf-8")
    assert "403" in readme
    assert "PARTIAL" in readme
    assert "pending_primary_archive" in readme


def test_civ_not_registered_as_supported_jurisdiction():
    from services.national_legal_calculation_service import SUPPORTED_JURISDICTIONS

    assert "CIV" not in SUPPORTED_JURISDICTIONS


def test_civ_has_no_fabricated_afcfta_offer():
    from etl.afcfta_national_offers import NATIONAL_OFFER_REGISTRY, check_conformity

    assert "CIV" not in NATIONAL_OFFER_REGISTRY
    assert check_conformity("CIV")["status"] == "NO_NATIONAL_OFFER_REGISTERED"
