"""Tests du dimensionnement conteneur à partir de la valeur FOB."""

import math

from services import shipment_estimator as se


def test_small_fob_single_teu():
    # Cacao (SH 1801, cours mondial ICE Cocoa ~5.88 USD/kg) :
    # 50 000 USD -> ~8.5 t -> 1 conteneur 20'.
    r = se.estimate_shipment(50000, "1801")
    assert r["available"] is True
    assert r["weight_source"] == "estimé"
    assert r["container_type"] == "teu"
    assert r["containers_needed"] == 1
    assert r["value_to_weight"]["classification_source"] == "cours_mondial"


def test_large_fob_multiple_feu():
    # 2 M USD de cacao -> plusieurs conteneurs 40'.
    r = se.estimate_shipment(2_000_000, "1801")
    assert r["container_type"] == "feu"
    assert r["containers_needed"] >= 2
    # Cohérence : nb = ceil(poids / capacité).
    assert r["containers_needed"] == math.ceil(r["weight_kg"] / r["container_capacity_kg"])


def test_heavy_cheap_commodity_more_containers_than_light_expensive():
    # Même valeur FOB : un minerai (lourd, bon marché) exige beaucoup plus de
    # conteneurs qu'un produit électronique (léger, cher).
    ore = se.estimate_shipment(500_000, "2601")  # minerai de fer, cours mondial
    electronics = se.estimate_shipment(500_000, "8517")  # chap. 85, estimation
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
    assert r["classification_source"] == "estimation_chapitre"
    assert r["negotiation"]["usable_as_price_reference"] is False


def test_world_market_benchmark_matched_by_6_digit_hs_takes_priority():
    # Café Arabica (090111) doit matcher le cours ICE Coffee C 6 chiffres,
    # pas retomber sur l'estimation par chapitre 09.
    r = se.usd_per_kg_for_hs("090111")
    assert r["classification_source"] == "cours_mondial"
    assert r["hs_match"] == "090111"
    assert r["commodity"].startswith("Café Arabica")
    assert r["is_estimate"] is False
    assert r["negotiation"]["usable_as_price_reference"] is True
    assert r["negotiation"]["caveat"]


def test_world_market_benchmark_matched_by_4_digit_hs():
    r = se.usd_per_kg_for_hs("7403.10")  # cuivre affiné, avec un sous-code
    assert r["classification_source"] == "cours_mondial"
    assert r["hs_match"] == "7403"
    assert r["commodity"].startswith("Cuivre")
    assert r["usd_per_kg"] == 13.335


def test_robusta_coffee_not_covered_by_arabica_benchmark():
    # Le Robusta (090121) n'est pas dans _WORLD_MARKET_BENCHMARKS -> retombe
    # sur l'estimation par chapitre (09), pas sur le cours Arabica.
    r = se.usd_per_kg_for_hs("090121")
    assert r["classification_source"] == "estimation_chapitre"
    assert r["hs_chapter"] == "09"


def test_gold_benchmark_used_as_negotiation_reference_end_to_end():
    r = se.estimate_shipment(1_000_000, "7108")
    assert r["value_to_weight"]["classification_source"] == "cours_mondial"
    assert r["negotiation_reference"] is not None
    assert r["negotiation_reference"]["commodity"].startswith("Or")
    assert r["negotiation_reference"]["caveat"]


def test_chapter_estimate_has_no_negotiation_reference():
    r = se.estimate_shipment(500_000, "8517")  # électronique, estimation chapitre
    assert r["value_to_weight"]["classification_source"] == "estimation_chapitre"
    assert r["negotiation_reference"] is None
