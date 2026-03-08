#!/usr/bin/env python3
"""
Tests for the North Africa (UMA/AMU) regional intelligence implementation.

Covers:
- uma_constants: Country metadata, trade blocs, VAT rates
- tariff_structures: Morocco reference bands, country profiles, chapter rates
- investment_zones: SEZ data for all 7 countries
- morocco_uma_scraper: Position generation and output schema
- uma_member_scraper: Country derivation logic
- API routes: All 7 endpoint paths
"""

import sys
import importlib.util
from pathlib import Path

# ── Path setup ────────────────────────────────────────────────────────────────
REPO_ROOT = Path(__file__).parent.parent
BACKEND_PATH = REPO_ROOT / "backend"
sys.path.insert(0, str(BACKEND_PATH))


# ─────────────────────────────────────────────────────────────────────────────
# 1. UMA Constants Tests
# ─────────────────────────────────────────────────────────────────────────────

def test_uma_countries_list():
    """All 7 North African countries are present in UMA_COUNTRIES."""
    from crawlers.countries.north_africa.uma_constants import UMA_COUNTRIES
    expected = {"MAR", "EGY", "TUN", "DZA", "LBY", "SDN", "MRT"}
    assert expected == set(UMA_COUNTRIES), (
        f"Expected {expected}, got {set(UMA_COUNTRIES)}"
    )
    print("✅ UMA_COUNTRIES contains all 7 North African countries")


def test_uma_core_members():
    """UMA core members are exactly the 5 Arab Maghreb Union states."""
    from crawlers.countries.north_africa.uma_constants import UMA_CORE_MEMBERS
    expected = {"MAR", "DZA", "TUN", "LBY", "MRT"}
    assert expected == set(UMA_CORE_MEMBERS)
    print("✅ UMA_CORE_MEMBERS: 5 members correct")


def test_country_metadata_completeness():
    """Each country has required metadata fields."""
    from crawlers.countries.north_africa.uma_constants import COUNTRY_METADATA, UMA_COUNTRIES
    required_fields = [
        "iso3", "name_en", "name_fr", "name_ar", "capital",
        "currency", "customs_url", "data_reliability",
    ]
    for code in UMA_COUNTRIES:
        meta = COUNTRY_METADATA.get(code)
        assert meta is not None, f"No metadata for {code}"
        for field in required_fields:
            assert field in meta, f"{code} missing field: {field}"
    print("✅ Country metadata complete for all 7 countries")


def test_vat_rates_all_countries():
    """VAT rates are defined for all 7 countries and are non-negative."""
    from crawlers.countries.north_africa.uma_constants import UMA_VAT_RATES, UMA_COUNTRIES
    for code in UMA_COUNTRIES:
        assert code in UMA_VAT_RATES, f"VAT rate missing for {code}"
        assert UMA_VAT_RATES[code] >= 0.0, f"Negative VAT for {code}"
    print("✅ VAT rates defined for all 7 countries")


def test_trade_blocs_all_countries():
    """Trade bloc memberships are defined for all 7 countries."""
    from crawlers.countries.north_africa.uma_constants import UMA_TRADE_BLOCS, UMA_COUNTRIES
    for code in UMA_COUNTRIES:
        assert code in UMA_TRADE_BLOCS, f"Trade blocs missing for {code}"
        assert len(UMA_TRADE_BLOCS[code]) > 0, f"Empty trade blocs for {code}"
    print("✅ Trade blocs defined for all 7 countries")


def test_sector_strengths_all_countries():
    """Sector strengths are defined for all 7 countries."""
    from crawlers.countries.north_africa.uma_constants import UMA_SECTOR_STRENGTHS, UMA_COUNTRIES
    for code in UMA_COUNTRIES:
        assert code in UMA_SECTOR_STRENGTHS, f"Sector strengths missing for {code}"
        assert len(UMA_SECTOR_STRENGTHS[code]) > 0, f"Empty sectors for {code}"
    print("✅ Sector strengths defined for all 7 countries")


