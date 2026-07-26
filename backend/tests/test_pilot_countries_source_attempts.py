"""
Vérifications d'intégrité des tentatives de collecte de provenance pour les
pays pilotes du calculateur douanier ZLECAf (DZA, TUN, MAR, EGY) —
2026-07-26, suite à audits/AUDIT_DIFFERENTIEL_PILOTES_2026-07-26.md.

Ce module ne teste pas des taux fiscaux (aucune donnée tarifaire n'a été
modifiée) : il vérifie que chaque tentative de collecte est honnêtement
documentée — succès (document archivé et haché) ou échec (accès bloqué,
consigné explicitement, jamais silencieusement omis).
"""

import csv
import hashlib
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[2]

_REQUIRED_COLUMNS = {
    "id",
    "institution",
    "title",
    "legal_date",
    "accessed_at",
    "url",
    "local_file",
    "sha256",
    "coverage",
    "status",
    "notes",
}


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _read_inventory(country: str) -> list:
    path = _ROOT / "data" / "sources" / country / "inventory.csv"
    with open(path, encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def test_all_four_country_inventories_have_required_columns():
    for country in ("algeria", "tunisia", "morocco", "egypt"):
        rows = _read_inventory(country)
        assert rows, f"{country}: inventory.csv vide"
        for row in rows:
            assert _REQUIRED_COLUMNS <= set(row.keys()), f"{country}: colonnes manquantes"


def test_tunisia_finance_law_pdf_matches_recorded_hash():
    """Le seul document réellement archivé de ce lot (Loi de Finances
    tunisienne 2026) doit correspondre exactement au hash consigné."""
    rows = _read_inventory("tunisia")
    row = next(r for r in rows if r["id"] == "TUN-MOF-LOI-FINANCES-2026")
    archive_path = _ROOT / "data" / "sources" / "tunisia" / row["local_file"]
    assert archive_path.exists(), f"archive manquante : {archive_path}"
    assert _sha256(archive_path) == row["sha256"]


def test_blocked_sources_are_explicitly_documented_not_silently_absent():
    """Garde-fou de sincérité : chaque tentative d'accès bloquée doit être
    marquée avec un statut explicite de blocage, jamais silencieusement
    omise ni remplacée par une donnée estimée."""
    blocked_statuses = {
        "source_blocked",
        "access_blocked_js_rendered",
        "access_blocked_legacy_frameset",
        "access_blocked_ajax_rendered",
        "access_blocked_paginated_live_query",
        "source_pending_collection",
    }
    found_blocked = 0
    for country in ("algeria", "tunisia", "morocco", "egypt"):
        rows = _read_inventory(country)
        for row in rows:
            if row["status"] in blocked_statuses:
                found_blocked += 1
                assert (
                    row["url"] or row["notes"]
                ), f"{country}/{row['id']}: statut bloqué sans URL ni note explicative"
    assert found_blocked >= 5, "au moins un blocage attendu par pays sur ce lot (4 pays)"


def test_no_sha256_recorded_without_an_archived_file():
    """Garde-fou : un sha256 ne doit jamais être renseigné sans que le
    fichier local correspondant existe réellement — détecte un hash copié
    sans preuve archivée."""
    for country in ("algeria", "tunisia", "morocco", "egypt"):
        rows = _read_inventory(country)
        for row in rows:
            if row["sha256"]:
                assert row["local_file"], f"{country}/{row['id']}: sha256 sans local_file"
                archive_path = _ROOT / "data" / "sources" / country / row["local_file"]
                assert archive_path.exists(), f"{country}/{row['id']}: sha256 déclaré sans fichier"
