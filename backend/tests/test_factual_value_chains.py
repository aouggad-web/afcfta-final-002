"""
Repli factuel des Chaînes de valeur — service ET route.

L'onglet servait, sans clé d'API, un jeu de chaînes ÉCRIT EN DUR : noms
d'étapes, pays, et valeurs par maillon sans aucune source. Il sert désormais
les producteurs réels, mesurés par FAOSTAT, l'USGS et l'UNIDO.

CE QUE CES TESTS VERROUILLENT, ET POURQUOI CHACUN
--------------------------------------------------
1. Le repli rend des producteurs RÉELS, chacun avec sa source, son année et
   son unité — sans quoi il ne vaudrait pas mieux que ce qu'il remplace.
2. Il ne rend AUCUNE étape. Découper une filière en maillons et y affecter des
   pays est une analyse, pas une mesure ; la seule façon honnête de ne pas
   l'inventer est de ne rien émettre. Un test le garantit, parce que c'est
   précisément le genre de champ qu'on se surprend à « compléter ».
3. Les rôles distinguent la matière première de la transformation. Confondre
   les deux ferait passer un transformateur pour un producteur — l'erreur que
   tout le module s'attache à éviter.
4. La ROUTE laisse passer le repli. Ce dernier point existe parce qu'il a déjà
   échoué une fois ailleurs : un repli vérifié au niveau du service, converti
   en HTTP 500 par la route, et annoncé livré sans atteindre aucun client.
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
from services.claude_trade_service import claude_trade_service  # noqa: E402

RAW_MATERIAL_DIMENSIONS = {"raw_material", "processor"}


@pytest.fixture(scope="module")
def payload():
    return claude_trade_service.factual_value_chains(lang="fr")


def test_serves_real_producers(payload):
    assert payload["value_chains"], "aucune chaîne servie"
    assert payload["grounding_stats"]["producers"] > 0
    for chain in payload["value_chains"]:
        assert chain["top_producers"], f"{chain['id']} sans producteur"


def test_every_producer_carries_its_source(payload):
    # Un chiffre dont on ne peut pas dire qui l'a publié, quand, et dans quelle
    # unité ne vaut pas mieux qu'un chiffre absent — il vaut moins, parce
    # qu'il inspire confiance.
    for chain in payload["value_chains"]:
        for prod in chain["top_producers"]:
            assert prod["source"]["institution"], prod
            assert prod["year"], prod
            assert prod["unit"], prod
            assert isinstance(prod["production_tonnes"], (int, float))


def test_no_stage_is_invented(payload):
    # Le repli n'a aucune source pour découper une filière en maillons.
    # Émettre une étape vide serait déjà trop : on n'en émet aucune.
    for chain in payload["value_chains"]:
        assert chain["stages"] == [], f"{chain['id']} invente des étapes"


def test_no_trade_potential_is_invented(payload):
    for chain in payload["value_chains"]:
        assert "intra_african_potential_musd" not in chain
        assert "global_exports_musd" not in chain


def test_roles_separate_extraction_from_transformation(payload):
    roles = {p["role"] for c in payload["value_chains"] for p in c["top_producers"]}
    assert roles <= RAW_MATERIAL_DIMENSIONS, roles
    # Les deux doivent être représentés : sinon la distinction ne sert à rien.
    assert roles == RAW_MATERIAL_DIMENSIONS


def test_a_country_appears_once_per_chain(payload):
    # Un pays peut produire plusieurs commodités du même secteur. Additionner
    # des tonnes de café et de cacao n'aurait pas de sens ; on garde la
    # première occurrence, et ce test empêche un doublon silencieux.
    for chain in payload["value_chains"]:
        iso3 = [p["iso3"] for p in chain["top_producers"]]
        assert len(iso3) == len(set(iso3)), chain["id"]


def test_sector_filter_narrows_the_answer(payload):
    one = claude_trade_service.factual_value_chains(sector="minerals", lang="fr")
    assert len(one["value_chains"]) < len(payload["value_chains"])
    assert one["value_chains"][0]["id"] == "minerals"


def test_notice_is_localised():
    fr = claude_trade_service.factual_value_chains(lang="fr")["notice"]
    en = claude_trade_service.factual_value_chains(lang="en")["notice"]
    assert fr != en and "indisponible" in fr and "unavailable" in en


def test_the_route_lets_the_degraded_payload_through(monkeypatch):
    # Le point qui a déjà échoué ailleurs : vérifier le service ne vaut pas
    # vérifier la fonctionnalité.
    app = FastAPI()
    app.include_router(gemini_analysis.router, prefix="/api")
    app.dependency_overrides[check_ai_quota] = lambda: None
    client = TestClient(app)

    async def fake(**_kwargs):
        out = claude_trade_service.factual_value_chains(lang="fr")
        out["error"] = "ANTHROPIC_API_KEY not configured"
        return out

    monkeypatch.setattr(gemini_analysis.claude_trade_service, "get_value_chains_analysis", fake)
    response = client.get("/api/ai/value-chains", params={"lang": "fr"})

    assert response.status_code == 200, response.text
    body = response.json()
    assert body["degraded"] is True
    assert body["value_chains"], "le repli n'atteint pas le client"
    assert body["notice"]
