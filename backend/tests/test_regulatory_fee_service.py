"""Tests du moteur de frais réglementaires — les 7 statuts + règles fail-closed."""

from services.regulatory_compliance_service import get_country_regulatory_compliance
from services.regulatory_fee_service import (
    FEE_STATUSES,
    build_regulatory_cost,
    compute_fee,
)

_SRC = "gazette-officielle-2024"


def test_calculable_percentage_of_fob_with_minimum():
    r = compute_fee(
        {
            "calculation_method": "PERCENTAGE_OF_FOB",
            "rate": 0.005,
            "minimum_amount": 250,
            "currency": "USD",
            "source": _SRC,
        },
        fob_value=100000,
        fee_exists=True,
    )
    assert r["fee_status"] == "CALCULABLE"
    assert r["calculated_amount"] == 500.0
    assert r["currency"] == "USD"
    # Le plancher s'applique quand le pourcentage est plus bas.
    low = compute_fee(
        {
            "calculation_method": "PERCENTAGE_OF_FOB",
            "rate": 0.005,
            "minimum_amount": 250,
            "currency": "USD",
            "source": _SRC,
        },
        fob_value=1000,
        fee_exists=True,
    )
    assert low["calculated_amount"] == 250.0


def test_documented_fixed_amount():
    r = compute_fee(
        {"calculation_method": "FIXED_AMOUNT", "fixed_amount": 100, "currency": "USD", "source": _SRC},
        fee_exists=True,
    )
    assert r["fee_status"] == "DOCUMENTED_FIXED_AMOUNT"
    assert r["calculated_amount"] == 100.0


def test_no_source_never_produces_a_cost():
    # Règle 1 : un frais sans source officielle n'est jamais chiffré.
    r = compute_fee(
        {"calculation_method": "FIXED_AMOUNT", "fixed_amount": 100, "currency": "USD"},
        fee_exists=True,
    )
    assert r["fee_status"] == "FEE_EXISTS_AMOUNT_NOT_AVAILABLE"
    assert r["calculated_amount"] is None


def test_percentage_without_base_is_partial_never_zero():
    # Règle 3 : pas de pourcentage sans assiette explicite.
    r = compute_fee(
        {"calculation_method": "PERCENTAGE_OF_CIF", "rate": 0.005, "currency": "USD", "source": _SRC},
        fob_value=100000,  # CIF non fourni → pas d'assiette pour la méthode CIF
        fee_exists=True,
    )
    assert r["fee_status"] == "PARTIAL"
    assert r["calculated_amount"] is None


def test_absent_detail_with_confirmed_existence_is_flagged():
    # Règle 2 : existence confirmée mais montant inconnu → signalé, jamais 0.
    r = compute_fee(None, fee_exists=True)
    assert r["fee_status"] == "FEE_EXISTS_AMOUNT_NOT_AVAILABLE"
    assert r["calculated_amount"] is None


def test_absent_detail_without_existence_is_not_available():
    r = compute_fee(None, fee_exists=False)
    assert r["fee_status"] == "NOT_AVAILABLE"
    assert r["calculated_amount"] is None


def test_all_returned_statuses_are_canonical():
    samples = [
        compute_fee(None, fee_exists=True),
        compute_fee(None, fee_exists=False),
        compute_fee({"calculation_method": "FIXED_AMOUNT", "fixed_amount": 1, "currency": "USD", "source": _SRC}),
        compute_fee({"calculation_method": "PERCENTAGE_OF_FOB", "rate": 0.01, "currency": "USD", "source": _SRC}, fob_value=100),
        compute_fee({"calculation_method": "PERCENTAGE_OF_FOB", "currency": "USD", "source": _SRC}, fob_value=None),
    ]
    for r in samples:
        assert r["fee_status"] in FEE_STATUSES


# ── build_regulatory_cost sur données réelles (fail-closed) ────────────────────

def test_active_provider_country_yields_unpriced_incomplete_block():
    # CMR : prestataires actifs, aucun frais chiffré publié → bloc présent mais
    # incomplet, tous FEE_EXISTS_AMOUNT_NOT_AVAILABLE, total None (jamais 0).
    rc = build_regulatory_cost(get_country_regulatory_compliance("CMR"), fob_value=50000, side="import")
    assert rc is not None
    assert rc["complete"] is False
    assert rc["has_unpriced_fees"] is True
    assert rc["regulatory_cost_total"] is None
    assert all(li["fee_status"] != "CALCULABLE" for li in rc["line_items"])


def test_country_without_active_provider_has_no_cost_block():
    # CIV : seul acteur TERMINATED → aucune rubrique de coût (pas de rubrique vide).
    assert build_regulatory_cost(get_country_regulatory_compliance("CIV"), fob_value=50000) is None


def test_provider_and_formality_fees_are_bucketed_separately():
    rc = build_regulatory_cost(get_country_regulatory_compliance("CMR"), fob_value=50000, side="import")
    scopes = {li["scope"] for li in rc["line_items"]}
    assert "provider" in scopes  # au moins une ligne prestataire
    # Chaque ligne est étiquetée soit formality soit provider, jamais fusionnée.
    assert scopes.issubset({"provider", "formality"})


def test_expired_only_country_is_excluded_from_calculation():
    # Un mandat expiré n'entre jamais dans le calcul (règle 5) : CIV n'a aucun
    # actif, donc aucun de ses acteurs historiques ne génère de ligne de coût.
    assert build_regulatory_cost(get_country_regulatory_compliance("CIV"), fob_value=1) is None
