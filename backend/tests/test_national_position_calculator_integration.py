"""
Test d'intégration du parcours complet du calculateur pour une position
nationale issue exclusivement des données crawled (PR #420) : GIN → SH6
761290 → positions nationales → 7612900000 → calcul.

Exigence : le taux appliqué doit être celui de la position nationale
source (search_tariff_lines()/get_sub_positions() ne suffisent pas comme
preuve — c'est bien calculate_import_taxes()/get_tariff_line() qui doivent
retenir ce taux, sans jamais retomber silencieusement sur celui du SH6
parent ni fabriquer un taux 0% artificiel).

Non-régression : même parcours pour Nigeria, Ghana, Côte d'Ivoire, Sénégal
(chacun avec un HS6 à taux variables selon la position nationale), pour
distinguer un défaut spécifique à la Guinée d'un défaut générique du
chemin get_sub_positions → get_tariff_line → calculate_import_taxes.
"""

import pytest

from services.authentic_tariff_service import (
    calculate_import_taxes,
    get_sub_positions,
    get_tariff_line,
)


def test_guinea_7612900000_national_position_found_and_selectable():
    """PASS attendu : position trouvée, sélectionnable, taux source retenu."""
    subs = get_sub_positions("GIN", "761290")
    codes = [s["code"] for s in subs]
    assert "7612900000" in codes, "position trouvée : FAIL — absente de get_sub_positions"

    line = get_tariff_line("GIN", "7612900000")
    assert line is not None, "position sélectionnable : FAIL — get_tariff_line() renvoie None"

    result = calculate_import_taxes(
        country_iso3="GIN",
        hs_code="7612900000",
        cif_value=1000.0,
        origin_country="SEN",
    )

    assert result["rates"]["dd_rate_pct"] == 20.0, "DD attendu 20% — pas de taux 0% artificiel"
    assert result["rates"]["vat_rate_pct"] == 18.0
    assert result["rates"]["other_taxes_pct"] == 0.5
    assert result["sub_position"]["code"] == "7612900000", (
        "code utilisé doit être la position nationale, pas le SH6 parent"
    )


def test_guinea_sibling_position_not_substituted_by_parent_rate():
    """7612901000 (DD=10%) ne doit jamais recevoir le taux 20% du parent 761290
    ou d'un autre enfant (7612900000/7612909000, DD=20%) — preuve qu'il n'y a
    pas de substitution silencieuse par un taux SH6 générique."""
    result = calculate_import_taxes(
        country_iso3="GIN",
        hs_code="7612901000",
        cif_value=1000.0,
        origin_country="SEN",
    )
    assert result["rates"]["dd_rate_pct"] == 10.0
    assert result["sub_position"]["code"] == "7612901000"


@pytest.mark.parametrize(
    "iso3,origin,hs6,varying_code,expected_dd",
    [
        ("NGA", "SEN", "010121", "0101210000", 5.0),
        ("GHA", "SEN", "010130", "0101309000", 10.0),
        ("CIV", "SEN", "761290", "7612901000", 10.0),
        ("SEN", "GIN", "761290", "7612901000", 10.0),
    ],
)
def test_national_position_calculator_path_non_regression(
    iso3, origin, hs6, varying_code, expected_dd
):
    """Contrôle de non-régression : le chemin générique fonctionne aussi pour
    d'autres pays des nouveaux fichiers positions[] de la PR #420, pas
    uniquement pour la Guinée."""
    subs = get_sub_positions(iso3, hs6)
    codes = [s["code"] for s in subs]
    assert varying_code in codes, f"{iso3}: position {varying_code} absente de get_sub_positions"

    result = calculate_import_taxes(
        country_iso3=iso3,
        hs_code=varying_code,
        cif_value=1000.0,
        origin_country=origin,
    )
    assert result["rates"]["dd_rate_pct"] == expected_dd, (
        f"{iso3}/{varying_code}: DD attendu {expected_dd}%, "
        f"obtenu {result['rates']['dd_rate_pct']}% (substitution suspectée)"
    )
    assert result["sub_position"]["code"] == varying_code
