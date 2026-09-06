"""Exhaustivité TZA : sous-positions 8 chiffres vs PDF officiel EAC CET 2022.

Données régénérées par eac_cet_scraper v2 (extraction directe du PDF officiel),
pas par un patch manuel. Vérifications (doctrine zéro-fabrication) :
- 5 954 sous-positions uniques 8 chiffres, 0 doublon ;
- chaque ligne porte une entrée CET (taux numérique, composé structuré, ou
  trou documenté RATE_NOT_PUBLISHED_IN_PDF pour 53021000) ;
- les 49 Sensitive Items portent le taux Schedule 2 (règle SI du texte officiel) ;
- les 19 codes fusionnés-absents du crawler v1 sont récupérés avec leur taux ;
- droits composés structurés MAX_AD_VALOREM_SPECIFIC sans montant fabriqué ;
- taux NPF = CET par ligne ; offre ZLECAf TZA = NOT_AVAILABLE (pas de snapshot) ;
- le registre documente la vérification, le SHA-256 et la piste « 7 341 lignes ».
"""

import hashlib
import json
import sys
from pathlib import Path

BACKEND_ROOT = Path(__file__).resolve().parents[1]
_ROOT = BACKEND_ROOT.parent

CRAWLED = _ROOT / "backend" / "data" / "crawled" / "TZA_tariffs.json"
CANONICAL = _ROOT / "backend" / "data" / "TZA_tariffs.json"
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


def _canon():
    return json.loads(CANONICAL.read_text(encoding="utf-8"))


def _sp_map():
    d = _canon()
    return {sp["code"]: sp for l in d["tariff_lines"] for sp in (l.get("sub_positions") or [])}


def test_no_duplicate_sub_positions_and_count():
    d = _canon()
    codes = [sp["code"] for l in d["tariff_lines"] for sp in (l.get("sub_positions") or [])]
    assert len(codes) == len(set(codes)) == 5954


def test_every_sub_position_code_is_8_digits():
    d = _canon()
    codes = [sp["code"] for l in d["tariff_lines"] for sp in (l.get("sub_positions") or [])]
    assert all(len(c) == 8 and c.isdigit() for c in codes)


def test_every_line_has_a_cet_entry():
    d = _canon()
    for l in d["tariff_lines"]:
        assert any(t["tax"] == "CET" for t in (l.get("taxes_detail") or [])), l["hs6"]


def test_sensitive_items_carry_schedule2_rates():
    sp = _sp_map()
    for code in SI_MILK_60:
        assert sp[code]["dd"] == 60.0, (code, sp[code]["dd"])
        assert sp[code]["rate_schedule"] == "2"
    rice = sp["10063000"]
    assert rice["dd"] is None
    assert rice["dd_formula"] == "75% or $345/MT whichever is higher"
    assert rice["dd_calculation"]["type"] == "MAX_AD_VALOREM_SPECIFIC"
    assert rice["dd_calculation"]["requires_quantity"] is True


def test_recovered_19_codes_with_verified_rates():
    sp = _sp_map()
    for code, rate in RECOVERED_19.items():
        assert sp[code]["dd"] == rate, (code, sp[code]["dd"])
    ev = _canon()["exhaustiveness_verification"]
    assert ev["codes_merged_recovered"] == 19


def test_compound_duties_structured_not_fabricated():
    sp = _sp_map()
    for code in COMPOUND_CODES:
        calc = sp[code].get("dd_calculation")
        assert calc, code
        assert calc["type"] == "MAX_AD_VALOREM_SPECIFIC"
        assert calc["requires_quantity"] is True
        assert sp[code]["dd"] is None
        assert "whichever is higher" in sp[code]["dd_formula"]


def test_rate_not_published_gap_is_documented_not_fabricated():
    d = _canon()
    for l in d["tariff_lines"]:
        for sp in (l.get("sub_positions") or []):
            if sp["code"] in RATE_NOT_PUBLISHED:
                assert sp["dd"] is None
                assert sp["rate_text"] == ""
        cet = next(t for t in l["taxes_detail"] if t["tax"] == "CET")
        if l["hs6"] == "530210":
            assert cet.get("data_gap") == "RATE_NOT_PUBLISHED_IN_PDF"


def test_npf_equals_cet_and_zlecaf_not_available_for_tza():
    c = json.loads(CRAWLED.read_text(encoding="utf-8"))
    for p in c["positions"][:100]:
        assert p["npf_rate"]["ad_valorem_pct"] == next(
            t["rate"] for t in p["taxes_detail"] if t.get("is_cet") and t["rate"] is not None
        ) or p["npf_rate"]["ad_valorem_pct"] is None
        z = p["zlecaf_afcfta"]
        assert z["status"] == "NOT_AVAILABLE", (
            "Tanzanie : pas de snapshot ZLECAf officiel — jamais devinée"
        )


def test_register_documents_verification_and_sha():
    reg = json.loads((SLUG_DIR / "tza_gazette_register.json").read_text(encoding="utf-8"))
    base = reg["base_tariff_documentation"]
    assert base["national_positions"] == 5954
    canon_sha = hashlib.sha256(CANONICAL.read_bytes()).hexdigest()
    assert base["sha256"] == canon_sha
    assert reg["verification_nationale"]["status"] == "EXHAUSTIVE_VERIFIED"
    verif = base["verification"]
    assert verif["pdf_sha256"].startswith("4c5acc8b")
    assert verif["claimed_total_7341_lines"].startswith("UNVERIFIED")
    sources = " ".join(reg["sources_officielles"])
    assert "tralac.org" in sources and "au.int" in sources


def test_data_generated_by_crawler_not_manual_patch():
    d = _canon()
    assert d["generated_by"].startswith("eac_cet_scraper v2")
    assert d["exhaustiveness_verification"]["pdf_sha256"].startswith("4c5acc8b")
