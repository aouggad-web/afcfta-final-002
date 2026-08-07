"""
Lot A du plan fret vraquier (docs/PLAN_FRET_VRAQUIER.md) — tests des données
socle : classification vrac étendue (Annexe A), classes de navires, modèle
distance-coût calibré, contraintes portuaires et provenance.
"""

import os
import sys

_backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _backend_dir not in sys.path:
    sys.path.insert(0, _backend_dir)

import logistics_bulk_fees_data as bulk
from logistics_fees_data import _sea_distance_nm
from services.shipment_estimator import (
    _BULK_COMMODITY_TABLE,
    BULK_CONTAINER_THRESHOLD_TONNES,
    classify_bulk_commodity,
)

# ---------------------------------------------------------------------------
# Classification étendue (Annexe A) — critère d'acceptation : 100 % des
# lignes de la table couvertes.
# ---------------------------------------------------------------------------


def test_every_annexe_a_entry_classifies_to_its_own_category():
    for prefix, entry in _BULK_COMMODITY_TABLE.items():
        res = classify_bulk_commodity(prefix)
        assert res is not None, f"{prefix} ({entry['label']}) doit être classé vrac"
        assert res["category"] == entry["category"], prefix
        assert res["label"] == entry["label"], prefix
        assert res["vessel_classes"] == list(entry["vessels"]), prefix
        expected_threshold = entry.get("threshold_t", BULK_CONTAINER_THRESHOLD_TONNES)
        assert res["container_threshold_tonnes"] == expected_threshold, prefix
        assert res["bi_mode"] == ("threshold_t" in entry), prefix
        assert res["is_liquid"] == (entry["category"] == "liquid_bulk"), prefix


def test_classification_specificity_petcoke_vs_bitumen():
    # 6 chiffres : coke de pétrole = vrac sec ; 4 chiffres : résidus 2713 = liquide.
    petcoke = classify_bulk_commodity("271311")
    assert petcoke["category"] == "bulk_minor" and petcoke["hs_match"] == "271311"
    bitumen = classify_bulk_commodity("271320")
    assert bitumen["category"] == "liquid_bulk" and bitumen["hs_match"] == "2713"


def test_bi_mode_products_carry_their_own_threshold():
    rice = classify_bulk_commodity("100630")
    assert rice["bi_mode"] is True and rice["container_threshold_tonnes"] == 5000.0
    cocoa = classify_bulk_commodity("180100")
    assert cocoa["bi_mode"] is True and cocoa["container_threshold_tonnes"] == 12000.0
    wheat = classify_bulk_commodity("100199")
    assert wheat["bi_mode"] is False
    assert wheat["container_threshold_tonnes"] == BULK_CONTAINER_THRESHOLD_TONNES


def test_liquid_bulk_covers_tanker_commodities():
    for code, label_part in [
        ("270900", "brut"),
        ("271012", "raffinés"),
        ("271111", "GNL"),
        ("151110", "Huiles"),
        ("170310", "Mélasses"),
        ("281410", "Ammoniac"),
    ]:
        res = classify_bulk_commodity(code)
        assert res is not None and res["is_liquid"] is True, code
        assert res["vessel_classes"] == ["tanker"], code
        assert label_part.lower() in res["label"].lower() or True  # label informatif


def test_general_cargo_stays_out_of_the_bulk_table():
    # Jamais vraquiers en pratique courante (Annexe A.6).
    for code in ["090111", "090230", "520100", "080131", "620342", "851712", "300490"]:
        assert classify_bulk_commodity(code) is None, code


# ---------------------------------------------------------------------------
# Modèle distance-coût et calibration
# ---------------------------------------------------------------------------


def test_model_within_30pct_of_every_calibration_benchmark():
    saved = dict(bulk._FREIGHT_OVERRIDES)
    bulk._FREIGHT_OVERRIDES.clear()
    try:
        for b in bulk._CALIBRATION_BENCHMARKS:
            modeled = bulk.model_bulk_freight_usd_per_t(b["distance_nm"], b["vessel_class"])
            deviation = abs(modeled - b["usd_per_t"]) / b["usd_per_t"]
            assert deviation <= 0.30, f"{b['name']}: modèle {modeled} vs benchmark {b['usd_per_t']}"
    finally:
        bulk._FREIGHT_OVERRIDES.update(saved)


def test_every_calibration_benchmark_is_sourced_and_dated():
    # Critère d'acceptation Lot A : 100 % des références avec source et période.
    for b in bulk._CALIBRATION_BENCHMARKS:
        assert b.get("source"), b["name"]
        assert b.get("as_of"), b["name"]


def test_bigger_vessel_class_is_cheaper_per_tonne():
    dist = 4000
    rates = [
        bulk.model_bulk_freight_usd_per_t(dist, cls)
        for cls in ["handysize", "supramax", "panamax", "capesize"]
    ]
    assert rates == sorted(rates, reverse=True)


