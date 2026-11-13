"""
Anomalies du comparateur multimodal constatées sur les engrais azotés algériens
(urée 310210, ammoniac 281410) — un test par cas.

1. Vrac liquide : le marqueur « tanker » indisponible ne doit pas déclasser les
   options conteneur.
2. Frontière fermée (Maghnia DZA-MAR) : le corridor Trans-Maghreb n'est pas
   opérationnel pour cette paire.
3. Distances/jambes : un corridor n'est facturé que sur le tronçon de la paire ;
   une dérivation partant de Tamanrasset n'est pas une route depuis l'Algérie.
4. Passerelles : Cotonou-Niamey proposé pour le Niger ; Malawi via Nacala.
"""

import contextlib
import io
import os
import sys

_backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _backend_dir not in sys.path:
    sys.path.insert(0, _backend_dir)

from services import multimodal_freight_service as service
from services.shipment_estimator import classify_bulk_commodity

AMMONIA = classify_bulk_commodity("281410")
UREA = classify_bulk_commodity("310210")
FEU_KG = 26_400.0


def _compare(origin, dest, weight_kg=FEU_KG, bulk=None, **kw):
    with contextlib.redirect_stdout(io.StringIO()):
        return service.compare_multimodal(
            origin,
            dest,
            weight_kg,
            container_type="feu",
            is_bulk_commodity=bool(bulk),
            bulk_commodity_dict=bulk,
            **kw,
        )


def _operational(result):
    return [o for o in result["options"] if o.get("available") and not o.get("is_future")]


# ── 1. Vrac liquide ─────────────────────────────────────────────────────────
def test_liquid_below_threshold_keeps_container_operational():
    assert AMMONIA["is_liquid"] and AMMONIA["container_threshold_tonnes"] == 2000.0
    res = _compare("DZA", "ZAF", bulk=AMMONIA)
    sea = [o for o in res["options"] if o["mode"] == "sea"]
    assert sea and all(o["available"] for o in sea)
    assert not any(o["mode"] == "sea_bulk" for o in res["options"])
    assert res["operational_count"] >= 1


def test_liquid_below_threshold_mar_keeps_sea_and_land():
    res = _compare("DZA", "MAR", bulk=AMMONIA)
    modes = {o["mode"] for o in _operational(res)}
    assert "sea" in modes


def test_liquid_above_threshold_states_tanker_unavailable_without_demoting():
    res = _compare("DZA", "ZAF", weight_kg=5_000_000, bulk=AMMONIA)
    tanker = [o for o in res["options"] if o["mode"] == "sea_bulk"]
    assert len(tanker) == 1 and tanker[0]["available"] is False
    sea = [o for o in res["options"] if o["mode"] == "sea"]
    assert sea and all(o["available"] and o["feasibility"] != "reference_only" for o in sea)


def test_dry_bulk_above_threshold_still_demotes_containers():
    res = _compare("DZA", "ZAF", weight_kg=5_000_000, bulk=UREA)
    assert any(o["mode"] == "sea_bulk" and o["available"] for o in res["options"])
    assert all(not o["available"] for o in res["options"] if o["mode"] == "sea")


def test_landed_cost_ammonia_dza_zaf_available():
    from services.report_engine import get_opportunity_report

    with contextlib.redirect_stdout(io.StringIO()):
        rep = get_opportunity_report("281410", "DZA", "ZAF", goods_value_usd=100000)
    landed = rep["composite_indicators"]["landed_cost"]
    assert landed["available"] is True and landed["value_usd"] > 100000


# ── 2. Frontière fermée ─────────────────────────────────────────────────────
def test_closed_border_corridor_not_operational_for_dza_mar():
    res = _compare("DZA", "MAR", bulk=UREA)
    for o in _operational(res):
        assert o["mode"] != "land", f"route terrestre DZA→MAR via frontière fermée : {o['label']}"
    assert "Trans-Maghreb (Tanger" not in " ".join(o["label"] for o in res["options"])


def test_closed_border_does_not_block_other_pairs():
    # Maghnia ne concerne que DZA-MAR : TUN-EGY garde le corridor.
    ids = lambda a, b: {c["corridor_id"] for c in service._find_all_corridors_for_pair(a, b)}
    assert "CORR-TRANS-MAGHREB-007" in ids("TUN", "EGY")
    assert "CORR-TRANS-MAGHREB-007" not in ids("DZA", "MAR")