def test_multilang_names():
    """Multi-language names include Arabic for all countries."""
    from crawlers.countries.north_africa.uma_constants import MULTILANG_NAMES, UMA_COUNTRIES
    for code in UMA_COUNTRIES:
        names = MULTILANG_NAMES.get(code, {})
        assert "ar" in names, f"Arabic name missing for {code}"
        assert "en" in names, f"English name missing for {code}"
    print("✅ Multi-language names (AR + EN) present for all 7 countries")


# ─────────────────────────────────────────────────────────────────────────────
# 2. Tariff Structures Tests
# ─────────────────────────────────────────────────────────────────────────────

def test_morocco_reference_bands():
    """Morocco tariff bands match the specification."""
    from crawlers.countries.north_africa.tariff_structures import MOROCCO_TARIFFS
    assert MOROCCO_TARIFFS["raw_materials"] == 2.5
    assert MOROCCO_TARIFFS["intermediate_goods"] == 10.0
    assert MOROCCO_TARIFFS["final_goods"] == 25.0
    assert MOROCCO_TARIFFS["agricultural"] == 40.0
    assert MOROCCO_TARIFFS["luxury_goods"] == 45.0
    print("✅ Morocco reference tariff bands correct")


def test_get_country_tariff_profile_all_7():
    """Tariff profiles exist for all 7 countries."""
    from crawlers.countries.north_africa.tariff_structures import get_country_tariff_profile
    for code in ["MAR", "EGY", "TUN", "DZA", "LBY", "SDN", "MRT"]:
        profile = get_country_tariff_profile(code)
        assert profile is not None, f"Profile missing for {code}"
        assert "bands" in profile, f"'bands' missing in {code} profile"
        assert "vat" in profile, f"'vat' missing in {code} profile"
    print("✅ Tariff profiles present for all 7 countries")


def test_get_country_tariff_profile_unknown():
    """get_country_tariff_profile returns None for unknown country."""
    from crawlers.countries.north_africa.tariff_structures import get_country_tariff_profile
    assert get_country_tariff_profile("ZZZ") is None
    print("✅ Unknown country returns None")


def test_get_chapter_rate_agricultural():
    """Chapter 1-24 returns agricultural rate for Morocco."""
    from crawlers.countries.north_africa.tariff_structures import get_chapter_rate
    rate = get_chapter_rate("MAR", 10)   # Chapter 10 = Cereals
    assert rate == 40.0, f"Expected 40.0, got {rate}"
    print("✅ Chapter 10 (cereals) → agricultural rate 40.0% for MAR")


def test_get_chapter_rate_machinery():
    """Chapter 84 returns final_goods rate."""
    from crawlers.countries.north_africa.tariff_structures import get_chapter_rate
    rate = get_chapter_rate("MAR", 84)
    assert rate == 25.0, f"Expected 25.0, got {rate}"
    print("✅ Chapter 84 (machinery) → final_goods rate 25.0% for MAR")


def test_get_chapter_rate_unknown_country():
    """Unknown country returns 0.0."""
    from crawlers.countries.north_africa.tariff_structures import get_chapter_rate
    rate = get_chapter_rate("ZZZ", 84)
    assert rate == 0.0
    print("✅ Unknown country get_chapter_rate → 0.0")


def test_get_regional_tariff_comparison():
    """Regional comparison returns rates for all 7 countries."""
    from crawlers.countries.north_africa.tariff_structures import get_regional_tariff_comparison
    comparison = get_regional_tariff_comparison(84)
    for code in ["MAR", "EGY", "TUN", "DZA", "LBY", "SDN", "MRT"]:
        assert code in comparison, f"{code} missing from comparison"
        assert isinstance(comparison[code], float)
    print("✅ Regional tariff comparison covers all 7 countries")


