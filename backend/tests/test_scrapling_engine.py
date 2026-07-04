"""
Tests du moteur Scrapling (S1 — squelette) : normalizer + quality_gate.

Hermétiques : s'appuient sur le dataset crawlé DZA réel (committé) et les
pivots CSV — aucun réseau. Prouvent que le harnais d'étalonnage fonctionne
AVANT d'écrire la première spec de crawl (S2).
"""

import json
from pathlib import Path

from crawlers.scrapling_engine import normalizer, quality_gate

BACKEND = Path(__file__).resolve().parent.parent
DZA_JSON = BACKEND / "data" / "crawled" / "DZA_tariffs.json"
DZA_PIVOTS = BACKEND.parent / "frontend" / "public" / "DZA_tarif_douanier_echantillon.csv"


# ── Normalizer ────────────────────────────────────────────────────────────────
def test_parse_formality_extracts_document_and_authority():
    f = normalizer.parse_formality("Derogation sanitaire veterinaire (m. agriculture)")
    assert f["document"].startswith("Derogation sanitaire")
    assert f["issuing_authority"] == "Ministère de l'Agriculture"
    assert f["raw"]  # texte brut toujours conservé


def test_parse_formality_delivered_by_pattern():
    f = normalizer.parse_formality("Autorisation delivree par le ministere de l'energie")
    assert f["issuing_authority"] == "Ministère de l'Énergie"


def test_parse_advantage_detects_regimes_beyond_fta():
    cases = {
        "Certificat d'Origine dans le cadre ZLECAf - Exonération D.D": "ZLECAF",
        "Certificat d'origine dans le cadre -zale- exo d.d": "ZALE",
        "Exoneration d.d et d.a.p dans cadre convention algero-jordanienne": "CONV_JOR",
        "Exonération dans le cadre des activités hydrocarbures": "HYDROCARB",
        "Attestation d'emploi (pour exo. du d.d)": "ANDI_INVEST",
        "Texte totalement inconnu": "AUTRE",
    }
    for condition, expected in cases.items():
        adv = normalizer.parse_advantage(condition)
        assert adv["regime"] == expected, condition
        assert adv["condition_raw"] == condition  # zéro perte


def test_parse_advantage_keeps_tax_and_rate_from_dict():
    adv = normalizer.parse_advantage(
        {"tax": "D.D", "rate": 0.0, "condition_fr": "Certificat d'Origine ZLECAf"}
    )
    assert adv["tax"] == "D.D" and adv["rate"] == 0.0
    assert adv["regime"] == "ZLECAF"
    assert adv["requires"] == "Certificat d'origine"


def test_assemble_output_contract_v2():
    positions = [
        {
            "hs_code": "0101211100",
            "chapter": "01",
            "section": "01",
            "taxes": {"DD": {"name": "Droit de Douane", "rate": 15.0}},
            "advantages": ["Certificat d'origine dans le cadre ZLECAf - exo D.D"],
            "formalities": ["Visa de controle sanitaire veterinaire (m. agriculture)"],
        }
    ]
    out = normalizer.assemble_output("dza", "Algérie", "douane.gov.dz", positions)
    assert out["country"] == "DZA"
    assert out["source_quality"] == "crawled_authentic"
    assert out["stats"]["sub_positions"] == 1 and out["stats"]["errors"] == 0
    assert out["regimes_registry"][0]["code"] == "ZLECAF"
    pos = out["sub_positions"][0]
    assert pos["formalities"][0]["issuing_authority"] == "Ministère de l'Agriculture"


