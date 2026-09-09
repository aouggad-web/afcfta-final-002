"""
Logistics adapter for the premium Opportunités report engine.

Thin wrapper over the platform's *existing* multimodal freight comparator and
free-zone dataset. It exposes, for an (origin → destination) pair, the freight
options, the cheapest operational route (a real cost input to the landed-cost
indicator) and the free zones available at destination.

No fabrication: costs come straight from the underlying modules (which already
flag ``is_modeled`` and carry disclaimers); when a module is unavailable the
adapter returns ``available: False`` with a note.

The multimodal service keys on ISO3 country codes; free zones on ISO3 too.
"""

import logging
from typing import Dict, List, Optional

_log = logging.getLogger(__name__)


def get_freight_options(
    origin_iso3: str,
    destination_iso3: str,
    weight_kg: float = 21600.0,
    volume_m3: float = 33.5,
    container_type: str = "teu",
    hs_code: Optional[str] = None,
) -> Dict:
    """Full multimodal comparison for the pair (sea/air/land/multimodal).

    ``hs_code``, when provided, is used to detect a genuine bulk commodity
    (cement, ores, cereals, coal, crude oil, fertilizers...) so the air option
    is never offered for it and the land leg defaults to "bulk" cargo instead
    of "container" — see ``services.shipment_estimator.classify_bulk_commodity``.
    """
    try:
        from services.multimodal_freight_service import compare_multimodal
        from services.shipment_estimator import classify_bulk_commodity

        bulk = classify_bulk_commodity(hs_code) if hs_code else None
        result = compare_multimodal(
            (origin_iso3 or "").upper(),
            (destination_iso3 or "").upper(),
            weight_kg,
            volume_m3=volume_m3,
            container_type=container_type,
            is_bulk_commodity=bool(bulk),
            bulk_label=bulk.get("label") if bulk else None,
            bulk_commodity_dict=bulk,
        )
        return {"available": True, **result}
    except Exception as exc:
        _log.warning("multimodal comparison unavailable: %s", exc)
        return {"available": False, "options": [], "note": str(exc)}


def _cheapest_operational(options: List[Dict]) -> Optional[Dict]:
    operational = [o for o in options if o.get("available") and o.get("total_cost_usd") is not None]
    if not operational:
        return None
    return min(operational, key=lambda o: o["total_cost_usd"])


def get_free_zones(destination_iso3: str) -> Dict:
    """Free / special economic zones at the destination market."""
    try:
        from free_zones_data import get_free_zones_by_country

        zones = get_free_zones_by_country((destination_iso3 or "").upper())
        return {"available": True, "zones": zones or [], "count": len(zones or [])}
    except Exception as exc:
        _log.warning("free zones unavailable: %s", exc)
        return {"available": False, "zones": [], "count": 0, "note": str(exc)}


def get_logistics_profile(
    origin_iso3: str,
    destination_iso3: str,
    weight_kg: float = 21600.0,
    volume_m3: float = 33.5,
    container_type: str = "teu",
    hs_code: Optional[str] = None,
) -> Dict:
    """Compose the logistics view for an origin → destination shipment."""
    freight = get_freight_options(
        origin_iso3, destination_iso3, weight_kg, volume_m3, container_type, hs_code=hs_code
    )
    options = freight.get("options", []) if freight.get("available") else []
    cheapest = _cheapest_operational(options)
    return {
        "origin_iso3": (origin_iso3 or "").upper(),
        "destination_iso3": (destination_iso3 or "").upper(),
        "freight": freight,
        "cheapest_operational_option": cheapest,
        "best_operational_cost_usd": cheapest.get("total_cost_usd") if cheapest else None,
        "free_zones": get_free_zones(destination_iso3),
    }


def summarize_logistics_accessibility(profile: Dict) -> Dict:
    """
    Transparent logistics-accessibility index in [0, 1].

    Based on how many freight modes are actually *operational* for the pair and
    the feasibility of the cheapest one. Returns ``available: False`` when the
    freight comparator could not be reached.
    """
    freight = profile.get("freight") or {}
    if not freight.get("available"):
        return {"available": False, "index": None, "note": freight.get("note")}

    # Nombre de MODES distincts opérationnels — pas le nombre brut d'options.
    # `compare_multimodal` peut renvoyer plusieurs options pour un même mode
    # (ex. deux itinéraires maritimes) ; les compter séparément surestimerait
    # l'accessibilité d'un corridor qui ne dispose en réalité que d'un seul
    # mode de transport (ex. mer uniquement).
    options = freight.get("options")
    if options:
        operational = len(
            {o.get("mode") for o in options if not o.get("is_future") and o.get("mode")}
        )
    else:
        operational = freight.get("operational_count")
        if operational is None:
            operational = 0

    cheapest = profile.get("cheapest_operational_option") or {}
    feasibility = (cheapest.get("feasibility") or "").lower()
    feas_bonus = {"high": 0.3, "medium": 0.15, "low": 0.05}.get(feasibility, 0.0)

    # 0 operational -> 0.0 ; each operational mode adds up to 0.7 (capped at 3).
    base = min(operational, 3) / 3.0 * 0.7
    index = round(min(base + feas_bonus, 1.0), 3)
    return {
        "available": True,
        "index": index,
        "operational_modes": operational,
        "cheapest_feasibility": feasibility or None,
    }