# ── 3. Distances et jambes ──────────────────────────────────────────────────
def test_land_distance_is_pair_leg_not_whole_corridor():
    res = _compare("DZA", "NER", bulk=UREA)
    land = [o for o in res["options"] if o["mode"] == "land" and o["available"]]
    assert land
    assert land[0]["distance_km"] < 4504
    assert land[0]["distance_rule"] == "straight_line_x_sinuosity"
    assert "vol d'oiseau" in land[0]["notes"]


def test_detached_derivation_not_offered_as_land_from_origin():
    for dest in ("MLI", "NER", "BFA"):
        res = _compare("DZA", dest, bulk=UREA)
        for o in res["options"]:
            if o["mode"] == "land":
                assert o["segments"][0]["corridor_id"] not in (
                    "CORR-TRANSSAH-BAMAKO-017",
                    "CORR-TRANSSAH-OUAGA-021",
                ), f"{dest}: dérivation sans jambe Alger-Tamanrasset"


def test_roi_compares_complete_routes():
    for dest in ("MLI", "NER"):
        res = _compare("DZA", dest, bulk=UREA)
        roi = res["roi_infrastructure"]
        assert roi is not None
        best = next(o for o in res["options"] if o["label"] == roi["best_future_cost"]["label"])
        first_seg = best["segments"][0]
        assert first_seg["from"] in ("Alger",) or first_seg["mode"] == "rail", best["label"]


# ── 4. Passerelles ──────────────────────────────────────────────────────────
def test_niger_gateways_include_cotonou():
    ports = {g["port"] for g in service.LANDLOCKED_GATEWAYS["NER"]}
    assert "BJCOO" in ports


def test_cotonou_niamey_proposed_for_niger():
    res = _compare("DZA", "NER", bulk=UREA)
    labels = " ".join(o["label"] for o in res["options"])
    assert "Cotonou-Niamey" in labels


def test_lagos_niger_leg_not_billed_on_whole_transsaharan():
    res = _compare("DZA", "NER", bulk=UREA)
    for o in res["options"]:
        if o["mode"] == "multimodal" and o.get("via_port_locode") == "NGAPP":
            assert o["segments"][1]["distance_km"] < 4504


def test_malawi_gateways_are_consistent():
    assert all(gw["port"] != "MZMPM" for gw in service.LANDLOCKED_GATEWAYS["MWI"]), "Maputo"
    res = _compare("DZA", "MWI", bulk=UREA)
    for o in res["options"]:
        if o["mode"] == "multimodal":
            corridor_start = o["segments"][1]["from"]
            assert (
                o["via_port"].lower() in corridor_start.lower()
            ), f"jambe terrestre part de {corridor_start}, mer arrive à {o['via_port']}"


def test_fermeture_maghnia_bloque_egalement_le_transit():
    corridor_id = "CORR-TRANS-MAGHREB-007"
    for origin, dest in (("MAR", "TUN"), ("TUN", "MAR")):
        assert corridor_id not in {
            c["corridor_id"] for c in service._find_all_corridors_for_pair(origin, dest)
        }


def test_prix_maritime_du_lot_et_non_d_un_conteneur():
    result = _compare("DZA", "ZAF", weight_kg=60_000, bulk=AMMONIA)
    sea = next(o for o in result["options"] if o["mode"] == "sea")
    assert sea["containers_needed"] == 3
    assert sea["cost_basis"] == "shipment"
    assert sea["total_cost_usd"] == 3 * sea["segments"][0]["cost_usd_per_container"]


# ── Revue Codex (#802) ──────────────────────────────────────────────────────
def test_shared_terminus_does_not_detach_corridors_starting_there():
    # Durban-Dar es Salaam aboutit à Dar es Salaam : Central et TAZARA y partent
    # légitimement pour une origine tanzanienne.
    ids = lambda a, b: {o["segments"][0]["corridor_id"] for o in service._land_option(a, b, 26.4)}
    assert "CORR-CENTRAL-009" in ids("TZA", "BDI")
    assert "CORR-TAZARA-008" in ids("TZA", "ZMB")


def test_osbp_crossing_keeps_osbp_cost_for_pair_leg():
    import logistics_land_fees_data as land

    res = land.get_land_freight_cost(
        "CORR-ABIDJAN-OUAGA-001", "road", 26.4, "container", country_pair=("CIV", "BFA")
    )
    assert res["border_crossings"] == 1 and res["osbp_crossings"] == 1
    assert res["border_cost_usd"] == 250


def test_every_osbp_border_node_resolves_its_country_pair():
    import logistics_land_fees_data as land

    for cid, corridor in land._corridor_index().items():
        for node in corridor["nodes"]:
            if node.get("node_type") == "border_crossing" and node.get("is_osbp"):
                assert land.border_node_pair(node), f"{cid}: OSBP sans couple de pays"


