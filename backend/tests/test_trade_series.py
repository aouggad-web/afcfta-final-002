"""
Tests de l'agrégation de série temporelle commerciale (build_trade_series).

Fonction pure, sans réseau : valide le parsing/agrégation des lignes OEC
(drilldown par année) en série exports/imports/balance.
"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from services.oec_trade_service import build_trade_series


def test_aggregates_by_year_and_computes_balance():
    years = [2022, 2023, 2024]
    exports_rows = [
        {"Year": 2022, "Trade Value": 100.0},
        {"Year": 2022, "Trade Value": 50.0},  # 2 lignes même année → sommées
        {"Year": 2023, "Trade Value": 200.0},
        {"Year": 2024, "Trade Value": 300.0},
    ]
    imports_rows = [
        {"Year": 2022, "Trade Value": 80.0},
        {"Year": 2023, "Trade Value": 250.0},
        {"Year": 2024, "Trade Value": 120.0},
    ]
    series = build_trade_series(exports_rows, imports_rows, years)

    assert [r["year"] for r in series] == years
    assert series[0] == {
        "year": 2022,
        "exports": 150.0,
        "imports": 80.0,
        "balance": 70.0,
        "exports_quantity": 0.0,
        "imports_quantity": 0.0,
    }
    assert series[1]["balance"] == -50.0  # 200 - 250
    assert series[2]["exports"] == 300.0
    assert series[2]["imports"] == 120.0
    assert series[2]["balance"] == 180.0


def test_missing_years_are_zero_filled():
    years = [2018, 2019, 2020]
    # Seule 2019 a des données.
    series = build_trade_series([{"Year": 2019, "Trade Value": 42.0}], [], years)
    assert series[0]["exports"] == 0
    assert series[0]["imports"] == 0
    assert series[0]["balance"] == 0
    assert series[1]["exports"] == 42.0
    assert series[2]["exports"] == 0


def test_quantity_is_aggregated_by_year():
    years = [2022, 2023]
    exports_rows = [
        {"Year": 2022, "Trade Value": 100.0, "Quantity": 10.0},
        {"Year": 2022, "Trade Value": 50.0, "Quantity": 5.0},
        {"Year": 2023, "Trade Value": 200.0, "Quantity": 20.0},
    ]
    imports_rows = [
        {"Year": 2022, "Trade Value": 80.0, "Quantity": 8.0},
    ]
    series = build_trade_series(exports_rows, imports_rows, years)
    assert series[0]["exports_quantity"] == 15.0
    assert series[0]["imports_quantity"] == 8.0
    assert series[1]["exports_quantity"] == 20.0
    assert series[1]["imports_quantity"] == 0.0


def test_ignores_years_outside_range_and_handles_nulls():
    years = [2023, 2024]
    exports_rows = [
        {"Year": 2021, "Trade Value": 999.0},  # hors plage → ignoré
        {"Year": 2023, "Trade Value": None},  # valeur nulle → 0
        {"Year": 2024, "Trade Value": 10.0},
    ]
    series = build_trade_series(exports_rows, [], years)
    assert series[0]["exports"] == 0  # 2023, None traité comme 0
    assert series[1]["exports"] == 10.0
    # 2021 n'apparaît pas.
    assert all(r["year"] in years for r in series)


def test_empty_input_returns_zero_series():
    years = [2022, 2023]
    series = build_trade_series([], None, years)
    assert len(series) == 2
    assert all(r["exports"] == 0 and r["imports"] == 0 and r["balance"] == 0 for r in series)
