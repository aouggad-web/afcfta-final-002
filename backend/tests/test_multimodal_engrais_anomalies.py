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
    assert "pro rata" in land[0]["notes"].lower() or land[0].get("distance_rule")


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
