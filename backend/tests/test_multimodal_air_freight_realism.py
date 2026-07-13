"""
Regression tests: air freight must not be offered for unrealistic cases.

PROBLÈME RÉSOLU : le comparateur multimodal proposait un fret aérien pour
n'importe quel poids et n'importe quelle marchandise — un conteneur de ciment
(vrac minéral, plusieurs tonnes) se voyait chiffrer une option "aérien direct"
alors que ce n'est jamais un mode de transport réaliste pour ce type de
marchandise. Deux garde-fous sont couverts ici :

  1. Poids : l'aérien n'est éligible qu'en dessous d'un plafond général
     (AIR_FREIGHT_MAX_KG_GENERAL, 1000 kg) — un conteneur complet ne vole pas.
  2. Nature de la marchandise : les matières premières en vrac (ciment,
     minerai de fer, céréales, charbon, pétrole brut, engrais...) ne sont
     jamais aériennes, quel que soit le poids, et leur jambe terrestre bascule
     par défaut sur le type de cargaison "bulk" plutôt que "container".
"""

import os
import sys

_backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _backend_dir not in sys.path:
    sys.path.insert(0, _backend_dir)

from services import multimodal_freight_service as service
from services import shipment_estimator
from services.logistics_opportunity_adapter import get_logistics_profile


def test_air_option_excluded_above_general_weight_ceiling():
    heavy = service._air_option("DZA", "MAR", 21_600.0, "general", 0.0)
    assert heavy is None, "a full container's weight must never be quoted for air freight"

    light = service._air_option("DZA", "MAR", 500.0, "general", 2.0)
    assert light is not None, "a small, light shipment stays air-eligible"
    assert light["mode"] == "air"


def test_air_option_excluded_for_bulk_commodity_regardless_of_weight():
    # Even a small quantity of a bulk raw material never flies.
    small_bulk = service._air_option("DZA", "MAR", 200.0, "general", 0.0, is_bulk=True)
    assert small_bulk is None


def test_classify_bulk_commodity_flags_cement_ore_and_cereals():
    cement = shipment_estimator.classify_bulk_commodity("2523")
    assert cement is not None
    assert cement["category"] == "bulk_mineral"

    iron_ore = shipment_estimator.classify_bulk_commodity("260111")
    assert iron_ore is not None
    assert iron_ore["category"] == "bulk_mineral"

    wheat = shipment_estimator.classify_bulk_commodity("100199")
    assert wheat is not None
    assert wheat["category"] == "bulk_agri"

    # Non-bulk goods (coffee, smartphones) are not flagged.
    assert shipment_estimator.classify_bulk_commodity("090111") is None
    assert shipment_estimator.classify_bulk_commodity("851712") is None


def test_compare_multimodal_excludes_air_and_defaults_bulk_cargo_for_cement():
    result = service.compare_multimodal(
        "DZA",
        "MAR",
        weight_kg=26_400.0,
        volume_m3=15.0,
        container_type="feu",
        is_bulk_commodity=True,
        bulk_label="Ciment",
    )
    assert result["is_bulk_commodity"] is True
    assert result["air_excluded"] is True
    assert result["land_cargo_type"] == "bulk"
    assert all(o["mode"] != "air" for o in result["options"])

    sea_opts = [o for o in result["options"] if o["mode"] == "sea"]
    if sea_opts:
        assert "bulk_cargo_note" in sea_opts[0]


def test_logistics_profile_detects_bulk_from_hs_code_end_to_end():
    profile = get_logistics_profile(
        "DZA", "MAR", weight_kg=26_400.0, volume_m3=15.0, container_type="feu", hs_code="2523"
    )
    freight = profile["freight"]
    assert freight["is_bulk_commodity"] is True
    assert freight["bulk_label"] == "Ciment"
    assert freight["land_cargo_type"] == "bulk"
    assert freight["air_excluded"] is True

    # A non-bulk, lightweight product on the same route stays air-eligible.
    coffee_profile = get_logistics_profile(
        "DZA", "MAR", weight_kg=200.0, volume_m3=1.0, container_type="teu", hs_code="090111"
    )
    coffee_freight = coffee_profile["freight"]
    assert coffee_freight["is_bulk_commodity"] is False
    assert coffee_freight["air_excluded"] is False