def test_algeria_higher_than_morocco_intermediates():
    """Algeria intermediate goods rate > Morocco (import substitution)."""
    from crawlers.countries.north_africa.tariff_structures import get_chapter_rate
    mar_rate = get_chapter_rate("MAR", 39)  # Plastics (intermediate)
    dza_rate = get_chapter_rate("DZA", 39)
    assert dza_rate > mar_rate, (
        f"Expected DZA ({dza_rate}) > MAR ({mar_rate}) for intermediates"
    )
    print(f"✅ Algeria ({dza_rate}%) > Morocco ({mar_rate}%) for intermediate goods")


def test_libya_lower_rates_reconstruction():
    """Libya rates are lower than Morocco (reconstruction incentives)."""
    from crawlers.countries.north_africa.tariff_structures import get_chapter_rate
    mar_rate = get_chapter_rate("MAR", 84)  # Machinery (final goods)
    lby_rate = get_chapter_rate("LBY", 84)
    assert lby_rate < mar_rate, (
        f"Expected LBY ({lby_rate}) < MAR ({mar_rate}) for final goods"
    )
    print(f"✅ Libya ({lby_rate}%) < Morocco ({mar_rate}%) for final goods (reconstruction)")


# ─────────────────────────────────────────────────────────────────────────────
# 3. Investment Zones Tests
# ─────────────────────────────────────────────────────────────────────────────

def test_investment_zones_all_countries():
    """Investment zones are defined for all 7 countries."""
    from crawlers.countries.north_africa.investment_zones import get_investment_zones
    for code in ["MAR", "EGY", "TUN", "DZA", "LBY", "SDN", "MRT"]:
        zones = get_investment_zones(code)
        assert isinstance(zones, list), f"{code}: expected list"
        assert len(zones) > 0, f"{code}: no investment zones defined"
    print("✅ Investment zones defined for all 7 countries")


def test_investment_zones_unknown_country():
    """Unknown country returns empty list."""
    from crawlers.countries.north_africa.investment_zones import get_investment_zones
    zones = get_investment_zones("ZZZ")
    assert zones == []
    print("✅ Unknown country → empty zones list")


def test_tangermed_in_morocco_zones():
    """Tanger-Med appears in Morocco zones."""
    from crawlers.countries.north_africa.investment_zones import get_investment_zones
    zones = get_investment_zones("MAR")
    names = [z["name"] for z in zones]
    assert any("Tanger" in n for n in names), f"Tanger-Med not found: {names}"
    print("✅ Tanger-Med present in Morocco investment zones")


def test_sczone_in_egypt_zones():
    """SCZONE appears in Egypt zones."""
    from crawlers.countries.north_africa.investment_zones import get_investment_zones
    zones = get_investment_zones("EGY")
    names = [z["name"] for z in zones]
    assert any("SCZONE" in n or "Suez" in n for n in names), (
        f"SCZONE not found: {names}"
    )
    print("✅ SCZONE present in Egypt investment zones")


def test_zone_schema_fields():
    """Each zone has required schema fields."""
    from crawlers.countries.north_africa.investment_zones import get_all_sez_data
    required_fields = ["name", "type", "location", "incentives", "target_sectors"]
    all_data = get_all_sez_data()
    for country, zones in all_data.items():
        for zone in zones:
            for field in required_fields:
                assert field in zone, f"{country}/{zone.get('name','?')} missing: {field}"
    print("✅ All zone entries have required schema fields")


def test_zone_summary():
    """Zone summary returns expected structure."""
    from crawlers.countries.north_africa.investment_zones import get_zone_summary
    summary = get_zone_summary()
    assert "total_zones" in summary
    assert "operational_zones" in summary
    assert "port_connected_zones" in summary
    assert "by_country" in summary
    assert summary["total_zones"] > 0
    print(f"✅ Zone summary: {summary['total_zones']} total, "
          f"{summary['operational_zones']} operational, "
          f"{summary['port_connected_zones']} port-connected")


# ─────────────────────────────────────────────────────────────────────────────
# 4. Morocco UMA Scraper Tests
# ─────────────────────────────────────────────────────────────────────────────

