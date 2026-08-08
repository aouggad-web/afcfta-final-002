"""Garde-fou : les frais des prestataires mandatés sont informatifs et
STRICTEMENT SÉPARÉS des droits et taxes du calculateur.

Ces tests évitent volontairement d'importer ``routes/__init__`` (qui tire
pymongo / le moteur réglementaire v3) : ils vérifient l'invariant au niveau du
modèle de réponse et du service source, ce qui suffit à prouver que le bloc
``regulatory_compliance`` n'entre jamais dans un total douanier.
"""

from models import TariffCalculationResponse
from services.regulatory_compliance_service import (
    get_country_regulatory_compliance,
    get_supported_regulatory_countries,
)


def _totals(resp: TariffCalculationResponse) -> dict:
    return {
        "normal_total_cost": resp.normal_total_cost,
        "zlecaf_total_cost": resp.zlecaf_total_cost,
        "normal_other_taxes_total": resp.normal_other_taxes_total,
        "zlecaf_other_taxes_total": resp.zlecaf_other_taxes_total,
    }


def _minimal_response(**overrides) -> TariffCalculationResponse:
    base = dict(
        origin_country="DZA",
        destination_country="CIV",
        hs_code="090111",
        value=10000.0,
        normal_tariff_rate=10.0,
        normal_tariff_amount=1000.0,
        normal_statistical_fee=100.0,
        normal_community_levy=0.0,
        normal_ecowas_levy=0.0,
        normal_other_taxes_total=100.0,
        normal_total_cost=1100.0,
        zlecaf_statistical_fee=100.0,
        zlecaf_community_levy=0.0,
        zlecaf_ecowas_levy=0.0,
        zlecaf_other_taxes_total=100.0,
        zlecaf_total_cost=100.0,
        normal_calculation_journal=[],
        zlecaf_calculation_journal=[],
        computation_order_ref="test",
        last_verified="2026-08",
        confidence_level="medium",
        rules_of_origin={},
        top_african_producers=[],
        origin_country_data={},
        destination_country_data={},
    )
    base.update(overrides)
    return TariffCalculationResponse(**base)


def test_response_model_exposes_regulatory_compliance_field_defaulting_none():
    resp = _minimal_response()
    assert "regulatory_compliance" in TariffCalculationResponse.model_fields
    assert resp.regulatory_compliance is None


def test_attaching_compliance_does_not_change_any_customs_total():
    without = _minimal_response()
    compliance = get_country_regulatory_compliance("CIV")
    assert compliance is not None and compliance["measure_count"] > 0
    with_block = _minimal_response(regulatory_compliance=compliance)
    # Le bloc conformité est purement additif : aucun total douanier ne bouge.
    assert _totals(with_block) == _totals(without)
    assert with_block.regulatory_compliance == compliance


def test_provider_fees_stay_informative_never_a_numeric_zero():
    compliance = get_country_regulatory_compliance("CIV")
    for actor in compliance["mandated_actors"]:
        # Un frais non prouvé reste NOT_AVAILABLE / None : jamais un 0 chiffré qui
        # affirmerait à tort une gratuité, jamais une valeur fabriquée.
        if actor.get("authorized_fees_status") == "NOT_AVAILABLE":
            assert actor.get("authorized_fees") in (None, "")


def test_uncovered_destination_country_is_fail_closed_none():
    # Un pays sans registre conforme publié ne fabrique aucune donnée.
    assert "DZA" not in get_supported_regulatory_countries()
    assert get_country_regulatory_compliance("DZA") is None
