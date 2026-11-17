"""
Repli factuel des Chaînes de valeur (service).

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
La route /api/ai/value-chains, sans appelant, a été retirée le 17/11/2026
(audit D3, D8) ; seul le service reste vérifié ici.
"""

import os
import sys

_backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _backend_dir not in sys.path:
    sys.path.insert(0, _backend_dir)

import pytest  # noqa: E402
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
