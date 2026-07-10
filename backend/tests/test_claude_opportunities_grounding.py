"""
Tests de l'ancrage données réelles du module Opportunités (analyze_trade_opportunities).

Problème signalé : même avec la clé API configurée, les résultats des
Opportunités restaient en deçà des attentes. Trois causes corrigées ici :
1. Les 3 prompts (export/import/industrial) n'étaient PAS ancrés sur les
   données réelles de la plateforme — le LLM choisissait ses 15 opportunités
   de mémoire (produits non produits/échangés par le pays, chiffres inventés).
2. max_tokens=8192 tronquait régulièrement le JSON de 15 opportunités
   détaillées (~9-12k tokens) → perte totale ("Failed to parse") ou partielle.
3. Modèle non configurable : impossible de monter en qualité ou de replier
   proprement quand un proxy (ex. clé universelle Emergent) n'expose pas le
   modèle demandé.

Tests purs (aucun appel réseau/API réel : _call_claude est monkeypatché).
"""

import asyncio
import json
import os
import sys

_backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _backend_dir not in sys.path:
    sys.path.insert(0, _backend_dir)

from services import production_capacity_service  # noqa: E402
from services.claude_trade_service import ClaudeTradeService  # noqa: E402


def _service():
    svc = ClaudeTradeService()
    # Les tests n'appellent jamais l'API réelle : _call_claude est remplacé.
    svc._is_ready = lambda: True
    return svc


# ── get_country_profile (production_capacity_service) ─────────────────────────


def test_country_profile_civ_includes_cocoa_leadership():
    profile = production_capacity_service.get_country_profile("CIV")
    assert profile["available"] is True
    cocoa = next(p for p in profile["products"] if p["commodity"] == "Cocoa beans")
    assert cocoa["rank"] == 1
    assert cocoa["share_pct"] and cocoa["share_pct"] > 30
    assert cocoa["unit"] == "tonnes"
    assert cocoa["year"] >= 2023


def test_country_profile_sorted_by_african_share_desc():
    profile = production_capacity_service.get_country_profile("ETH")
    shares = [p["share_pct"] or 0.0 for p in profile["products"]]
    assert shares == sorted(shares, reverse=True)


def test_country_profile_unknown_country_unavailable():
    profile = production_capacity_service.get_country_profile("XXX")
    assert profile["available"] is False
    assert profile["products"] == []


def test_country_profile_mauritius_no_fabricated_leadership():
    # Maurice importe ~75% de ses besoins : son profil réel ne doit contenir
    # aucun rang 1 continental sur une matière première à large couverture.
    profile = production_capacity_service.get_country_profile("MUS")
    for p in profile["products"]:
        if p["rank"] == 1:
            # Un rang 1 n'est tolérable que sur couverture partielle,
            # explicitement signalée par le caveat.
            assert p["coverage_caveat"], p


# ── Salvage JSON tronqué ───────────────────────────────────────────────────────


def test_salvage_truncated_list_recovers_complete_items():
    svc = _service()
    truncated = (
        '{"opportunities": [{"product": {"name": "Cacao"}}, {"product": {"name": "Or"}},'
        ' {"product": {"name": "Tronqu'
    )
    items = svc._salvage_truncated_list(truncated)
    assert len(items) == 2
    assert items[1]["product"]["name"] == "Or"


def test_salvage_handles_markdown_fences_and_no_array():
    svc = _service()
    fenced = '```json\n{"opportunities": [{"a": 1}]\n```'
    assert svc._salvage_truncated_list(fenced) == [{"a": 1}]
    assert svc._salvage_truncated_list("aucun tableau ici") == []


# ── Configuration des modèles ──────────────────────────────────────────────────


def test_model_env_overrides(monkeypatch):
    svc = _service()
    monkeypatch.delenv("CLAUDE_BULK_MODE", raising=False)
    monkeypatch.delenv("CLAUDE_QUALITY_MODEL", raising=False)
    assert svc.MODEL == svc.QUALITY_MODEL
    monkeypatch.setenv("CLAUDE_QUALITY_MODEL", "claude-opus-4-8")
    assert svc.MODEL == "claude-opus-4-8"
    monkeypatch.setenv("CLAUDE_BULK_MODE", "true")
    assert svc.MODEL == svc.BULK_MODEL
    monkeypatch.setenv("CLAUDE_BULK_MODEL", "claude-haiku-x")
    assert svc.MODEL == "claude-haiku-x"


def test_quality_fallback_model_is_widely_available():
    svc = _service()
    # Le repli doit rester un modèle stable exposé par les passerelles tierces.
    assert svc.QUALITY_FALLBACK_MODEL == "claude-sonnet-4-6"
    assert svc.QUALITY_MODEL != svc.QUALITY_FALLBACK_MODEL


# ── Ancrage du prompt d'analyze_trade_opportunities ───────────────────────────


def _bypass_cache(monkeypatch):
    # Le cache (Redis → fichier JSON) persiste entre processus : sans ce
    # bypass, une exécution précédente masquerait le prompt réellement généré.
    from services import claude_trade_service as mod

    monkeypatch.setattr(mod.cache_service, "get", lambda *a, **k: None)
    monkeypatch.setattr(mod.cache_service, "set", lambda *a, **k: None)


