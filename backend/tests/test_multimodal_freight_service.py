import os
import sys


_backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _backend_dir not in sys.path:
    sys.path.insert(0, _backend_dir)

from services import multimodal_freight_service as service


def test_compare_multimodal_tags_options_and_computes_roi(monkeypatch):
    monkeypatch.setattr(service, "_sea_option", lambda *args, **kwargs: {
        "label": "Sea Direct",
        "mode": "sea",
        "total_cost_usd": 500,
        "co2_kg": 100,
        "transit_days_min": 8,
        "transit_days_max": 10,
    })
    monkeypatch.setattr(service, "_air_option", lambda *args, **kwargs: {
        "label": "Air Direct",
        "mode": "air",
        "total_cost_usd": 900,
        "co2_kg": 600,
        "transit_days_min": 1,
        "transit_days_max": 2,
    })
    monkeypatch.setattr(service, "_land_option", lambda *args, **kwargs: [
        {
            "label": "Land Operational",
            "mode": "road",
            "total_cost_usd": 450,
            "co2_kg": 80,
            "transit_days_min": 6,
            "transit_days_max": 8,
        },
        {
            "label": "Land Future",
            "mode": "multimodal",
            "total_cost_usd": 300,
            "co2_kg": 60,
            "transit_days_min": 4,
            "transit_days_max": 5,
            "is_future": True,
            "status": "Planifié",
            "phase": "planned",
        },
    ])
    monkeypatch.setattr(service, "_rail_then_road_option", lambda *args, **kwargs: [])
    monkeypatch.setattr(service, "_sea_then_land_option", lambda *args, **kwargs: [{
        "label": "Rail Future",
        "mode": "rail",
        "total_cost_usd": 320,
        "co2_kg": 40,
        "transit_days_min": 3,
        "transit_days_max": 4,
        "is_future": True,
        "status": "En construction",
        "phase": "under_construction",
    }])

    result = service.compare_multimodal("MAR", "MLI", weight_kg=10_000, include_future=True)

    assert result["options_count"] == 5
    assert result["operational_count"] == 3
    assert result["future_count"] == 2

    options_by_label = {option["label"]: option for option in result["options"]}
    assert options_by_label["Land Operational"]["is_cheapest"] is True
    assert options_by_label["Air Direct"]["is_fastest"] is True
    assert options_by_label["Land Operational"]["is_greenest"] is True
    assert options_by_label["Land Future"]["is_future_cheapest"] is True
    assert options_by_label["Rail Future"]["is_future_greenest"] is True

    roi = result["roi_infrastructure"]
    assert roi["reference_operational"]["label"] == "Land Operational"
    assert (
        roi["per_shipment"]["cost_savings_usd"]
        == roi["reference_operational"]["cost_usd"] - roi["best_future_cost"]["cost_usd"]
    )
    assert (
        roi["per_shipment"]["co2_savings_kg"]
        == roi["reference_operational"]["co2_kg"] - roi["best_future_co2"]["co2_kg"]
    )
    assert (
        roi["per_shipment"]["time_savings_days"]
        == round(
            roi["reference_operational"]["transit_days_avg"] - roi["best_future_time"]["transit_days_avg"], 1,
        )
    )
    assert roi["per_shipment"]["cost_savings_usd"] == 150
    assert roi["per_shipment"]["co2_savings_kg"] == 40
    assert roi["per_shipment"]["time_savings_days"] == 3.5
    assert roi["per_shipment"]["cost_savings_vs_air_usd"] == 600


def test_compare_multimodal_excludes_future_when_requested(monkeypatch):
    monkeypatch.setattr(service, "_sea_option", lambda *args, **kwargs: {
        "label": "Sea Direct",
        "mode": "sea",
        "total_cost_usd": 500,
        "co2_kg": 100,
        "transit_days_min": 8,
        "transit_days_max": 10,
    })
    monkeypatch.setattr(service, "_air_option", lambda *args, **kwargs: None)
    monkeypatch.setattr(service, "_land_option", lambda *args, **kwargs: [{
        "label": "Land Future",
        "mode": "road",
        "total_cost_usd": 300,
        "co2_kg": 60,
        "transit_days_min": 4,
        "transit_days_max": 5,
        "is_future": True,
        "status": "Planifié",
        "phase": "planned",
    }])
    monkeypatch.setattr(service, "_rail_then_road_option", lambda *args, **kwargs: [])
    monkeypatch.setattr(service, "_sea_then_land_option", lambda *args, **kwargs: [])

    result = service.compare_multimodal("MAR", "MLI", weight_kg=10_000, include_future=False)

    assert result["options_count"] == 1
    assert result["operational_count"] == 1
    assert result["future_count"] == 0
    assert result["roi_infrastructure"] is None
    assert all(not option.get("is_future") for option in result["options"])
