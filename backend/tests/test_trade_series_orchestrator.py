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
    extract_year_value_map,
    get_trade_series_resilient,
    probe_sources,
    series_from_year_maps,
)


def _run(coro):
    return asyncio.run(coro)


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


def test_series_from_year_maps():
    years = [2022, 2023, 2024]
    exports = {2022: 100.0, 2024: 300.0}  # 2023 manquant → 0
    imports = {2022: 80.0, 2023: 250.0}
    series = series_from_year_maps(exports, imports, years)
    assert series[0] == {"year": 2022, "exports": 100.0, "imports": 80.0, "balance": 20.0}
    assert series[1] == {"year": 2023, "exports": 0, "imports": 250.0, "balance": -250.0}
    assert series[2]["exports"] == 300.0


def test_extract_year_value_map_sums_and_skips_bad_rows():
    rows = [
        {"Year": "2023", "Value": "100"},
        {"Year": "2023", "Value": 50},  # même année → sommée
        {"Year": None, "Value": 9},  # année invalide → ignorée
        {"Year": "2024", "Value": None},  # valeur nulle → 0
    ]
    out = extract_year_value_map(rows, "Year", "Value")
    assert out[2023] == 150.0
    assert out[2024] == 0.0
    assert None not in out


def test_wto_unctad_providers_disabled_by_default(monkeypatch):
    # Sans variables d'env, WTO/UNCTAD ne sont pas dans la chaîne par défaut.
    import services.trade_series_orchestrator as orch

    for var in ("COMTRADE_FALLBACK_ENABLED", "WTO_FALLBACK_ENABLED", "UNCTAD_FALLBACK_ENABLED"):
        monkeypatch.delenv(var, raising=False)
    names = [name for name, _ in orch.default_providers()]
    assert names == ["OEC / BACI"]


def test_free_sources_come_before_paid_in_registry():
    # Les API gratuites (OEC, WTO) doivent précéder celles à clé (Comtrade).
    import services.trade_series_orchestrator as orch

    names = [e["name"] for e in orch.SOURCE_REGISTRY]
    assert names[0] == "OEC / BACI"
    assert names.index("OMC / WTO") < names.index("UN Comtrade")
    # WTO est marqué gratuit, Comtrade payant.
    by_name = {e["name"]: e for e in orch.SOURCE_REGISTRY}
    assert by_name["OMC / WTO"]["free"] is True
    assert by_name["UN Comtrade"]["free"] is False


def test_when_wto_enabled_it_joins_the_chain(monkeypatch):
    import services.trade_series_orchestrator as orch

    monkeypatch.setenv("WTO_FALLBACK_ENABLED", "true")
    for var in ("COMTRADE_FALLBACK_ENABLED", "UNCTAD_FALLBACK_ENABLED"):
        monkeypatch.delenv(var, raising=False)
    names = [name for name, _ in orch.default_providers()]
    assert names == ["OEC / BACI", "OMC / WTO"]


def test_probe_sources_reports_each_source(monkeypatch):
    # La sonde rapporte chaque source du registre avec un statut, sans lever.
    import services.trade_series_orchestrator as orch

    async def fake_oec(iso3, s, e):
        return {
            "has_data": True,
            "chart_rows": [{"year": e, "exports": 1, "imports": 0, "balance": 1}],
        }

    async def boom(iso3, s, e):
        raise RuntimeError("réseau indisponible")

    registry = [
        {"name": "OEC / BACI", "flag": None, "fetch": fake_oec, "free": True},
        {"name": "OMC / WTO", "flag": "WTO_FALLBACK_ENABLED", "fetch": boom, "free": True},
    ]
    monkeypatch.setattr(orch, "SOURCE_REGISTRY", registry)
    monkeypatch.delenv("WTO_FALLBACK_ENABLED", raising=False)

    report = _run(probe_sources("KEN", 2023, 2024))
    by_name = {s["source"]: s for s in report["sources"]}
    assert by_name["OEC / BACI"]["status"] == "ok"
    assert by_name["OEC / BACI"]["enabled"] is True
    # WTO sondé même désactivé; l'exception est capturée en statut "error".
    assert by_name["OMC / WTO"]["status"] == "error"
    assert by_name["OMC / WTO"]["enabled"] is False


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


def test_aggregate_comtrade_prefers_total_row_to_avoid_double_count():
    # Si une ligne agrégée cmdCode='TOTAL' existe, on l'utilise seule.
    years = [2024]
    records = [
        {"period": "2024", "flowCode": "X", "primaryValue": 100.0, "cmdCode": "TOTAL"},
        {"period": "2024", "flowCode": "X", "primaryValue": 40.0, "cmdCode": "0101"},
        {"period": "2024", "flowCode": "X", "primaryValue": 60.0, "cmdCode": "0202"},
    ]
    series = aggregate_comtrade_series(records, years)
    # 100 (TOTAL) et non 200 (TOTAL + lignes produits).
    assert series[0]["exports"] == 100.0


def test_aggregate_comtrade_total_is_per_year():
    # 2023 n'a que des lignes détaillées (→ sommées); 2024 a un TOTAL (→ utilisé seul).
    years = [2023, 2024]
    records = [
        {"period": "2023", "flowCode": "X", "primaryValue": 30.0, "cmdCode": "0101"},
        {"period": "2023", "flowCode": "X", "primaryValue": 20.0, "cmdCode": "0202"},
        {"period": "2024", "flowCode": "X", "primaryValue": 500.0, "cmdCode": "TOTAL"},
        {"period": "2024", "flowCode": "X", "primaryValue": 99.0, "cmdCode": "0101"},
    ]
    series = aggregate_comtrade_series(records, years)
    assert series[0]["exports"] == 50.0  # 2023: 30+20 (détail), pas perdu
    assert series[1]["exports"] == 500.0  # 2024: TOTAL seul
