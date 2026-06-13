"""
Tests de l'adaptateur générique JSON tarifaires (RWA/LBR/CMR…).

Politique de données :
  - fichier avec source_document + date passée  → PARTIAL/B (mode strict OK)
  - fichier sans source_document ou daté d'aujourd'hui → SYNTHETIC/D (permissif)
                                                         ou SourceNotVerifiedException (strict)
"""

import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

from adapters.json_tariffs_adapter import (
    _dedup_taxes, _is_fictitious, _build_measures, process_file, run,
    SourceNotVerifiedException,
)
from schemas.canonical_model import DataStatus, ReliabilityGrade, DutyBasis, MeasureType


# ----------------------------------------------------------------------
# Helpers / fixtures inline
# ----------------------------------------------------------------------

def _make_file(tmp_path, country: str, lines: list, *,
               source_document: str = "",
               generated_at: str = "2026-06-12T14:00:00+00:00") -> str:
    """Crée un fichier JSON tarifaire de test.

    Par défaut : pas de source_document + date = aujourd'hui
    → non vérifiable (SYNTHETIC/D ou rejet strict).
    Utiliser source_document + generated_at passé pour obtenir PARTIAL/B.
    """
    data = {
        "country_code": country,
        "country_name": country,
        "generated_at": generated_at,
        "data_format": "test",
        "data_source": "test_source",
        "source_url": "https://example.com",
        "notes": [],
        "summary": {},
        "tariff_lines": lines,
    }
    if source_document:
        data["source_document"] = source_document
    p = tmp_path / f"{country}_tariffs.json"
    p.write_text(json.dumps(data), encoding="utf-8")
    return str(p)


def _make_verified_file(tmp_path, country: str, lines: list) -> str:
    """Fichier avec source officielle vérifiable (date passée + source_document)."""
    return _make_file(
        tmp_path, country, lines,
        source_document="Direction Générale des Douanes — Tarif officiel 2022",
        generated_at="2024-01-15T10:00:00+00:00",
    )


SIMPLE_LINE = {
    "hs6": "010110",
    "chapter": "01",
    "description_fr": "Chevaux reproducteurs",
    "description_en": "Pure-bred horses",
    "category": "livestock",
    "unit": "KG",
    "sensitivity": "normal",
    "dd_rate": 25.0,
    "zlecaf_rate": 2.5,
    "vat_rate": 18.0,
    "other_taxes_rate": 0,
    "taxes_detail": [
        {"tax": "D.D", "rate": 25.0, "base": "CIF", "methode": "CIF × 25%",
         "observation": "EAC CET 25%"},
        {"tax": "T.V.A", "rate": 18.0, "base": "CIF + DD",
         "methode": "(CIF+DD) × 18%", "observation": "VAT"},
    ],
    "fiscal_advantages": [
        {"tax": "D.D", "rate": 0.0, "condition_fr": "Exo ZLECAf",
         "condition_en": "AfCFTA"},
    ],
    "administrative_formalities": [],
    "total_import_taxes": 29.5,
    "sub_positions": [],
    "has_sub_positions": False,
    "sub_position_count": 0,
    "data_quality": "authentic",
}

FICTITIOUS_LINE = {
    "hs6": "000001",
    "chapter": "00",
    "description_fr": "Position fictive",
    "taxes_detail": [],
    "fiscal_advantages": [],
    "data_quality": "authentic",
}

LBR_LINE = {
    **SIMPLE_LINE,
    "hs6": "252329",
    "chapter": "25",
    "taxes_detail": [
        {"tax": "D.D",  "rate": 20.0, "base": "CIF",    "observation": "TEC CEDEAO 20%"},
        {"tax": "GST",  "rate": 10.0, "base": "CIF+DD", "observation": "Goods and Services Tax"},
        {"tax": "T.V.A","rate": 10.0, "base": "CIF + DD","observation": "Goods and Services Tax (GST)"},
    ],
}

