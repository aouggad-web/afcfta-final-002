"""TUN-mode-like validation : RWA — exhaustivité du tarif national authentique.

Principe SH6 : les 6 premiers chiffres sont internationaux ; le tarif national
rwandais (EAC CET 2022) se développe au-delà — 8 chiffres (SH6+2). Le fichier
national (backend/data/RWA_tariffs.json = backend/data/crawled/RWA_tariffs.json,
extrait du PDF officiel kra.go.ke par eac_cet_scraper) est la source unique —
pas de canonique dérivé.
"""

import hashlib
import json
from pathlib import Path

BACKEND_ROOT = Path(__file__).resolve().parents[1]
_ROOT = BACKEND_ROOT.parent

NATIONAL = BACKEND_ROOT / "data" / "crawled" / "RWA_tariffs.json"
NATIONAL_SLOT = BACKEND_ROOT / "data" / "RWA_tariffs.json"
SLUG_DIR = _ROOT / "data" / "rwanda"

AD_VALOREM_FIXES = {"58110000": 25.0, "92099200": 10.0, "92099400": 10.0}
RATE_NOT_PUBLISHED = {"53021000"}
SI_MILK_60 = {"04011000", "04012000", "04014000", "04015000", "04069000"}
COMPOUND_CODES = {
    "63090010", "63090020", "63090090",
    "72104900", "72106100", "72106900", "72107000", "72109000", "72123000",
    "72131000", "72132000", "72139110", "72139190", "72139900", "72271000",
    "72272000", "72279000", "72281000", "72282000", "72283000", "72284000",
    "72285000", "72286000", "72287000", "72288000",
}
COMPOUND_RICE = {"10061000", "10062000", "10063000", "10064000", "11029010"}


def _national():
    return json.loads(NATIONAL.read_text(encoding="utf-8"))


def _pos_map():
    return {p["hs_code"]: p for p in _national()["positions"]}


def test_national_file_is_the_single_source():
    """Pas de canonique dérivé : backend/data/RWA_tariffs.json = tarif national verbatim."""
    assert NATIONAL.read_bytes() == NATIONAL_SLOT.read_bytes()


def test_no_duplicate_positions_and_count():
    d = _national()
    codes = [p["hs_code"] for p in d["positions"]]
    assert len(codes) == len(set(codes)) == 5954


def test_every_position_has_a_cet_entry():
    d = _national()
    for p in d["positions"]:
        assert any(t.get("is_cet") for t in (p.get("taxes_detail") or [])), p["hs_code"]


def test_ad_valorem_fixes_applied():
    pos = _pos_map()
    for code, rate in AD_VALOREM_FIXES.items():
        cet = next(t for t in pos[code]["taxes_detail"] if t.get("is_cet"))
        assert cet["rate"] == rate, (code, cet["rate"])


def test_rate_not_published_gap_documented():
    """53021000 : colonne taux VIDE dans le PDF officiel — trou documenté,
    jamais comblé."""
    pos = _pos_map()
    cet = next(t for t in pos["53021000"]["taxes_detail"] if t.get("is_cet"))
    assert cet["rate"] is None
    assert cet.get("data_gap") == "RATE_NOT_PUBLISHED_IN_PDF"


def test_sensitive_items_carry_schedule2_rates():
    pos = _pos_map()
    for code in SI_MILK_60:
        cet = next(t for t in pos[code]["taxes_detail"] if t.get("is_cet"))
        assert cet["rate"] == 60.0, (code, cet["rate"])
    rice = pos["10063000"]
    cet = next(t for t in rice["taxes_detail"] if t.get("is_cet"))
    assert cet["rate"] is None and "75% or $345/MT" in cet.get("note", "")


def test_compound_duties_structured_not_fabricated():
    pos = _pos_map()
    for code in COMPOUND_CODES | COMPOUND_RICE:
        cet = next(t for t in pos[code]["taxes_detail"] if t.get("is_cet"))
        calc = cet.get("calculation")
        assert calc and calc["type"] == "MAX_AD_VALOREM_SPECIFIC", code
        assert calc["requires_quantity"] is True
        assert cet["rate"] is None


def test_register_documents_verification_and_sha():
    reg = json.loads((SLUG_DIR / "rwa_gazette_register.json").read_text(encoding="utf-8"))
    base = reg["base_tariff_documentation"]
    assert base["national_positions"] == 5954
    sha = hashlib.sha256(NATIONAL_SLOT.read_bytes()).hexdigest()
    assert base["sha256"] == sha
    assert reg["verification_nationale"]["status"] == "EXHAUSTIVE_VERIFIED"
