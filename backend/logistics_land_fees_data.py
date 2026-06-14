"""
Calculateur de fret terrestre pour les corridors routiers et ferroviaires africains.

S'appuie sur les 15 corridors PIDA majeurs (``logistics_land_data``) avec leur
longueur réelle (km), leur type (route / rail / multimodal), leurs postes-frontières
(dont OSBP) et leurs opérateurs.

Méthodologie du coût :
- Transport = taux ($/tonne-km) × tonnage × distance × coefficient marchandise
- Passages frontières = coût par poste (réduit pour les postes OSBP « guichet unique »)
- Documentation / manutention = forfait
- Délai = distance / vitesse effective + délais de franchissement des frontières

Calibrage / sources :
- Banque Mondiale — Africa Transport Policy (SSATP) : coûts de transport routier africains
- UNECA / CEA — Coûts des corridors de transport africains 2024
- African Development Bank — Africa Transport Corridors Cost Reports
- PIDA (Programme de Développement des Infrastructures en Afrique)

Les taux sont ESTIMÉS par un modèle calibré ; les coûts réels varient fortement
(±20-30 %) selon l'état des routes, les temps d'attente aux frontières et les pratiques.
"""
from typing import Optional, List, Dict, Any
from functools import lru_cache

import logistics_land_data

# Taux de base par mode ($/tonne-km), corridors africains (SSATP / UNECA 2024)
_RATE_TON_KM = {
    "road": 0.085,
    "rail": 0.045,
}

# Coût de franchissement par poste-frontière et par envoi ($)
_BORDER_COST_OSBP = 250.0      # poste OSBP (guichet unique, plus rapide)
_BORDER_COST_STD = 450.0       # poste-frontière classique
_HANDLING_USD = 150.0          # documentation + manutention
_MIN_CHARGE_USD = 150.0

# Vitesse effective (km/jour) incluant arrêts
_SPEED_KM_DAY = {"road": 300, "rail": 400}
# Délai de franchissement par poste (jours)
_BORDER_DELAY_OSBP = 0.5
_BORDER_DELAY_STD = 1.5

# Paramètres multimodal (rail + route)
_RAIL_SHARE = 0.65          # part de la distance par rail (tronçon principal)
_ROAD_SHARE = 0.35          # part par camion (premier/dernier km + tronçons sans rail)
_TRANSSHIP_PER_TON = 7.0    # coût de transbordement par tonne et par rupture de charge
_TRANSSHIPMENTS = 2         # nombre de ruptures de charge (rail↔route)
_TRANSSHIP_DELAY = 0.75     # délai par rupture de charge (jours)

# Coefficients par nature de marchandise
CARGO_FACTORS = {
    "general": {"factor": 1.0, "label_fr": "Marchandise générale", "label_en": "General cargo"},
    "container": {"factor": 1.05, "label_fr": "Conteneurisé", "label_en": "Containerised"},
    "perishable": {"factor": 1.25, "label_fr": "Périssable (camion frigo)", "label_en": "Perishable (reefer)"},
    "dangerous": {"factor": 1.30, "label_fr": "Marchandise dangereuse (ADR)", "label_en": "Dangerous goods (ADR)"},
    "bulk": {"factor": 0.90, "label_fr": "Vrac", "label_en": "Bulk"},
}


def _count_borders(corridor: Dict[str, Any]) -> tuple:
    nodes = corridor.get("nodes", []) or []
    borders = [n for n in nodes if n.get("node_type") == "border_crossing"]
    osbp = [n for n in borders if n.get("is_osbp")]
    return len(borders), len(osbp)


def _modes_for(corridor_type: str) -> List[str]:
    if corridor_type == "road":
        return ["road"]
    if corridor_type == "rail":
        return ["rail"]
    return ["multimodal", "rail", "road"]  # multimodal : combiné par défaut


@lru_cache(maxsize=1)
def _corridor_index() -> Dict[str, Dict[str, Any]]:
    idx: Dict[str, Dict[str, Any]] = {}
    for c in logistics_land_data.get_all_corridors():
        borders, osbp = _count_borders(c)
        operators = [
            {"name": o.get("operator_name"), "type": o.get("operator_type")}
            for o in (c.get("operators") or [])
            if o.get("operator_name")
        ]
        idx[c["corridor_id"]] = {
            "corridor_id": c["corridor_id"],
            "name": c.get("corridor_name"),
            "type": c.get("corridor_type"),
            "length_km": c.get("length_km", 0),
            "countries": c.get("countries_spanned", []),
            "importance": c.get("importance"),
            "start_node": c.get("start_node"),
            "end_node": c.get("end_node"),
            "status": c.get("status", "Opérationnel"),
            "infra_details": c.get("infra_details"),
            "source_org": c.get("source_org"),
            "borders": borders,
            "osbp": osbp,
            "modes": _modes_for(c.get("corridor_type", "road")),
            "operators": operators,
        }
    return idx


# ------------------------------------------------------------------
# API publique
# ------------------------------------------------------------------
def get_land_corridors_list() -> List[Dict[str, Any]]:
    """Liste des corridors sélectionnables (triés par nom)."""
    items = list(_corridor_index().values())
    items.sort(key=lambda x: (x["name"] or ""))
    return items


def get_cargo_types() -> List[Dict[str, Any]]:
    return [
        {"value": k, "label_fr": v["label_fr"], "label_en": v["label_en"], "factor": v["factor"]}
        for k, v in CARGO_FACTORS.items()
    ]


