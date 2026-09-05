"""
Calculateur de fret aérien pour les aéroports cargo africains.

Couvre les 64 aéroports du registre cargo panafricain (``logistics_air_data``).
Le calcul suit la méthodologie standard du fret aérien :
- Poids taxable = max(poids réel, poids volumétrique) avec 1 m³ = 167 kg (norme IATA TACT).
- Coût = fret aérien (taux/kg × poids taxable) + surcharge carburant (FSC)
  + surcharge sûreté (SSC) + manutention/LTA, avec une charge minimale.

Sources / calibrage :
- IATA TACT (The Air Cargo Tariff) 2024 — barèmes généraux de fret aérien
- Tarifs cargo publiés des compagnies africaines (Ethiopian Cargo, Kenya Airways Cargo,
  EgyptAir Cargo, Royal Air Maroc Cargo, ASKY, TAAG, South African Airways Cargo)
- IATA Air Cargo Market Analysis 2024 ; AFRAA Annual Report 2024

Les taux sont ESTIMÉS par un modèle distance-coût calibré ; les tarifs réels varient
fortement (±25-35 %) selon la compagnie, la capacité, la saisonnalité et la nature de
la marchandise.
"""

from functools import lru_cache
from math import asin, cos, radians, sin, sqrt
from typing import Any, Dict, List, Optional

import logistics_air_data

# Drapeau + région (FR) par code ISO3 — aéroports africains
COUNTRY_META: Dict[str, Dict[str, str]] = {
    # Afrique du Nord
    "DZA": {"flag": "🇩🇿", "region": "Afrique du Nord"},
    "EGY": {"flag": "🇪🇬", "region": "Afrique du Nord"},
    "LBY": {"flag": "🇱🇾", "region": "Afrique du Nord"},
    "MAR": {"flag": "🇲🇦", "region": "Afrique du Nord"},
    "TUN": {"flag": "🇹🇳", "region": "Afrique du Nord"},
    # Afrique de l'Ouest
    "BEN": {"flag": "🇧🇯", "region": "Afrique de l'Ouest"},
    "BFA": {"flag": "🇧🇫", "region": "Afrique de l'Ouest"},
    "CPV": {"flag": "🇨🇻", "region": "Afrique de l'Ouest"},
    "CIV": {"flag": "🇨🇮", "region": "Afrique de l'Ouest"},
    "GMB": {"flag": "🇬🇲", "region": "Afrique de l'Ouest"},
    "GHA": {"flag": "🇬🇭", "region": "Afrique de l'Ouest"},
    "GIN": {"flag": "🇬🇳", "region": "Afrique de l'Ouest"},
    "GNB": {"flag": "🇬🇼", "region": "Afrique de l'Ouest"},
    "LBR": {"flag": "🇱🇷", "region": "Afrique de l'Ouest"},
    "MLI": {"flag": "🇲🇱", "region": "Afrique de l'Ouest"},
    "MRT": {"flag": "🇲🇷", "region": "Afrique de l'Ouest"},
    "NER": {"flag": "🇳🇪", "region": "Afrique de l'Ouest"},
    "NGA": {"flag": "🇳🇬", "region": "Afrique de l'Ouest"},
    "SEN": {"flag": "🇸🇳", "region": "Afrique de l'Ouest"},
    "SLE": {"flag": "🇸🇱", "region": "Afrique de l'Ouest"},
    "TGO": {"flag": "🇹🇬", "region": "Afrique de l'Ouest"},
    # Afrique Centrale
    "AGO": {"flag": "🇦🇴", "region": "Afrique Centrale"},
    "CMR": {"flag": "🇨🇲", "region": "Afrique Centrale"},
    "CAF": {"flag": "🇨🇫", "region": "Afrique Centrale"},
    "TCD": {"flag": "🇹🇩", "region": "Afrique Centrale"},
    "COG": {"flag": "🇨🇬", "region": "Afrique Centrale"},
    "COD": {"flag": "🇨🇩", "region": "Afrique Centrale"},
    "GNQ": {"flag": "🇬🇶", "region": "Afrique Centrale"},
    "GAB": {"flag": "🇬🇦", "region": "Afrique Centrale"},
    "STP": {"flag": "🇸🇹", "region": "Afrique Centrale"},
    # Afrique de l'Est
    "BDI": {"flag": "🇧🇮", "region": "Afrique de l'Est"},
    "DJI": {"flag": "🇩🇯", "region": "Afrique de l'Est"},
    "ERI": {"flag": "🇪🇷", "region": "Afrique de l'Est"},
    "ETH": {"flag": "🇪🇹", "region": "Afrique de l'Est"},
    "KEN": {"flag": "🇰🇪", "region": "Afrique de l'Est"},
    "MWI": {"flag": "🇲🇼", "region": "Afrique de l'Est"},
    "RWA": {"flag": "🇷🇼", "region": "Afrique de l'Est"},
    "SOM": {"flag": "🇸🇴", "region": "Afrique de l'Est"},
    "SSD": {"flag": "🇸🇸", "region": "Afrique de l'Est"},
    "SDN": {"flag": "🇸🇩", "region": "Afrique de l'Est"},
    "TZA": {"flag": "🇹🇿", "region": "Afrique de l'Est"},
    "UGA": {"flag": "🇺🇬", "region": "Afrique de l'Est"},
    # Afrique Australe
    "BWA": {"flag": "🇧🇼", "region": "Afrique Australe"},
    "LSO": {"flag": "🇱🇸", "region": "Afrique Australe"},
    "MOZ": {"flag": "🇲🇿", "region": "Afrique Australe"},
    "NAM": {"flag": "🇳🇦", "region": "Afrique Australe"},
    "ZAF": {"flag": "🇿🇦", "region": "Afrique Australe"},
    "SWZ": {"flag": "🇸🇿", "region": "Afrique Australe"},
    "ZMB": {"flag": "🇿🇲", "region": "Afrique Australe"},
    "ZWE": {"flag": "🇿🇼", "region": "Afrique Australe"},
    # Océan Indien
    "COM": {"flag": "🇰🇲", "region": "Océan Indien"},
    "MDG": {"flag": "🇲🇬", "region": "Océan Indien"},
    "MUS": {"flag": "🇲🇺", "region": "Océan Indien"},
    "SYC": {"flag": "🇸🇨", "region": "Océan Indien"},
}

