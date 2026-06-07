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
    return ["road", "rail"]  # multimodal


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
    rate = _RATE_TON_KM[mode]

    transport = rate * weight_tons * length * cargo["factor"]
    border_cost = corridor["osbp"] * _BORDER_COST_OSBP + (corridor["borders"] - corridor["osbp"]) * _BORDER_COST_STD
    subtotal = transport + border_cost + _HANDLING_USD
    total = max(subtotal, _MIN_CHARGE_USD)

    # Délais
    travel_days = length / _SPEED_KM_DAY[mode]
    border_days = corridor["osbp"] * _BORDER_DELAY_OSBP + (corridor["borders"] - corridor["osbp"]) * _BORDER_DELAY_STD
    transit_min = max(1, int(round(travel_days + border_days)))
    transit_max = transit_min + max(1, corridor["borders"]) + 1

    # Opérateurs pertinents pour le mode choisi
    op_type = "rail_operator" if mode == "rail" else "trucking_company"
    operators = [o["name"] for o in corridor["operators"] if o["type"] == op_type] or \
                [o["name"] for o in corridor["operators"]]

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
        "rate_per_ton_km_usd": rate,
        "border_crossings": corridor["borders"],
        "osbp_crossings": corridor["osbp"],
        "transport_cost_usd": round(transport),
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
        "notes": (
            "Coût = transport ($/tonne-km × tonnage × distance) + franchissement frontières "
            "(réduit pour les postes OSBP) + documentation. Mode : route ou rail."
        ),
        "disclaimer": (
            "Tarif ESTIMÉ par modèle calibré. Les coûts réels varient ±20-30 % selon l'état des "
            "infrastructures, les temps d'attente aux frontières, le carburant et les pratiques locales. "
            "Hors droits de douane, escortes et frais informels."
        ),
    }
