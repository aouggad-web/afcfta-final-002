"""
Tests du ratio de risque pays composite (module Opportunités).

Croisement notations souveraines (S&P/Moody's/Fitch/Scope, crans standard)
× évaluation opérationnelle type assurance-crédit (convention Coface/OCDE,
profils curés banking_system). Zéro fabrication : profil par défaut exclu,
NR jamais converti, composante manquante = poids reporté + confiance dégradée.
"""

import os
import sys

_backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _backend_dir not in sys.path:
    sys.path.insert(0, _backend_dir)

from services import country_risk_service as crs  # noqa: E402


def test_notch_mapping_standard_scales():
    assert crs._notch_of("AAA") == 1
    assert crs._notch_of("Aaa") == 1
    assert crs._notch_of("BB-") == 13
    assert crs._notch_of("Ba3") == 13
    assert crs._notch_of("B+ (stable)") == 14  # perspective tolérée
    assert crs._notch_of("SD") == 22
    # NR / vide : jamais converti en score.
    assert crs._notch_of("NR") is None
    assert crs._notch_of(None) is None
    assert crs._notch_of("Non évalué") is None


def test_notch_to_score_bounds():
    assert crs._notch_to_score(1) == 100.0
    assert crs._notch_to_score(22) == 0.0
    assert 0 < crs._notch_to_score(13) < 50


def test_composite_uses_both_components_with_documented_weights():
    r = crs.get_risk_ratio("MAR")
    assert r["available"] is True
    assert r["confidence"] == "normale"
    assert r["weights"] == {"operational": 0.6, "sovereign": 0.4}
    sov = r["components"]["sovereign"]["score"]
    op = r["components"]["operational"]["score"]
    assert r["risk_ratio"] == round(0.6 * op + 0.4 * sov, 1)
    # Explications détaillées présentes et substantielles.
    assert len(r["methodology"]) >= 4
    assert any("60 % opérationnel" in m for m in r["methodology"])
    assert any("PAS une garantie" in c for c in r["caveats"])
    assert r["components"]["operational"]["grade"] in crs._OPERATIONAL_GRADE_SCORES
    assert "Coface" in r["components"]["operational"]["scale"]


def test_uncurated_country_never_gets_default_operational_grade():
    # COM n'a pas de profil opérationnel curé : le profil générique par défaut
    # de banking_system ne doit JAMAIS entrer dans le ratio (donnée fabriquée).
    r = crs.get_risk_ratio("COM")
    assert r["available"] is True
    assert r["components"]["operational"]["available"] is False
    assert r["weights"] == {"operational": 0.0, "sovereign": 1.0}
    assert "dégradée" in r["confidence"]
    assert r["risk_ratio"] == r["components"]["sovereign"]["score"]


def test_unknown_country_returns_no_ratio():
    r = crs.get_risk_ratio("XXX")
    assert r["available"] is False
    assert r["risk_ratio"] is None
    assert "inventer" in r["note"]


def test_risk_classes():
    assert crs._risk_class(80) == "faible"
    assert crs._risk_class(60) == "modéré"
    assert crs._risk_class(40) == "élevé"
    assert crs._risk_class(20) == "très élevé"


def test_compact_block_for_opportunities():
    compact = crs.compact_risk_for_opportunity("DZA")
    assert compact is not None
    assert compact["risk_ratio"] == crs.get_risk_ratio("DZA")["risk_ratio"]
    assert compact["operational_grade"] == "A4"
    assert "/api/reports/risk-ratio/DZA" in compact["note"]
    assert crs.compact_risk_for_opportunity("XXX") is None


def test_opportunities_enrichment_attaches_partner_risk(monkeypatch):
    import asyncio
    import json as _json

    from services import claude_trade_service as mod
    from services.claude_trade_service import ClaudeTradeService

    monkeypatch.setattr(mod.cache_service, "get", lambda *a, **k: None)
    monkeypatch.setattr(mod.cache_service, "set", lambda *a, **k: None)

    svc = ClaudeTradeService()
    svc._is_ready = lambda: True

    async def fake_call(prompt, max_tokens=8192):
        return _json.dumps(
            {
                "opportunities": [
                    {
                        "product": {"name": "Dattes", "hs6Code": "080410"},
                        "potentialPartner": "Maroc",
                    }
                ]
            }
        )

    svc._call_claude = fake_call
    result = asyncio.run(svc.analyze_trade_opportunities("Algérie", mode="export"))
    assert result.get("risk_enrichment") is True
    opp = result["opportunities"][0]
    assert opp["partner_risk"]["risk_class"] in ("faible", "modéré", "élevé", "très élevé")
    assert opp["partner_risk"]["operational_grade"] == "A4"  # Maroc, profil curé
