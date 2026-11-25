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
    assert reverse_route["teu_usd"] == get_route_between("MACAS", "SNDKR")["teu_usd"]


def test_total_cost_breakdown_for_new_route():
    """Total cost should include ocean freight plus THC at both route endpoints."""
    result = get_total_cost("TZDAR", "ZADUR", "feu_hc")

    assert result is not None
    assert result["route_id"] == "TZDAR-ZADUR"
    freight = get_route_between("TZDAR", "ZADUR")["feu_hc_usd"]
    assert result["ocean_freight_usd"] == freight
    assert result["origin_thc_usd"] == PORT_THC["TZDAR"]["feu_hc_usd"]
    assert result["destination_thc_usd"] == PORT_THC["ZADUR"]["feu_hc_usd"]
    assert (
        result["total_cost_usd"]
        == freight + PORT_THC["TZDAR"]["feu_hc_usd"] + PORT_THC["ZADUR"]["feu_hc_usd"]
    )


# ------------------------------------------------------------------
# Calibrage 2026 sur des devis réels
# ------------------------------------------------------------------
def test_short_sea_to_algiers_matches_marseille_quote():
    """Tanger Med→Alger (447 milles) ≈ Marseille→Alger (434 milles) : 1 200 USD/20'
    fret + surcharges selon les professionnels (2026)."""
    teu = get_route_between("MAPTM", "DZALG")["teu_usd"]
    assert 1100 <= teu <= 1300


def test_douala_algiers_is_transshipped_and_dearer_than_short_sea():
    """Douala→Alger n'a pas de service direct : transbordement, donc nettement
    plus cher que Marseille→Alger (1 200 USD)."""
    route = get_route_between("CMDLA", "DZALG")
    assert route["transshipment"] is not None
    assert route["transshipment"]["hub_locode"] == "MAPTM"
    assert route["teu_usd"] >= 1200 * 1.5
    direct = get_route_between("MAPTM", "DZALG")
    assert route["transit_days_min"] > direct["transit_days_max"]


def test_benchmarks_routed_via_a_hub_carry_transshipment_metadata():
    """Les benchmarks publiés « via hub » gardent le hub dans la réponse."""
    hubs = [o["hub_locode"] for o in get_route_between("TNRAD", "KEMBA")["transshipment"]["options"]]
    assert "EGPSD" in hubs
    assert get_route_between("NGAPP", "DZALG")["transshipment"]["hub_locode"] == "MAPTM"
    assert get_route_between("MAPTM", "SNDKR")["transshipment"] is None


def test_transshipment_offers_mediterranean_hubs_and_their_carriers():
    """Douala→Alger : plusieurs hubs possibles (Tanger Med, Valence, Gênes, Malte…),
    chacun avec ses compagnies, du moins cher au plus cher."""
    result = get_total_cost("CMDLA", "DZALG", "teu")
    options = result["transshipment_options"]
    hubs = [o["hub_locode"] for o in options]
    assert {"MAPTM", "ESALG", "ESVLC", "ITGOA", "MTMAR"} <= set(hubs)
    prices = [o["ocean_freight_usd"] for o in options]
    assert prices == sorted(prices) and prices[0] == result["ocean_freight_usd"]
    assert next(o for o in options if o["hub_locode"] == "MTMAR")["carriers"] == ["CMA CGM"]
    assert {"Hapag-Lloyd", "COSCO"} <= set(result["carriers"])


def test_option_freight_excludes_the_separately_reported_imdg_surcharge():
    dg = get_total_cost("CMDLA", "DZALG", "teu", dangerous=True)
    assert dg["transshipment_options"][0]["ocean_freight_usd"] == dg["ocean_freight_usd"]


def test_benchmark_options_are_anchored_on_the_benchmark_rate():
    route = get_route_between("NGAPP", "DZALG")
    options = route["transshipment"]["options"]
    assert options[0]["teu_usd"] == route["teu_usd"]
    assert all(o["teu_usd"] >= route["teu_usd"] for o in options)


def test_reverse_route_swaps_option_legs():
    out = get_route_between("CMDLA", "DZALG")["transshipment"]["options"][0]
    back = get_route_between("DZALG", "CMDLA")["transshipment"]["options"][0]
    assert (out["leg1_nm"], out["leg2_nm"]) == (back["leg2_nm"], back["leg1_nm"])


def test_algeria_import_premium_is_directional():
    """La prime marché Algérie s'applique à l'import, pas à l'export."""
    imp = get_route_between("CMDLA", "DZALG")
    exp = get_route_between("DZALG", "CMDLA")
    assert imp["market_factor"] == 1.18 and exp["market_factor"] == 1.0
    assert imp["teu_usd"] > exp["teu_usd"]


def test_benchmarks_keep_2024_published_rates_for_traceability():
    route = get_route_between("MACAS", "SNDKR")
    assert route["rate_basis"] == "benchmark_actualise"
    assert route["published_2024"]["teu_usd"] == 510
    assert route["teu_usd"] > 510


def test_new_algerian_ports_are_covered():
    for locode in ("DZDJE", "DZMOS", "DZAAE", "DZSKI"):
        assert locode in PORT_THC
        assert get_total_cost("CMDLA", locode, "teu") is not None


def test_reefer_and_dangerous_goods_cost_more():
    dry = get_total_cost("CMDLA", "DZALG", "teu")
    reefer = get_total_cost("CMDLA", "DZALG", "teu_rf")
    dg = get_total_cost("CMDLA", "DZALG", "teu", dangerous=True)
    assert reefer["ocean_freight_usd"] > dry["ocean_freight_usd"]
    assert reefer["origin_thc_usd"] > dry["origin_thc_usd"]
    assert dg["dg_surcharge_usd"] > 0
    assert dg["total_cost_usd"] > dry["total_cost_usd"]
    assert get_total_cost("CMDLA", "DZALG", "feu_rf")["ocean_freight_usd"] > reefer[
        "ocean_freight_usd"
    ]
