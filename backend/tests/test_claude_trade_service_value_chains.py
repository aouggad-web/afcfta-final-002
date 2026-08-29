"""
Tests du garde-fou anti-hallucination des chaînes de valeur IA.

Bug signalé : Maurice (qui importe ~75% de ses besoins) apparaissait comme
"producteur principal" dans presque tous les sous-modules d'Opportunités —
un LLM non ancré à des données réelles confond hub de réexport/transformation
et producteur de matière première. Ces tests couvrent les deux garde-fous
purs (sans appel réseau/API) : l'ancrage du prompt sur production_capacity_service
et le filtrage post-réponse.
"""

import os
import sys

_backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _backend_dir not in sys.path:
    sys.path.insert(0, _backend_dir)

from services.claude_trade_service import ClaudeTradeService  # noqa: E402


def _service():
    # __init__ ne fait qu'un warning si ANTHROPIC_API_KEY est absent — aucun
    # appel réseau n'est déclenché par les méthodes testées ici.
    return ClaudeTradeService()


def test_real_producers_grounding_never_includes_mauritius_for_raw_materials():
    svc = _service()
    _, real_iso3 = svc._real_producers_grounding(None)
    assert "MUS" not in real_iso3


def test_real_producers_grounding_covers_known_real_producers():
    svc = _service()
    block, real_iso3 = svc._real_producers_grounding(None)
    # Ghana/Mali (or), Burkina Faso/Mali (coton) sont des producteurs réels
    # attendus (FAOSTAT/USGS) — le bloc de contexte doit les citer.
    assert "GHA" in real_iso3 or "MLI" in real_iso3
    assert block  # non vide


def test_real_producers_grounding_sector_filter_narrows_seeds():
    svc = _service()
    _, cotton_only = svc._real_producers_grounding("cotton/textiles")
    _, all_sectors = svc._real_producers_grounding(None)
    assert cotton_only.issubset(all_sectors)
    assert cotton_only  # le secteur coton a bien des producteurs réels


def test_filter_unverified_raw_producers_drops_hallucinated_mauritius():
    real_iso3 = {"GHA", "MLI", "ZAF"}
    result = {
        "value_chains": [
            {
                "top_producers": [
                    {"country": "Ghana", "iso3": "GHA", "role": "raw_material"},
                    {"country": "Mauritius", "iso3": "MUS", "role": "raw_material"},
                    {"country": "Mauritius", "iso3": "MUS", "role": "exporter"},
                ]
            }
        ]
    }
    removed = ClaudeTradeService._filter_unverified_raw_producers(result, real_iso3)
    assert removed == 1
    remaining_iso3 = [p["iso3"] for p in result["value_chains"][0]["top_producers"]]
    assert remaining_iso3 == ["GHA", "MUS"]  # Ghana gardé, Maurice gardé UNIQUEMENT comme exporter
    remaining_roles = {p["iso3"]: p["role"] for p in result["value_chains"][0]["top_producers"]}
    assert remaining_roles["MUS"] == "exporter"


def test_filter_unverified_raw_producers_noop_when_no_grounding():
    result = {"value_chains": [{"top_producers": [{"iso3": "MUS", "role": "raw_material"}]}]}
    removed = ClaudeTradeService._filter_unverified_raw_producers(result, set())
    assert removed == 0
    assert len(result["value_chains"][0]["top_producers"]) == 1


def test_filter_unverified_raw_producers_handles_missing_or_malformed_fields():
    real_iso3 = {"GHA"}
    result = {
        "value_chains": [
            {"top_producers": "not-a-list"},  # ignoré, pas d'exception
            {},  # pas de top_producers du tout
            {"top_producers": [{"country": "X"}]},  # sans role -> conservé tel quel
        ]
    }
    removed = ClaudeTradeService._filter_unverified_raw_producers(result, real_iso3)
    assert removed == 0


def test_filter_unverified_raw_producers_handles_non_dict_chain_entries():
    # Un LLM peut renvoyer une liste "value_chains" mal formée (élément qui
    # n'est pas un dict) — ne doit jamais lever d'exception et casser toute
    # la réponse par ailleurs exploitable.
    result = {
        "value_chains": [
            "not-a-dict",
            42,
            None,
            {"top_producers": [{"iso3": "MUS", "role": "raw_material"}]},
        ]
    }
    removed = ClaudeTradeService._filter_unverified_raw_producers(result, {"GHA"})
    assert removed == 1
    assert result["value_chains"][0] == "not-a-dict"
    assert result["value_chains"][3]["top_producers"] == []
