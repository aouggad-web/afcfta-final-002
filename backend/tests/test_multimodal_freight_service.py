import os
import sys

_backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _backend_dir not in sys.path:
    sys.path.insert(0, _backend_dir)

from services import multimodal_freight_service as service


def test_compare_multimodal_tags_options_and_computes_roi(monkeypatch):
    monkeypatch.setattr(
        service,
        "_sea_options",
        lambda *args, **kwargs: [
            {
                "label": "Sea Direct",
                "mode": "sea",
                "total_cost_usd": 500,
                "co2_kg": 100,
                "transit_days_min": 8,
                "transit_days_max": 10,
            }
        ],
    )
    monkeypatch.setattr(
        service,
        "_air_option",
        lambda *args, **kwargs: {
            "label": "Air Direct",
            "mode": "air",
            "total_cost_usd": 900,
            "co2_kg": 600,
            "transit_days_min": 1,
            "transit_days_max": 2,
        },
    )
    monkeypatch.setattr(
        service,
        "_land_option",
        lambda *args, **kwargs: [
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
        ],
    )
    monkeypatch.setattr(service, "_rail_then_road_option", lambda *args, **kwargs: [])
    monkeypatch.setattr(
        service,
        "_sea_then_land_option",
        lambda *args, **kwargs: [
            {
                "label": "Rail Future",
                "mode": "rail",
                "total_cost_usd": 320,
                "co2_kg": 40,
                "transit_days_min": 3,
                "transit_days_max": 4,
                "is_future": True,
                "status": "En construction",
                "phase": "under_construction",
            }
        ],
    )

    # Weight below AIR_FREIGHT_MAX_KG_GENERAL so the (mocked) air option stays
    # eligible — heavier shipments are policy-excluded from air entirely.
    result = service.compare_multimodal("MAR", "MLI", weight_kg=900, include_future=True)

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
    assert roi["per_shipment"]["time_savings_days"] == round(
        roi["reference_operational"]["transit_days_avg"]
        - roi["best_future_time"]["transit_days_avg"],
        1,
    )
    assert roi["per_shipment"]["cost_savings_usd"] == 150
    assert roi["per_shipment"]["co2_savings_kg"] == 40
    assert roi["per_shipment"]["time_savings_days"] == 3.5
    assert roi["per_shipment"]["cost_savings_vs_air_usd"] == 600


def test_compare_multimodal_excludes_future_when_requested(monkeypatch):
    monkeypatch.setattr(
        service,
        "_sea_options",
        lambda *args, **kwargs: [
            {
                "label": "Sea Direct",
                "mode": "sea",
                "total_cost_usd": 500,
                "co2_kg": 100,
                "transit_days_min": 8,
                "transit_days_max": 10,
            }
        ],
    )
    monkeypatch.setattr(service, "_air_option", lambda *args, **kwargs: None)
    monkeypatch.setattr(
        service,
        "_land_option",
        lambda *args, **kwargs: [
            {
                "label": "Land Future",
                "mode": "road",
                "total_cost_usd": 300,
                "co2_kg": 60,
                "transit_days_min": 4,
                "transit_days_max": 5,
                "is_future": True,
                "status": "Planifié",
                "phase": "planned",
            }
        ],
    )
    monkeypatch.setattr(service, "_rail_then_road_option", lambda *args, **kwargs: [])
    monkeypatch.setattr(service, "_sea_then_land_option", lambda *args, **kwargs: [])

    result = service.compare_multimodal("MAR", "MLI", weight_kg=10_000, include_future=False)

    assert result["options_count"] == 1
    assert result["operational_count"] == 1
    assert result["future_count"] == 0
    assert result["roi_infrastructure"] is None
    assert all(not option.get("is_future") for option in result["options"])


def test_country_ports_derived_from_maritime_registry():
    for iso in ["TGO", "BEN", "GAB", "COD", "MDG", "MRT", "GIN", "SLE", "LBR", "GNQ", "COM", "SYC"]:
        assert service.COUNTRY_PORTS.get(iso), f"{iso} should map to at least one port"

    assert service.COUNTRY_DEFAULT_PORT["LBY"].startswith("LY")

    assert set(service.COUNTRY_DEFAULT_PORT) == set(service.COUNTRY_PORTS)
    for iso, ports in service.COUNTRY_PORTS.items():
        assert service.COUNTRY_DEFAULT_PORT[iso] == ports[0]


def test_sea_options_returns_list_for_coastal_pair():
    opts = service._sea_options("TGO", "NGA", weight_kg=20_000, container_type="teu")
    assert isinstance(opts, list) and len(opts) >= 1
    assert all(o["mode"] == "sea" for o in opts)
    assert all(o.get("origin_locode") and o.get("destination_locode") for o in opts)

    assert service._sea_options("MAR", "MLI", weight_kg=20_000, container_type="teu") == []


