"""
Tests du service d'enrichissement ISIC4/IDSB des opportunités.

Vérifient l'ancrage « zéro fabrication » : la classification vient de la
correspondance UNSD réelle (``unido_hs_mapping``), l'offre/demande des données
UNIDO IDSB réelles (``etl.isic4_idsb_data``, ici mockées), et tout ce qui n'est
pas mesuré est explicitement marqué indisponible — jamais estimé.
"""

import os
import sys
from unittest.mock import patch

_backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _backend_dir not in sys.path:
    sys.path.insert(0, _backend_dir)

from etl import isic4_idsb_data  # noqa: E402
from services.isic_idsb_opportunity_service import get_isic_idsb_service  # noqa: E402

# Jeu IDSB minimal : CIV (origine, division 10 alimentaire) et EGY (destination).
_FAKE_RECORDS = [
    {
        "dataset_code": "IDSB_R4", "country_iso3": "CIV", "country_name": "Côte d'Ivoire",
        "isic_code": "1040", "isic_description": "Vegetable and animal oils and fats",
        "year": 2023, "indicator_code": "100", "indicator_name": "Output",
        "value": 2_000_000_000.0, "unit": "current_USD", "data_nature": "UNIDO_DERIVED_ESTIMATE",
    },
    {
        "dataset_code": "IDSB_R4", "country_iso3": "CIV", "country_name": "Côte d'Ivoire",
        "isic_code": "1040", "isic_description": "Vegetable and animal oils and fats",
        "year": 2023, "indicator_code": "104", "indicator_name": "Exports World",
        "value": 1_500_000_000.0, "unit": "current_USD", "data_nature": "UNIDO_DERIVED_ESTIMATE",
    },
    {
        "dataset_code": "INDSTAT_R4", "country_iso3": "CIV", "country_name": "Côte d'Ivoire",
        "isic_code": "1040", "isic_description": "Vegetable and animal oils and fats",
        "year": 2022, "indicator_code": "20", "indicator_name": "Value added",
        "value": 900_000_000.0, "unit": "current_USD", "data_nature": "OFFICIAL_STATISTICS",
    },
    {
        "dataset_code": "IDSB_R4", "country_iso3": "EGY", "country_name": "Egypt",
        "isic_code": "1071", "isic_description": "Bakery products",
        "year": 2023, "indicator_code": "107", "indicator_name": "Apparent Consumption",
        "value": 5_000_000_000.0, "unit": "current_USD", "data_nature": "UNIDO_DERIVED_ESTIMATE",
    },
]


def _patch_records():
    isic4_idsb_data._load_records.cache_clear()
    isic4_idsb_data.list_covered_countries.cache_clear()
    return patch.object(isic4_idsb_data, "_load_records", lambda: list(_FAKE_RECORDS))


def teardown_module(module):
    isic4_idsb_data._load_records.cache_clear()
    isic4_idsb_data.list_covered_countries.cache_clear()


def test_manufacturing_product_classified_via_unsd_mapping():
    """1806 (chocolat) → division ISIC 10, chaîne de transformation réelle."""
    with _patch_records():
        r = get_isic_idsb_service().assess_opportunity_by_sector("1806", "CIV", "EGY")
    assert r["available"] is True
    assert r["isic4"]["code"] == "10"
    assert r["transformation_chain"]["input"]  # intrant précis non vide
    assert r["product_label"]  # libellé SH4 réel


def test_primary_product_flagged_not_manufacturing():
    """0901 (café vert) n'est pas manufacturier → analyse non applicable, pas d'invention."""
    with _patch_records():
        r = get_isic_idsb_service().assess_opportunity_by_sector("0901", "ETH", "EGY")
    assert r["available"] is False
    assert r["reason"] == "not_manufacturing"


def test_real_supply_and_demand_are_aggregated_from_idsb():
    """Offre origine et demande destination agrégées depuis les vraies mesures UNIDO."""
    with _patch_records():
        r = get_isic_idsb_service().assess_opportunity_by_sector("1806", "CIV", "EGY")
    base = r["industrial_base"]
    assert base["available"] is True
    assert base["output_usd"] == 2_000_000_000.0
    assert base["exports_world_usd"] == 1_500_000_000.0
    assert base["value_added_usd"] == 900_000_000.0
    assert base["has_official"] is True
    demand = r["market_demand"]
    assert demand["available"] is True
    assert demand["apparent_consumption_usd"] == 5_000_000_000.0
    assert r["demand_supply_balance"]["verdict"] == "supply_and_demand"
    assert r["demand_supply_balance"]["origin_exports_division"] is True


def test_uncovered_country_is_flagged_never_estimated():
    """Un pays hors des 20 couverts → indisponible explicite, aucun chiffre inventé."""
    with _patch_records():
        r = get_isic_idsb_service().assess_opportunity_by_sector("1806", "NGA", "EGY")
    assert r["available"] is True  # la classification ISIC reste disponible
    assert r["industrial_base"]["available"] is False
    assert r["industrial_base"]["reason"] == "country_not_in_unido_idsb_coverage"
    assert r["coverage"]["origin_in_idsb"] is False
    # Demande mesurée à destination mais pas d'offre → verdict honnête.
    assert r["demand_supply_balance"]["verdict"] == "demand_without_supply"


def test_hs_import_demand_counts_as_demand_signal():
    """Les imports OEC du SH exact activent la demande même hors IDSB destination."""
    with _patch_records():
        r = get_isic_idsb_service().assess_opportunity_by_sector(
            "1806", "CIV", "MAR", market_potential=750_000.0
        )
    # MAR absent du jeu IDSB mocké → demande IDSB indisponible, mais OEC la porte.
    assert r["demand_supply_balance"]["demand_measured"] is True
    assert r["demand_supply_balance"]["hs_import_demand_usd"] == 750_000.0


def test_diversification_lists_sibling_products_excluding_current():
    with _patch_records():
        r = get_isic_idsb_service().assess_opportunity_by_sector("1806", "CIV", "EGY")
    codes = {p["hs4"] for p in r["diversification_products"]}
    assert "1806" not in codes  # le produit courant est exclu
    assert codes  # d'autres produits SH4 de la division 10 sont proposés
