"""
Tests du démantèlement ZLECAf à deux niveaux (etl/afcfta_national_offers.py).

Niveau 1 : canevas générique ZLECAf (SH2, indicatif). Niveau 2 : offre
tarifaire nationale officielle (ligne à ligne, à sa précision propre),
qui prime sur le canevas quand elle couvre la ligne demandée.
"""

from etl.afcfta_national_offers import (
    CLASSIFICATION_SOURCE_CANVAS,
    CLASSIFICATION_SOURCE_NATIONAL,
    NATIONAL_OFFER_REGISTRY,
    NationalOfferAdapter,
    check_conformity,
    resolve_classification,
)
from etl.afcfta_schedule import get_dismantlement_schedule
from services.zlecaf_schedule_dza import LIST_B_CODES, LIST_C_CODES


def _a_list_b_code() -> str:
    return sorted(LIST_B_CODES)[0]


def _a_list_c_code() -> str:
    return sorted(LIST_C_CODES)[0]


# ---------------------------------------------------------------------------
# resolve_classification : précédence et respect de la précision publiée
# ---------------------------------------------------------------------------


def test_hs6_only_falls_back_to_canvas_even_for_a_country_with_a_national_offer():
    """Sans code à la précision de l'offre (SH10 pour l'Algérie), on ne
    devine jamais par troncature/padding : le canevas générique s'applique."""
    category, source, adapter = resolve_classification("DZA", "010511")
    assert category is None
    assert source == CLASSIFICATION_SOURCE_CANVAS
    assert adapter is None


def test_precise_code_in_list_b_uses_national_offer():
    code = _a_list_b_code()
    category, source, adapter = resolve_classification("DZA", code)
    assert category == "B"
    assert source == CLASSIFICATION_SOURCE_NATIONAL
    assert adapter is not None
    assert adapter.iso3 == "DZA"


def test_precise_code_in_list_c_uses_national_offer():
    code = _a_list_c_code()
    category, source, adapter = resolve_classification("DZA", code)
    assert category == "C"
    assert source == CLASSIFICATION_SOURCE_NATIONAL


def test_precise_code_not_in_b_or_c_resolves_to_implicit_list_a_via_national_offer():
    """La liste (A) algérienne est la liste par défaut (tout ce qui n'est
    pas explicitement en (B) ou (C)) : ce n'est pas une absence de
    classification, c'est une caractéristique documentée de l'offre
    officielle elle-même (cf. services/zlecaf_schedule_dza.py::tariff_list).
    Un code précis hors des listes (B)/(C) reste donc classé par l'offre
    nationale, pas par le canevas."""
    category, source, _ = resolve_classification("DZA", "2901101099")
    assert category == "A"
    assert source == CLASSIFICATION_SOURCE_NATIONAL


def test_country_without_registered_offer_always_uses_canvas():
    category, source, adapter = resolve_classification("GHA", "0105111000")
    assert category is None
    assert source == CLASSIFICATION_SOURCE_CANVAS
    assert adapter is None


# ---------------------------------------------------------------------------
# get_dismantlement_schedule : la ligne d'offre nationale prime sur le canevas
# ---------------------------------------------------------------------------


def test_dismantlement_schedule_uses_canvas_by_default_for_dza():
    result = get_dismantlement_schedule("DZA", "010511", npf_rate=30.0)
    assert result["classification_source"] == CLASSIFICATION_SOURCE_CANVAS
    assert "national_offer" not in result


def test_dismantlement_schedule_prefers_national_offer_when_precise_code_given():
    code = _a_list_b_code()
    result = get_dismantlement_schedule("DZA", code[:6], npf_rate=30.0, hs_code_precise=code)
    assert result["classification_source"] == CLASSIFICATION_SOURCE_NATIONAL
    assert result["category"] == "B"
    assert result["national_offer"]["source_id"] == NATIONAL_OFFER_REGISTRY["DZA"].source_id
    assert result["classification_source_label_fr"] == "Offre tarifaire nationale officielle"


def test_forced_category_bypasses_classification_source_resolution():
    """Une catégorie explicitement forcée par l'appelant n'est ni une
    résolution d'offre nationale ni une résolution du canevas."""
    result = get_dismantlement_schedule("DZA", "999999", npf_rate=10.0, category="A")
    assert result["classification_source"] is None
    assert result["category"] == "A"


# ---------------------------------------------------------------------------
# check_conformity : ne bloque jamais, remonte les écarts pour revue
# ---------------------------------------------------------------------------


def test_dza_real_offer_is_within_canvas_tolerance():
    """L'offre algérienne réelle (1163 lignes B, 456 lignes C sur 17115)
    est proche du canevas ~90/7/3 : aucun écart au-delà de la tolérance."""
    result = check_conformity("DZA")
    assert result["status"] == "WITHIN_TOLERANCE"
    assert result["findings"] == []
    shares = result["observed_shares_pct"]
    assert 85.0 < shares["A"] < 95.0
    assert 5.0 < shares["B"] < 9.0
    assert 1.0 < shares["C"] < 5.0


def test_country_without_offer_reports_not_registered():
    result = check_conformity("GHA")
    assert result["status"] == "NO_NATIONAL_OFFER_REGISTERED"


def test_non_conforming_offer_is_flagged_for_review_not_silently_accepted_or_rejected():
    """Constat synthétique : une offre s'écartant fortement du canevas
    (ex: 50% de lignes en catégorie B) doit être signalée pour revue —
    sans jamais être rejetée (elle reste l'offre officielle applicable)
    ni acceptée silencieusement."""
    fake = NationalOfferAdapter(
        iso3="ZZZ",
        hs_precision=6,
        classify=lambda code: None,
        legal_reference="Instrument de test",
        source_id="TEST-NON-CONFORMING",
        explicit_line_counts={"B": 500, "C": 10},
        total_line_count=1000,
    )
    NATIONAL_OFFER_REGISTRY["ZZZ"] = fake
    try:
        result = check_conformity("ZZZ")
    finally:
        del NATIONAL_OFFER_REGISTRY["ZZZ"]

    assert result["status"] == "REVIEW_FLAGGED"
    assert result["findings"], "un écart de 50% en catégorie B doit produire un constat"
    assert any("B" in finding for finding in result["findings"])
    # L'offre reste applicable : aucun statut de type "rejeté"/"invalide".
    assert "reject" not in result["status"].lower()
    assert "invalid" not in result["status"].lower()


def test_conformity_not_computable_without_total_line_count():
    fake = NationalOfferAdapter(
        iso3="YYY",
        hs_precision=6,
        classify=lambda code: None,
        legal_reference="Instrument de test",
        source_id="TEST-NO-TOTAL",
        explicit_line_counts={"B": 5, "C": 1},
        total_line_count=None,
    )
    NATIONAL_OFFER_REGISTRY["YYY"] = fake
    try:
        result = check_conformity("YYY")
    finally:
        del NATIONAL_OFFER_REGISTRY["YYY"]

    assert result["status"] == "NOT_COMPUTABLE"
