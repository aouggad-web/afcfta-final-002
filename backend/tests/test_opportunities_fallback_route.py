"""
Tests de bout en bout du repli factuel — au niveau ROUTE, pas service.

Ce fichier existe à cause d'une erreur précise, et il la nomme pour qu'elle
ne se répète pas : le repli avait été vérifié au niveau du service, où il
fonctionnait, puis annoncé livré. La route, elle, convertissait en HTTP 500
toute réponse portant ``error`` avec une liste d'opportunités vide —
exactement la forme du repli. La fonctionnalité n'atteignait aucun client.

Vérifier une couche ne vaut pas vérifier une fonctionnalité.
"""

import os
import sys

_backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _backend_dir not in sys.path:
    sys.path.insert(0, _backend_dir)

import pytest  # noqa: E402
from auth import check_ai_quota  # noqa: E402
from fastapi import FastAPI  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402
from routes import gemini_analysis  # noqa: E402


@pytest.fixture()
def client():
    app = FastAPI()
    app.include_router(gemini_analysis.router, prefix="/api")
    # Le quota IA est une garde d'abonnement, hors sujet ici : sans
    # neutralisation la route répond 503 avant d'atteindre le code testé.
    app.dependency_overrides[check_ai_quota] = lambda: None
    return TestClient(app)


def _degraded_payload():
    return {
        "country": "Kenya",
        "country_iso3": "KEN",
        "mode": "export",
        "ai_available": False,
        "degraded": True,
        "degraded_reason": "ANTHROPIC_API_KEY not configured",
        "notice": "Analyse narrative indisponible : aucune clé d'API n'est configurée.",
        "grounding": "VERIFIED PRODUCTION OF Kenya … Tea (HS 0902): 2,687,200 tonnes",
        "grounding_stats": {"production_products": 20, "oec_flows": 0, "oec_year": None},
        "opportunities": [],
        "error": "ANTHROPIC_API_KEY not configured",
    }


def test_degraded_payload_reaches_the_client(client, monkeypatch):
    async def fake(**_kwargs):
        return _degraded_payload()

    monkeypatch.setattr(gemini_analysis.claude_trade_service, "analyze_trade_opportunities", fake)
    response = client.get("/api/ai/opportunities/Kenya", params={"mode": "export"})

    assert response.status_code == 200, response.text
    body = response.json()
    assert body["degraded"] is True
    assert body["grounding"], "l'ancrage factuel n'est pas servi"
    assert body["grounding_stats"]["production_products"] == 20
    assert body["notice"]


def test_a_real_error_without_content_is_still_a_500(client, monkeypatch):
    # Le repli ne doit pas servir de tapis sous lequel glisser les vraies
    # pannes : une erreur SANS contenu reste une erreur.
    async def fake(**_kwargs):
        return {"error": "upstream exploded", "opportunities": []}

    monkeypatch.setattr(gemini_analysis.claude_trade_service, "analyze_trade_opportunities", fake)
    response = client.get("/api/ai/opportunities/Kenya", params={"mode": "export"})
    assert response.status_code == 500


def test_a_normal_analysis_is_untouched(client, monkeypatch):
    async def fake(**_kwargs):
        return {"country": "Kenya", "opportunities": [{"product": {"name": "Tea"}}]}

    monkeypatch.setattr(gemini_analysis.claude_trade_service, "analyze_trade_opportunities", fake)
    response = client.get("/api/ai/opportunities/Kenya", params={"mode": "export"})
    assert response.status_code == 200
    assert response.json()["opportunities"]
    assert "degraded" not in response.json()
