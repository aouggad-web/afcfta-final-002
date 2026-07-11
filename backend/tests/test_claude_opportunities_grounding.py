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


# ── _call_claude : paramètres d'échantillonnage + repli + contextvar ──────────


class _FakeAnthropicError(Exception):
    pass


def _install_fake_anthropic(monkeypatch, create_impl):
    """
    Monkeypatche le module `anthropic` importé par claude_trade_service (non
    installé dans ce sandbox — ANTHROPIC_AVAILABLE=False) par un faux client
    dont `messages.create` délègue à `create_impl(**kwargs)`.
    """
    from services import claude_trade_service as mod

    class _Messages:
        async def create(self, **kwargs):
            return await create_impl(**kwargs)

    class _FakeClient:
        def __init__(self, api_key=None):
            self.messages = _Messages()

    fake_anthropic = type(
        "FakeAnthropicModule",
        (),
        {
            "AsyncAnthropic": _FakeClient,
            "NotFoundError": _FakeAnthropicError,
            "BadRequestError": _FakeAnthropicError,
        },
    )
    monkeypatch.setattr(mod, "anthropic", fake_anthropic)
    monkeypatch.setattr(mod, "ANTHROPIC_AVAILABLE", True)


class _FakeMessage:
    def __init__(self, text):
        self.content = [type("Block", (), {"text": text})()]


def test_call_claude_omits_temperature_for_sampling_restricted_models(monkeypatch):
    captured = {}

    async def create_impl(**kwargs):
        captured.update(kwargs)
        return _FakeMessage("{}")

    _install_fake_anthropic(monkeypatch, create_impl)
    svc = _service()
    svc.api_key = "fake-key"
    monkeypatch.setenv("CLAUDE_QUALITY_MODEL", "claude-sonnet-5")

    import asyncio

    asyncio.run(svc._call_claude("prompt", max_tokens=100))
    assert captured["model"] == "claude-sonnet-5"
    assert "temperature" not in captured


def test_call_claude_includes_temperature_for_unrestricted_models(monkeypatch):
    captured = {}

    async def create_impl(**kwargs):
        captured.update(kwargs)
        return _FakeMessage("{}")

    _install_fake_anthropic(monkeypatch, create_impl)
    svc = _service()
    svc.api_key = "fake-key"
    monkeypatch.setenv("CLAUDE_QUALITY_MODEL", "claude-sonnet-4-6")

    import asyncio

    asyncio.run(svc._call_claude("prompt", max_tokens=100))
    assert captured["model"] == "claude-sonnet-4-6"
    assert captured["temperature"] == 0.2


def test_call_claude_falls_back_on_400_not_mentioning_model(monkeypatch):
    # Reproduit le cas réel : claude-sonnet-5 rejette temperature avec un 400
    # dont le message ne contient jamais le mot "model" — l'ancienne condition
    # `"model" in str(e).lower()` aurait laissé ce 400 se propager tel quel.
    calls = []

    async def create_impl(**kwargs):
        calls.append(kwargs["model"])
        if kwargs["model"] != "claude-sonnet-4-6":
            raise _FakeAnthropicError("temperature: extra field not permitted")
        return _FakeMessage('{"ok": true}')

    _install_fake_anthropic(monkeypatch, create_impl)
    svc = _service()
    svc.api_key = "fake-key"
    monkeypatch.setenv("CLAUDE_QUALITY_MODEL", "claude-sonnet-5")

    import asyncio

    async def run():
        # last_model_used est porté par une contextvar isolée par tâche
        # asyncio : la lire dans la MÊME tâche que _call_claude (pas après
        # un asyncio.run() séparé, qui copie le contexte).
        text = await svc._call_claude("prompt", max_tokens=100)
        return text, svc.last_model_used

    text, model_used = asyncio.run(run())
    assert text == '{"ok": true}'
    assert calls == ["claude-sonnet-5", "claude-sonnet-4-6"]
    assert model_used == "claude-sonnet-4-6"


