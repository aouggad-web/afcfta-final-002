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

import pytest

BACKEND_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND_ROOT))

from services.national_legal_calculation_service import (  # noqa: E402
    SUPPORTED_JURISDICTIONS,
    calculate_national_legal_layer,
)

_ROOT = BACKEND_ROOT.parent
_ON_DATE = date(2026, 9, 5)
_NUMERIC_ONLY = re.compile(r"^\d+(?:[.,]\d+)?$")


def _calc(hs_code: str, value: float = 10000.0, base_rate: float = 15.0):
    return calculate_national_legal_layer(
        jurisdiction="EGY",
        hs_code=hs_code,
        on_date=_ON_DATE,
        customs_value=value,
        base_cet_rate=base_rate,
    )


def test_egy_is_a_supported_jurisdiction():
    assert "EGY" in SUPPORTED_JURISDICTIONS
    cfg = SUPPORTED_JURISDICTIONS["EGY"]
    assert cfg.default_currency == "EGP"
    assert cfg.fiscal_data_dir.name == "egypt"


def test_egy_quality_dimensions_all_documented():
    """Plus aucun « Non vérifié » / « Partiel » injustifié sur le calcul EGY."""
    r = _calc("0101210000")
    q = r["quality_dimensions"]
    assert q["source"] == "DOCUMENTED"
    assert q["temporal_validity"] == "DOCUMENTED"
    assert q["classification"] == "DOCUMENTED"
    assert q["taxes_and_levies"] == "DOCUMENTED"
    assert q["preference_and_origin"] == "DOCUMENTED"
    assert r["overall_status"] == "INFORMATIVE_COMPLETE"


def test_egy_no_missing_coverage_messages():
    """Les messages « gazette / national-measure coverage » ne doivent pas apparaître."""
    r = _calc("0101210000")
    gaps = " ".join(r.get("known_data_gaps", []) + r.get("missing_elements", []))
    assert "gazette coverage" not in gaps
    assert "national-measure coverage" not in gaps


def test_egy_vat_by_national_position():
    """TVA par position : 0 % (viande 010121 exonérée), 14 % standard (020680)."""
    r_exempt = _calc("0101210000")
    assert (r_exempt.get("vat") or {}).get("rate") == 0.0
    r_std = _calc("0206800000")
    assert (r_std.get("vat") or {}).get("rate") == 14.0
    assert r_std["currency_code"] == "EGP"


def test_egy_schedule_table_tax_applied_by_position():
    """Taxe de Table (TJ/ضريبة الجدول) 8 % sur 2202910000 (lait)."""
    r = _calc("2202910000")
    levies = r.get("other_levies") or {}
    tj = levies.get("schedule_table_tax") or {}
    assert tj.get("rate") == 8.0
    assert "جدول" in tj.get("legal_reference", "") or "Table" in tj.get("legal_reference", "")


def test_egy_fap_attached_by_national_position():
    """F.A.P attachées à 0101210000 (حجر بيطري — quarantaine vétérinaire)."""
    r = _calc("0101210000")
    assert r["quality_dimensions"]["formalities"] == "DOCUMENTED"
    reqs = r.get("administrative_requirements") or []
    assert reqs, "au moins une FAP attendue (quarantaine vétérinaire)"
    for req in reqs:
        assert req.get("measure_id", "").startswith("EGY-FAP-")
        assert req.get("legal_reference")


def test_egy_fap_trilingual_arabic_kept():
    """Chaque FAP conserve l'arabe original + traductions FR et EN."""
    r = _calc("0101210000")
    reqs = r.get("administrative_requirements") or []
    assert reqs
    desc = reqs[0].get("product_description", "")
    assert "[AR]" in desc and "[FR]" in desc and "[EN]" in desc
    # l'arabe original (langue d'origine) est présent
    assert re.search(r"[\u0600-\u06FF]", desc)
    # la traduction FR diffère de l'arabe
    ar_part = desc.split("[FR]")[0]
    fr_part = desc.split("[FR]")[1].split("[EN]")[0] if "[FR]" in desc else ""
    assert fr_part.strip() and not re.search(r"[\u0600-\u06FF]", fr_part)


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


def test_dza_and_kenya_unaffected_by_egy_wiring():
    """Non-régression : DZA et KEN gardent leurs configurations."""
    assert SUPPORTED_JURISDICTIONS["DZA"].default_currency == "DZD"
    assert SUPPORTED_JURISDICTIONS["KEN"].default_currency == "USD"
    assert (
        SUPPORTED_JURISDICTIONS["EGY"].legal_overrides_path
        != SUPPORTED_JURISDICTIONS["DZA"].legal_overrides_path
    )
