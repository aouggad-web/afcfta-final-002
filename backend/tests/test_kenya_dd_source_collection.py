"""
Vérifications d'intégrité de la provenance documentaire du droit de douane
(DD/CET) kényan dans backend/data/KEN_tariffs.json.

Contexte : l'audit différentiel des 6 pays pilotes ZLECAf (2026-07-26,
audits/AUDIT_DIFFERENTIEL_PILOTES_2026-07-26.md) a constaté que le DD/CET
kényan (5604 lignes SH6) ne portait aucune preuve documentaire structurée
(pas de sha256, pas de source_id), contrairement à la couche TVA/accises
déjà vérifiée depuis la PR #307. Le fichier declarait seulement une URL
(kra.go.ke) en texte libre.

Ce module vérifie que le document exact cité par KEN_tariffs.json comme
source du DD est désormais archivé et haché — sans prétendre que chaque
taux DD individuel a été re-vérifié ligne par ligne contre ce texte
(chantier séparé, non réalisé ici).
"""

import hashlib
import json
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[2]
_KEN_TARIFFS = _ROOT / "backend" / "data" / "KEN_tariffs.json"
_KEN_LEGAL_SOURCES = _ROOT / "data" / "kenya" / "legal_sources.json"
_KEN_SOURCES_DIR = _ROOT / "data" / "sources" / "kenya"


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_ken_tariffs_summary_declares_dd_source_provenance():
    """Le résumé de KEN_tariffs.json doit référencer un source_id et un
    sha256 pour le droit de douane, pas seulement une URL en texte libre."""
    data = json.loads(_KEN_TARIFFS.read_text(encoding="utf-8"))
    summary = data["summary"]
    assert summary.get("dd_source_id") == "KE-KRA-EAC-CET-2022-30JUN"
    assert summary.get("dd_source_sha256")
    assert summary.get("dd_source_archive_file")


def test_ken_dd_source_pdf_matches_declared_hash():
    """Le PDF archivé doit correspondre exactement au SHA-256 déclaré dans
    KEN_tariffs.json ET dans le registre legal_sources.json — les deux
    doivent être cohérents."""
    summary = json.loads(_KEN_TARIFFS.read_text(encoding="utf-8"))["summary"]
    archive_path = _ROOT / summary["dd_source_archive_file"]
    assert archive_path.exists(), f"archive manquante : {archive_path}"
    actual_hash = _sha256(archive_path)
    assert actual_hash == summary["dd_source_sha256"]

    sources = json.loads(_KEN_LEGAL_SOURCES.read_text(encoding="utf-8"))["sources"]
    legal_source = next(s for s in sources if s["source_id"] == "KE-KRA-EAC-CET-2022-30JUN")
    assert legal_source["sha256"] == actual_hash


def test_ken_dd_source_url_matches_archived_document():
    """Le document archivé doit correspondre à l'URL exacte que
    KEN_tariffs.json déclarait déjà comme source (source_url) avant cette
    collecte — l'archive documente le texte réellement cité, pas un autre."""
    summary = json.loads(_KEN_TARIFFS.read_text(encoding="utf-8"))["summary"]
    sources = json.loads(_KEN_LEGAL_SOURCES.read_text(encoding="utf-8"))["sources"]
    legal_source = next(s for s in sources if s["source_id"] == "KE-KRA-EAC-CET-2022-30JUN")
    assert legal_source["pdf_url"] == summary["source_url"]


def test_ken_dd_line_extraction_honestly_not_claimed_complete():
    """Garde-fou de sincérité : l'archivage du document source ne doit pas
    être présenté comme une vérification ligne par ligne des 5604 taux DD.
    Le statut data_status doit rester PARTIAL tant que cette extraction
    n'est pas faite."""
    data = json.loads(_KEN_TARIFFS.read_text(encoding="utf-8"))
    assert data["summary"]["data_status"] == "PARTIAL"
    note = data["summary"]["dd_source_verification_note"]
    assert "n'a pas été re-vérifié ligne par ligne" in note


def test_ken_inventory_csv_has_the_new_dd_source_row():
    import csv

    with open(_KEN_SOURCES_DIR / "inventory.csv", encoding="utf-8", newline="") as f:
        rows = list(csv.DictReader(f))
    row = next(r for r in rows if r["id"] == "KE-KRA-EAC-CET-2022-30JUN")
    assert row["status"] == "official_downloaded"
    assert (
        row["sha256"]
        == json.loads(_KEN_TARIFFS.read_text(encoding="utf-8"))["summary"]["dd_source_sha256"]
    )