# Hubs cargo majeurs (vols directs probables)
_HUBS = {"ADD", "NBO", "JNB", "CAI", "CMN", "LOS", "DSS", "KGL", "MRU"}

# Compagnies cargo par région
_REGION_CARRIERS = {
    "Afrique du Nord": ["Royal Air Maroc Cargo", "EgyptAir Cargo", "Air Algérie", "Tunisair"],
    "Afrique de l'Ouest": ["ASKY", "Air Côte d'Ivoire", "Ethiopian Cargo", "Royal Air Maroc Cargo"],
    "Afrique Centrale": ["ASKY", "Ethiopian Cargo", "Kenya Airways Cargo"],
    "Afrique de l'Est": ["Ethiopian Cargo", "Kenya Airways Cargo", "RwandAir", "Astral Aviation"],
    "Afrique Australe": ["South African Airways Cargo", "Ethiopian Cargo", "Airlink"],
    "Océan Indien": ["Air Austral", "Kenya Airways Cargo", "Ethiopian Cargo"],
}

# Multiplicateurs par nature de marchandise (TACT commodity factors)
COMMODITY_FACTORS = {
    "general": {"factor": 1.0, "label_fr": "Marchandise générale", "label_en": "General cargo"},
    "perishable": {
        "factor": 1.18,
        "label_fr": "Périssable (chaîne du froid)",
        "label_en": "Perishable (cold chain)",
    },
    "pharma": {
        "factor": 1.45,
        "label_fr": "Pharmaceutique / temp. contrôlée",
        "label_en": "Pharma / temp-controlled",
    },
    "dangerous": {
        "factor": 1.55,
        "label_fr": "Marchandise dangereuse (DGR)",
        "label_en": "Dangerous goods (DGR)",
    },
    "valuable": {"factor": 1.65, "label_fr": "Valeur / sécurisé", "label_en": "Valuable / secured"},
    "live": {"factor": 1.40, "label_fr": "Animaux vivants", "label_en": "Live animals"},
}

