"""
Tests for RealSubstitutionService.

Focus: the service must derive products AND volumes from real OEC trade flows
(deterministic, reproducible), and fall back to the curated static profiles only
when OEC is unreachable — never producing randomised values.

OEC is mocked so the tests are hermetic (no network).
"""

import asyncio

import pytest
from services import cache_service
from services import real_substitution_service as mod
from services.real_substitution_service import RealSubstitutionService


def run(coro):
    return asyncio.run(coro)


@pytest.fixture(autouse=True)
def isolated_shared_cache(monkeypatch):
    """The service now caches through the SHARED cache_service (Redis, or
    memory+disk fallback) instead of a private per-instance dict. Keep tests
    hermetic: no Redis, no real disk writes, fresh in-memory store per test."""
    monkeypatch.setattr(cache_service, "get_redis_client", lambda: None)
    monkeypatch.setattr(cache_service, "_DISK_CACHE_ENABLED", False)
    cache_service._MEMORY_STORE.clear()
    yield
    cache_service._MEMORY_STORE.clear()


@pytest.fixture
def svc():
    return RealSubstitutionService()


def _patch_oec(monkeypatch, *, bilateral, exports, imports):
    async def fake_bilateral(importer, year=2022, limit=50):
        return bilateral

    async def fake_exports(iso3, year=2022, limit=100):
        return exports.get(iso3, [])

    async def fake_imports(iso3, year=2022, limit=100):
        return imports.get(iso3, [])

    monkeypatch.setattr(mod.real_trade_service, "get_oec_bilateral_from_world", fake_bilateral)
    monkeypatch.setattr(mod.real_trade_service, "get_oec_exports", fake_exports)
    monkeypatch.setattr(mod.real_trade_service, "get_oec_imports", fake_imports)


def test_import_substitution_uses_real_oec_values(svc, monkeypatch):
    bilateral = {
        "from_outside": 30_000_000_000,
        "africa_share": 12.5,
        "products_from_outside": [
            {
                "hs_code": "8703",
                "product_name": "Motor cars",
                "import_value": 3_000_000_000,
                "source_regions": ["China"],
            },
            {
                "hs_code": "1001",
                "product_name": "Wheat",
                "import_value": 2_000_000_000,
                "source_regions": ["France"],
            },
            # below the default 5M min_value -> filtered out
            {
                "hs_code": "9999",
                "product_name": "Niche",
                "import_value": 1_000_000,
                "source_regions": ["X"],
            },
        ],
    }
    exports = {
        "ZAF": [{"hs_code": "8703", "product_name": "Cars", "trade_value": 5_000_000_000}],
        "MAR": [{"hs_code": "8708", "product_name": "Parts", "trade_value": 1_000_000_000}],
        "EGY": [{"hs_code": "1001", "product_name": "Wheat", "trade_value": 800_000_000}],
    }
    _patch_oec(monkeypatch, bilateral=bilateral, exports=exports, imports={})

    result = run(svc.find_import_substitution_opportunities("DZA", year=2022))

    assert result["is_estimation"] is False
    assert "OEC" in result["data_source"]
    # Sub-threshold product filtered out
    assert len(result["opportunities"]) == 2

    cars = next(o for o in result["opportunities"] if o["imported_product"]["hs_code"] == "8703")
    # Substitution potential is bounded by real African export capacity AND the
    # product's substitutability coefficient (brand effect for cars: 0.5) —
    # a car dollar is not as substitutable as a wheat dollar.
    cars_coef = cars["substitution_feasibility"]["coefficient"]
    assert cars_coef == 0.5  # 8703: effet marque / réseau après-vente
    assert cars["substitution_potential"] == int(
        min(3_000_000_000 * cars_coef, 5_000_000_000 + 1_000_000_000)
    )
    assert cars["binding_constraint"] == "substituabilité"
    supplier_isos = {s["country_iso3"] for s in cars["african_suppliers"]}
    assert supplier_isos == {"ZAF", "MAR"}

    wheat = next(o for o in result["opportunities"] if o["imported_product"]["hs_code"] == "1001")
    # Wheat (commodity, coef 0.9): addressable 1.8B, still capped by EGY supply
    assert wheat["substitution_feasibility"]["coefficient"] == 0.9
    assert wheat["substitution_potential"] == 800_000_000  # capped by EGY supply
    assert wheat["binding_constraint"] == "capacité africaine"

    # Frontend response-shape contract preserved
    ip = cars["imported_product"]
    assert set(ip) >= {"hs_code", "name", "import_value", "current_source"}
    sup = cars["african_suppliers"][0]
    assert set(sup) >= {"country_iso3", "country_name", "export_value", "share_potential"}
    assert set(result["summary"]) >= {"total_substitutable_value", "top_sectors"}