CMR_LINE = {
    **SIMPLE_LINE,
    "hs6": "100630",
    "chapter": "10",
    "taxes_detail": [
        {"tax": "D.D",   "rate": 10.0, "base": "CIF",           "observation": "TEC CEMAC 10%"},
        {"tax": "TCI",   "rate": 1.0,  "base": "CIF",           "observation": "Taxe Communautaire d'Intégration"},
        {"tax": "TS",    "rate": 1.0,  "base": "CIF",           "observation": "Taxe de Solidarité"},
        {"tax": "T.V.A", "rate": 19.25,"base": "CIF + DD + TCI","observation": "TVA CMR 17.5% + CAC"},
    ],
}


# ----------------------------------------------------------------------
# Tests unitaires (sans I/O — aucune validation de source requise)
# ----------------------------------------------------------------------

def test_fictitious_line_detected():
    assert _is_fictitious(FICTITIOUS_LINE)
    assert not _is_fictitious(SIMPLE_LINE)


def test_dedup_gst_tva():
    taxes = [
        {"tax": "D.D",   "rate": 20.0},
        {"tax": "GST",   "rate": 10.0},
        {"tax": "T.V.A", "rate": 10.0},   # doublon de GST
    ]
    deduped = _dedup_taxes(taxes)
    codes = [t["tax"] for t in deduped]
    assert codes == ["D.D", "GST"]         # T.V.A supprimé
    assert "T.V.A" not in codes


def test_measures_dd_is_customs_duty():
    measures = _build_measures("RWA", "010110", SIMPLE_LINE["taxes_detail"])
    dd = next(m for m in measures if m.code == "D.D")
    assert dd.measure_type == MeasureType.CUSTOMS_DUTY
    assert dd.basis == DutyBasis.CIF
    assert dd.is_zlecaf_applicable is True


def test_vat_basis_includes_upstream():
    measures = _build_measures("RWA", "010110", SIMPLE_LINE["taxes_detail"])
    vat = next(m for m in measures if m.measure_type == MeasureType.VAT)
    assert vat.basis == DutyBasis.CIF_PLUS_INCLUDED
    assert "D.D" in vat.basis_includes
    assert vat.code not in vat.basis_includes


def test_total_npf_includes_vat(tmp_path):
    """total_npf_pct doit inclure la TVA (CIF_PLUS_INCLUDED), pas seulement CIF."""
    f = _make_verified_file(tmp_path, "RWA", [SIMPLE_LINE])
    process_file(f, str(tmp_path))
    record = json.loads(
        (tmp_path / "RWA_canonical.jsonl").read_text().splitlines()[0])
    # D.D 25% (CIF) + T.V.A 18% (CIF_PLUS_INCLUDED) = 43.0
    assert record["total_npf_pct"] == pytest.approx(43.0)


def test_cmr_vat_includes_tci_ts():
    measures = _build_measures("CMR", "100630", CMR_LINE["taxes_detail"])
    vat = next(m for m in measures if m.measure_type == MeasureType.VAT)
    assert "TCI" in vat.basis_includes
    assert "TS" in vat.basis_includes


def test_lbr_dedup_in_measures():
    measures = _build_measures("LBR", "252329", LBR_LINE["taxes_detail"])
    codes = [m.code for m in measures]
    # GST et T.V.A sont le même impôt → seul GST conservé
    assert "T.V.A" not in codes
    assert "GST" in codes
    assert len(measures) == 2    # D.D + GST


# ----------------------------------------------------------------------
# Validation de source — mode strict
# ----------------------------------------------------------------------

def test_strict_rejects_file_without_source_document(tmp_path):
    """Mode strict (défaut) : fichier sans source_document → exception."""
    f = _make_file(tmp_path, "TST", [SIMPLE_LINE])
    with pytest.raises(SourceNotVerifiedException, match="source_document"):
        process_file(f, str(tmp_path), strict=True)