def get_land_freight_cost(
    corridor_id: str,
    mode: str = "road",
    weight_tons: float = 30.0,
    cargo_type: str = "general",
) -> Optional[Dict[str, Any]]:
    """
    Calcule le coût de fret terrestre sur un corridor donné.

    Args:
        corridor_id : identifiant du corridor (ex: CORR-ABIDJAN-LAGOS-002)
        mode : 'road' ou 'rail' (doit être disponible pour le corridor)
        weight_tons : tonnage transporté (tonnes)
        cargo_type : nature de la marchandise (clé de CARGO_FACTORS)
    """
    corridor = _corridor_index().get(corridor_id)
    if not corridor:
        return None
    if weight_tons is None or weight_tons <= 0:
        return None

    mode = mode.lower()
    if mode not in corridor["modes"]:
        mode = corridor["modes"][0]

    cargo = CARGO_FACTORS.get(cargo_type, CARGO_FACTORS["general"])
    length = corridor["length_km"]
    factor = cargo["factor"]

    if mode == "multimodal":
        rail_km = length * _RAIL_SHARE
        road_km = length * _ROAD_SHARE
        transport = (
            _RATE_TON_KM["rail"] * weight_tons * rail_km * factor
            + _RATE_TON_KM["road"] * weight_tons * road_km * factor
        )
        transshipment = _TRANSSHIP_PER_TON * weight_tons * _TRANSSHIPMENTS
        travel_days = rail_km / _SPEED_KM_DAY["rail"] + road_km / _SPEED_KM_DAY["road"]
        travel_days += _TRANSSHIP_DELAY * _TRANSSHIPMENTS
        rate_display = round((transport / weight_tons / length), 4) if length else 0
    else:
        rail_km = length if mode == "rail" else 0
        road_km = length if mode == "road" else 0
        transport = _RATE_TON_KM[mode] * weight_tons * length * factor
        transshipment = 0.0
        travel_days = length / _SPEED_KM_DAY[mode]
        rate_display = _RATE_TON_KM[mode]

    border_cost = corridor["osbp"] * _BORDER_COST_OSBP + (corridor["borders"] - corridor["osbp"]) * _BORDER_COST_STD
    subtotal = transport + transshipment + border_cost + _HANDLING_USD
    total = max(subtotal, _MIN_CHARGE_USD)

    # Délais
    border_days = corridor["osbp"] * _BORDER_DELAY_OSBP + (corridor["borders"] - corridor["osbp"]) * _BORDER_DELAY_STD
    transit_min = max(1, int(round(travel_days + border_days)))
    transit_max = transit_min + max(1, corridor["borders"]) + 1

    # Opérateurs pertinents pour le mode choisi
    if mode == "rail":
        operators = [o["name"] for o in corridor["operators"] if o["type"] == "rail_operator"]
    elif mode == "road":
        operators = [o["name"] for o in corridor["operators"] if o["type"] == "trucking_company"]
    else:  # multimodal : rail + route
        operators = [o["name"] for o in corridor["operators"]]
    if not operators:
        operators = [o["name"] for o in corridor["operators"]]

    if mode == "multimodal":
        notes = (
            f"Estimation multimodale A→B : tronçon principal par rail (~{round(rail_km)} km) + "
            f"acheminement/desserte par camion (~{round(road_km)} km) + {_TRANSSHIPMENTS} ruptures de "
            "charge (transbordement rail↔route). Coûts et délais combinés."
        )
    else:
        notes = (
            "Coût = transport ($/tonne-km × tonnage × distance) + franchissement frontières "
            "(réduit pour les postes OSBP) + documentation."
        )

    return {
        "corridor_id": corridor_id,
        "corridor_name": corridor["name"],
        "mode": mode,
        "corridor_type": corridor["type"],
        "countries": corridor["countries"],
        "length_km": length,
        "weight_tons": round(weight_tons, 2),
        "cargo_type": cargo_type,
        "cargo_label": cargo["label_fr"],
        "cargo_factor": cargo["factor"],
        "rate_per_ton_km_usd": rate_display,
        "rail_km": round(rail_km),
        "road_km": round(road_km),
        "border_crossings": corridor["borders"],
        "osbp_crossings": corridor["osbp"],
        "transport_cost_usd": round(transport),
        "transshipment_cost_usd": round(transshipment),
        "border_cost_usd": round(border_cost),
        "handling_usd": round(_HANDLING_USD),
        "total_cost_usd": round(total),
        "cost_per_ton_usd": round(total / weight_tons, 2),
        "cost_per_ton_km_usd": round(total / (weight_tons * length), 4) if length else 0,
        "transit_days_min": transit_min,
        "transit_days_max": transit_max,
        "operators": operators[:4],
        "currency": "USD",
        "data_year": 2024,
        "is_modeled": True,
        "source": "Modèle distance-coût calibré — Banque Mondiale SSATP / UNECA / AfDB (coûts corridors africains 2024)",
        "notes": notes,
        "disclaimer": (
            "Tarif ESTIMÉ par modèle calibré. Les coûts réels varient ±20-30 % selon l'état des "
            "infrastructures, les temps d'attente aux frontières, le carburant et les pratiques locales. "
            "Hors droits de douane, escortes et frais informels."
        ),
    }
