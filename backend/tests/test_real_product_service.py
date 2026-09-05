"""
Tests for RealProductService (the "Par Produit" tab).

The product analysis must come from REAL sources — OEC trade flows and
FAO/USGS/UNIDO production — never LLM-generated or randomised figures. OEC and
production are mocked so the tests are hermetic (no network).
"""

import asyncio

import pytest
from services import real_product_service as mod


def run(coro):
    return asyncio.run(coro)


@pytest.fixture(autouse=True)
def _clear_cache():
    mod._CACHE.clear()
    yield
    mod._CACHE.clear()


def _patch(monkeypatch, *, exporters, importers, producers):
    async def fake_exporters(hs_code, year=2022):
        return exporters

    async def fake_importers(hs_code, year=2022):
        return importers

    monkeypatch.setattr(mod.real_trade_service, "get_african_exporters_for_product", fake_exporters)
    monkeypatch.setattr(mod.real_trade_service, "get_african_importers_for_product", fake_importers)
    monkeypatch.setattr(
        mod.production_capacity_service, "get_continental_producers", lambda hs_code: producers
    )


def test_product_analysis_uses_real_values(monkeypatch):
    exporters = [
        {"country_iso3": "CIV", "country_name": "Côte d'Ivoire", "export_value": 6_000_000_000},
        {"country_iso3": "GHA", "country_name": "Ghana", "export_value": 2_000_000_000},
    ]
    importers = [
        {"country_iso3": "ZAF", "country_name": "Afrique du Sud", "import_value": 1_000_000_000},
    ]
    producers = {
        "available": True,
        "unit": "tonnes",
        "source": {"institution": "FAOSTAT", "dataset": "QCL"},
        "top_producers": [
            {
                "country_iso3": "CIV",
                "country_name": "Côte d'Ivoire",
                "value": 2_200_000,
                "share_pct": 38.0,
            },
        ],
    }
    _patch(monkeypatch, exporters=exporters, importers=importers, producers=producers)

    result = run(mod.analyze_product_by_hs_code("1801", lang="fr"))

    assert result["is_estimation"] is False
    assert result["data_quality"] == "real"
    assert "OEC" in result["data_source"]

    # Exporters: real values converted to MUSD with real shares (6B of 8B = 75%)
    civ = result["top_african_exporters"][0]
    assert civ["iso3"] == "CIV"
    assert civ["export_value_musd"] == 6000.0
    assert civ["share_percent"] == 75.0
    assert result["african_trade_summary"]["total_african_exports_musd"] == 8000.0

    # Importer shape
    imp = result["top_african_importers"][0]
    assert imp["iso3"] == "ZAF" and imp["import_value_musd"] == 1000.0

    # Production capacity from FAO/USGS/UNIDO
    prod = result["production_capacities"][0]
    assert prod["iso3"] == "CIV" and prod["capacity"] == 2_200_000 and prod["source"] == "FAOSTAT"

    # Frontend response-shape contract
    assert set(result["product"]) >= {"hs6Code", "hs2_code", "hs4_code", "name"}
    assert set(civ) >= {"country", "iso3", "export_value_musd", "share_percent"}


def test_product_analysis_is_reproducible(monkeypatch):
    exporters = [{"country_iso3": "NGA", "country_name": "Nigeria", "export_value": 3_000_000_000}]
    _patch(monkeypatch, exporters=exporters, importers=[], producers={"available": False})

    r1 = run(mod.analyze_product_by_hs_code("2709", lang="fr"))
    mod._CACHE.clear()
    r2 = run(mod.analyze_product_by_hs_code("2709", lang="fr"))
    assert r1 == r2


def test_product_analysis_flags_estimation_when_no_data(monkeypatch):
    _patch(monkeypatch, exporters=[], importers=[], producers={"available": False})

    result = run(mod.analyze_product_by_hs_code("9999", lang="fr"))
    # No fabricated rows; clearly flagged as having no real data
    assert result["top_african_exporters"] == []
    assert result["top_african_importers"] == []
    assert result["production_capacities"] == []
    assert result["is_estimation"] is True
    assert result["data_quality"] == "unavailable"
    # Product nomenclature is still present so the frontend doesn't fall back to mocks
    assert result["product"]["hs2_code"] == "99"


def test_partial_when_only_production_available(monkeypatch):
    producers = {
        "available": True,
        "unit": "tonnes",
        "source": {"institution": "USGS", "dataset": "MCS"},
        "top_producers": [
            {
                "country_iso3": "COD",
                "country_name": "RD Congo",
                "value": 1_800_000,
                "share_pct": 70.0,
            }
        ],
    }
    _patch(monkeypatch, exporters=[], importers=[], producers=producers)

    result = run(mod.analyze_product_by_hs_code("2603", lang="fr"))
    assert result["is_estimation"] is False
    assert result["data_quality"] == "partial"
    assert result["production_capacities"][0]["iso3"] == "COD"