def test_import_substitution_is_reproducible(svc, monkeypatch):
    """Volumes must not change between identical calls (no randomisation)."""
    bilateral = {
        "from_outside": 10_000_000_000,
        "africa_share": 8.0,
        "products_from_outside": [
            {
                "hs_code": "8703",
                "product_name": "Cars",
                "import_value": 3_000_000_000,
                "source_regions": ["China"],
            }
        ],
    }
    exports = {"ZAF": [{"hs_code": "8703", "product_name": "Cars", "trade_value": 5_000_000_000}]}
    _patch_oec(monkeypatch, bilateral=bilateral, exports=exports, imports={})

    r1 = run(svc.find_import_substitution_opportunities("DZA", year=2022))
    cache_service._MEMORY_STORE.clear()  # bypass the result cache to prove determinism, not memoisation
    r2 = run(svc.find_import_substitution_opportunities("DZA", year=2022))
    assert r1["opportunities"] == r2["opportunities"]


def test_import_substitution_falls_back_when_oec_unavailable(svc, monkeypatch):
    bilateral = {"products_from_outside": []}  # OEC returned nothing
    _patch_oec(monkeypatch, bilateral=bilateral, exports={}, imports={})

    r1 = run(svc.find_import_substitution_opportunities("DZA", year=2022))
    cache_service._MEMORY_STORE.clear()
    r2 = run(svc.find_import_substitution_opportunities("DZA", year=2022))

    assert r1["is_estimation"] is True
    assert "statique" in r1["data_source"].lower()
    assert len(r1["opportunities"]) > 0
    # Fallback must also be deterministic
    assert r1["opportunities"] == r2["opportunities"]


def test_export_opportunities_use_real_oec_values(svc, monkeypatch):
    exports = {"ZAF": [{"hs_code": "8703", "product_name": "Cars", "trade_value": 5_000_000_000}]}
    imports = {
        "NGA": [{"hs_code": "8703", "product_name": "Cars", "trade_value": 2_000_000_000}],
        "EGY": [{"hs_code": "8708", "product_name": "Parts", "trade_value": 8_000_000_000}],
    }
    _patch_oec(
        monkeypatch, bilateral={"products_from_outside": []}, exports=exports, imports=imports
    )

    result = run(svc.find_export_opportunities("ZAF", year=2022))

    assert result["is_estimation"] is False
    assert len(result["opportunities"]) == 1
    opp = result["opportunities"][0]
    caps = {m["country_iso3"]: m["capture_potential"] for m in opp["potential_markets"]}
    # Capture potential is bounded by the exporter's real capacity
    assert caps["NGA"] == round(min(5_000_000_000, 2_000_000_000) / 2_000_000_000, 2) == 1.0
    assert caps["EGY"] == round(min(5_000_000_000, 8_000_000_000) / 8_000_000_000, 2)
    # Shape contract
    assert set(opp) >= {
        "export_product",
        "potential_markets",
        "total_market_potential",
        "afcfta_advantage",
    }


def test_export_opportunities_fall_back_when_oec_unavailable(svc, monkeypatch):
    _patch_oec(monkeypatch, bilateral={"products_from_outside": []}, exports={}, imports={})

    result = run(svc.find_export_opportunities("ZAF", year=2022))
    assert result["is_estimation"] is True
    assert "statique" in result["data_source"].lower()


def test_unknown_country_returns_error(svc, monkeypatch):
    _patch_oec(monkeypatch, bilateral={"products_from_outside": []}, exports={}, imports={})
    result = run(svc.find_import_substitution_opportunities("XXX", year=2022))
    assert result.get("error")