VOLUMETRIC_FACTOR = 167.0  # kg par m³ (norme IATA TACT)
MIN_CHARGE_USD = 120.0
FSC_PER_KG = 0.65  # surcharge carburant
SSC_PER_KG = 0.12  # surcharge sûreté
AWB_FEE_USD = 40.0  # frais de LTA (AWB)
TERMINAL_PER_KG = 0.09  # manutention terminal


@lru_cache(maxsize=1)
def _airport_registry() -> Dict[str, Dict[str, Any]]:
    """Construit le registre {IATA: {...}} à partir des données aéroports."""
    reg: Dict[str, Dict[str, Any]] = {}
    for a in logistics_air_data.get_all_airports():
        iata = a.get("iata_code")
        lat, lon = a.get("geo_lat"), a.get("geo_lon")
        if not iata or lat is None or lon is None:
            continue
        iso = a.get("country_iso", "")
        meta = COUNTRY_META.get(iso, {"flag": "🌍", "region": "Afrique"})
        # Nom de ville court (partie avant le tiret)
        full = a.get("airport_name", iata)
        city = full.split(" - ")[0].strip() if " - " in full else full
        reg[iata] = {
            "iata": iata,
            "name": city,
            "full_name": full,
            "country": a.get("country_name", iso),
            "iso": iso,
            "flag": meta["flag"],
            "region": meta["region"],
            "lat": lat,
            "lon": lon,
            "is_hub": iata in _HUBS,
        }
    return reg


def _haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    r_km = 6371.0
    dlat = radians(lat2 - lat1)
    dlon = radians(lon2 - lon1)
    a = sin(dlat / 2) ** 2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlon / 2) ** 2
    return 2 * r_km * asin(sqrt(a))


def _air_distance_km(o: str, d: str) -> int:
    reg = _airport_registry()
    a, b = reg[o], reg[d]
    direct = _haversine_km(a["lat"], a["lon"], b["lat"], b["lon"])
    # Si aucun des deux n'est un hub, le routage passe souvent par un hub → +12%
    factor = 1.06 if (a["is_hub"] or b["is_hub"]) else 1.18
    return int(round(direct * factor))


def _rate_per_kg(dist_km: int) -> float:
    """Taux de base $/kg en fonction de la distance (calibré IATA TACT 2024)."""
    rate = 1.5 + 0.00040 * dist_km
    return max(1.6, min(4.8, rate))


def _carriers_air(o: str, d: str) -> List[str]:
    reg = _airport_registry()
    regions = [reg[o]["region"], reg[d]["region"]]
    out: List[str] = []
    for r in regions:
        for c in _REGION_CARRIERS.get(r, []):
            if c not in out:
                out.append(c)
    # Royal Air Maroc Cargo n'opère plus en Algérie : l'exclure des routes touchant un aéroport algérien
    if reg[o]["iso"] == "DZA" or reg[d]["iso"] == "DZA":
        out = [c for c in out if c != "Royal Air Maroc Cargo"]
    if "Ethiopian Cargo" not in out:
        out.append("Ethiopian Cargo")
    return out[:4]


def _transit_days(o: str, d: str) -> tuple:
    reg = _airport_registry()
    both_hub_side = reg[o]["is_hub"] or reg[d]["is_hub"]
    if both_hub_side:
        return 1, 3  # direct ou 1 correspondance
    return 2, 4  # via hub, double correspondance


# ------------------------------------------------------------------
# API publique
# ------------------------------------------------------------------
def get_air_fee_airports() -> List[Dict[str, Any]]:
    """Liste des aéroports sélectionnables (triés par région puis nom)."""
    reg = _airport_registry()
    return [
        {
            "iata": a["iata"],
            "name": a["name"],
            "country": a["country"],
            "iso": a["iso"],
            "flag": a["flag"],
            "region": a["region"],
            "is_hub": a["is_hub"],
        }
        for a in sorted(reg.values(), key=lambda x: (x["region"], x["name"]))
    ]


