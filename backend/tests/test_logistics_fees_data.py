import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from logistics_fees_data import (  # noqa: E402
    PORT_THC,
    SHIPPING_ROUTES,
    get_route_between,
    get_total_cost,
)


def test_all_shipping_route_ports_have_thc_data():
    """Every route endpoint should have THC data on both ends for total-cost calculations."""
    missing = []

    for route in SHIPPING_ROUTES:
        for locode in (route["origin_locode"], route["destination_locode"]):
            if locode not in PORT_THC:
                missing.append((route["route_id"], locode))

    assert missing == []


def test_audit_added_routes_are_available():
    """Recently added corridor coverage should be present in the maritime fee dataset."""
    expected_route_ids = {
        "MACAS-SNDKR",
        "MACAS-GHTEM",
        "EGALY-KEMBA",
        "EGALY-TZDAR",
        "SNDKR-CMDLA",
        "CIABJ-CMDLA",
        "GHTEM-CMDLA",
        "CMDLA-AOLAD",
        "DJJIB-TZDAR",
        "TZDAR-ZADUR",
        "MZMPM-ZACPT",
        "MUPLU-ZADUR",
    }

    route_ids = {route["route_id"] for route in SHIPPING_ROUTES}
    assert expected_route_ids.issubset(route_ids)


def test_reverse_route_uses_symmetric_pricing():
    """Reverse lookups should remain available for newly audited corridors."""
    reverse_route = get_route_between("SNDKR", "MACAS")

    assert reverse_route is not None
    assert reverse_route["route_id"] == "MACAS-SNDKR_REV"
    assert reverse_route["origin_port"] == "Dakar"
    assert reverse_route["destination_port"] == "Casablanca"
    assert reverse_route["teu_usd"] == 510


def test_total_cost_breakdown_for_new_route():
    """Total cost should include ocean freight plus THC at both route endpoints."""
    result = get_total_cost("TZDAR", "ZADUR", "feu_hc")

    assert result is not None
    assert result["route_id"] == "TZDAR-ZADUR"
    assert result["ocean_freight_usd"] == 907
    assert result["origin_thc_usd"] == PORT_THC["TZDAR"]["feu_hc_usd"]
    assert result["destination_thc_usd"] == PORT_THC["ZADUR"]["feu_hc_usd"]
    assert (
        result["total_cost_usd"]
        == 907 + PORT_THC["TZDAR"]["feu_hc_usd"] + PORT_THC["ZADUR"]["feu_hc_usd"]
    )
