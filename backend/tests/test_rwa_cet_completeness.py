"""Exhaustivité RWA : sous-positions 8 chiffres vs PDF officiel EAC CET 2022.

Vérifications (doctrine zéro-fabrication) :
- aucune sous-position dupliquée (49 doublons Schedule 1/Schedule 2 arbités) ;
- aucune ligne sans entrée DD/CET ;
- les 4 taux ad valorem omis ont été ajoutés (valeurs vérifiées page par page) ;
- les 25 droits composés sont structurés MAX_AD_VALOREM_SPECIFIC sans montant fabriqué ;
- les 49 Sensitive Items portent le taux Schedule 2 ;
- le registre documente la vérification et le SHA-256 du fichier canonique.
"""

import hashlib
import json
import sys
from pathlib import Path

BACKEND_ROOT = Path(__file__).resolve().parents[1]
_ROOT = BACKEND_ROOT.parent

CRAWLED = _ROOT / "backend" / "data" / "crawled" / "RWA_tariffs.json"
CANONICAL = _ROOT / "backend" / "data" / "RWA_tariffs.json"
SLUG_DIR = _ROOT / "data" / "rwanda"

AD_VALOREM_FIXES = {"53021000": 0.0, "58110000": 25.0, "92099200": 10.0, "92099400": 10.0}
COMPOUND_CODES = {
    "63090010", "63090020", "63090090",
    "72104900", "72106100", "72106900", "72107000", "72109000", "72123000",
    "72131000", "72132000", "72139110", "72139190", "72139900", "72271000",
    "72272000", "72279000", "72281000", "72282000", "72283000", "72284000",
    "72285000", "72286000", "72287000", "72288000",
}
SI_MILK_60 = {"04011000", "04012000", "04014000", "04015000", "04069000"}


def _canon():
    return json.loads(CANONICAL.read_text(encoding="utf-8"))


def test_no_duplicate_sub_positions():
    d = _canon()
    codes = [sp["code"] for l in d["tariff_lines"] for sp in (l.get("sub_positions") or [])]
    assert len(codes) == len(set(codes)) == 5954


def test_every_sub_position_code_is_8_digits():
    d = _canon()
    codes = [sp["code"] for l in d["tariff_lines"] for sp in (l.get("sub_positions") or [])]
    assert all(len(c) == 8 and c.isdigit() for c in codes)


def test_no_line_without_dd_or_cet():
    d = _canon()
    for l in d["tariff_lines"]:
        assert any(
            t["tax"] in ("DD", "D.D", "CET", "DDDROIT") for t in (l.get("taxes_detail") or [])
        ), l["hs6"]


def test_ad_valorem_fixes_applied():
    d = _canon()
    sp = {sp["code"]: sp for l in d["tariff_lines"] for sp in (l.get("sub_positions") or [])}
    for code, rate in AD_VALOREM_FIXES.items():
        assert sp[code]["dd"] == rate, (code, sp[code]["dd"])


def test_compound_duties_structured_not_fabricated():
    d = _canon()
    sp = {sp["code"]: sp for l in d["tariff_lines"] for sp in (l.get("sub_positions") or [])}
    for code in COMPOUND_CODES:
        calc = sp[code].get("dd_calculation")
        assert calc, code
        assert calc["type"] == "MAX_AD_VALOREM_SPECIFIC"
        assert calc["requires_quantity"] is True
        assert sp[code]["dd"] is None, (code, "un montant numérique serait une fabrication")
        assert "whichever is higher" in sp[code]["dd_formula"]


def test_sensitive_items_carry_schedule2_rates():
    d = _canon()
    sp = {sp["code"]: sp for l in d["tariff_lines"] for sp in (l.get("sub_positions") or [])}
    for code in SI_MILK_60:
        assert sp[code]["dd"] == 60.0, (code, sp[code]["dd"])
    rice = sp["10063000"]
    assert rice["dd"] is None and rice["dd_formula"] == "75% or $345/MT whichever is higher"


def test_crawled_file_matches_canonical_exhaustiveness():
    c = json.loads(CRAWLED.read_text(encoding="utf-8"))
    codes = [p["hs_code"] for p in c["positions"]]
    assert len(codes) == len(set(codes)) == 5954
    assert all(
        any(t.get("is_cet") for t in p["taxes_detail"]) for p in c["positions"]
    )


def test_register_documents_verification_and_sha():
    reg = json.loads((SLUG_DIR / "rwa_gazette_register.json").read_text(encoding="utf-8"))
    base = reg["base_tariff_documentation"]
    assert base["national_positions"] == 5954
    assert base["verification"]["corrections"]["duplicates_removed"] == 49
    canon_sha = hashlib.sha256(CANONICAL.read_bytes()).hexdigest()
    assert base["sha256"] == canon_sha
    assert reg["verification_nationale"]["status"] == "EXHAUSTIVE_VERIFIED"


def test_calculation_method_documents_full_cascade():
    cm = json.loads((SLUG_DIR / "calculation_method.json").read_text(encoding="utf-8"))
    taxes = [step["tax"] for step in cm["cascade"]]
    assert taxes == [
        "VALEUR_EN_DOUANE", "DD_CET", "EXCISE", "IDL", "AUL", "QIF", "TVA",
        "ENV_PLASTIC", "WHT_IMPORT",
    ]
    unverified = [s for s in cm["cascade"] if s.get("source_type") == "A_VERIFIER"]
    assert all(s["status"].startswith("UNVERIFIED") for s in unverified)
    compound = next(s for s in cm["cascade"] if s["tax"] == "DD_CET")
    assert "whichever is higher" in compound["rate_structure"]["compound_rule"]


def test_missed_19_codes_recovered():
    """Les 19 codes fusionnés-absents du crawl d'origine sont présents avec leur taux vérifié."""
    d = _canon()
    sp = {sp["code"]: sp for l in d["tariff_lines"] for sp in (l.get("sub_positions") or [])}
    expected = {
        "24049100": 35.0, "24049200": 35.0, "24049900": 35.0,
        "29031990": 0.0, "38089119": 10.0, "38089121": 10.0, "38089129": 10.0,
        "38089132": 25.0, "38089210": 0.0, "38089290": 0.0, "38089310": 0.0,
        "38089390": 0.0, "38089410": 0.0, "38089490": 0.0, "38089910": 0.0,
        "38089990": 0.0, "39239010": 0.0, "39239020": 25.0, "41051000": 10.0,
    }
    for code, rate in expected.items():
        assert code in sp, code
        assert sp[code]["dd"] == rate, (code, sp[code]["dd"])
    assert d["exhaustiveness_verification"]["missed_codes_recovered"] == 19


def test_register_sources_include_tralac_and_au():
    reg = json.loads((SLUG_DIR / "rwa_gazette_register.json").read_text(encoding="utf-8"))
    sources = " ".join(reg.get("sources_officielles", []))
    assert "tralac.org" in sources
    assert "au.int" in sources
    assert "claimed_total_7341_lines" in reg["base_tariff_documentation"]["verification"]
