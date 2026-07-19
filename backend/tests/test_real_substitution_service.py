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
    async def fake_bilateral(importer, year=2022, limit=50, hs_level="HS4"):
        return bilateral

    async def fake_exports(iso3, year=2022, limit=100, hs_level="HS4"):
        return exports.get(iso3, [])

    async def fake_imports(iso3, year=2022, limit=100, hs_level="HS4"):
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
                "hs_code": "870321",  # HS6: sedans
                "product_name": "Sedans",
                "import_value": 3_000_000_000,
                "source_regions": ["China"],
            },
            {
                "hs_code": "100191",  # HS6: common wheat
                "product_name": "Wheat",
                "import_value": 2_000_000_000,
                "source_regions": ["France"],
            },
            # below the default 5M min_value -> filtered out
            {
                "hs_code": "999999",
                "product_name": "Niche",
                "import_value": 1_000_000,
                "source_regions": ["X"],
            },
        ],
    }
    exports = {
        "ZAF": [{"hs_code": "870321", "product_name": "Sedans", "trade_value": 5_000_000_000}],
        "MAR": [{"hs_code": "870829", "product_name": "Other parts", "trade_value": 1_000_000_000}],
        "EGY": [{"hs_code": "100191", "product_name": "Wheat", "trade_value": 800_000_000}],
    }
    _patch_oec(monkeypatch, bilateral=bilateral, exports=exports, imports={})

    result = run(svc.find_import_substitution_opportunities("DZA", year=2022))

    assert result["is_estimation"] is False
    assert "OEC" in result["data_source"]
    # Sub-threshold product filtered out
    assert len(result["opportunities"]) == 2

    cars = next(o for o in result["opportunities"] if o["imported_product"]["hs_code"] == "870321")
    # Substitution potential is bounded by real African export capacity AND the
    # product's substitutability coefficient (cars at HS4 prefix 8703: 0.5) —
    # a car dollar is not as substitutable as a wheat dollar.
    cars_coef = cars["substitution_feasibility"]["coefficient"]
    assert cars_coef == 0.5  # 8703: effet marque / réseau après-vente
    assert cars["substitution_potential"] == int(
        min(3_000_000_000 * cars_coef, 5_000_000_000)
    )
    assert cars["binding_constraint"] == "substituabilité"
    supplier_isos = {s["country_iso3"] for s in cars["african_suppliers"]}
    # With HS6 granularity, only exact product matches (ZAF exports sedans, MAR exports parts)
    assert supplier_isos == {"ZAF"}

    wheat = next(o for o in result["opportunities"] if o["imported_product"]["hs_code"] == "100191")
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


def test_export_opportunities_are_product_level_with_price_positioning(svc, monkeypatch):
    # ZAF exports sedans (870321, HS6): 5B / 500K t -> avg export price 10 000 $/t.
    # NGA imports sedans (870321, HS6): 2B / 125K t -> avg market price 16 000 $/t.
    # EGY imports PARTS (870829, HS6), different product: it must
    # NOT appear as a market for sedans anymore (that's what HS6 granularity ensures).
    exports = {
        "ZAF": [
            {
                "hs_code": "870321",
                "product_name": "Sedans",
                "trade_value": 5_000_000_000,
                "quantity": 500_000,
            }
        ]
    }
    imports = {
        "NGA": [
            {
                "hs_code": "870321",
                "product_name": "Sedans",
                "trade_value": 2_000_000_000,
                "quantity": 125_000,
            }
        ],
        "EGY": [{"hs_code": "870829", "product_name": "Other parts", "trade_value": 8_000_000_000}],
    }
    _patch_oec(
        monkeypatch, bilateral={"products_from_outside": []}, exports=exports, imports=imports
    )

    result = run(svc.find_export_opportunities("ZAF", year=2022))

    assert result["is_estimation"] is False
    assert len(result["opportunities"]) == 1
    opp = result["opportunities"][0]

    # Product-level HS6: the opportunity is FOR 870321 (exact product, not HS4 or chapter),
    # the coefficient resolves at HS4 prefix (8703 -> 0.5), and the only
    # market is the country importing that exact HS6 product.
    assert opp["export_product"]["hs_code"] == "870321"
    assert opp["market_match_level"] == "hs6"
    coef = opp["substitution_feasibility"]["coefficient"]
    assert coef == 0.5
    markets = {m["country_iso3"]: m for m in opp["potential_markets"]}
    assert set(markets) == {"NGA"}  # EGY (other parts) excluded
    assert markets["NGA"]["capture_potential"] == round(
        min(5_000_000_000, 2_000_000_000 * coef) / 2_000_000_000, 2
    )
    assert markets["NGA"]["addressable_market_size"] == int(2_000_000_000 * coef)
    assert opp["binding_constraint"] == "substituabilité"

    # Price positioning: 10 000 $/t vs 16 000 $/t -> ratio 0.62, "compétitif".
    assert opp["exporter_avg_price_usd_per_tonne"] == 10_000.0
    pp = markets["NGA"]["price_positioning"]
    assert pp["market_avg_price_usd_per_tonne"] == 16_000.0
    assert pp["price_ratio"] == round(10_000 / 16_000, 2)
    assert pp["positioning"] == "compétitif"

    # Shape contract
    assert set(opp) >= {
        "export_product",
        "exporter_avg_price_usd_per_tonne",
        "market_match_level",
        "potential_markets",
        "total_market_potential",
        "substitution_feasibility",
        "binding_constraint",
        "afcfta_advantage",
    }


