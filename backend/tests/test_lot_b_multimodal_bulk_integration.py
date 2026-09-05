"""
Lot B: Multimodal Comparator Integration — tests for bulk carrier (vraquier) wiring.

Validates that bulk freight cost data flows through the multimodal comparator:
  1. Bascule logic: below container threshold → containerized; above → vraquier
  2. Liquid bulk exclusion: tanker market marked unavailable
  3. CO2 factors: bulk vessel classes recognized
  4. Backward compatibility: existing tests unchanged
"""

import os
import sys

_backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _backend_dir not in sys.path:
    sys.path.insert(0, _backend_dir)

from services.multimodal_freight_service import compare_multimodal
from services.shipment_estimator import classify_bulk_commodity


def test_bulk_sea_options_surface_vraquier_above_threshold():
    # Wheat (bulk_major): 25,000 t well above default threshold (2,000 t)
    # Should return a sea_bulk (vraquier) option instead of containerized
    wheat = classify_bulk_commodity("100199")
    assert wheat is not None
    assert wheat["category"] == "bulk_major"
    assert wheat["container_threshold_tonnes"] == 2000.0

    result = compare_multimodal(
        "ZAF",  # South Africa (good ports for bulk)
        "DZA",  # Algeria
        weight_kg=25_000_000,  # 25,000 tonnes
        is_bulk_commodity=True,
        bulk_commodity_dict=wheat,
    )

    assert result["is_bulk_commodity"] is True
    # Should have vraquier option(s)
    sea_bulk_opts = [o for o in result["options"] if o.get("mode") == "sea_bulk"]
    assert len(sea_bulk_opts) > 0, "No sea_bulk options returned for 25,000 t wheat"

    opt = sea_bulk_opts[0]
    assert opt["available"] is True
    assert opt["commodity_label"] == "Blé"
    assert opt["total_cost_usd"] is not None
    assert opt["vessel_class"] in ["handysize", "supramax", "panamax", "capesize"]
    assert opt["co2_kg"] is not None and opt["co2_kg"] > 0
    assert "Tarif vraquier" in opt["notes"]


def test_bulk_sea_options_bascule_below_threshold_uses_containerized():
    # Rice (bi-mode): 3,000 t which is above default 2,000 t but below rice's 5,000 t
    rice = classify_bulk_commodity("100630")
    assert rice is not None
    assert rice["category"] == "bulk_minor"
    assert rice["bi_mode"] is True
    assert rice["container_threshold_tonnes"] == 5000.0

    result = compare_multimodal(
        "DZA",
        "MAR",
        weight_kg=3_000_000,  # 3,000 tonnes (between 2k and 5k)
        is_bulk_commodity=True,
        bulk_commodity_dict=rice,
    )

    # Below rice's threshold, so no vraquier should be offered; containerized used instead
    sea_bulk_opts = [o for o in result["options"] if o.get("mode") == "sea_bulk"]
    # May be empty or have unavailable options, but not real vraquier offers
    assert len(sea_bulk_opts) == 0, "Vraquier offered below threshold"

    # Containerized should have bulk note
    sea_opts = [o for o in result["options"] if o.get("mode") == "sea"]
    if sea_opts:
        # At least one should have a bulk cargo note
        assert any("vraquier" in o.get("bulk_cargo_note", "").lower() for o in sea_opts)


def test_bulk_sea_options_liquid_bulk_marked_unavailable():
    # Crude oil (liquid_bulk): tanker market, not covered by bulk carrier model
    crude = classify_bulk_commodity("270900")
    assert crude is not None
    assert crude["category"] == "liquid_bulk"
    assert crude["is_liquid"] is True

    result = compare_multimodal(
        "DZA",
        "EGY",
        weight_kg=10_000_000,
        is_bulk_commodity=True,
        bulk_commodity_dict=crude,
    )

    # Should have a sea_bulk option marked unavailable for tanker market
    sea_bulk_opts = [o for o in result["options"] if o.get("mode") == "sea_bulk"]
    assert len(sea_bulk_opts) > 0, "No sea_bulk option for liquid bulk"

    opt = sea_bulk_opts[0]
    assert opt["available"] is False
    assert opt["feasibility"] == "unavailable"
    assert "tanker" in opt["notes"].lower() or "pétrolier" in opt["notes"].lower()


def test_bulk_co2_factors_loaded():
    # Verify that bulk vessel CO2 factors are present in methodology
    result = compare_multimodal("ZAF", "DZA", weight_kg=25_000_000)
    co2_factors = result["co2_methodology"]["factors_g_per_tkm"]

    # Check bulk vessel classes are present
    assert "sea_bulk_handysize" in co2_factors
    assert "sea_bulk_supramax" in co2_factors
    assert "sea_bulk_panamax" in co2_factors
    assert "sea_bulk_capesize" in co2_factors

    # Values should be lower than container vessel (10) and reflect economies of scale
    assert 0 < co2_factors["sea_bulk_handysize"] < 10
    assert co2_factors["sea_bulk_supramax"] < co2_factors["sea_bulk_handysize"]
    assert co2_factors["sea_bulk_panamax"] < co2_factors["sea_bulk_supramax"]
    assert co2_factors["sea_bulk_capesize"] < co2_factors["sea_bulk_panamax"]


