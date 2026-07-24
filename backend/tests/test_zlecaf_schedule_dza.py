"""
Tests du calendrier de démantèlement ZLECAf à l'importation en Algérie
(circulaire DGD n°482/2024). Vérifie : éligibilité par pays partenaire,
classement liste (A)/(B)/(C), gel des règles d'origine, et les facteurs de
réduction des deux calendriers (standard vs réciprocité) à des dates clés.
"""

import datetime

from services.zlecaf_schedule_dza import (
    ACTIVE_PARTNERS,
    LIST_B_BASE_RATES_2019,
    LIST_B_CODES,
    RECIPROCITY_PARTNERS,
    compute_dza_zlecaf_rate,
    daps_exempt,
    is_frozen,
    tariff_list,
)


def _non_frozen_list_b_code() -> str:
    """LIST_B_CODES is a frozenset: iteration order depends on the hash
    seed of the process, so picking via next(iter(...)) can flakily land
    on a code whose heading is also in FROZEN_HEADINGS. Pick deterministically."""
    for code in sorted(LIST_B_CODES):
        if not is_frozen(code):
            return code
    raise AssertionError("aucun code liste (B) non gelé trouvé")


def test_non_active_partner_gets_npf_rate():
    rate, source = compute_dza_zlecaf_rate("0101211100", "NGA", 0.15)
    assert rate == 0.15
    assert "non encore activé" in source


def test_active_non_reciprocity_partner_list_a_fully_eliminated_2026():
    # TUN n'est pas dans RECIPROCITY_PARTNERS -> calendrier standard.
    # Code hors liste B/C connue -> liste (A), éliminée depuis 1.1.2025.
    rate, source = compute_dza_zlecaf_rate(
        "2901101000", "TUN", 0.15, as_of=datetime.date(2026, 6, 18)
    )
    assert rate == 0.0
    assert "liste (A)" in source


def test_reciprocity_partner_list_a_partial_reduction_2026():
    # CMR est dans RECIPROCITY_PARTNERS -> calendrier plus long.
    # 2026 -> facteur 0.4 (60% de réduction cumulée depuis 2021).
    rate, source = compute_dza_zlecaf_rate(
        "2901101000", "CMR", 0.30, as_of=datetime.date(2026, 6, 18)
    )
    assert abs(rate - 0.12) < 1e-9
    assert "réciprocité" in source


def test_list_b_standard_partner_full_rate_during_transition():
    # Le taux de base officiel 2019 (table détaillée liste (B)/réciprocité)
    # prévaut sur le taux normal transmis, qui peut être obsolète/différent.
    code = _non_frozen_list_b_code()
    base = LIST_B_BASE_RATES_2019[code]
    rate, source = compute_dza_zlecaf_rate(code, "TUN", 0.999, as_of=datetime.date(2024, 6, 18))
    assert rate == base  # transition 2021-2025 : droit commun (taux de base) maintenu
    assert "liste (B)" in source
    assert "taux de base 2019" in source


def test_list_b_standard_partner_reduction_starts_2026():
    code = _non_frozen_list_b_code()
    base = LIST_B_BASE_RATES_2019[code]
    rate, _ = compute_dza_zlecaf_rate(code, "TUN", 0.999, as_of=datetime.date(2026, 6, 18))
    assert abs(rate - base * 0.8) < 1e-9  # 80% du droit de base


def test_list_c_never_reduced():
    code = next(
        iter(__import__("services.zlecaf_schedule_dza", fromlist=["LIST_C_CODES"]).LIST_C_CODES)
    )
    assert tariff_list(code) == "C"
    rate, source = compute_dza_zlecaf_rate(code, "EGY", 0.30, as_of=datetime.date(2030, 1, 1))
    assert rate == 0.30
    assert "liste (c)" in source.lower()


def test_frozen_textile_heading_kept_at_npf():
    assert is_frozen("5111100000")
    rate, source = compute_dza_zlecaf_rate(
        "5111100000", "TUN", 0.30, as_of=datetime.date(2030, 1, 1)
    )
    assert rate == 0.30
    assert "gelée" in source


def test_frozen_vehicle_heading_kept_at_npf():
    assert is_frozen("8703231900")


def test_non_frozen_heading_outside_ranges():
    assert not is_frozen("2901101000")


def test_unknown_code_defaults_to_list_a():
    assert tariff_list("9999999999") == "A"


def test_list_b_uses_authoritative_2019_base_rate_not_stale_normal_rate():
    # 0201.10.11.00 (viande de veau) : taux de base ZLECAf 2019 = 30%, mais
    # la nomenclature tarifaire générale affiche aujourd'hui 5% (réduction
    # postérieure à 2019, hors ZLECAf). Le calendrier ZLECAf doit s'appliquer
    # sur le taux de base figé (30%), pas sur le taux normal courant (5%).
    code = "0201101100"
    assert LIST_B_BASE_RATES_2019[code] == 0.30
    rate, source = compute_dza_zlecaf_rate(code, "TUN", 0.05, as_of=datetime.date(2026, 6, 18))
    assert abs(rate - 0.30 * 0.8) < 1e-9
    assert "taux de base 2019" in source


def test_list_a_code_keeps_passed_normal_rate_no_base_override():
    # La table de base 2019 ne couvre que la liste (B) : pour la liste (A),
    # le taux normal transmis par l'appelant reste la seule source.
    rate, _ = compute_dza_zlecaf_rate("2901101000", "TUN", 0.15, as_of=datetime.date(2026, 6, 18))
    assert rate == 0.0


def test_daps_exempt_for_list_a_active_partner():
    assert daps_exempt("2901101000", "TUN") is True


def test_daps_not_exempt_for_inactive_partner():
    assert daps_exempt("2901101000", "NGA") is False


def test_daps_not_exempt_for_frozen_heading():
    assert daps_exempt("5111100000", "TUN") is False


def test_active_partners_count():
    assert len(ACTIVE_PARTNERS) == 9


def test_reciprocity_partners_count():
    assert len(RECIPROCITY_PARTNERS) == 13


def test_list_a_full_elimination_after_2030_reciprocity():
    rate, _ = compute_dza_zlecaf_rate("2901101000", "ZAF", 0.30, as_of=datetime.date(2031, 1, 1))
    assert rate == 0.0


def test_list_a_full_rate_before_agreement_entry():
    rate, _ = compute_dza_zlecaf_rate("2901101000", "TUN", 0.30, as_of=datetime.date(2020, 1, 1))
    assert rate == 0.30