def test_last_model_used_is_none_before_any_call():
    svc = _service()
    assert svc.last_model_used is None


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


def test_truncated_response_handles_top_level_array_without_crashing(monkeypatch):
    # _extract_json peut renvoyer une list nue (Claude a omis l'enveloppe
    # {"opportunities": [...]}) — l'ancien code appelait result.get(...)
    # dessus sans garde et levait AttributeError.
    _bypass_cache(monkeypatch)
    svc = _service()

    async def fake_call(prompt, max_tokens=8192):
        return '[{"product": {"name": "Cacao"}}]'

    svc._call_claude = fake_call
    result = asyncio.run(svc.analyze_trade_opportunities("Togo", mode="export", lang="fr"))
    assert "error" not in result
    assert len(result["opportunities"]) == 1


def test_opportunities_cache_key_includes_model(monkeypatch):
    from services import claude_trade_service as mod

    captured = {}

    def fake_set(prefix, params, value, cache_type):
        captured["params"] = params

    monkeypatch.setattr(mod.cache_service, "get", lambda *a, **k: None)
    monkeypatch.setattr(mod.cache_service, "set", fake_set)
    monkeypatch.setenv("CLAUDE_QUALITY_MODEL", "claude-opus-4-8")

    svc = _service()

    async def fake_call(prompt, max_tokens=8192):
        return json.dumps({"opportunities": [], "summary": {}})

    svc._call_claude = fake_call
    asyncio.run(svc.analyze_trade_opportunities("Kenya", mode="export", lang="fr"))
    assert captured["params"]["model"] == "claude-opus-4-8"
    # v3 : proxy d'exportations + suppression des rangs/parts sous couverture
    # partielle + ratio de risque — invalide les analyses en cache antérieures.
    assert captured["params"]["pv"] == 3


def test_industrial_oec_year_uses_first_flow_not_last(monkeypatch):
    from services import claude_trade_service as mod

    calls = {"n": 0}

    async def fake_get_top_imports(iso3, year, n=15):
        calls["n"] += 1
        # Le premier flux (imports, candidate inputs) trouve des données à
        # OEC_DEFAULT_YEAR directement.
        return [{"hs6Name": "Compresseurs", "hs6Code": "841430", "value_musd": 5.0}]

    async def fake_get_top_exports(iso3, year, n=15):
        # Le second flux (exports) ne retourne des données qu'après repli
        # sur une année antérieure — ne doit PAS écraser oec_year.
        if year == mod.OEC_DEFAULT_YEAR:
            return []
        return [{"hs6Name": "Cacao", "hs6Code": "180100", "value_musd": 3.0}]

    monkeypatch.setattr(mod.oec_data_service, "get_top_imports", fake_get_top_imports)
    monkeypatch.setattr(mod.oec_data_service, "get_top_exports", fake_get_top_exports)

    svc = _service()
    text, stats = asyncio.run(svc._country_opportunity_grounding("Maroc", "MAR", "industrial"))
    assert stats["oec_year"] == mod.OEC_DEFAULT_YEAR


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


# ── Ancrage de analyze_product_by_hs_code et compare_countries ─────────────────
#
# Plainte utilisateur : malgré l'ancrage des Opportunités, un petit pays
# (ex. Mauritanie) ressortait toujours comme "producteur majeur" de
# médicaments et de téléviseurs — deux vues IA distinctes (recherche par code
# HS, comparaison de pays) n'étaient pas ancrées du tout sur les données
# réelles de la plateforme et généraient ces classements de mémoire.


def _no_op_importers(monkeypatch):
    """Empêche tout appel réseau OEC réel dans les tests d'ancrage HS."""
    from services import claude_trade_service as mod

    async def fake_importers(hs_code, year):
        return {"data": []}

    monkeypatch.setattr(mod.oec_service, "get_top_african_importers", fake_importers)