def get_commodity_types() -> List[Dict[str, Any]]:
    return [
        {"value": k, "label_fr": v["label_fr"], "label_en": v["label_en"], "factor": v["factor"]}
        for k, v in COMMODITY_FACTORS.items()
    ]


def get_air_freight_cost(
    origin_iata: str,
    destination_iata: str,
    weight_kg: float,
    volume_m3: Optional[float] = None,
    commodity: str = "general",
) -> Optional[Dict[str, Any]]:
    """
    Calcule le coût de fret aérien pour un envoi entre deux aéroports africains.

    Args:
        origin_iata / destination_iata : codes IATA (ex: NBO, LOS)
        weight_kg : poids brut réel (kg)
        volume_m3 : volume total (m³) — sert au calcul du poids volumétrique
        commodity : nature de la marchandise (clé de COMMODITY_FACTORS)
    """
    o, d = origin_iata.upper(), destination_iata.upper()
    reg = _airport_registry()
    if o not in reg or d not in reg or o == d:
        return None
    if weight_kg is None or weight_kg <= 0:
        return None

    comm = COMMODITY_FACTORS.get(commodity, COMMODITY_FACTORS["general"])

    dist_km = _air_distance_km(o, d)
    volumetric_kg = round((volume_m3 or 0) * VOLUMETRIC_FACTOR, 1)
    chargeable_kg = round(max(weight_kg, volumetric_kg), 1)

    base_rate = _rate_per_kg(dist_km)
    rate_per_kg = round(base_rate * comm["factor"], 2)

    air_freight = rate_per_kg * chargeable_kg
    fsc = FSC_PER_KG * chargeable_kg
    ssc = SSC_PER_KG * chargeable_kg
    handling = AWB_FEE_USD + TERMINAL_PER_KG * chargeable_kg
    subtotal = air_freight + fsc + ssc + handling
    total = max(subtotal, MIN_CHARGE_USD)
    min_charge_applied = subtotal < MIN_CHARGE_USD

    tmin, tmax = _transit_days(o, d)
    a, b = reg[o], reg[d]

    return {
        "origin_iata": o,
        "destination_iata": d,
        "origin_airport": a["full_name"],
        "destination_airport": b["full_name"],
        "origin_country": a["country"],
        "destination_country": b["country"],
        "origin_region": a["region"],
        "destination_region": b["region"],
        "distance_km": dist_km,
        "commodity": commodity,
        "commodity_label": comm["label_fr"],
        "commodity_factor": comm["factor"],
        "actual_weight_kg": round(weight_kg, 1),
        "volume_m3": round(volume_m3, 2) if volume_m3 else 0,
        "volumetric_weight_kg": volumetric_kg,
        "chargeable_weight_kg": chargeable_kg,
        "rate_per_kg_usd": rate_per_kg,
        "air_freight_usd": round(air_freight),
        "fuel_surcharge_usd": round(fsc),
        "security_surcharge_usd": round(ssc),
        "handling_awb_usd": round(handling),
        "total_cost_usd": round(total),
        "min_charge_applied": min_charge_applied,
        "transit_days_min": tmin,
        "transit_days_max": tmax,
        "carriers": _carriers_air(o, d),
        "currency": "USD",
        "data_year": 2024,
        "is_modeled": True,
        "source": "Modèle distance-coût calibré — IATA TACT 2024 & tarifs cargo compagnies africaines",
        "notes": (
            "Poids taxable = max(poids réel, poids volumétrique à 167 kg/m³). "
            "FSC = surcharge carburant, SSC = surcharge sûreté, LTA = frais de lettre de transport aérien."
        ),
        "disclaimer": (
            "Tarif ESTIMÉ par modèle calibré (IATA TACT 2024). Les tarifs réels varient ±25-35 % selon "
            "la compagnie, la capacité disponible, la saison et la nature de la marchandise. "
            "Hors droits de douane, assurance et acheminement terrestre."
        ),
    }
