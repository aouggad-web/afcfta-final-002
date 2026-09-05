"""
Tests du comparateur tarifaire bilatéral (compute_bilateral_tariff_comparison).

S'appuie sur les données tarifaires locales (pas de réseau) : valide la
structure et la cohérence des deux directions d'une paire de pays.
"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from etl.country_tariffs_complete import compute_bilateral_tariff_comparison


def test_structure_and_directions():
    res = compute_bilateral_tariff_comparison("KEN", "NGA", "520100")
    assert res["country_a"] == "KEN"
    assert res["country_b"] == "NGA"
    # Flux A→B : le tarif appliqué est celui de l'importateur B (NGA).
    assert res["flow_a_to_b"]["importer"] == "NGA"
    # Flux B→A : le tarif appliqué est celui de l'importateur A (KEN).
    assert res["flow_b_to_a"]["importer"] == "KEN"


def test_preference_margin_is_mfn_minus_zlecaf_and_non_negative():
    res = compute_bilateral_tariff_comparison("ZAF", "EGY", "100190")
    for flow in (res["flow_a_to_b"], res["flow_b_to_a"]):
        # ZLECAf ≤ NPF (le taux préférentiel ne dépasse jamais le NPF).
        assert flow["zlecaf_rate"] <= flow["mfn_rate"]
        # La marge = NPF − ZLECAf, à l'arrondi près.
        assert flow["preference_margin"] == round(flow["mfn_rate"] - flow["zlecaf_rate"], 2)
        assert flow["preference_margin"] >= 0


def test_best_direction_matches_larger_margin():
    res = compute_bilateral_tariff_comparison("MAR", "GHA", "870321")
    mab = res["flow_a_to_b"]["preference_margin"]
    mba = res["flow_b_to_a"]["preference_margin"]
    if mab > mba:
        assert res["best_preference_direction"] == "a_to_b"
    elif mba > mab:
        assert res["best_preference_direction"] == "b_to_a"
    else:
        assert res["best_preference_direction"] == "equal"


def test_case_insensitive_country_codes():
    upper = compute_bilateral_tariff_comparison("KEN", "NGA", "520100")
    lower = compute_bilateral_tariff_comparison("ken", "nga", "520100")
    assert lower["country_a"] == "KEN"
    assert lower["flow_a_to_b"] == upper["flow_a_to_b"]
