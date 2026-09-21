"""
Tests du repli factuel des Opportunités, sans clé d'API.

Quatre sous-onglets sur neuf renvoyaient ``{"error": "ANTHROPIC_API_KEY not
configured"}`` — un écran vide — alors que l'ancrage factuel qui nourrit
l'analyse est calculé AVANT tout appel au modèle et n'en dépend pas.

Ce que ces tests verrouillent :
  • sans clé, le service sert les faits au lieu d'une erreur nue ;
  • l'état dégradé est ANNONCÉ, jamais déguisé en analyse complète ;
  • le champ ``error`` historique est conservé, pour ne pas casser les
    consommateurs qui le testent déjà.
"""

import asyncio
import os
import sys

_backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _backend_dir not in sys.path:
    sys.path.insert(0, _backend_dir)

import pytest  # noqa: E402

from services.claude_trade_service import ClaudeTradeService  # noqa: E402


@pytest.fixture()
def keyless_service(monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    service = ClaudeTradeService()
    monkeypatch.setattr(service, "_is_ready", lambda: False)
    return service


def _run(coro):
    return asyncio.run(coro)


def test_without_key_the_tab_serves_facts_not_an_empty_error(keyless_service):
    result = _run(keyless_service.analyze_trade_opportunities("Kenya", mode="export"))
    assert result["grounding"], "aucun ancrage servi — le sous-onglet reste vide"
    assert len(result["grounding"]) > 200
    assert result["grounding_stats"]["production_products"] > 0


def test_degraded_state_is_announced_not_disguised(keyless_service):
    result = _run(keyless_service.analyze_trade_opportunities("Kenya", mode="export"))
    assert result["degraded"] is True
    assert result["ai_available"] is False
    assert result["degraded_reason"]
    # Le lecteur doit savoir que la narration manque, pas croire à une analyse
    # complète qui n'aurait rien trouvé.
    assert "indisponible" in result["notice"].lower()
    assert result["opportunities"] == []


def test_historic_error_field_is_preserved(keyless_service):
    # Des consommateurs testent déjà ce champ ; le repli ne doit pas le retirer.
    result = _run(keyless_service.analyze_trade_opportunities("Kenya", mode="export"))
    assert result["error"] == "ANTHROPIC_API_KEY not configured"


def test_notice_follows_the_requested_language(keyless_service):
    fr = _run(keyless_service.analyze_trade_opportunities("Kenya", lang="fr"))
    en = _run(keyless_service.analyze_trade_opportunities("Kenya", lang="en"))
    assert "indisponible" in fr["notice"].lower()
    assert "unavailable" in en["notice"].lower()


def test_country_is_resolved_even_in_fallback(keyless_service):
    result = _run(keyless_service.analyze_trade_opportunities("Kenya"))
    assert result["country"] == "Kenya"
    assert result["country_iso3"] == "KEN"


def test_fallback_is_callable_on_its_own(keyless_service):
    # Le repli sert aussi quand le quota est épuisé ou le fournisseur
    # indisponible : il doit s'appeler sans passer par le chemin d'erreur.
    result = _run(keyless_service.factual_opportunities("Ghana", mode="export"))
    assert result["country_iso3"] == "GHA"
    assert result["degraded"] is True
    assert result["grounding_stats"]["production_products"] > 0
    assert "error" not in result


def test_import_mode_also_gets_a_fallback(keyless_service):
    result = _run(keyless_service.analyze_trade_opportunities("Kenya", mode="import"))
    assert result["mode"] == "import"
    assert result["degraded"] is True
    assert result["grounding"] is not None
