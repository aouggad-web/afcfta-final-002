"""TZA — exhaustivité du tarif national authentique (source unique, pas de canonique).

Principe SH6 : 6 chiffres internationaux ; le tarif national tanzanien (EAC CET
2022) = 8 chiffres (SH6+2). Fichier national = backend/data/TZA_tariffs.json
(verbatim du crawl eac_cet_scraper v2) — npf = CET par ligne, offre ZLECAf
TZA non archivée → NOT_AVAILABLE.
"""

import hashlib
import json
from pathlib import Path

BACKEND_ROOT = Path(__file__).resolve().parents[1]
_ROOT = BACKEND_ROOT.parent

NATIONAL = BACKEND_ROOT / "data" / "crawled" / "TZA_tariffs.json"
NATIONAL_SLOT = BACKEND_ROOT / "data" / "TZA_tariffs.json"
SLUG_DIR = _ROOT / "data" / "tanzania"

SI_MILK_60 = {"04011000", "04012000", "04014000", "04015000", "04069000"}
RECOVERED_19 = {
    "24049100": 35.0, "24049200": 35.0, "24049900": 35.0,
    "29031990": 0.0, "38089119": 10.0, "38089121": 10.0, "38089129": 10.0,
    "38089132": 25.0, "38089210": 0.0, "38089290": 0.0, "38089310": 0.0,
    "38089390": 0.0, "38089410": 0.0, "38089490": 0.0, "38089910": 0.0,
    "38089990": 0.0, "39239010": 0.0, "39239020": 25.0, "41051000": 10.0,
}
COMPOUND_CODES = {
    "63090010", "63090020", "63090090",
    "72104900", "72106100", "72106900", "72107000", "72109000", "72123000",
    "72131000", "72132000", "72139110", "72139190", "72139900", "72271000",
    "72272000", "72279000", "72281000", "72282000", "72283000", "72284000",
    "72285000", "72286000", "72287000", "72288000",
}
RATE_NOT_PUBLISHED = {"53021000"}


def _national():
    return json.loads(NATIONAL.read_text(encoding="utf-8"))


def _pos_map():
    return {p["hs_code"]: p for p in _national()["positions"]}


def test_national_file_is_the_single_source():
    assert NATIONAL.read_bytes() == NATIONAL_SLOT.read_bytes()


def test_no_duplicate_positions_and_count():
    d = _national()
    codes = [p["hs_code"] for p in d["positions"]]
    assert len(codes) == len(set(codes)) == 5954


def test_every_position_has_a_cet_entry():
    d = _national()
    for p in d["positions"]:
        assert any(t.get("is_cet") for t in (p.get("taxes_detail") or [])), p["hs_code"]


def test_sensitive_items_carry_schedule2_rates():
    pos = _pos_map()
    for code in SI_MILK_60:
        cet = next(t for t in pos[code]["taxes_detail"] if t.get("is_cet"))
        assert cet["rate"] == 60.0, (code, cet["rate"])
    rice = pos["10063000"]
    cet = next(t for t in rice["taxes_detail"] if t.get("is_cet"))
    assert cet["rate"] is None and "75% or $345/MT" in cet.get("note", "")


def test_recovered_19_codes_with_verified_rates():
    pos = _pos_map()
    for code, rate in RECOVERED_19.items():
        cet = next(t for t in pos[code]["taxes_detail"] if t.get("is_cet"))
        assert cet["rate"] == rate, (code, cet["rate"])


def test_compound_duties_structured_not_fabricated():
    pos = _pos_map()
    for code in COMPOUND_CODES:
        cet = next(t for t in pos[code]["taxes_detail"] if t.get("is_cet"))
        calc = cet.get("calculation")
        assert calc and calc["type"] == "MAX_AD_VALOREM_SPECIFIC", code
        assert calc["requires_quantity"] is True
        assert cet["rate"] is None
        assert "whichever is higher" in cet.get("note", "")


def test_rate_not_published_gap_documented():
    pos = _pos_map()
    cet = next(t for t in pos["53021000"]["taxes_detail"] if t.get("is_cet"))
    assert cet["rate"] is None
    assert cet.get("data_gap") == "RATE_NOT_PUBLISHED_IN_PDF"


def test_npf_equals_cet_and_zlecaf_not_available_for_tza():
    d = _national()
    for p in d["positions"][:100]:
        cet = next(t["rate"] for t in p["taxes_detail"] if t.get("is_cet") and t["rate"] is not None)
        assert p["npf_rate"]["ad_valorem_pct"] == cet or p["npf_rate"]["ad_valorem_pct"] is None
        assert p["zlecaf_afcfta"]["status"] == "NOT_AVAILABLE"


def test_register_documents_verification_and_sha():
    import hashlib
    reg = json.loads((SLUG_DIR / "tza_gazette_register.json").read_text(encoding="utf-8"))
    base = reg["base_tariff_documentation"]
    assert base["national_positions"] == 5954
    sha = hashlib.sha256(NATIONAL_SLOT.read_bytes()).hexdigest()
    assert base["sha256"] == sha
    assert reg["verification_nationale"]["status"] == "EXHAUSTIVE_VERIFIED"
    assert reg["preference_and_origin_status"] == "PARTIAL"
    ev = reg["afcfta_application_evidence"]
    assert ev["gti_participant"] is True
    assert "DZA-DGD-CIRC-482-2024" == ev["algeria_reciprocity"]["source_id"]