def test_generate_reference_positions():
    """generate_reference_positions produces 96 chapters (skip 77)."""
    from crawlers.countries.morocco_uma_scraper import generate_reference_positions
    positions = generate_reference_positions()
    assert len(positions) == 96, f"Expected 96, got {len(positions)}"
    print(f"✅ Morocco UMA: {len(positions)} reference positions generated")


def test_reference_position_schema():
    """Each position has required UMA schema fields."""
    from crawlers.countries.morocco_uma_scraper import generate_reference_positions
    positions = generate_reference_positions()
    required = ["code", "designation", "chapter", "taxes", "taxes_detail",
                "country", "trade_bloc", "source"]
    for pos in positions:
        for field in required:
            assert field in pos, f"Position missing field: {field}"
    print("✅ Morocco UMA positions have correct schema")


def test_reference_position_dd_rates():
    """DD rates in positions are non-negative."""
    from crawlers.countries.morocco_uma_scraper import generate_reference_positions
    positions = generate_reference_positions()
    for pos in positions:
        dd = pos["taxes"].get("DD", 0)
        assert dd >= 0, f"Negative DD rate in position {pos['code']}: {dd}"
    print("✅ Morocco UMA: all DD rates non-negative")


def test_build_uma_position():
    """build_uma_position produces correct structure."""
    from crawlers.countries.morocco_uma_scraper import build_uma_position
    pos = build_uma_position(
        code="8704100000",
        designation="Véhicules automobiles pour le transport de marchandises",
        chapter=87,
    )
    assert pos["country"] == "MAR"
    assert pos["trade_bloc"] == "UMA"
    assert "DD" in pos["taxes"]
    assert "TVA" in pos["taxes"]
    assert pos["taxes"]["DD"] == 25.0   # chapter 87 → final_goods band
    assert pos["taxes"]["TVA"] == 20.0  # standard rate for ch 87
    print("✅ build_uma_position produces correct structure for ch 87")


def test_run_scraper_returns_result(tmp_path):
    """run_scraper returns a valid result dict."""
    from crawlers.countries.morocco_uma_scraper import run_scraper
    out = tmp_path / "MAR_test.json"
    result = run_scraper(output_file=str(out))
    assert result["country"] == "MAR"
    assert result["total_positions"] == 96
    assert out.exists()
    print("✅ Morocco UMA scraper produces output file with 96 positions")


# ─────────────────────────────────────────────────────────────────────────────
# 5. UMA Member Scraper Tests
# ─────────────────────────────────────────────────────────────────────────────

def test_uma_country_configs_all_6_derived():
    """COUNTRY_CONFIGS covers the 6 derived countries (not MAR)."""
    from crawlers.countries.uma_member_scraper import COUNTRY_CONFIGS
    expected = {"EGY", "TUN", "DZA", "LBY", "SDN", "MRT"}
    assert expected == set(COUNTRY_CONFIGS.keys()), (
        f"Expected {expected}, got {set(COUNTRY_CONFIGS.keys())}"
    )
    print("✅ UMA member scraper has configs for all 6 derived countries")


def test_build_country_position_egypt():
    """Egypt position derived from Morocco base uses correct factors."""
    from crawlers.countries.uma_member_scraper import build_country_position, COUNTRY_CONFIGS
    # Simulate a Morocco base position for chapter 10 (agricultural)
    mar_pos = {
        "code": "1001100000",
        "designation": "Blé dur",
        "chapter": "10",
    }
    egy_config = COUNTRY_CONFIGS["EGY"]
    pos = build_country_position(mar_pos, egy_config)

    assert pos["country"] == "EGY"
    assert pos["country_name"] == "Egypt"
    # Agricultural factor for EGY = 0.50 → 40 * 0.50 = 20%
    assert pos["taxes"]["DD"] == 20.0, f"Expected 20.0, got {pos['taxes']['DD']}"
    assert "TVA" in pos["taxes"]
    assert pos["taxes"]["TVA"] == 14.0   # Egypt VAT standard
    print("✅ Egypt position derived correctly from Morocco base (agricultural ch10)")


