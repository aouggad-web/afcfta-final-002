"""
Tests de l'orchestrateur résilient de séries temporelles commerciales.

Cœur testé sans réseau:
- chaîne de fallback (1re source avec données gagne, isolation des échecs,
  dégradation propre si tout échoue),
- agrégation pure des enregistrements UN Comtrade.
"""

import asyncio
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from services.trade_series_orchestrator import (
    aggregate_comtrade_series,
    get_trade_series_resilient,
)


def _run(coro):
    return asyncio.get_event_loop().run_until_complete(coro)


def _series(has_data, src):
    return {
        "country_iso3": "KEN",
        "chart_rows": (
            [{"year": 2024, "exports": 1, "imports": 1, "balance": 0}] if has_data else []
        ),
        "has_data": has_data,
        "source_used": src,
    }


def test_first_source_with_data_wins():
    async def p1(iso3, s, e):
        return _series(True, "OEC / BACI")

    async def p2(iso3, s, e):
        raise AssertionError("ne doit pas être appelée")

    res = _run(get_trade_series_resilient("KEN", 2022, 2024, providers=[("OEC", p1), ("CT", p2)]))
    assert res["has_data"] is True
    assert res["source_used"] == "OEC / BACI"
    assert res["sources_tried"] == [{"source": "OEC", "status": "success"}]


def test_falls_through_on_no_data_then_succeeds():
    async def p1(iso3, s, e):
        return None  # pas de données

    async def p2(iso3, s, e):
        return _series(True, "UN Comtrade")

    res = _run(get_trade_series_resilient("KEN", 2022, 2024, providers=[("OEC", p1), ("CT", p2)]))
    assert res["source_used"] == "UN Comtrade"
    assert res["sources_tried"] == [
        {"source": "OEC", "status": "no_data"},
        {"source": "CT", "status": "success"},
    ]


def test_isolates_exceptions_and_continues():
    async def p1(iso3, s, e):
        raise RuntimeError("OEC down")

    async def p2(iso3, s, e):
        return _series(True, "UN Comtrade")

    res = _run(get_trade_series_resilient("KEN", 2022, 2024, providers=[("OEC", p1), ("CT", p2)]))
    assert res["source_used"] == "UN Comtrade"
    assert res["sources_tried"][0] == {"source": "OEC", "status": "error"}


def test_graceful_when_all_sources_fail():
    async def p1(iso3, s, e):
        raise RuntimeError("down")

    async def p2(iso3, s, e):
        return None

    res = _run(get_trade_series_resilient("KEN", 2022, 2024, providers=[("OEC", p1), ("CT", p2)]))
    assert res["has_data"] is False
    assert res["source_used"] is None
    assert res["chart_rows"] == []
    assert res["years"] == [2022, 2023, 2024]
    assert len(res["sources_tried"]) == 2


def test_aggregate_comtrade_series():
    years = [2023, 2024]
    records = [
        {"period": "2023", "flowCode": "X", "primaryValue": 100.0},
        {"period": "2023", "flowCode": "M", "primaryValue": 60.0},
        {"period": "2024", "flowCode": "X", "primaryValue": 200.0},
        {"period": "2021", "flowCode": "X", "primaryValue": 999.0},  # hors plage → ignoré
        {"period": "2024", "flowCode": "?", "primaryValue": 5.0},  # flux inconnu → ignoré
    ]
    series = aggregate_comtrade_series(records, years)
    assert series[0] == {"year": 2023, "exports": 100.0, "imports": 60.0, "balance": 40.0}
    assert series[1] == {"year": 2024, "exports": 200.0, "imports": 0, "balance": 200.0}
