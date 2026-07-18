"""
Tests du sous-module « faisabilité de substitution » : coefficients de
substituabilité par classe SH (effet marque, écart technologique,
certification...) et leur application au potentiel de substitution.
"""

from services.substitution_feasibility_service import (
    DEFAULT_COEFFICIENT,
    realistic_substitution_potential,
    substitutability_for_hs,
)


def test_brand_sensitive_products_have_low_coefficients():
    # Véhicules de tourisme : effet marque + réseau après-vente
    cars = substitutability_for_hs("870323")
    assert cars["coefficient"] == 0.5
    assert cars["barriers"]["brand_effect"] == "fort"
    assert "marque" in cars["rationale"].lower()

    # Téléphonie : branding + technologie propriétaire
    phones = substitutability_for_hs("851712")
    assert phones["coefficient"] == 0.2
    assert phones["barriers"]["technology_gap"] == "fort"

    # Informatique : concentration mondiale extrême
    computers = substitutability_for_hs("847130")
    assert computers["coefficient"] == 0.15


def test_commodities_have_high_coefficients():
    assert substitutability_for_hs("100199")["coefficient"] == 0.9  # blé
    assert substitutability_for_hs("090111")["coefficient"] == 0.9  # café
    assert substitutability_for_hs("2709")["coefficient"] == 0.9  # pétrole brut


def test_pharma_reflects_certification_barrier():
    pharma = substitutability_for_hs("300490")
    assert pharma["coefficient"] == 0.45
    assert pharma["barriers"]["certification"] == "fort"


def test_longest_prefix_wins():
    # 8708 (pièces, 0.65) doit primer sur 87 (véhicules divers, 0.45)
    assert substitutability_for_hs("870829")["coefficient"] == 0.65
    # 8703 (voitures, 0.5) doit primer sur 87
    assert substitutability_for_hs("8703")["coefficient"] == 0.5
    # 87 seul (ex. 8711 motos) tombe sur la classe chapitre
    assert substitutability_for_hs("871120")["coefficient"] == 0.45


def test_unmapped_hs_gets_labelled_default():
    res = substitutability_for_hs("990000")
    assert res["coefficient"] == DEFAULT_COEFFICIENT
    assert "non mappée" in res["product_class"]


def test_caller_override_is_exposed_as_such():
    res = substitutability_for_hs("8703", override=0.8)
    assert res["coefficient"] == 0.8
    assert res["product_class"] == "surcharge appelant"
    # Bornage 0-1
    assert substitutability_for_hs("8703", override=1.7)["coefficient"] == 1.0


def test_realistic_potential_binding_constraints():
    # Substituabilité contraint : capacité abondante mais produit de marque
    r = realistic_substitution_potential(1_000_000_000, 5_000_000_000, "8703")
    assert r["potential_usd"] == 500_000_000  # 1B × 0.5
    assert r["binding_constraint"] == "substituabilité"

    # Capacité contraint : commodité largement substituable mais offre limitée
    r = realistic_substitution_potential(1_000_000_000, 300_000_000, "1001")
    assert r["potential_usd"] == 300_000_000
    assert r["binding_constraint"] == "capacité africaine"

    # Les deux bornes sont exposées pour lecture honnête
    assert r["addressable_value_usd"] == 900_000_000
    assert r["african_capacity_usd"] == 300_000_000


def test_report_engine_exposes_substitution_feasibility():
    from services.substitution_feasibility_service import substitutability_for_hs as fn

    # Le bloc intégré au rapport Opportunités est le même payload transparent
    block = fn("8517")
    assert block["is_estimation"] is True
    assert set(block) >= {"coefficient", "product_class", "barriers", "rationale"}