def test_hs_grounding_uses_real_production_when_available(monkeypatch):
    _no_op_importers(monkeypatch)
    svc = _service()
    # HS 1801 (cacao) est couvert par production_capacity_service (FAOSTAT).
    text, real_iso3 = asyncio.run(svc._hs_code_grounding("1801"))
    assert "REAL PRODUCTION" in text
    assert "CIV" in real_iso3


def test_hs_grounding_flags_no_data_for_unmapped_code(monkeypatch):
    _no_op_importers(monkeypatch)
    svc = _service()
    # Code HS sans aucune correspondance FAOSTAT/USGS/UNIDO (chaussures).
    text, real_iso3 = asyncio.run(svc._hs_code_grounding("640299"))
    assert real_iso3 == set()
    rules = svc._product_grounding_rules(text, bool(real_iso3))
    assert "do NOT invent a list of producing countries" in rules


def test_hs_grounding_relays_partial_coverage_caveat(monkeypatch):
    # Cœur du défaut rapporté : pour les médicaments (HS 30) et l'électronique/
    # TV (HS 85), UNIDO ne couvre qu'1-2 pays africains dans notre base (dont
    # Maurice) — sans relayer le garde-fou, le LLM voit "Maurice (100.0%)" et
    # la présente comme producteur majeur continental de médicaments/TV.
    _no_op_importers(monkeypatch)
    svc = _service()
    for hs in ("300490", "8528"):
        text, real_iso3 = asyncio.run(svc._hs_code_grounding(hs))
        assert real_iso3, hs
        assert "[PARTIAL COVERAGE" in text, hs
        assert "NEVER present as continental leadership" in text, hs
        rules = svc._product_grounding_rules(text, bool(real_iso3))
        assert "must NEVER be described as continental" in rules, hs


def test_hs_grounding_included_in_product_prompt(monkeypatch):
    _bypass_cache(monkeypatch)
    _no_op_importers(monkeypatch)
    svc = _service()

    captured = {}

    async def fake_call(prompt, max_tokens=8192):
        captured["prompt"] = prompt
        return json.dumps({"product": {}, "top_african_exporters": []})

    svc._call_claude = fake_call
    asyncio.run(svc.analyze_product_by_hs_code("1801", lang="fr"))
    assert "VERIFIED REAL DATA" in captured["prompt"]
    assert "STRICT DATA RULES" in captured["prompt"]
    assert "REAL PRODUCTION" in captured["prompt"]


def test_filter_unverified_hs_producers_strips_unverified_entries():
    svc = _service()
    result = {
        "production_capacities": [
            {"country": "Côte d'Ivoire", "iso3": "CIV", "capacity": "cacao"},
            {"country": "Mauritanie", "iso3": "MRT", "capacity": "cacao"},
        ]
    }
    removed = svc._filter_unverified_hs_producers(result, {"CIV"})
    assert removed == 1
    assert [p["iso3"] for p in result["production_capacities"]] == ["CIV"]


def test_filter_unverified_hs_producers_noop_when_no_real_data():
    svc = _service()
    result = {"production_capacities": [{"country": "Mauritanie", "iso3": "MRT"}]}
    removed = svc._filter_unverified_hs_producers(result, set())
    assert removed == 0
    assert len(result["production_capacities"]) == 1


def test_product_cache_key_includes_prompt_version(monkeypatch):
    from services import claude_trade_service as mod

    captured = {}

    def fake_set(prefix, params, value, cache_type):
        captured["params"] = params

    monkeypatch.setattr(mod.cache_service, "get", lambda *a, **k: None)
    monkeypatch.setattr(mod.cache_service, "set", fake_set)
    _no_op_importers(monkeypatch)

    svc = _service()

    async def fake_call(prompt, max_tokens=8192):
        return json.dumps({"product": {}})

    svc._call_claude = fake_call
    asyncio.run(svc.analyze_product_by_hs_code("1801", lang="fr"))
    assert captured["params"]["pv"] == 2