# ── Vérification finale : règle de distance ────────────────────────────────
def _straight_km(p, q):
    import math

    (la1, lo1), (la2, lo2) = p, q
    r = math.radians
    h = (
        math.sin(r(la2 - la1) / 2) ** 2
        + math.cos(r(la1)) * math.cos(r(la2)) * math.sin(r(lo2 - lo1) / 2) ** 2
    )
    return 2 * 6371 * math.asin(math.sqrt(h))


def _capital(iso):
    from logistics_air_fees_data import _airport_registry

    airport = _airport_registry().get(service.COUNTRY_DEFAULT_AIRPORT.get(iso, ""))
    return (airport["lat"], airport["lon"]) if airport else None


def test_land_leg_never_shorter_than_straight_line():
    # Un tronçon facturé ne peut pas être plus court que la distance à vol
    # d'oiseau entre ses extrémités, sauf si tout le corridor est facturé (le
    # corridor n'atteint alors pas la capitale de destination).
    from logistics_fees_data import PORTS

    lengths = {c["corridor_id"]: c["length_km"] for c in service.get_land_corridors_list()}
    checked = []
    for dest, gateways in service.LANDLOCKED_GATEWAYS.items():
        for o in _compare("DZA", dest)["options"]:
            if o["mode"] != "multimodal" or o["segments"][0]["mode"] != "sea":
                continue
            port, leg = PORTS[o["segments"][0]["to_locode"]], o["segments"][1]
            checked.append((dest, leg, (port["lat"], port["lon"]), _capital(dest)))
    for c in service.get_land_corridors_list():
        for a in c["countries"]:
            for b in c["countries"]:
                if a == b or not _capital(a) or not _capital(b):
                    continue
                for o in service._land_option(a, b, 26.4):
                    checked.append((f"{a}>{b}", o["segments"][0], _capital(a), _capital(b)))
    assert len(checked) > 100
    for label, leg, start, end in checked:
        floor = min(lengths[leg["corridor_id"]], _straight_km(start, end))
        assert leg["distance_km"] >= floor - 1, f"{label} {leg['corridor_id']}: {leg}"


def test_mombasa_uganda_leg_between_straight_line_and_whole_corridor():
    res = _compare("DZA", "UGA")
    leg = next(
        o["segments"][1]
        for o in res["options"]
        if o.get("via_port_locode") == "KEMBA"
        and o["segments"][1]["corridor_id"] == "CORR-MOMBASA-NAIROBI-003"
    )
    assert 922 < leg["distance_km"] < 1720


def test_leg_spanning_corridor_ends_is_billed_full_length():
    # Tamanrasset → Ouagadougou passe par Agadez et Niamey : la ligne droite
    # raccourcirait ce coude ; entre les deux pays extrêmes, tout le corridor.
    res = _compare("DZA", "BFA")
    road = next(
        o["segments"][1]
        for o in res["options"]
        if o.get("corridor_mode") == "rail_road"
        and o["segments"][1]["corridor_id"] == "CORR-TRANSSAH-OUAGA-021"
    )
    assert road["distance_km"] == 2150
    assert any(
        o["segments"][1]["distance_km"] == 1035
        for o in _compare("DZA", "NER")["options"]
        if o.get("via_port_locode") == "BJCOO"
    )


def test_gateway_land_leg_starts_or_ends_at_gateway_port():
    # Même défaut que Malawi (anomalie 4) : la jambe terrestre doit partir du port
    # où arrive la jambe maritime (ou y aboutir), pas d'un autre port.
    for dest in service.LANDLOCKED_GATEWAYS:
        for o in _compare("DZA", dest)["options"]:
            if o["mode"] != "multimodal" or o["segments"][0]["mode"] != "sea":
                continue
            city = o["via_port"].split(" (")[0].lower()
            leg = o["segments"][1]
            assert city in f"{leg['from']} {leg['to']}".lower(), f"{dest}: {o['label']}"


def test_zimbabwe_gateway_uses_beira_port_for_beira_corridor():
    ports = {g["port"] for g in service.LANDLOCKED_GATEWAYS["ZWE"]}
    assert "MZBEW" in ports and "MZMPM" not in ports
    assert any(
        o.get("via_port_locode") == "MZBEW" and o["segments"][1]["corridor_id"] == "CORR-BEIRA-010"
        for o in _compare("DZA", "ZWE")["options"]
    )