def test_strict_rejects_file_generated_today(tmp_path):
    """Mode strict : même avec source_document, si généré aujourd'hui → exception."""
    import datetime
    today = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT12:00:00+00:00")
    f = _make_file(tmp_path, "TST", [SIMPLE_LINE],
                   source_document="Doc officiel — version 2022",
                   generated_at=today)
    with pytest.raises(SourceNotVerifiedException, match="généré automatiquement"):
        process_file(f, str(tmp_path), strict=True)


def test_rejects_invalid_country_code(tmp_path):
    """country_code non-ISO3 (ex. traversée de chemin) → ValueError."""
    f = _make_file(tmp_path, "TST", [SIMPLE_LINE])
    data = json.loads(Path(f).read_text())
    data["country_code"] = "../../EVIL"
    Path(f).write_text(json.dumps(data), encoding="utf-8")
    with pytest.raises(ValueError, match="country_code invalide"):
        process_file(f, str(tmp_path), strict=False)


def test_permissive_accepts_unverified_as_synthetic(tmp_path):
    """Mode permissif : fichier non-vérifiable → SYNTHETIC/D accepté."""
    f = _make_file(tmp_path, "TST", [SIMPLE_LINE])
    result = process_file(f, str(tmp_path), strict=False)
    record = json.loads(
        (tmp_path / "TST_canonical.jsonl").read_text().splitlines()[0])
    assert result["data_status"] == "SYNTHETIC"
    assert record["provenance"]["data_status"] == "SYNTHETIC"
    assert record["provenance"]["reliability"] == "D"


# ----------------------------------------------------------------------
# Traitement complet avec fichier vérifié (PARTIAL/B)
# ----------------------------------------------------------------------

def test_provenance_partial_b(tmp_path):
    """Fichier avec source officielle + date passée → PARTIAL/B."""
    f = _make_verified_file(tmp_path, "RWA", [SIMPLE_LINE])
    result = process_file(f, str(tmp_path))
    record = json.loads(
        (tmp_path / "RWA_canonical.jsonl").read_text().splitlines()[0])
    assert record["provenance"]["data_status"] == "PARTIAL"
    assert record["provenance"]["reliability"] == "B"
    assert record["schema_version"] == "4.0"


def test_fictitious_line_filtered(tmp_path):
    f = _make_file(tmp_path, "TST", [FICTITIOUS_LINE, SIMPLE_LINE])
    result = process_file(f, str(tmp_path), strict=False)
    assert result["lines_written"] == 1
    assert result["lines_skipped"] == 1


def test_fiscal_advantages_written(tmp_path):
    f = _make_verified_file(tmp_path, "RWA", [SIMPLE_LINE])
    process_file(f, str(tmp_path))
    record = json.loads(
        (tmp_path / "RWA_canonical.jsonl").read_text().splitlines()[0])
    assert len(record["fiscal_advantages"]) == 1
    assert record["fiscal_advantages"][0]["agreement"] == "ZLECAf"


def test_run_multi_country(tmp_path):
    f1 = _make_verified_file(tmp_path, "RWA", [SIMPLE_LINE])
    f2 = _make_verified_file(tmp_path, "CMR", [CMR_LINE])
    result = run([f1, f2], str(tmp_path))
    assert set(result["countries"].keys()) == {"RWA", "CMR"}
    assert result["countries"]["RWA"]["lines_written"] == 1
    assert result["countries"]["CMR"]["lines_written"] == 1
    assert (tmp_path / "CMR_canonical.jsonl").exists()


def test_run_permissive_multi_country(tmp_path):
    """run() en mode permissif traite les fichiers non-vérifiés en SYNTHETIC/D."""
    f1 = _make_file(tmp_path, "RWA", [SIMPLE_LINE])
    f2 = _make_file(tmp_path, "CMR", [CMR_LINE])
    result = run([f1, f2], str(tmp_path), strict=False)
    assert result["countries"]["RWA"]["data_status"] == "SYNTHETIC"
    assert result["countries"]["CMR"]["data_status"] == "SYNTHETIC"