def test_compare_countries_grounded_on_real_production(monkeypatch):
    _bypass_cache(monkeypatch)
    svc = _service()

    captured = {}

    async def fake_call(prompt, max_tokens=8192):
        captured["prompt"] = prompt
        return json.dumps({"country_a": "Côte d'Ivoire", "country_b": "Kenya"})

    svc._call_claude = fake_call
    asyncio.run(svc.compare_countries("Côte d'Ivoire", "Kenya", lang="fr"))
    prompt = captured["prompt"]
    assert "VERIFIED REAL DATA" in prompt
    assert "STRICT DATA RULES" in prompt
    assert "VERIFIED PRODUCTION OF Côte d'Ivoire" in prompt
    assert "Cocoa beans" in prompt


def test_compare_countries_cache_key_includes_prompt_version(monkeypatch):
    from services import claude_trade_service as mod

    captured = {}

    def fake_set(prefix, params, value, cache_type):
        captured["params"] = params

    monkeypatch.setattr(mod.cache_service, "get", lambda *a, **k: None)
    monkeypatch.setattr(mod.cache_service, "set", fake_set)

    svc = _service()

    async def fake_call(prompt, max_tokens=8192):
        return json.dumps({"country_a": "Ghana", "country_b": "Togo"})

    svc._call_claude = fake_call
    asyncio.run(svc.compare_countries("Ghana", "Togo", lang="fr"))
    # v3 : le bloc economic_comparison est écrasé par les indicateurs réels
    # du module Profils Pays — invalide les caches aux chiffres LLM.
    assert captured["params"]["pv"] == 3


# ── Garde-fou origine ZLECAf : hubs de réexportation (zone franche) ──────────


def _fake_psr(hs_code, lang="fr"):
    return {
        "status": "AGREED",
        "regional_content": 40,
        "primary_rule": {"code": "VA40", "name": "Valeur ajoutée ≥ 40 %"},
        "source_detail": "AfCFTA Appendix IV (PSR) - test",
    }


def test_import_from_mauritius_gets_origin_warning(monkeypatch):
    # La réexportation depuis la zone franche mauricienne ne confère PAS
    # l'origine ZLECAf (opérations minimales) : toute opportunité d'import
    # dont le fournisseur est Maurice doit porter l'avertissement + la règle
    # d'origine réelle du produit.
    import routes.rules_of_origin as roo

    monkeypatch.setattr(roo, "get_rule_of_origin", _fake_psr)
    svc = _service()
    opps = svc._post_process_opportunities(
        [
            {
                "product": {"name": "Thon en conserve", "hs6Code": "160414"},
                "potentialSupplier": "Maurice",
            },
            {
                "product": {"name": "Café", "hs6Code": "090111"},
                "potentialSupplier": "Kenya",
            },
        ],
        "Sénégal",
        "import",
    )
    mus = next(o for o in opps if o.get("potentialSupplier") == "Maurice")
    ken = next(o for o in opps if o.get("potentialSupplier") == "Kenya")
    oq = mus["origin_qualification"]
    assert oq["warning"] is True
    assert oq["hub_iso3"] == "MUS"
    assert "ne confèrent PAS l'origine" in oq["note"]
    assert oq["product_specific_rule"]["regional_content_pct"] == 40
    assert "certificat d'origine" in oq["note"]
    # Fournisseur non-hub : aucun avertissement parasite.
    assert "origin_qualification" not in ken


def test_export_mode_hub_analyzed_country_gets_origin_warning(monkeypatch):
    import routes.rules_of_origin as roo

    monkeypatch.setattr(roo, "get_rule_of_origin", _fake_psr)
    svc = _service()
    opps = svc._post_process_opportunities(
        [
            {
                "product": {"name": "Textile", "hs6Code": "610910"},
                "potentialPartner": "Kenya",
            }
        ],
        "Maurice",
        "export",
    )
    assert opps[0]["origin_qualification"]["hub_iso3"] == "MUS"


