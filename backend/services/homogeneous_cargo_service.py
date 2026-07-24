"""
Homogeneous Cargo Service — centralized handler for bulk, liquid, and uniform shipments.

Coordinates classification, mode selection, and cost calculation for:
  - Dry bulk (vraquier / bulk carriers) — cereals, ores, coal, fertilizers
  - Liquid bulk (tanker market) — crude oil, petroleum products
  - General cargo — high-value containerizable goods

Uses data from logistics_bulk_fees_data for vraquier costing and logistics_fees_data
for containerized reference.

Determines:
  1. Cargo type classification (dry bulk, liquid bulk, general cargo)
  2. Shipping mode selection (sea_bulk vs containerized based on weight threshold)
  3. Defers vessel selection and cost to logistics_bulk_fees_data (Lot A calibration)
  4. Multiple-voyage scenarios for lots exceeding single-vessel capacity
"""

import logging
from typing import Any, Dict, List, Optional

_log = logging.getLogger(__name__)


def classify_homogeneous_cargo(
    bulk_commodity_dict: Optional[Dict[str, Any]],
) -> Optional[Dict[str, Any]]:
    """
    Classify a commodity as homogeneous cargo and return its shipping profile.
    Returns None if not homogeneous cargo (e.g., containerizable goods).
    """
    if not bulk_commodity_dict:
        return None

    return {
        "category": bulk_commodity_dict.get("category"),
        "is_liquid": bulk_commodity_dict.get("is_liquid", False),
        "container_threshold_tonnes": bulk_commodity_dict.get("container_threshold_tonnes", 2000.0),
        "vessel_classes": bulk_commodity_dict.get("vessel_classes"),
        "label": bulk_commodity_dict.get("label"),
    }


def select_shipping_mode(
    weight_kg: float,
    homogeneous_cargo: Optional[Dict[str, Any]],
) -> str:
    """
    Determine whether to use sea_bulk or containerized mode.

    Returns: "sea_bulk" if weight exceeds threshold, "containerized" otherwise.
    """
    if not homogeneous_cargo:
        return "containerized"

    threshold_kg = homogeneous_cargo.get("container_threshold_tonnes", 2000.0) * 1000.0
    return "sea_bulk" if weight_kg >= threshold_kg else "containerized"


def get_bulk_freight_option(
    origin_locode: str,
    destination_locode: str,
    weight_kg: float,
    homogeneous_cargo: Optional[Dict[str, Any]],
) -> Optional[Dict[str, Any]]:
    """
    Unified entry point for homogeneous cargo freight costing.

    Calls logistics_bulk_fees_data.get_bulk_freight_cost() and wraps the result
    for integration into multimodal freight comparator.

    Args:
        origin_locode: Port LOCODE (e.g., "ZASIZ")
        destination_locode: Port LOCODE (e.g., "DZALG")
        weight_kg: Shipment weight in kg
        homogeneous_cargo: Commodity classification from classify_homogeneous_cargo()

    Returns:
        Formatted bulk freight option dict or None if not applicable/available.
    """
    if not homogeneous_cargo or not origin_locode or not destination_locode:
        return None

    try:
        from logistics_bulk_fees_data import get_bulk_freight_cost

        weight_tonnes = weight_kg / 1000.0
        result = get_bulk_freight_cost(
            origin_locode,
            destination_locode,
            weight_tonnes,
            allowed_classes=homogeneous_cargo.get("vessel_classes"),
        )
        return result
    except ImportError:
        _log.warning("logistics_bulk_fees_data not available")
        return None
    except Exception as e:
        _log.warning("bulk freight costing failed: %s", e)
        return None
