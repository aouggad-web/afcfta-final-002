"""Tests du dimensionnement conteneur à partir de la valeur FOB."""

import math

from services import shipment_estimator as se


def test_small_fob_single_teu():
    # Cacao (chap. 18, ~3.5 USD/kg) : 50 000 USD -> ~14 t -> 1 conteneur 20'.
    r = se.estimate_shipment(50000, "1801")
    assert r["available"] is True
    assert r["weight_source"] == "estimé"
    assert r["container_type"] == "teu"
    assert r["containers_needed"] == 1


def test_large_fob_multiple_feu():
    # 2 M USD de cacao -> ~571 t -> plusieurs conteneurs 40'.
    r = se.estimate_shipment(2_000_000, "1801")
    assert r["container_type"] == "feu"
    assert r["containers_needed"] >= 2
    # Cohérence : nb = ceil(poids / capacité).
    assert r["containers_needed"] == math.ceil(r["weight_kg"] / r["container_capacity_kg"])


def test_heavy_cheap_commodity_more_containers_than_light_expensive():
    # Même valeur FOB : un minerai (lourd, bon marché) exige beaucoup plus de
    # conteneurs qu'un produit électronique (léger, cher).
    ore = se.estimate_shipment(500_000, "2601")  # chap. 26
    electronics = se.estimate_shipment(500_000, "8517")  # chap. 85
    assert ore["weight_kg"] > electronics["weight_kg"]
    assert ore["containers_needed"] > electronics["containers_needed"]


def test_weight_override_ignores_value_ratio():
    r = se.estimate_shipment(999, "1801", weight_kg_override=60000)
    assert r["weight_source"] == "fourni"
    assert r["is_estimate"] is False
    assert r["value_to_weight"] is None
    # 60 t -> 40' (26,4 t) -> 3 conteneurs.
    assert r["container_type"] == "feu"
    assert r["containers_needed"] == 3


def test_no_value_no_weight_unavailable():
    r = se.estimate_shipment(None, "1801")
    assert r["available"] is False


def test_unknown_chapter_uses_default_ratio():
    r = se.usd_per_kg_for_hs("9999")
    assert r["usd_per_kg"] == se._DEFAULT_USD_PER_KG
    assert r["is_estimate"] is True