def test_build_country_position_algeria_higher_intermediate():
    """Algeria intermediate goods rate is higher than Morocco base."""
    from crawlers.countries.uma_member_scraper import (
        build_country_position, COUNTRY_CONFIGS, MOROCCO_BASE_BANDS
    )
    mar_pos = {
        "code": "3901100000",
        "designation": "Polyéthylène",
        "chapter": "39",
    }
    dza_config = COUNTRY_CONFIGS["DZA"]
    pos = build_country_position(mar_pos, dza_config)

    # intermediate_goods factor for DZA = 1.50 → 10 * 1.50 = 15%
    assert pos["taxes"]["DD"] == 15.0, f"Expected 15.0, got {pos['taxes']['DD']}"
    print("✅ Algeria plastics (ch39) intermediate rate: 15.0% (vs MAR 10%)")


def test_build_country_position_libya_low():
    """Libya raw materials are zero (reconstruction waiver)."""
    from crawlers.countries.uma_member_scraper import build_country_position, COUNTRY_CONFIGS
    mar_pos = {
        "code": "2601100000",
        "designation": "Minerais de fer",
        "chapter": "26",
    }
    lby_config = COUNTRY_CONFIGS["LBY"]
    pos = build_country_position(mar_pos, lby_config)

    # raw_materials factor for LBY = 0.0 → 2.5 * 0 = 0%
    assert pos["taxes"]["DD"] == 0.0, f"Expected 0.0, got {pos['taxes']['DD']}"
    print("✅ Libya raw materials (ch26) → 0% (reconstruction waiver)")


# ─────────────────────────────────────────────────────────────────────────────
# 6. API Routes Tests
# ─────────────────────────────────────────────────────────────────────────────

def _build_app():
    """Build a minimal FastAPI app with the UMA regions router."""
    from fastapi import FastAPI
    from routes.uma_regions import router
    app = FastAPI()
    app.include_router(router, prefix="/api")
    return app


def test_api_north_africa_countries():
    """GET /api/regions/north-africa/countries returns all 7 countries."""
    from fastapi.testclient import TestClient
    app = _build_app()
    with TestClient(app, raise_server_exceptions=False) as client:
        response = client.get("/api/regions/north-africa/countries")
    assert response.status_code == 200, f"Status {response.status_code}: {response.text}"
    data = response.json()
    assert "countries" in data
    assert data["total_countries"] == 7
    codes = {c["iso3"] for c in data["countries"]}
    assert codes == {"MAR", "EGY", "TUN", "DZA", "LBY", "SDN", "MRT"}
    print("✅ GET /api/regions/north-africa/countries → 7 countries")


def test_api_north_africa_countries_core_only():
    """GET /api/regions/north-africa/countries?include_extended=false returns 4."""
    from fastapi.testclient import TestClient
    app = _build_app()
    with TestClient(app, raise_server_exceptions=False) as client:
        response = client.get(
            "/api/regions/north-africa/countries?include_extended=false"
        )
    assert response.status_code == 200
    data = response.json()
    assert data["total_countries"] == 4
    codes = {c["iso3"] for c in data["countries"]}
    assert codes == {"MAR", "EGY", "TUN", "DZA"}
    print("✅ GET /api/regions/north-africa/countries?include_extended=false → 4 countries")


def test_api_uma_intelligence():
    """GET /api/regions/uma/intelligence returns regional overview."""
    from fastapi.testclient import TestClient
    app = _build_app()
    with TestClient(app, raise_server_exceptions=False) as client:
        response = client.get("/api/regions/uma/intelligence")
    assert response.status_code == 200, f"{response.status_code}: {response.text}"
    data = response.json()
    assert "country_intelligence" in data
    assert "strategic_corridors" in data
    assert "multilanguage_support" in data
    assert "arabic" in data["multilanguage_support"]
    assert len(data["country_intelligence"]) == 7
    print("✅ GET /api/regions/uma/intelligence → full intelligence data")


