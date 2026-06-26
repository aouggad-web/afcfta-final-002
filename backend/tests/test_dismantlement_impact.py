"""
Tests du simulateur d'impact ZLECAf (compute_impact_projection).

Fonction pure, déterministe, sans réseau : valide la projection année par année
de l'économie de droits de douane sur le calendrier de démantèlement officiel.
"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from etl.afcfta_schedule import CAT_A, CAT_C, compute_impact_projection


def _by_year(rows):
    return {r["year"]: r for r in rows}


def test_category_a_non_ldc_linear_savings():
    # NPF 10%, valeur 1M USD, Catégorie A non-PMA → 5 ans linéaires jusqu'à 0%.
    rows = compute_impact_projection(
        npf_rate=10.0, category=CAT_A, is_ldc=False, trade_value=1_000_000
    )
    by_year = _by_year(rows)

    # Droit NPF constant = 100 000 USD/an.
    assert all(r["duty_npf"] == 100_000 for r in rows)

    # Année 0 (baseline, taux = NPF) → aucune économie.
    assert by_year[0]["annual_saving"] == 0
    assert by_year[0]["cumulative_saving"] == 0

    # Réduction linéaire: année 1 → 8% (économie 20k), année 5 → 0% (économie 100k).
    assert by_year[1]["zlecaf_rate"] == 8.0
    assert by_year[1]["annual_saving"] == 20_000
    assert by_year[5]["zlecaf_rate"] == 0.0
    assert by_year[5]["annual_saving"] == 100_000

    # Cumul à l'année 5 = 20k+40k+60k+80k+100k = 300k.
    assert by_year[5]["cumulative_saving"] == 300_000

    # Le cumul est monotone non décroissant.
    cums = [r["cumulative_saving"] for r in rows]
    assert cums == sorted(cums)


def test_category_c_excluded_no_savings():
    # Catégorie C (produits exclus) → aucune réduction, économie nulle partout.
    rows = compute_impact_projection(
        npf_rate=20.0, category=CAT_C, is_ldc=False, trade_value=500_000
    )
    assert all(r["zlecaf_rate"] == 20.0 for r in rows)
    assert all(r["annual_saving"] == 0 for r in rows)
    assert rows[-1]["cumulative_saving"] == 0


def test_zero_npf_means_no_duty_and_no_saving():
    # NPF déjà à 0% → droits nuls des deux côtés, aucune économie.
    rows = compute_impact_projection(
        npf_rate=0.0, category=CAT_A, is_ldc=False, trade_value=1_000_000
    )
    assert all(r["duty_npf"] == 0 for r in rows)
    assert all(r["annual_saving"] == 0 for r in rows)


def test_ldc_has_longer_schedule_than_non_ldc():
    # PMA: Catégorie A en 10 ans (vs 5 ans non-PMA) → libéralisation plus lente.
    non_ldc = _by_year(compute_impact_projection(10.0, CAT_A, is_ldc=False, trade_value=1_000_000))
    ldc = _by_year(compute_impact_projection(10.0, CAT_A, is_ldc=True, trade_value=1_000_000))

    # À l'année 5, le non-PMA est déjà à 0% alors que le PMA réduit encore.
    assert non_ldc[5]["zlecaf_rate"] == 0.0
    assert ldc[5]["zlecaf_rate"] > 0.0
    # Le PMA atteint 0% à l'année 10.
    assert ldc[10]["zlecaf_rate"] == 0.0