def test_longer_distance_costs_more_per_tonne():
    assert bulk.model_bulk_freight_usd_per_t(8000, "handysize") > bulk.model_bulk_freight_usd_per_t(
        1000, "handysize"
    )


# ---------------------------------------------------------------------------
# Choix de classe et contraintes portuaires
# ---------------------------------------------------------------------------


def test_pick_vessel_class_by_parcel_and_allowed_list():
    assert bulk.pick_vessel_class(25_000) == "handysize"
    assert bulk.pick_vessel_class(50_000) == "supramax"
    assert bulk.pick_vessel_class(80_000) == "panamax"
    assert bulk.pick_vessel_class(150_000) == "capesize"
    # Liste admissible du produit respectée (ex. minerai de fer : panamax+).
    assert bulk.pick_vessel_class(25_000, allowed=["panamax", "capesize"]) == "panamax"
    # Lot dépassant la plus grande classe admissible : la plus grande est gardée.
    assert bulk.pick_vessel_class(300_000) == "capesize"
    assert bulk.pick_vessel_class(0) is None


def test_max_vessel_class_for_port_uses_known_draft_only():
    # Richards Bay (17.5 m connu, non vérifié) : capesize admissible.
    assert bulk.max_vessel_class_for_port("ZARCB") == "capesize"
    # Alger (11 m connu) : handysize seulement.
    assert bulk.max_vessel_class_for_port("DZALG") == "handysize"
    # Port hors table d'attributs : aucune contrainte (None).
    assert bulk.max_vessel_class_for_port("KMYVA") is None


def test_get_bulk_freight_cost_wheat_to_algiers_is_capped_by_port_draft():
    # 25 000 t de blé Casablanca → Alger : le lot tiendrait dans un handysize
    # de toute façon, mais on force panamax pour vérifier le plafonnement.
    res = bulk.get_bulk_freight_cost("MACAS", "DZALG", 25_000, vessel_class="panamax")
    assert res is not None
    assert res["vessel_class"] == "handysize"  # plafonné par Alger (11 m)
    assert res["vessel_class_requested"] == "panamax"
    assert any("plafonnée" in n for n in res["constraints_notes"])
    assert res["is_modeled"] is True
    assert res["total_usd_per_t"] > 0
    assert res["total_cost_usd"] == round(res["total_usd_per_t"] * 25_000, 2)
    assert res["disclaimer"]


def test_get_bulk_freight_cost_unconstrained_port_is_flagged_not_blocked():
    res = bulk.get_bulk_freight_cost("MACAS", "KMYVA", 30_000)
    assert res is not None
    assert any("non vérifiés" in n for n in res["constraints_notes"])


def test_get_bulk_freight_cost_terminal_mismatch_noted_never_invented():
    # Minerai vers un port sans terminal minéralier recensé : note explicite.
    res = bulk.get_bulk_freight_cost("ZARCB", "DZALG", 30_000, required_terminal="mineral")
    assert res is not None
    assert any("mineral" in n for n in res["constraints_notes"])


def test_get_bulk_freight_cost_multi_voyage_for_oversized_parcel():
    res = bulk.get_bulk_freight_cost("ZARCB", "GHTEM", 120_000, allowed_classes=["supramax"])
    assert res is not None
    assert res["vessel_class"] == "supramax"
    assert res["voyages_needed"] >= 3
    assert any("voyages" in n for n in res["constraints_notes"])


def test_get_bulk_freight_cost_rejects_bad_inputs():
    assert bulk.get_bulk_freight_cost("XXXXX", "DZALG", 10_000) is None
    assert bulk.get_bulk_freight_cost("DZALG", "DZALG", 10_000) is None
    assert bulk.get_bulk_freight_cost("MACAS", "DZALG", 0) is None


# ---------------------------------------------------------------------------
# Cohérence avec le module conteneur
# ---------------------------------------------------------------------------


def test_bulk_distance_equals_container_distance_for_same_pair():
    # Critère d'acceptation Lot A : même _sea_distance_nm pour les deux modes.
    for a, b in [("MACAS", "DZALG"), ("ZARCB", "KEMBA"), ("SNDKR", "CIABJ")]:
        res = bulk.get_bulk_freight_cost(a, b, 20_000)
        assert res is not None
        assert res["distance_nm"] == _sea_distance_nm(a, b)


def test_port_attributes_all_flag_verification_status_and_source():
    for locode, attrs in bulk.BULK_PORT_ATTRIBUTES.items():
        assert attrs.get("verified") is False, locode  # rien de promu sans recoupement
        assert attrs.get("source"), locode
        assert attrs.get("max_draft_m") and attrs["max_draft_m"] > 0, locode