def test_origin_warning_graceful_without_psr_dataset(monkeypatch):
    # RULES_DATA non initialisé (hors démarrage app) -> statut UNKNOWN :
    # l'avertissement reste, la règle produit est absente, rien ne casse.
    import routes.rules_of_origin as roo

    monkeypatch.setattr(roo, "get_rule_of_origin", lambda hs, lang="fr": {"status": "UNKNOWN"})
    svc = _service()
    opps = svc._post_process_opportunities(
        [{"product": {"name": "X", "hs6Code": "999999"}, "potentialSupplier": "Djibouti"}],
        "Sénégal",
        "import",
    )
    oq = opps[0]["origin_qualification"]
    assert oq["warning"] is True
    assert oq["product_specific_rule"] is None
    assert "Annexe 2" in oq["note"]


def test_non_hub_countries_never_get_origin_warning():
    svc = _service()
    opps = svc._post_process_opportunities(
        [{"product": {"name": "Cacao", "hs6Code": "180100"}, "potentialPartner": "Ghana"}],
        "Côte d'Ivoire",
        "export",
    )
    assert "origin_qualification" not in opps[0]


def test_system_instruction_forbids_preference_on_reexports():
    from services import claude_trade_service as mod

    instr = mod.TRADE_SYSTEM_INSTRUCTION
    assert "RE-EXPORTS NEVER CONFER AfCFTA ORIGIN" in instr
    assert "minimal operations" in instr
    assert "SUBSTANTIAL transformation" in instr


# ── Statistiques officielles nationales (EDB Mauritius 2023) ─────────────────


def test_official_stats_mauritius_domestic_vs_reexport():
    from services import national_official_stats as nos

    stats = nos.get_official_stats("mus")
    assert stats is not None
    assert stats["source"]["currency"] == "MUR"
    assert stats["source"]["data_year"] == 2023
    # Thon en conserve : 1er produit d'export DOMESTIQUE 2023 (11,5 Md MUR).
    top = stats["top_domestic_export_product"]
    assert top["hs4"] == "1604" and top["value_mur_mn"] == 11_500
    # Les réexportations sont suivies SÉPARÉMENT — leurs marchés diffèrent
    # des marchés d'export domestique (Vietnam en tête des réexports).
    assert stats["top_reexport_markets"][0]["iso3"] == "VNM"
    assert stats["top_domestic_export_markets"][0]["iso3"] == "ZAF"
    # Aucune statistique inventée pour les autres pays.
    assert nos.get_official_stats("KEN") is None
    assert nos.grounding_lines("KEN") == []


def test_official_stats_grounding_lines_flag_currency_and_origin():
    from services import national_official_stats as nos

    text = "\n".join(nos.grounding_lines("MUS"))
    assert "LOCAL CURRENCY, not USD" in text
    assert "does NOT acquire local AfCFTA origin" in text
    assert "Thon en conserve" in text


def test_opportunity_grounding_includes_official_stats_for_mauritius(monkeypatch):
    from services import claude_trade_service as mod

    async def no_flows(iso3, year=None, n=15):
        return []

    monkeypatch.setattr(mod.oec_data_service, "get_top_exports", no_flows)
    monkeypatch.setattr(mod.oec_data_service, "get_top_imports", no_flows)
    svc = _service()
    text, stats = asyncio.run(svc._country_opportunity_grounding("Maurice", "MUS", "export"))
    assert stats["official_national_stats"] is True
    assert "OFFICIAL NATIONAL STATISTICS FOR Maurice" in text
    assert "RE-EXPORTS are tracked SEPARATELY" in text
    # Pays sans source officielle intégrée : pas de section, flag False.
    text2, stats2 = asyncio.run(svc._country_opportunity_grounding("Kenya", "KEN", "export"))
    assert stats2["official_national_stats"] is False
    assert "OFFICIAL NATIONAL STATISTICS" not in text2


