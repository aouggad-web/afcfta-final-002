"""Exhaustivité TUN : sous-positions nationales 11 caractères vs Tarif Web 2026.

Données : re-crawl complet 2026-08-30 (17 542 codes = énumération officielle
du 2026-08-29, 0 manquant, 0 superflu, tous avec taux publiés) + canonique
reconstruit (build_tun_canonical.py). Doctrine zéro-fabrication :
- 17 625 sous-positions uniques (17 542 re-crawlées + 83 conservées flaggées) ;
- les 16 divergences DD juin→re-crawl sont documentées une à une ;
- les formalités riches (2 018 lignes) sont préservées ;
- l'offre ZLECAf (9 chiffres, OFFER_ONLY, 2 périodes) est attachée par ligne ;
- le registre documente la vérification et le SHA-256 du canonique.
"""

import hashlib
import json
from pathlib import Path

import pytest

BACKEND_ROOT = Path(__file__).resolve().parents[1]
_ROOT = BACKEND_ROOT.parent

CRAWLED = BACKEND_ROOT / "data" / "crawled" / "TUN_tariffs.json"
CANONICAL = BACKEND_ROOT / "data" / "TUN_tariffs.json"
ENUM = BACKEND_ROOT / "data" / "crawled" / "TUN_enumeration_2026-08.json"
SLUG_DIR = _ROOT / "data" / "tunisia"


def _canon():
    return json.loads(CANONICAL.read_text(encoding="utf-8"))


def _sp_map():
    d = _canon()
    return {sp["code"]: sp for l in d["tariff_lines"] for sp in (l.get("sub_positions") or [])}


def test_crawl_exhaustive_vs_official_enumeration():
    nat = json.loads(CRAWLED.read_text(encoding="utf-8"))
    enum = json.loads(ENUM.read_text(encoding="utf-8"))
    nat_codes = {l["hs_code"] for l in nat["sub_positions"]}
    enum_codes = set()
    for _ch, codes in enum["chapters"].items():
        enum_codes |= set(codes.keys()) if isinstance(codes, dict) else set(codes)
    assert nat_codes == enum_codes, (
        f"manquants: {len(enum_codes - nat_codes)}, superflus: {len(nat_codes - enum_codes)}"
    )
    with_rates = sum(1 for l in nat["sub_positions"] if l.get("taxes_import"))
    assert with_rates == len(nat_codes)


def test_no_duplicate_sub_positions_and_count():
    d = _canon()
    codes = [sp["code"] for l in d["tariff_lines"] for sp in (l.get("sub_positions") or [])]
    assert len(codes) == len(set(codes)) == 17625


def test_every_line_has_a_dd_or_documented_gap():
    d = _canon()
    for l in d["tariff_lines"]:
        taxes = l.get("taxes_detail") or []
        has_dd = any(
            (t["tax"] in ("DD", "D.D", "CET", "DDDROIT") or t["tax"].startswith("DD"))
            and t.get("rate") is not None
            for t in taxes
        )
        assert has_dd or l["hs6"] == "360300", (
            f"{l['hs6']}: ni DD ni groupe legacy documenté"
        )


def test_dd_divergences_documented_not_silently_merged():
    d = _canon()
    divs = d["dd_divergences_juin_vs_recrawl"]
    assert len(divs) == 16
    for div in divs:
        assert div["resolution"] == "taux du re-crawl officiel retenu"
    sp = _sp_map()
    assert sp["73090090109"]["dd"] == 30.0
    assert sp["90031100003"]["dd"] == 10.0


def test_legacy_codes_kept_and_flagged():
    sp = _sp_map()
    legacy = [c for c, s in sp.items() if s.get("consolidation_flag")]
    assert len(legacy) == 83
    assert all("CODE_ABSENT_ENUMERATION_2026-08-30" in s.get("consolidation_flag", "")
               for s in sp.values() if s.get("consolidation_flag"))


def test_formalities_preserved():
    d = _canon()
    n = sum(1 for l in d["tariff_lines"] if l.get("administrative_formalities"))
    assert n == 2018


def test_zlecaf_offer_attached_with_published_granularity():
    d = _canon()
    sp = _sp_map()
    z = sp["01012100015"].get("zlecaf_afcfta")
    assert z and z["status"] == "OFFER_ONLY"
    # offre publiée en 9 chiffres : code national tronqué vers le bas, jamais l'inverse
    assert z["published_code_length"] == 9
    assert "period_1" in z["periods"] and "period_2" in z["periods"]
    ev = d["exhaustiveness_verification"]["zlecaf_npf_crosscheck"]
    assert ev["npf_matches"] + ev["npf_mismatches"] > 12000


def test_register_documents_verification_and_sha():
    reg = json.loads((SLUG_DIR / "tun_gazette_register.json").read_text(encoding="utf-8"))
    base = reg["base_tariff_documentation"]
    assert base["national_positions"] == 17625
    canon_sha = hashlib.sha256(CANONICAL.read_bytes()).hexdigest()
    assert base["sha256"] == canon_sha
    assert reg["verification_nationale"]["status"] == "EXHAUSTIVE_VERIFIED"
    assert "douane.gov.tn" in " ".join(reg["sources_officielles"])
    assert "tralac.org" in " ".join(reg["sources_officielles"])
    assert "au.int" in " ".join(reg["sources_officielles"])
