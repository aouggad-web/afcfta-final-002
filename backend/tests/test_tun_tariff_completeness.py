"""TUN — validation du tarif national authentique (source unique, pas de canonique).

Principe SH6 : les 6 premiers chiffres sont internationaux ; le tarif national
tunisien se développe au-delà — 10 chiffres (SH6+4) + 1 chiffre de CLÉ DE
VALIDATION DÉFINITIVE de la déclaration en douane (11 caractères publiés par
le Tarif Web). Le fichier national (backend/data/TUN_tariffs.json =
backend/data/crawled/TUN_tariffs.json) est la source unique :
- crawl exhaustif : 17 542 codes re-crawlés (2026-08-30) = énumération officielle
  du 2026-08-29, tous avec taux publiés ;
- 83 codes retirés de la source conservés et flaggés (valid_to) ;
- 16 divergences DD juin→re-crawl documentées dans le registre ;
- TVA, assiettes verbatim, préférences par zone (dont ZLECAf : 14 075 lignes)
  et réglementations d'import (26 codes officiels) portés par sous-position.
"""

import hashlib
import json
from pathlib import Path

BACKEND_ROOT = Path(__file__).resolve().parents[1]
_ROOT = BACKEND_ROOT.parent

NATIONAL = BACKEND_ROOT / "data" / "crawled" / "TUN_tariffs.json"
CANONICAL_SLOT = BACKEND_ROOT / "data" / "TUN_tariffs.json"
ENUM = BACKEND_ROOT / "data" / "crawled" / "TUN_enumeration_2026-08.json"
SLUG_DIR = _ROOT / "data" / "tunisia"


def _national():
    return json.loads(NATIONAL.read_text(encoding="utf-8"))


def _sp_map():
    d = _national()
    return {sp["hs_code"]: sp for sp in d["sub_positions"]}


def test_national_file_is_the_single_source():
    """Le canonique est abandonné : le fichier backend/data/TUN_tariffs.json
    est la copie verbatim du tarif national (pas une restructuration dérivée)."""
    assert NATIONAL.read_bytes() == CANONICAL_SLOT.read_bytes()


def test_crawl_exhaustive_vs_official_enumeration():
    nat = _national()
    enum = json.loads(ENUM.read_text(encoding="utf-8"))
    nat_codes = {l["hs_code"] for l in nat["sub_positions"] if not l.get("consolidation_flag")}
    enum_codes = set()
    for _ch, codes in enum["chapters"].items():
        enum_codes |= set(codes.keys()) if isinstance(codes, dict) else set(codes)
    assert nat_codes == enum_codes
    with_rates = sum(1 for l in nat["sub_positions"] if l.get("taxes_import"))
    assert with_rates == len(nat["sub_positions"])  # 17 542 re-crawlés + 83 legacy documentaires


def test_no_duplicate_codes_and_total():
    d = _national()
    codes = [sp["hs_code"] for sp in d["sub_positions"]]
    assert len(codes) == len(set(codes)) == 17625


def test_every_position_has_published_dd_except_documented_gap():
    d = _national()
    gaps = []
    for sp in d["sub_positions"]:
        if sp.get("consolidation_flag"):
            continue
        if not any(
            t.get("code", "").startswith("DD") and t.get("rate_pct") is not None
            for t in (sp.get("taxes_import") or [])
        ):
            gaps.append(sp["hs_code"])
    assert gaps == ["27090090967"], (
        "1 seul trou documenté : huiles brutes de pétrole (régime pétrolier "
        "spécifique) — taux non publié par la source"
    )


def test_dd_divergences_documented_in_register():
    reg = json.loads((SLUG_DIR / "tun_gazette_register.json").read_text(encoding="utf-8"))
    divs = reg["dd_divergences_juin_vs_recrawl"]
    assert len(divs) == 16
    assert all(d["resolution"] == "taux du re-crawl officiel retenu" for d in divs)


def test_retired_codes_kept_and_flagged():
    sp = _sp_map()
    legacy = [c for c, s in sp.items() if s.get("consolidation_flag")]
    assert len(legacy) == 83
    assert all(s.get("valid_to") == "2026-08-30" for s in sp.values() if s.get("consolidation_flag"))


def test_zlecaf_preferences_published_by_source():
    d = _national()
    n = sum(
        1 for sp in d["sub_positions"]
        if any(p.get("zone") == "ZLECAf" for p in (sp.get("preferences") or []))
    )
    assert n == 14075
    reg = json.loads((SLUG_DIR / "tun_gazette_register.json").read_text(encoding="utf-8"))
    assert reg["zlecaf_source_preferences"]["lines_with_zlecaf_preference"] == 14075


def test_import_regulations_official_codes():
    reg = json.loads((SLUG_DIR / "tun_gazette_register.json").read_text(encoding="utf-8"))
    ro = reg["import_regulations_officielles"]
    assert ro["count_codes"] == 26
    assert ro["positions_couvertes"] == 7790
    assert any("monopole" in c["description"].lower() for c in ro["codes"])


def test_register_documents_verification_and_sha():
    reg = json.loads((SLUG_DIR / "tun_gazette_register.json").read_text(encoding="utf-8"))
    base = reg["base_tariff_documentation"]
    assert base["national_positions"] == 17625
    canon_sha = hashlib.sha256(CANONICAL_SLOT.read_bytes()).hexdigest()
    assert base["sha256"] == canon_sha
    assert reg["verification_nationale"]["status"] == "EXHAUSTIVE_VERIFIED"
    assert "douane.gov.tn" in " ".join(reg["sources_officielles"])
    assert "tralac.org" in " ".join(reg["sources_officielles"])
    assert "au.int" in " ".join(reg["sources_officielles"])
    assert "CLÉ DE VALIDATION" in reg.get("national_tariff_note", "")


def test_zlecaf_rates_are_partner_asymmetric():
    """Doctrine ZLECAf : le taux préférentiel dépend du COUPLE (importateur,
    origine) — le calendrier de démantèlement du pays importateur envers
    l'origine s'applique. La source tunisienne le publie elle-même : 14 075
    lignes ZLECAf à taux variables par partenaire (ex. Tanzanie 0% vs
    Cameroun 40% sur la même ligne nationale)."""
    d = _national()
    var = uniform = 0
    partner_variants = set()
    for sp in d["sub_positions"]:
        zl = [(p.get("country_name"), p.get("rate")) for p in (sp.get("preferences") or []) if p.get("zone") == "ZLECAf"]
        if not zl:
            continue
        rates = {r for _, r in zl}
        if len(rates) > 1:
            var += 1
        else:
            uniform += 1
        for name, rate in zl:
            partner_variants.add(name)
    assert var == 14075 and uniform == 0
    assert {"TANZANIE", "CAMEROUN", "KENYA"} <= partner_variants
    reg = json.loads((SLUG_DIR / "tun_gazette_register.json").read_text(encoding="utf-8"))
    assert reg["zlecaf_asymetrie_partenaires"]["preuve_source"]["lignes_avec_taux_variables_par_partenaire"] == 14075
