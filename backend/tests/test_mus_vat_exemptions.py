"""Exhaustivité MUS : exonérations TVA documentées par position (tarif MRA HS2022).

Le tarif MRA Integrated Tariff Schedule HS2022 publie une colonne TVA par ligne :
3 470 lignes portent 15 %, 1 309 lignes n'en publient aucune — documentées comme
exonérations explicites par position (jamais comblées au taux standard).
"""

import hashlib
import json
import sys
from pathlib import Path

BACKEND_ROOT = Path(__file__).resolve().parents[1]
_ROOT = BACKEND_ROOT.parent

CANONICAL = BACKEND_ROOT / "data" / "MUS_tariffs.json"
SLUG_DIR = _ROOT / "data" / "mauritius"


def _canon():
    return json.loads(CANONICAL.read_text(encoding="utf-8"))


def test_sub_positions_unique_and_count():
    d = _canon()
    codes = [sp["code"] for l in d["tariff_lines"] for sp in (l.get("sub_positions") or [])]
    assert len(codes) == len(set(codes)) == 6073


def test_vat_coverage_matches_source():
    d = _canon()
    with_vat = without_vat = 0
    for l in d["tariff_lines"]:
        taxes = l.get("taxes_detail") or []
        has_vat = any(
            str(t.get("tax", "")).replace(".", "").upper().startswith("TVA")
            or str(t.get("tax", "")).upper().startswith("VAT")
            for t in taxes
        )
        if has_vat:
            with_vat += 1
        else:
            without_vat += 1
    assert with_vat == 3470
    assert without_vat == 1309


def test_vat_exemptions_documented_by_position():
    vat = json.loads((SLUG_DIR / "vat_measures.json").read_text(encoding="utf-8"))
    recs = vat["vat_exemptions"]
    assert len(recs) == 66
    covered = set()
    for r in recs:
        assert r["hs_codes_explicit"], r["record_id"]
        assert r["source_id"] == "MUS-CANONICAL-TARIFF"
        covered |= set(r["hs_codes_explicit"])
    assert len(covered) == 1508
    # les codes exemptés ne portent AUCUNE TVA dans le canonique
    d = _canon()
    by_code = {
        sp["code"]: l
        for l in d["tariff_lines"]
        for sp in (l.get("sub_positions") or [])
    }
    for code in list(covered)[:200]:
        l = by_code[code]
        assert not any(
            str(t.get("tax", "")).replace(".", "").upper().startswith("TVA")
            for t in (l.get("taxes_detail") or [])
        ), code


def test_engine_resolves_exempt_treatment():
    d = _canon()
    exempt_codes = set()
    vat = json.loads((SLUG_DIR / "vat_measures.json").read_text(encoding="utf-8"))
    for r in vat["vat_exemptions"]:
        exempt_codes |= set(r["hs_codes_explicit"])
    code = sorted(exempt_codes)[0]
    sys.path.insert(0, str(BACKEND_ROOT))
    from services.national_legal_calculation_service import SUPPORTED_JURISDICTIONS
    assert "MUS" in SUPPORTED_JURISDICTIONS
    from engine.national_customs_calculation import NationalFiscalStore
    store = NationalFiscalStore(SUPPORTED_JURISDICTIONS["MUS"].fiscal_data_dir)
    from datetime import date
    t = store.vat_treatment(date(2026, 9, 6), code)
    assert t is not None and t["treatment"] == "EXEMPT" and t["rate_pct"] == 0.0, (code, t)


def test_register_documents_verification_and_sha():
    import hashlib
    reg = json.loads((SLUG_DIR / "mus_gazette_register.json").read_text(encoding="utf-8"))
    base = reg["base_tariff_documentation"]
    canon_sha = hashlib.sha256(CANONICAL.read_bytes()).hexdigest()
    assert base["sha256"] == canon_sha
    assert reg["verification_nationale"]["status"] == "EXHAUSTIVE_VERIFIED"
    sources = " ".join(reg["sources_officielles"])
    assert "mra.mu" in sources and "tralac.org" in sources and "au.int" in sources
