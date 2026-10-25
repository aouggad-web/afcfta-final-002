"""Regression tests for the real DZA tariff calculator path.

These tests exercise the production calculator chain used by the frontend for
Algeria: socle (DGD crawl) -> fiscal cascade -> dual-regime breakdown, through
the public `POST /calcul` contract. The local-currency block is computed by
the frontend from the Banque module rate (`localiserResultat`).
"""

from routes.calcul import DemandeCalcul, calcul


def test_real_dza_tariff_line_cascade_breakdown():
    """DZA 0101211100 : taux de la fiche DGD de la sous-position — DD 5 %,
    TCS 3 %, TVA 9 % sur CIF + DAPS + DD, PRCT 2 % sur CIF + DD + TCS + TVA.
    Un partenaire ZLECAf actif (EGY) élimine le DD et recalcule les bases
    dépendantes.
    """
    result = calcul(
        DemandeCalcul(
            destination="DZA",
            origine="EGY",
            code_sh="0101211100",
            valeur_cif=1_000_000.0,
            devise_cif="USD",
        )
    )
    npf = {row["code"]: row for row in result["npf"]["lignes"]}
    pref = {row["code"]: row for row in result["preference"]["lignes"]}
    assert set(npf) == set(pref) == {"DD", "TCS", "TVA", "PRCT"}

    assert npf["DD"]["taux_pct"] == 5.0
    assert pref["DD"]["taux_pct"] == 0.0
    assert pref["DD"]["regime_applique"] == "preference"
    assert npf["DD"]["montant"] == 50_000.0
    assert pref["DD"]["montant"] == 0.0

    assert npf["TCS"]["taux_pct"] == pref["TCS"]["taux_pct"] == 3.0
    assert npf["TCS"]["montant"] == pref["TCS"]["montant"] == 30_000.0

    assert npf["TVA"]["taux_pct"] == 9.0
    assert npf["TVA"]["assiette"] == "CIF+DAPS+DD"
    assert npf["TVA"]["base"] == 1_050_000.0
    assert pref["TVA"]["base"] == 1_000_000.0
    assert npf["TVA"]["montant"] == 94_500.0
    assert pref["TVA"]["montant"] == 90_000.0

    assert npf["PRCT"]["taux_pct"] == 2.0
    assert npf["PRCT"]["assiette"] == "CIF+DD+TCS+TVA"
    assert npf["PRCT"]["base"] == 1_174_500.0
    assert pref["PRCT"]["base"] == 1_120_000.0
    assert npf["PRCT"]["montant"] == 23_490.0
    assert pref["PRCT"]["montant"] == 22_400.0

    assert result["npf"]["etat"] == result["preference"]["etat"] == "COMPLET"
    assert result["npf"]["total_droits"] == 197_990.0
    assert result["npf"]["total_a_payer"] == 1_197_990.0
    assert result["preference"]["total_droits"] == 142_400.0
    assert result["preference"]["total_a_payer"] == 1_142_400.0