# ── Quality gate — auto-test sur le dataset DZA réel (l'étalon) ──────────────
# DÉCOUVERTE S1 (2026-07-04) : le gate a détecté que 5 des 11 pivots du CSV
# échantillon divergent du JSON crawlé (millésimes différents : DD 5↔15 %,
# TVA 9↔19 %, sucre, carburants). Les deux sources citent conformepro.dz mais
# à des dates différentes. L'arbitrage = le crawl FRAIS de l'étape S2 sur la
# source officielle (les pivots seront re-vérifiés à cette occasion). D'ici
# là, le self-test prouve le harnais SANS les pivots ; la sensibilité du gate
# est prouvée par le test de falsification ci-dessous.
def test_gate_dza_dataset_against_itself_passes():
    """Le harnais d'étalonnage : le dataset authentique DZA, normalisé v2,
    doit passer le gate contre lui-même (couverture, taxes, zéro perte).
    Prérequis de l'étape S2 : la spec Scrapling devra faire aussi bien."""
    raw = json.load(open(DZA_JSON, encoding="utf-8"))
    candidate = normalizer.assemble_output(
        country=raw["country"],
        country_name=raw["country_name"],
        source=raw["source"],
        sub_positions=raw["sub_positions"],
    )
    candidate_path = BACKEND / "engine" / "sources" / "_gate_selftest_dza.json"
    candidate_path.parent.mkdir(parents=True, exist_ok=True)
    json.dump(candidate, open(candidate_path, "w", encoding="utf-8"), ensure_ascii=False)

    report = quality_gate.run_gate(candidate_path, DZA_JSON, None)
    candidate_path.unlink()

    ref = report["reference_check"]
    assert ref["coverage"] >= 0.995
    assert ref["tax_divergences_count"] == 0
    assert ref["lost_advantages"] == 0 and ref["lost_formalities"] == 0
    assert report["verdict"] == "PASS"


def test_gate_pivots_surface_vintage_discrepancy():
    """Les pivots CSV actuels divergent du JSON crawlé (millésimes) : le gate
    doit le DIRE (échouer bruyamment), jamais le masquer. Ce test fige la
    découverte ; il sera inversé en S2 quand le crawl frais aura arbitré."""
    report = quality_gate.run_gate(DZA_JSON, None, DZA_PIVOTS)
    piv = report["pivots_check"]
    assert piv["pivots_checked"] >= 10
    # Divergence connue documentée — le gate la détecte et échoue.
    assert not piv["pivots_pass"]
    assert report["verdict"] == "FAIL"


def test_gate_scopes_to_candidate_chapters():
    """Un crawl PAR TRANCHES (ex. chapitre 01 seul) est comparé au seul
    chapitre 01 de l'étalon — pas aux 17 061 positions (sinon couverture
    toujours en échec). C'est le correctif du run tariff_crawl #2."""
    raw = json.load(open(DZA_JSON, encoding="utf-8"))
    ch01 = [p for p in raw["sub_positions"] if (p.get("chapter") or "") == "01"]
    assert ch01, "chapitre 01 attendu dans l'étalon"
    candidate = normalizer.assemble_output("DZA", "Algérie", raw["source"], ch01)

    cand_path = BACKEND / "engine" / "sources" / "_gate_scope_ch01.json"
    cand_path.parent.mkdir(parents=True, exist_ok=True)
    json.dump(candidate, open(cand_path, "w", encoding="utf-8"), ensure_ascii=False)
    report = quality_gate.run_gate(cand_path, DZA_JSON, None)  # scope_to_candidate par défaut
    cand_path.unlink()

    ref = report["reference_check"]
    assert ref["scoped_to_chapters"] == ["01"]
    assert ref["reference_positions"] == len(ch01)  # étalon restreint au chap. 01
    assert ref["reference_positions_full"] > ref["reference_positions"]
    assert ref["coverage"] >= 0.995  # couverture pleine SUR LE PÉRIMÈTRE crawlé
    assert report["verdict"] == "PASS"


def test_gate_fails_on_tax_divergence():
    """Un taux modifié doit faire échouer le gate (jamais de données
    silencieusement fausses)."""
    raw = json.load(open(DZA_JSON, encoding="utf-8"))
    tampered = json.loads(json.dumps(raw))  # copie profonde
    tampered["sub_positions"][0]["taxes"]["DD"]["rate"] = 99.0

    tampered_path = BACKEND / "engine" / "sources" / "_gate_selftest_tampered.json"
    tampered_path.parent.mkdir(parents=True, exist_ok=True)
    json.dump(tampered, open(tampered_path, "w", encoding="utf-8"), ensure_ascii=False)

    report = quality_gate.run_gate(tampered_path, DZA_JSON, None)
    tampered_path.unlink()

    assert report["reference_check"]["tax_divergences_count"] == 1
    assert report["verdict"] == "FAIL"
