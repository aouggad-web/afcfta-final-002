import os
import sys

import pytest

# Ensure backend directory is on path
_backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _backend_dir not in sys.path:
    sys.path.insert(0, _backend_dir)

from logistics_air_data import calculate_air_freight_cost, get_airport_by_id


def test_enhanced_airport_fields_are_merged():
    airport = get_airport_by_id("ZAF-JNB-001")
    assert airport is not None
    assert "airport_authority" in airport
    assert "logistics_network" in airport


def test_calculate_air_freight_cost_returns_breakdown():
    result = calculate_air_freight_cost(
        origin_airport_id="ZAF-JNB-001",
        destination_airport_id="KEN-NBO-001",
        weight_kg=1200,
        service_level="standard",
        cargo_type="general",
    )

    assert result is not None
    assert result["distance_km"] > 0
    assert result["chargeable_weight_kg"] == 1200
    assert result["cost_breakdown_usd"]["total_cost_usd"] > 0
    assert result["cost_breakdown_usd"]["freight_base_usd"] > 0


def test_calculate_air_freight_cost_uses_volumetric_weight_when_higher():
    result = calculate_air_freight_cost(
        origin_airport_id="ZAF-JNB-001",
        destination_airport_id="KEN-NBO-001",
        weight_kg=100,
        volume_m3=2.0,  # volumetric = 334 kg
        service_level="standard",
        cargo_type="general",
    )

    assert result["volumetric_weight_kg"] == 334
    assert result["chargeable_weight_kg"] == 334


def test_calculate_air_freight_cost_rejects_invalid_service_level():
    with pytest.raises(ValueError, match="Invalid service_level"):
        calculate_air_freight_cost(
            origin_airport_id="ZAF-JNB-001",
            destination_airport_id="KEN-NBO-001",
            weight_kg=100,
            service_level="ultra",
            cargo_type="general",
        )