def test_land_carriers_fallback_matches_trucking_and_rail_operators():
    # Fallback path: trucking companies by africa_presence intersection.
    road = service._land_carriers(["CIV", "GHA", "NGA"], "road")
    assert road, "road corridor should surface trucking companies"
    assert all(isinstance(name, str) for name in road)
    assert len(road) <= 5

    # Fallback rail matching uses country_iso ...
    assert any("ONCF" in name for name in service._land_carriers(["MAR"], "rail"))
    # ... and the transnational `countries` field (e.g. TAZARA spans TZA/ZMB).
    assert any("TAZARA" in name for name in service._land_carriers(["TZA", "ZMB"], "rail"))
    assert any(
        "SITARAIL" in name.upper() for name in service._land_carriers(["CIV", "BFA"], "rail")
    )

    assert service._land_carriers([], "road") == []


def test_options_expose_exact_corridor_operators():
    # Sea direct option carries shipping lines (from the maritime route matrix).
    sea_opts = service._sea_options("TGO", "NGA", weight_kg=20_000, container_type="teu")
    assert sea_opts and sea_opts[0].get("carriers"), "sea option must list carriers"

    # Land-only option uses the exact corridor operator, not a broad country match.
    lome_ouaga = service._land_option("TGO", "BFA", weight_tonnes=20.0)
    assert lome_ouaga and any(
        "ASKY Logistics" in (o.get("carriers") or []) for o in lome_ouaga
    ), "Lomé-Ouagadougou corridor must surface its exact operator"

    # Multimodal (sea + land) aggregates shipping lines + the exact corridor operator.
    result = service.compare_multimodal("MAR", "MLI", weight_kg=20_000)
    multimodal = [o for o in result["options"] if o["mode"] == "multimodal"]
    assert multimodal, "MAR->MLI should yield a multimodal option"
    assert multimodal[0].get("carriers"), "multimodal option must aggregate carriers"
    land_seg = [s for s in multimodal[0]["segments"] if s["mode"] in ("road", "rail", "multimodal")]
    assert land_seg, "multimodal option must have a land leg"
    assert "Transrail" in (
        land_seg[0].get("carriers") or []
    ), "Dakar-Bamako land leg must surface its exact rail operator (Transrail)"


def test_land_then_sea_option_is_symmetric_to_sea_then_land():
    # _sea_then_land_option only ever handled landlocked DESTINATIONS. Without
    # its mirror, a landlocked ORIGIN (e.g. Ethiopia exporting) had no
    # land+sea route at all — only air and often-nonoperational direct land
    # corridors, systematically overpricing landlocked-country exports.
    opts = service._land_then_sea_option(
        "ETH", "KEN", weight_kg=12_500, container_type="teu", weight_tonnes=12.5
    )
    assert opts, "landlocked origin ETH must yield a land+sea option via its Djibouti gateway"
    assert all(o["mode"] == "multimodal" for o in opts)
    assert any(o.get("via_country") == "DJI" for o in opts)
    rail_opt = next(o for o in opts if o.get("corridor_mode") == "rail")
    assert rail_opt["available"] is True
    assert rail_opt["total_cost_usd"] > 0
    seg_modes = [s["mode"] for s in rail_opt["segments"]]
    assert seg_modes == ["rail", "sea"], "land leg must come first, then the sea leg to destination"


def test_landlocked_origin_ethiopia_prefers_real_corridor_over_air():
    # Regression for the reported bug: $50k of coffee (ETH, landlocked) was
    # recommended via air freight because no rail/road+sea route existed in
    # the corridor registry for Ethiopia at all.
    #
    # A 12.5 t shipment also exceeds AIR_FREIGHT_MAX_KG_GENERAL (air freight is
    # only realistic below ~1000 kg for general cargo) — so air is now
    # excluded outright rather than merely losing on cost, which is a
    # stronger version of the same fix (see test_multimodal_air_freight_realism.py).
    result = service.compare_multimodal("ETH", "KEN", weight_kg=12_500, container_type="teu")
    multimodal = [o for o in result["options"] if o["mode"] == "multimodal" and o["available"]]
    air = next((o for o in result["options"] if o["mode"] == "air"), None)
    assert multimodal, "Ethiopia (landlocked) must have at least one operational multimodal route"
    assert air is None, "12.5 t exceeds the realistic air-freight weight ceiling"
    assert result.get("options_count", 0) >= 1
    cheapest_overall = min(
        (o for o in result["options"] if o["available"]), key=lambda o: o["total_cost_usd"]
    )
    assert cheapest_overall["mode"] == "multimodal", "rail+sea via Djibouti must beat air on cost"