def test_api_tariffs_country_morocco():
    """GET /api/tariffs/north-africa/MAR returns Morocco tariff profile."""
    from fastapi.testclient import TestClient
    app = _build_app()
    with TestClient(app, raise_server_exceptions=False) as client:
        response = client.get("/api/tariffs/north-africa/MAR")
    assert response.status_code == 200, f"{response.status_code}: {response.text}"
    data = response.json()
    assert data["country"] == "MAR"
    assert "bands" in data
    assert data["bands"]["agricultural"] == 40.0
    print("✅ GET /api/tariffs/north-africa/MAR → Morocco profile")


def test_api_tariffs_country_unknown():
    """GET /api/tariffs/north-africa/XYZ returns 404."""
    from fastapi.testclient import TestClient
    app = _build_app()
    with TestClient(app, raise_server_exceptions=False) as client:
        response = client.get("/api/tariffs/north-africa/XYZ")
    assert response.status_code == 404
    print("✅ GET /api/tariffs/north-africa/XYZ → 404")


def test_api_investment_zones():
    """GET /api/investment/north-africa/zones returns all zones."""
    from fastapi.testclient import TestClient
    app = _build_app()
    with TestClient(app, raise_server_exceptions=False) as client:
        response = client.get("/api/investment/north-africa/zones")
    assert response.status_code == 200, f"{response.status_code}: {response.text}"
    data = response.json()
    assert "zones_by_country" in data
    assert "summary" in data
    assert data["summary"]["total_zones"] > 0
    print(f"✅ GET /api/investment/north-africa/zones → {data['summary']['total_zones']} zones")


def test_api_investment_zones_country():
    """GET /api/investment/north-africa/zones/MAR returns Morocco zones."""
    from fastapi.testclient import TestClient
    app = _build_app()
    with TestClient(app, raise_server_exceptions=False) as client:
        response = client.get("/api/investment/north-africa/zones/MAR")
    assert response.status_code == 200, f"{response.status_code}: {response.text}"
    data = response.json()
    assert data["country"] == "MAR"
    assert data["total_zones"] > 0
    names = [z["name"] for z in data["zones"]]
    assert any("Tanger" in n for n in names)
    print(f"✅ GET /api/investment/north-africa/zones/MAR → {data['total_zones']} zones")


def test_api_trade_agreements():
    """GET /api/trade/north-africa/agreements returns agreements matrix."""
    from fastapi.testclient import TestClient
    app = _build_app()
    with TestClient(app, raise_server_exceptions=False) as client:
        response = client.get("/api/trade/north-africa/agreements")
    assert response.status_code == 200, f"{response.status_code}: {response.text}"
    data = response.json()
    assert "agreements_by_country" in data
    assert "key_multilateral" in data
    for code in ["MAR", "EGY", "TUN", "DZA", "LBY", "SDN", "MRT"]:
        assert code in data["agreements_by_country"], f"{code} missing from agreements"
    print("✅ GET /api/trade/north-africa/agreements → all 7 countries covered")


def test_api_trade_agreements_single_country():
    """GET /api/trade/north-africa/agreements?country_code=EGY returns Egypt."""
    from fastapi.testclient import TestClient
    app = _build_app()
    with TestClient(app, raise_server_exceptions=False) as client:
        response = client.get("/api/trade/north-africa/agreements?country_code=EGY")
    assert response.status_code == 200, f"{response.status_code}: {response.text}"
    data = response.json()
    assert data["country"] == "EGY"
    agreements = data["agreements"]
    names = [a["name"] for a in agreements]
    assert any("COMESA" in n for n in names), f"COMESA not in {names}"
    assert any("QIZ" in n for n in names), f"QIZ not in {names}"
    print("✅ GET /api/trade/north-africa/agreements?country_code=EGY → COMESA + QIZ")