def test_resolve_iso3_accepts_french_name_maurice():
    # Bug corrigé : « Maurice » (nom officiel français, constants.py) manquait
    # dans COUNTRY_NAME_TO_ISO3 — le filtre anti-boucle et le garde-fou origine
    # ne se déclenchaient jamais pour ce nom.
    svc = _service()
    assert svc._resolve_iso3("Maurice") == "MUS"
    assert svc._resolve_iso3("maurice") == "MUS"


# ── Indicateurs réels dans /ai/compare (module Profils Pays, jamais LLM) ─────


def test_compare_countries_economic_block_uses_real_profile_data(monkeypatch):
    from services import claude_trade_service as mod

    monkeypatch.setattr(mod.cache_service, "get", lambda *a, **k: None)
    monkeypatch.setattr(mod.cache_service, "set", lambda *a, **k: None)
    svc = _service()

    async def fake_call(prompt, max_tokens=8192):
        # Le LLM renvoie des zéros de mémoire — cas réel pour beaucoup de pays.
        return json.dumps(
            {
                "country_a": "Algérie",
                "country_b": "Comores",
                "economic_comparison": {"gdp_a_billion": 0.0, "hdi_a": 0.0, "inflation_a": 12.3},
            }
        )

    svc._call_claude = fake_call
    result = asyncio.run(svc.compare_countries("Algérie", "Comores", lang="fr"))
    eco = result["economic_comparison"]
    from country_data import REAL_COUNTRY_DATA

    # Écrasés par les valeurs réelles WDI 2024 du module Profils Pays.
    assert eco["gdp_a_billion"] == REAL_COUNTRY_DATA["DZA"]["gdp_usd_2024"]
    assert eco["gdp_b_billion"] == REAL_COUNTRY_DATA["COM"]["gdp_usd_2024"]
    assert eco["hdi_a"] == REAL_COUNTRY_DATA["DZA"]["development_index"]
    assert eco["gdp_per_capita_a"] == REAL_COUNTRY_DATA["DZA"]["gdp_per_capita_2024"]
    # Inflation : doit être EXACTEMENT la valeur du dataset BM (collectée par
    # l'ETL depuis la run 131) ou null si absente — jamais le chiffre de
    # mémoire du LLM (12.3 dans la réponse simulée ci-dessus).
    from services import wb_macro_service

    expected_inf = (
        wb_macro_service.get_macro("DZA")["indicators"].get("inflation_percent") or {}
    ).get("value")
    assert eco["inflation_a"] == expected_inf
    assert eco["inflation_a"] != 12.3
    assert "non générées" in eco["indicators_source"]


def test_wb_macro_service_reads_latest_year_and_never_invents():
    from services import wb_macro_service

    wb_macro_service.reset_cache()
    macro = wb_macro_service.get_macro("AGO")
    assert macro["available"] is True
    gdp = macro["indicators"]["gdp_usd"]
    assert gdp["value"] > 1e10 and gdp["year"] >= 2023
    growth = macro["indicators"]["gdp_growth_percent"]
    assert growth and growth["year"] >= 2023
    # Inflation : collectée par l'ETL depuis la run 131. Si présente, la valeur
    # doit venir EXACTEMENT du dataset brut (jamais inventée/ajustée) ; si
    # absente du fichier, None honnête.
    inf = macro["indicators"]["inflation_percent"]
    raw_path = os.path.join(
        os.path.dirname(_backend_dir), "data", "json", "worldbank_data_latest.json"
    )
    with open(raw_path, encoding="utf-8") as f:
        raw_inf = json.load(f)["data"].get("AGO", {}).get("indicators", {}).get("Inflation") or {}
    if raw_inf:
        best_year = max(int(y) for y in raw_inf)
        assert inf == {"value": raw_inf[str(best_year)], "year": best_year}
    else:
        assert inf is None
    # Pays hors dataset : indisponible.
    assert wb_macro_service.get_macro("XXX")["available"] is False