def _run_capture(svc, country, mode):
    captured = {}

    async def fake_call(prompt, max_tokens=8192):
        captured["prompt"] = prompt
        captured["max_tokens"] = max_tokens
        return json.dumps({"opportunities": [], "summary": {}})

    svc._call_claude = fake_call
    result = asyncio.run(svc.analyze_trade_opportunities(country, mode=mode, lang="fr"))
    return captured, result


def test_export_prompt_grounded_on_real_production(monkeypatch):
    _bypass_cache(monkeypatch)
    svc = _service()
    captured, result = _run_capture(svc, "Côte d'Ivoire", "export")
    prompt = captured["prompt"]
    assert "VERIFIED REAL DATA" in prompt
    assert "STRICT DATA RULES" in prompt
    # La production réelle du pays (FAOSTAT) doit être dans le prompt
    assert "Cocoa beans" in prompt
    assert "continental rank 1" in prompt
    # Transparence côté résultat
    assert result["grounding"]["grounded"] is True
    assert result["grounding"]["production_products"] > 0


def test_all_modes_carry_grounding_rules(monkeypatch):
    _bypass_cache(monkeypatch)
    svc = _service()
    for mode in ("export", "import", "industrial"):
        captured, _ = _run_capture(svc, "Kenya", mode)
        assert "STRICT DATA RULES" in captured["prompt"], mode
        assert "NEVER invent precise statistics" in captured["prompt"], mode


def test_opportunities_call_uses_raised_token_ceiling(monkeypatch):
    # 15 opportunités détaillées ≈ 9-12k tokens : 8192 tronquait la réponse.
    _bypass_cache(monkeypatch)
    svc = _service()
    captured, _ = _run_capture(svc, "Ghana", "export")
    assert captured["max_tokens"] >= 16000


def test_truncated_response_is_salvaged_not_lost(monkeypatch):
    _bypass_cache(monkeypatch)
    svc = _service()

    async def fake_call(prompt, max_tokens=8192):
        return (
            '{"opportunities": [{"product": {"name": "Cacao", "hs6Code": "180100"},'
            ' "potentialPartner": "Nigeria"}, {"product": {"name": "Coup'
        )

    svc._call_claude = fake_call
    result = asyncio.run(svc.analyze_trade_opportunities("Togo", mode="export", lang="fr"))
    assert result.get("truncated_response_salvaged") is True
    assert len(result["opportunities"]) == 1
    assert result["opportunities"][0]["product"]["name"] == "Cacao"


def test_partial_coverage_flagged_in_grounding_block():
    svc = _service()

    async def run():
        return await svc._country_opportunity_grounding("Maurice", "MUS", "export")

    text, stats = asyncio.run(run())
    assert stats["production_products"] > 0
    # Toute ligne à couverture partielle porte l'avertissement anti-leadership
    if "coverage" in text.lower() or "[PARTIAL COVERAGE" in text:
        assert "never present this rank as continental leadership" in text


# ── Signal d'assemblage par proxy d'intrants (biens hors FAOSTAT/USGS/UNIDO) ──


def test_industrial_grounding_includes_assembly_signal(monkeypatch):
    from services import claude_trade_service as mod

    async def fake_signal(iso3, hs_code):
        if hs_code != "8418":
            return {"available": False, "reason": "no_proxy_mapping", "hs_code": hs_code}
        return {
            "available": True,
            "method": "input_proxy_estimate",
            "hs_code": "8418",
            "output_label": "Réfrigérateurs, congélateurs et matériel frigorifique",
            "country_iso3": iso3,
            "input_signals": [
                {
                    "input_hs6": "841430",
                    "input_label": "Compresseurs pour équipement frigorifique",
                    "country_import_usd": 9_000_000.0,
                    "year": 2023,
                    "source": "OEC / BACI",
                    "continental_ranking": {
                        "available": True,
                        "rank": 3,
                        "total_countries": 12,
                        "top_importers": [],
                    },
                }
            ],
            "methodology": "PAS une production mesurée",
        }

    monkeypatch.setattr(mod.manufacturing_proxy_service, "estimate_assembly_signal", fake_signal)

    svc = _service()
    text, stats = asyncio.run(svc._country_opportunity_grounding("Maroc", "MAR", "industrial"))
    assert stats["assembly_signals"] > 0
    assert "ASSEMBLY SIGNAL FOR Maroc" in text
    assert "NOT measured production" in text
    assert "Réfrigérateurs" in text
    assert "African importer rank 3/12" in text


def test_assembly_signal_only_grounds_industrial_mode(monkeypatch):
    from services import claude_trade_service as mod

    calls = []

    async def spy_signal(iso3, hs_code):
        calls.append(hs_code)
        return {"available": False, "reason": "no_proxy_mapping", "hs_code": hs_code}

    monkeypatch.setattr(mod.manufacturing_proxy_service, "estimate_assembly_signal", spy_signal)

    svc = _service()
    asyncio.run(svc._country_opportunity_grounding("Maroc", "MAR", "export"))
    assert calls == []
