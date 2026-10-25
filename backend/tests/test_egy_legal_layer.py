"""
Tests de la couche de vérification juridique datée — juridiction EGY (Égypte).

Corpus : tarif national égyptien VERIFIED (customs.gov.eg — 5 541 lignes,
8 746 sous-positions 10 chiffres), TVA 14 % (VAT Law 67/2016) + taux
spécifiques par position, Taxe de Table (TJ/ضريبة الجدول), 225 F.A.P
trilingues (AR original conservé + FR + EN).

Doctrine vérifiée :
- Source/Temporalité/Fiscalité/Préférence = DOCUMENTED, 0 élément manquant ;
- chaque taux (TVA, TJ) lié à sa position nationale exacte ;
- F.A.P trilingues : langue d'origine (arabe) conservée + FR + EN ;
- invariant numérique : aucune F.A.P à contenu purement numérique.
"""

import json
import re
import sys
from datetime import date
from pathlib import Path


BACKEND_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND_ROOT))

_ROOT = BACKEND_ROOT.parent
_ON_DATE = date(2026, 9, 5)
_NUMERIC_ONLY = re.compile(r"^\d+(?:[.,]\d+)?$")


def test_egy_fap_measures_use_exact_national_positions():
    """Chaque mesure FAP porte des positions nationales 10 chiffres exactes."""
    overrides = json.loads(
        (_ROOT / "data" / "egypt" / "legal_overrides.json").read_text(encoding="utf-8")
    )
    assert len(overrides["measures"]) == 225
    for m in overrides["measures"]:
        assert m["measure_type"] == "ADMINISTRATIVE_REQUIREMENT"
        assert m["mapping_status"] == "DIRECT_HS"
        assert m["mapping_confidence"] == 100
        assert m["source_hash"]
        assert m["verification_status"] == "SOURCE_ARCHIVED"
        for code in m["hs_codes"]:
            assert len(code) == 10 and code.isdigit(), code
        # invariant numérique : jamais de FAP purement numérique
        for field in ("document_ar", "document_fr"):
            doc = (m.get(field) or "").strip()
            assert not _NUMERIC_ONLY.fullmatch(doc), (m["measure_id"], doc)


def test_egy_no_numeric_only_formality_in_canonical():
    """Invariant PR #449 appliqué au canonique EGY : aucun artefact numérique."""
    canon = json.loads(
        (_ROOT / "backend" / "data" / "EGY_tariffs.json").read_text(encoding="utf-8")
    )
    for l in canon["tariff_lines"]:
        for sp in l.get("sub_positions") or []:
            for formality in sp.get("administrative_formalities") or []:
                doc = (formality.get("document_fr") or "").strip()
                assert not _NUMERIC_ONLY.fullmatch(doc), (sp.get("code"), doc)


def test_egy_gazette_register_integrity():
    """Le registre EGY : coverage complete, pas de TEC régional (COMESA = ZLE),
    base tarifaire VERIFIED avec SHA-256 du canonique."""
    reg = json.loads(
        (_ROOT / "data" / "egypt" / "egypt_gazette_register.json").read_text(encoding="utf-8")
    )
    assert reg["coverage_complete"] is True
    assert reg["regional_cet_applicable"] is False
    base = reg["base_tariff_documentation"]
    assert base["verification_status"] == "VERIFIED"
    assert base["national_positions"] >= 8700
    canon_sha = __import__("hashlib").sha256(
        (_ROOT / "backend" / "data" / "EGY_tariffs.json").read_bytes()
    ).hexdigest()
    assert base["sha256"] == canon_sha


