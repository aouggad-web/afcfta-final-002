"""
Garde-fous du calendrier générique de démantèlement (etl/afcfta_schedule.py),
repris des tests de compute_impact_projection retirés au lot O2-0 : la fonction
reste lue par la route GET /dismantlement/{pays}/{sh6}, reportée au lot O2-0b.
Le calendrier linéaire des catégories A et B n'est volontairement pas figé : c'est
le canevas générique, pas un taux sourcé.
"""

from etl.afcfta_schedule import CAT_A, CAT_C, compute_annual_schedule


def test_categorie_c_jamais_reduite():
    calendrier = compute_annual_schedule(20.0, CAT_C, is_ldc=False)

    assert calendrier
    assert all(r["rate"] == 20.0 and r["reduction_pct"] == 0.0 for r in calendrier)


def test_npf_nul_reste_nul():
    assert [r["rate"] for r in compute_annual_schedule(0.0, CAT_A, is_ldc=False)] == [0.0]