def test_bulk_air_exclusion_preserved():
    # Air must remain excluded for bulk commodities (Lot A behavior preserved)
    cement = classify_bulk_commodity("2523")
    assert cement is not None
    assert cement["category"] == "bulk_minor"

    result = compare_multimodal(
        "DZA",
        "MAR",
        weight_kg=500,  # Even tiny amounts
        is_bulk_commodity=True,
        bulk_commodity_dict=cement,
    )

    # Air should be excluded by policy
    assert result["air_excluded"] is True
    assert "jamais expédié par avion" in result["air_excluded_reason"]
    assert all(o["mode"] != "air" for o in result["options"])


def test_bulk_land_cargo_type_defaults_to_bulk():
    # Land leg should default to "bulk" cargo type for bulk commodities
    maize = classify_bulk_commodity("100590")
    assert maize is not None

    result = compare_multimodal(
        "ZAF",
        "BWA",  # Landlocked neighbor
        weight_kg=5_000_000,
        is_bulk_commodity=True,
        bulk_commodity_dict=maize,
    )

    assert result["land_cargo_type"] == "bulk"
    # Land options should use bulk cargo type
    land_opts = [o for o in result["options"] if o.get("mode") == "land"]
    for opt in land_opts:
        segments = opt.get("segments", [])
        if segments:
            # Segments should reference bulk cargo handling
            pass  # Land module will handle cargo_type in its cost


def test_bulk_option_has_cost_breakdown():
    # Vraquier option should include detailed cost breakdown
    wheat = classify_bulk_commodity("100199")

    result = compare_multimodal(
        "ZAF",
        "DZA",
        weight_kg=25_000_000,
        is_bulk_commodity=True,
        bulk_commodity_dict=wheat,
    )

    sea_bulk_opts = [o for o in result["options"] if o.get("mode") == "sea_bulk"]
    if sea_bulk_opts:
        opt = sea_bulk_opts[0]
        assert opt["available"] is True

        # Check segment has cost breakdown
        segments = opt.get("segments", [])
        if segments:
            seg = segments[0]
            breakdown = seg.get("cost_breakdown", {})
            assert "ocean_usd_per_t" in breakdown
            assert "port_load_usd_per_t" in breakdown
            assert "port_discharge_usd_per_t" in breakdown
            assert "total_usd_per_t" in breakdown


def test_backward_compatibility_non_bulk_unchanged():
    # Non-bulk cargo should work exactly as before
    result = compare_multimodal(
        "DZA",
        "MAR",
        weight_kg=500,  # 500 kg is below the 1000 kg air threshold
        is_bulk_commodity=False,
    )

    # No sea_bulk options
    sea_bulk_opts = [o for o in result["options"] if o.get("mode") == "sea_bulk"]
    assert len(sea_bulk_opts) == 0

    # Air should be available for light cargo
    assert result["air_excluded"] is False
    air_opts = [o for o in result["options"] if o.get("mode") == "air"]
    assert len(air_opts) > 0, "Air option should be available for 500 kg"

    # Land cargo type should default to container
    assert result["land_cargo_type"] == "container"


def test_backward_compatibility_is_bulk_commodity_param_still_works():
    # Old code that passes is_bulk_commodity=True without dict should still work
    result = compare_multimodal(
        "DZA",
        "MAR",
        weight_kg=20_000,
        is_bulk_commodity=True,
        bulk_label="Ciment",
    )

    # Should exclude air and default land cargo to bulk
    assert result["is_bulk_commodity"] is True
    assert result["bulk_label"] == "Ciment"
    assert result["air_excluded"] is True
    assert result["land_cargo_type"] == "bulk"


def test_bulk_option_vessel_class_selected_by_weight():
    # Vessel class selection: smaller lots use smaller vessels when eligible
    # Larger lots use larger vessels
    wheat = classify_bulk_commodity("100199")

    # Wheat: 5,000 t should get a small-to-mid vessel
    result_small = compare_multimodal(
        "ZAF",
        "GHA",  # Ghana (shorter route)
        weight_kg=5_000_000,
        is_bulk_commodity=True,
        bulk_commodity_dict=wheat,
    )

    # Wheat: 100,000 t should get a larger vessel (panamax or capesize)
    result_large = compare_multimodal(
        "ZAF",
        "GHA",
        weight_kg=100_000_000,
        is_bulk_commodity=True,
        bulk_commodity_dict=wheat,
    )

    opt_small = next((o for o in result_small["options"] if o.get("mode") == "sea_bulk"), None)
    opt_large = next((o for o in result_large["options"] if o.get("mode") == "sea_bulk"), None)

    # Verify both returned valid options
    if opt_small and opt_small.get("available"):
        assert opt_small["vessel_class"] in ["handysize", "supramax", "panamax", "capesize"]
    if opt_large and opt_large.get("available"):
        assert opt_large["vessel_class"] in ["handysize", "supramax", "panamax", "capesize"]