def test_api_regional_summary():
    """GET /api/regions/north-africa/summary returns concise overview."""
    from fastapi.testclient import TestClient
    app = _build_app()
    with TestClient(app, raise_server_exceptions=False) as client:
        response = client.get("/api/regions/north-africa/summary")
    assert response.status_code == 200, f"{response.status_code}: {response.text}"
    data = response.json()
    assert data["total_countries"] == 7
    assert data["combined_gdp_bn_usd"] > 0
    print(f"✅ GET /api/regions/north-africa/summary → GDP ${data['combined_gdp_bn_usd']}B")


def test_api_compare_countries():
    """GET /api/regions/north-africa/compare returns comparison data."""
    from fastapi.testclient import TestClient
    app = _build_app()
    with TestClient(app, raise_server_exceptions=False) as client:
        response = client.get(
            "/api/regions/north-africa/compare?countries=MAR,EGY,TUN&chapter=84"
        )
    assert response.status_code == 200, f"{response.status_code}: {response.text}"
    data = response.json()
    assert "comparison" in data
    for code in ["MAR", "EGY", "TUN"]:
        assert code in data["comparison"]
        assert "indicative_dd_rate_chapter" in data["comparison"][code]
    print("✅ GET /api/regions/north-africa/compare?countries=MAR,EGY,TUN&chapter=84 → OK")


# ─────────────────────────────────────────────────────────────────────────────
# 7. Regional Config Tests
# ─────────────────────────────────────────────────────────────────────────────

def test_regional_config_includes_uma_countries():
    """regional_config.py exports UMA_COUNTRIES with all 7 countries."""
    from config.regional_config import UMA_COUNTRIES, NORTH_AFRICA_EXTENDED
    expected = {"MAR", "DZA", "TUN", "LBY", "MRT", "EGY", "SDN"}
    assert expected == set(UMA_COUNTRIES)
    assert expected == set(NORTH_AFRICA_EXTENDED)
    print("✅ regional_config exports UMA_COUNTRIES with all 7 countries")


def test_regional_config_vat_rates_extended():
    """NORTH_AFRICA_VAT_RATES covers all 7 countries including LBY, SDN, MRT."""
    from config.regional_config import NORTH_AFRICA_VAT_RATES
    for code in ["MAR", "EGY", "TUN", "DZA", "LBY", "SDN", "MRT"]:
        assert code in NORTH_AFRICA_VAT_RATES, f"VAT rate missing for {code}"
    assert NORTH_AFRICA_VAT_RATES["LBY"] == 0.0   # Libya: no VAT
    assert NORTH_AFRICA_VAT_RATES["MAR"] == 20.0
    print("✅ NORTH_AFRICA_VAT_RATES covers all 7 countries")


def test_regional_config_performance_target():
    """Performance target for full region scrape < 30s is present."""
    from config.regional_config import REGIONAL_CONFIG
    targets = REGIONAL_CONFIG["performance_targets"]
    assert "full_region_scrape_s" in targets
    assert targets["full_region_scrape_s"] == 30
    print("✅ Performance target <30s full region scrape defined")


# ─────────────────────────────────────────────────────────────────────────────
# Runner
# ─────────────────────────────────────────────────────────────────────────────

def run_all_tests():
    import inspect
    import traceback
    import tempfile

    tests = [
        (name, obj)
        for name, obj in sorted(globals().items())
        if name.startswith("test_") and callable(obj)
    ]

    passed = 0
    failed = 0

    print("=" * 70)
    print("North Africa (UMA/AMU) Regional Intelligence – Test Suite")
    print("=" * 70)

    for name, func in tests:
        try:
            # Handle tests that need tmp_path
            sig = inspect.signature(func)
            if "tmp_path" in sig.parameters:
                with tempfile.TemporaryDirectory() as td:
                    func(Path(td))
            else:
                func()
            passed += 1
        except Exception as exc:
            print(f"❌ {name}: {exc}")
            traceback.print_exc()
            failed += 1

    print("=" * 70)
    print(f"Results: {passed} passed, {failed} failed out of {passed + failed} tests")
    print("=" * 70)

    return failed == 0


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