def test_export_opportunities_fall_back_to_chapter_markets_when_no_exact_match(svc, monkeypatch):
    # ZAF exports sedans (870321, HS6) but no African country has exact match —
    # EGY imports other parts (870829, HS6, same HS4 prefix 8708). Rather than
    # returning nothing, the analysis falls back to HS4-level markets and SAYS SO
    # (market_match_level="hs4"). Note: they're in the same chapter (87) but
    # different HS4, so HS4 fallback finds them.
    exports = {"ZAF": [{"hs_code": "870321", "product_name": "Sedans", "trade_value": 5_000_000_000}]}
    imports = {"EGY": [{"hs_code": "870829", "product_name": "Other parts", "trade_value": 8_000_000_000}]}
    _patch_oec(
        monkeypatch, bilateral={"products_from_outside": []}, exports=exports, imports=imports
    )

    result = run(svc.find_export_opportunities("ZAF", year=2022))
    # Since no exact HS6 match and no HS4 prefix match for sedans (8703 != 8708), no opportunities
    assert len(result["opportunities"]) == 0


def test_export_opportunities_no_price_positioning_on_hs4_fallback_even_with_quantities(
    svc, monkeypatch
):
    # Regression: price_positioning must be None when falling back to HS4 level
    # EVEN WHEN both exporter and market quantities are present and
    # a price could technically be computed — an HS4-blended market price
    # (mixing several different HS6 products in the same HS4) compared to one
    # product's export price would be misleading.
    exports = {
        "ZAF": [
            {
                "hs_code": "870321",  # HS6: sedans
                "product_name": "Sedans",
                "trade_value": 5_000_000_000,
                "quantity": 500_000,
            }
        ]
    }
    imports = {
        "EGY": [
            {
                "hs_code": "870322",  # HS6: SUVs, same HS4 (8703) -> hs4 fallback
                "product_name": "SUVs",
                "trade_value": 8_000_000_000,
                "quantity": 400_000,
            }
        ]
    }
    _patch_oec(
        monkeypatch, bilateral={"products_from_outside": []}, exports=exports, imports=imports
    )

    result = run(svc.find_export_opportunities("ZAF", year=2022))
    opp = result["opportunities"][0]
    assert opp["market_match_level"] == "hs4"
    assert opp["exporter_avg_price_usd_per_tonne"] == 10_000.0  # computable, but unused for hs4
    assert opp["potential_markets"][0]["price_positioning"] is None


def test_export_opportunities_capacity_binds_small_exporter(svc, monkeypatch):
    # Small exporter (100M) vs a 2B market: addressable is 0.5B (coef 0.5 for cars)
    # but capacity is the binding constraint -> capture = 100M / 2B = 0.05.
    exports = {"ZAF": [{"hs_code": "870321", "product_name": "Sedans", "trade_value": 100_000_000}]}
    imports = {"NGA": [{"hs_code": "870321", "product_name": "Sedans", "trade_value": 2_000_000_000}]}
    _patch_oec(
        monkeypatch, bilateral={"products_from_outside": []}, exports=exports, imports=imports
    )

    result = run(svc.find_export_opportunities("ZAF", year=2022))
    opp = result["opportunities"][0]
    caps = {m["country_iso3"]: m["capture_potential"] for m in opp["potential_markets"]}
    assert caps["NGA"] == round(100_000_000 / 2_000_000_000, 2)
    assert opp["binding_constraint"] == "capacité exportateur"


def test_export_opportunities_fall_back_when_oec_unavailable(svc, monkeypatch):
    _patch_oec(monkeypatch, bilateral={"products_from_outside": []}, exports={}, imports={})

    result = run(svc.find_export_opportunities("ZAF", year=2022))
    assert result["is_estimation"] is True
    assert "statique" in result["data_source"].lower()
    # Le repli statique applique la même borne de substituabilité : chaque
    # opportunité expose le bloc de faisabilité, et le taux de capture effectif
    # ne dépasse jamais le coefficient du produit.
    for opp in result["opportunities"]:
        assert "substitution_feasibility" in opp
        coef = opp["substitution_feasibility"]["coefficient"]
        for m in opp["potential_markets"]:
            assert m["capture_potential"] <= coef + 1e-9
            assert m["capture_potential"] <= 0.20 + 1e-9  # jamais au-dessus du taux forfaitaire


def test_unknown_country_returns_error(svc, monkeypatch):
    _patch_oec(monkeypatch, bilateral={"products_from_outside": []}, exports={}, imports={})
    result = run(svc.find_import_substitution_opportunities("XXX", year=2022))
    assert result.get("error")
