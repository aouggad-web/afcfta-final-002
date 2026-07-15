"""
Fret maritime vraquier (bulk carrier) — classes de navires, contraintes
portuaires et modèle de coût USD/tonne.

Lot A du plan docs/PLAN_FRET_VRAQUIER.md : données socle, sans impact
utilisateur tant que le comparateur multimodal n'est pas branché (Lot B).

DISCIPLINE « zéro fabrication » :
- Aucun tarif vraquier intra-africain publié n'étant disponible de façon
  fiable, TOUTES les routes sont modélisées (``is_modeled: True``) par un
  modèle distance-coût par classe de navire, calibré sur des routes de
  référence mondiales publiées (_CALIBRATION_BENCHMARKS, chacune datée et
  sourcée). Le marché vraquier étant plus volatil que le conteneur, la
  fourchette affichée est ±30 %.
- Les frais portuaires vrac sont un ordre de grandeur régional modélisé,
  jamais présenté comme un barème officiel.
- Les attributs portuaires (tirant d'eau, terminaux) proviennent des fiches
  des autorités portuaires ; tant qu'ils ne sont pas recoupés, ils portent
  ``verified: False`` et un attribut absent n'applique AUCUNE contrainte
  (marqué « non vérifié » côté sortie).

La distance maritime réutilise ``_sea_distance_nm`` de logistics_fees_data —
même distance pour une paire de ports, que le mode soit conteneur ou vrac.
"""

from __future__ import annotations

import json
import math
import os
from typing import Any, Dict, List, Optional

from logistics_fees_data import PORTS, _sea_distance_nm

# ---------------------------------------------------------------------------
# Classes de navires vraquiers (vrac sec)
# ---------------------------------------------------------------------------
# ``freight_factor`` : multiplicateur du modèle distance-coût (plus le navire
# est grand, plus le coût par tonne baisse). ``co2_g_per_tkm`` : ordre de
# grandeur par classe (IMO 4th GHG Study 2020 / GLEC Framework v3).
# ``loaded_draft_m`` : tirant d'eau en charge typique, utilisé pour plafonner
# la classe admissible dans un port.
VESSEL_CLASSES: Dict[str, Dict[str, Any]] = {
    "handysize": {
        "label": "Handysize",
        "min_dwt": 10_000,
        "max_dwt": 39_999,
        "max_parcel_t": 35_000,
        "loaded_draft_m": 10.0,
        "freight_factor": 1.0,
        "co2_g_per_tkm": 8.5,
    },
    "supramax": {
        "label": "Supramax/Ultramax",
        "min_dwt": 40_000,
        "max_dwt": 64_999,
        "max_parcel_t": 57_000,
        "loaded_draft_m": 12.5,
        "freight_factor": 0.82,
        "co2_g_per_tkm": 6.0,
    },
    "panamax": {
        "label": "Panamax/Kamsarmax",
        "min_dwt": 65_000,
        "max_dwt": 99_999,
        "max_parcel_t": 90_000,
        "loaded_draft_m": 13.5,
        "freight_factor": 0.66,
        "co2_g_per_tkm": 4.5,
    },
    "capesize": {
        "label": "Capesize",
        "min_dwt": 100_000,
        "max_dwt": 220_000,
        "max_parcel_t": 180_000,
        "loaded_draft_m": 17.5,
        "freight_factor": 0.50,
        "co2_g_per_tkm": 3.0,
    },
}

# Ordre croissant de taille, pour les plafonnements par port.
_CLASS_ORDER = ["handysize", "supramax", "panamax", "capesize"]

# ---------------------------------------------------------------------------
# Modèle distance-coût (USD/tonne, fret océanique seul)
# ---------------------------------------------------------------------------
#   USD/t = max(FLOOR, (BASE + SLOPE × distance_nm) × freight_factor(classe))
#
# Calibré sur les routes de référence ci-dessous ; écart constaté ≤ ±25 %
# sur chaque point de calibration (voir tests).
_FREIGHT_MODEL_BASE_USD_PER_T = 7.0
_FREIGHT_MODEL_SLOPE_USD_PER_T_NM = 0.004
_FREIGHT_MODEL_FLOOR_USD_PER_T = 6.0

# Routes de référence mondiales publiées, utilisées UNIQUEMENT pour calibrer
# le modèle (pas servies telles quelles) : chaque entrée porte sa valeur, sa
# période et sa source. Ordres de grandeur de moyennes annuelles 2024 — à
# rafraîchir par le Lot D (indices Baltic).
_CALIBRATION_BENCHMARKS: List[Dict[str, Any]] = [
    {
        "name": "Saldanha → Qingdao, minerai de fer (capesize)",
        "vessel_class": "capesize",
        "distance_nm": 8000,
        "usd_per_t": 22.0,
        "as_of": "moyenne 2024",
        "source": "Baltic Exchange route C17 — ordre de grandeur moyenne annuelle 2024",
    },
    {
        "name": "Golfe US → Égypte, blé (panamax)",
        "vessel_class": "panamax",
        "distance_nm": 6300,
        "usd_per_t": 25.0,
        "as_of": "moyenne 2024",
        "source": "IGC Grain Market Report — ordre de grandeur moyenne 2024",
    },
    {
        "name": "Mer Noire → Afrique du Nord, blé (handysize)",
        "vessel_class": "handysize",
        "distance_nm": 1400,
        "usd_per_t": 16.0,
        "as_of": "moyenne 2024",
        "source": "IGC Grain Market Report — ordre de grandeur moyenne 2024",
    },
    {
        "name": "Richards Bay → Inde ouest, charbon (panamax)",
        "vessel_class": "panamax",
        "distance_nm": 4300,
        "usd_per_t": 16.5,
        "as_of": "moyenne 2024",
        "source": "Baltic Exchange / marché charbon — ordre de grandeur moyenne 2024",
    },
]

# Frais portuaires vrac (chargement OU déchargement), USD/tonne — ordre de
# grandeur régional modélisé (les barèmes réels varient fortement selon le
# terminal, la cadence et la marchandise : ~3-10 USD/t).
BULK_PORT_HANDLING_USD_PER_T_LOAD = 4.5
BULK_PORT_HANDLING_USD_PER_T_DISCHARGE = 5.5

# Vitesse commerciale vraquier (nœuds) pour les délais modélisés.
_BULK_SPEED_KNOTS = 11.5

# ---------------------------------------------------------------------------
# Attributs vrac des ports du registre (progressif — Annexe A / §3.4 du plan)
# ---------------------------------------------------------------------------
# ``max_draft_m`` : tirant d'eau admissible (plafonne la classe de navire).
# ``bulk_terminals`` : équipements connus (grain, mineral, cement, coal,
# fertilizer, general).
# ``verified: False`` = ordre de grandeur issu des fiches/annuaire des
# autorités portuaires, à recouper avant toute promotion. Un port ABSENT de
# cette table n'est PAS contraint (et la sortie le signale).
BULK_PORT_ATTRIBUTES: Dict[str, Dict[str, Any]] = {
    "ZARCB": {
        "max_draft_m": 17.5,
        "bulk_terminals": ["coal", "mineral"],
        "verified": False,
        "source": "Richards Bay Coal Terminal / Transnet — fiche port",
    },
    "ZADUR": {
        "max_draft_m": 12.8,
        "bulk_terminals": ["grain", "general"],
        "verified": False,
        "source": "Transnet — fiche port",
    },
    "ZACPT": {
        "max_draft_m": 13.5,
        "bulk_terminals": ["grain", "general"],
        "verified": False,
        "source": "Transnet — fiche port",
    },
    "SNDKR": {
        "max_draft_m": 12.0,
        "bulk_terminals": ["grain", "general"],
        "verified": False,
        "source": "Port autonome de Dakar — fiche port",
    },
    "CIABJ": {
        "max_draft_m": 15.0,
        "bulk_terminals": ["grain", "general"],
        "verified": False,
        "source": "Port autonome d'Abidjan — fiche port (canal de Vridi approfondi)",
    },
    "GHTEM": {
        "max_draft_m": 16.0,
        "bulk_terminals": ["grain", "general"],
        "verified": False,
        "source": "Ghana Ports and Harbours Authority — fiche port (nouveau terminal)",
    },
    "TGLFW": {
        "max_draft_m": 16.0,
        "bulk_terminals": ["general", "cement"],
        "verified": False,
        "source": "Port autonome de Lomé — fiche port",
    },
    "GNCKY": {
        "max_draft_m": 12.0,
        "bulk_terminals": ["mineral", "general"],
        "verified": False,
        "source": "Port autonome de Conakry — fiche port",
    },
    "NGAPP": {
        "max_draft_m": 13.0,
        "bulk_terminals": ["grain", "general"],
        "verified": False,
        "source": "Nigerian Ports Authority — fiche port",
    },
    "DZALG": {
        "max_draft_m": 11.0,
        "bulk_terminals": ["grain", "cement", "general"],
        "verified": False,
        "source": "EPAL — fiche port",
    },
    "DZBJA": {
        "max_draft_m": 12.0,
        "bulk_terminals": ["grain", "general"],
        "verified": False,
        "source": "EPB Bejaia — fiche port",
    },
    "DZORN": {
        "max_draft_m": 12.0,
        "bulk_terminals": ["grain", "general"],
        "verified": False,
        "source": "EPO Oran — fiche port",
    },
    "MACAS": {
        "max_draft_m": 12.0,
        "bulk_terminals": ["grain", "fertilizer", "general"],
        "verified": False,
        "source": "ANP Maroc — fiche port",
    },
    "EGALY": {
        "max_draft_m": 13.0,
        "bulk_terminals": ["grain", "general"],
        "verified": False,
        "source": "Alexandria Port Authority — fiche port",
    },
    "EGDAM": {
        "max_draft_m": 14.0,
        "bulk_terminals": ["grain", "general"],
        "verified": False,
        "source": "Damietta Port Authority — fiche port",
    },
    "TNSFA": {
        "max_draft_m": 10.0,
        "bulk_terminals": ["mineral", "fertilizer"],
        "verified": False,
        "source": "OMMP — fiche port (phosphates)",
    },
    "TNRAD": {
        "max_draft_m": 10.5,
        "bulk_terminals": ["general"],
        "verified": False,
        "source": "OMMP — fiche port",
    },
    "KEMBA": {
        "max_draft_m": 14.0,
        "bulk_terminals": ["grain", "cement", "general"],
        "verified": False,
        "source": "Kenya Ports Authority — fiche port",
    },
    "TZDAR": {
        "max_draft_m": 13.0,
        "bulk_terminals": ["grain", "general"],
        "verified": False,
        "source": "Tanzania Ports Authority — fiche port",
    },
    "DJJIB": {
        "max_draft_m": 17.0,
        "bulk_terminals": ["grain", "fertilizer", "general"],
        "verified": False,
        "source": "Djibouti Ports (SGTD/Doraleh) — fiche port",
    },
    "MZBEW": {
        "max_draft_m": 11.0,
        "bulk_terminals": ["grain", "coal", "general"],
        "verified": False,
        "source": "CFM/Cornelder Beira — fiche port",
    },
    "MZMPM": {
        "max_draft_m": 14.0,
        "bulk_terminals": ["coal", "mineral", "grain", "general"],
        "verified": False,
        "source": "MPDC Maputo — fiche port (Matola)",
    },
    "NAWVB": {
        "max_draft_m": 14.0,
        "bulk_terminals": ["mineral", "general"],
        "verified": False,
        "source": "Namport — fiche port (sel, minéraux)",
    },
    "SDPZU": {
        "max_draft_m": 12.0,
        "bulk_terminals": ["grain", "general"],
        "verified": False,
        "source": "Sea Ports Corporation Soudan — fiche port",
    },
    "AOLOB": {
        "max_draft_m": 12.0,
        "bulk_terminals": ["mineral", "general"],
        "verified": False,
        "source": "Porto do Lobito — fiche port (corridor de Lobito)",
    },
    "CMDLA": {
        "max_draft_m": 9.0,
        "bulk_terminals": ["grain", "general"],
        "verified": False,
        "source": "Port autonome de Douala — fiche port (accès fluvial limité)",
    },
    "CMKBI": {
        "max_draft_m": 15.0,
        "bulk_terminals": ["mineral", "general"],
        "verified": False,
        "source": "Port autonome de Kribi — fiche port (eau profonde)",
    },
    "MRNKC": {
        "max_draft_m": 10.5,
        "bulk_terminals": ["general"],
        "verified": False,
        "source": "PANPA Nouakchott — fiche port (le minéralier est à Nouadhibou, hors registre)",
    },
}

_DISCLAIMER = (
    "Fret vraquier ESTIMÉ par modèle distance-coût par classe de navire, calibré "
    "sur des routes de référence publiées (moyennes 2024). Le marché vraquier est "
    "volatil : les taux réels varient ±30 % et plus selon la période, le navire et "
    "les conditions d'affrètement. Frais portuaires = ordre de grandeur régional. "
    "Hors : surestaries (demurrage/despatch), pré/post-acheminement terrestre, "
    "assurance, droits de douane et frais documentaires."
)


def pick_vessel_class(parcel_tonnes: float, allowed: Optional[List[str]] = None) -> Optional[str]:
    """
    Plus petite classe capable d'embarquer le lot en un seul voyage, parmi les
    classes autorisées (`allowed`, ex. issues de classify_bulk_commodity).
    Si le lot dépasse la plus grande classe autorisée, celle-ci est retenue
    (plusieurs voyages ou co-chargement — signalé par l'appelant).
    """
    if parcel_tonnes is None or parcel_tonnes <= 0:
        return None
    candidates = [c for c in _CLASS_ORDER if allowed is None or c in allowed]
    if not candidates:
        return None
    for cls in candidates:
        if parcel_tonnes <= VESSEL_CLASSES[cls]["max_parcel_t"]:
            return cls
    return candidates[-1]


def max_vessel_class_for_port(locode: str) -> Optional[str]:
    """
    Plus grande classe admissible dans un port d'après son tirant d'eau connu.
    ``None`` = port absent de la table d'attributs → aucune contrainte
    appliquée (à signaler comme « non vérifié »).
    """
    attrs = BULK_PORT_ATTRIBUTES.get((locode or "").upper())
    if not attrs or attrs.get("max_draft_m") is None:
        return None
    draft = attrs["max_draft_m"]
    best = None
    for cls in _CLASS_ORDER:
        if VESSEL_CLASSES[cls]["loaded_draft_m"] <= draft:
            best = cls
    return best  # None si même un handysize ne passe pas


def _cap_class(cls: str, cap: Optional[str]) -> str:
    if cap is None:
        return cls
    return cls if _CLASS_ORDER.index(cls) <= _CLASS_ORDER.index(cap) else cap


# ---------------------------------------------------------------------------
# Fraîcheur (Lot D) : override live des indices Baltic par classe de navire
# ---------------------------------------------------------------------------
# data/json/fret_vraquier.json porte, par classe, un multiplicateur de marché
# (niveau d'indice Baltic courant / niveau de référence 2024) avec sa date et
# sa source. Le modèle distance-coût statique est multiplié par ce facteur.
# Discipline « zéro fabrication » identique aux cours mondiaux : fichier
# absent/corrompu → repli statique pur ; multiplicateur hors bornes de
# vraisemblance → ignoré (jamais d'écrasement silencieux du statique).
_FREIGHT_OVERRIDE_PATH = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "data", "json", "fret_vraquier.json"
)
# Bornes de vraisemblance du multiplicateur : un flux cassé (0, négatif, ou
# aberrant) ne doit jamais distordre le tarif. Le marché vraquier bouge fort
# mais reste dans un rapport ~0,3–3 autour de la moyenne 2024.
_MULTIPLIER_BOUNDS = (0.3, 3.0)


def _load_freight_overrides(path: str = _FREIGHT_OVERRIDE_PATH) -> Dict[str, Dict[str, Any]]:
    """Charge fret_vraquier.json ; dict vide si absent/corrompu (repli statique).

    Ne retient qu'une entrée par classe dont le ``multiplier`` est numérique et
    dans les bornes de vraisemblance — une valeur douteuse est écartée, jamais
    appliquée.
    """
    try:
        with open(path, encoding="utf-8") as fh:
            data = json.load(fh)
    except (OSError, ValueError):
        return {}
    raw = data.get("vessel_class_multipliers")
    if not isinstance(raw, dict):
        return {}
    lo, hi = _MULTIPLIER_BOUNDS
    out: Dict[str, Dict[str, Any]] = {}
    for cls, entry in raw.items():
        if cls not in VESSEL_CLASSES or not isinstance(entry, dict):
            continue
        m = entry.get("multiplier")
        if not isinstance(m, (int, float)) or isinstance(m, bool):
            continue
        if not (lo <= m <= hi):
            continue
        out[cls] = entry
    return out


_FREIGHT_OVERRIDES: Dict[str, Dict[str, Any]] = _load_freight_overrides()


def freight_market_override(vessel_class: str) -> Optional[Dict[str, Any]]:
    """Override de marché appliqué pour une classe (ou ``None`` si repli statique)."""
    return _FREIGHT_OVERRIDES.get(vessel_class)


def model_bulk_freight_usd_per_t(distance_nm: float, vessel_class: str) -> float:
    """Fret océanique modélisé (USD/tonne) pour une distance et une classe.

    Applique le multiplicateur de marché live (indice Baltic) si présent et
    valide pour la classe ; sinon, modèle statique pur (multiplicateur = 1,0).
    """
    factor = VESSEL_CLASSES[vessel_class]["freight_factor"]
    override = _FREIGHT_OVERRIDES.get(vessel_class)
    market_mult = override["multiplier"] if override else 1.0
    rate = (
        (_FREIGHT_MODEL_BASE_USD_PER_T + _FREIGHT_MODEL_SLOPE_USD_PER_T_NM * distance_nm)
        * factor
        * market_mult
    )
    return round(max(_FREIGHT_MODEL_FLOOR_USD_PER_T, rate), 2)


def get_bulk_freight_cost(
    origin_locode: str,
    destination_locode: str,
    tonnes: float,
    vessel_class: Optional[str] = None,
    allowed_classes: Optional[List[str]] = None,
    required_terminal: Optional[str] = None,
) -> Optional[Dict[str, Any]]:
    """
    Coût de fret vraquier modélisé entre deux ports du registre.

    Args:
        origin_locode / destination_locode : LOCODE du registre PORTS
        tonnes : taille du lot (t)
        vessel_class : classe imposée (sinon choisie depuis le tonnage)
        allowed_classes : classes admissibles pour le produit
            (cf. classify_bulk_commodity()["vessel_classes"])
        required_terminal : équipement requis (grain, mineral, cement, coal,
            fertilizer) — vérifié seulement quand les attributs du port sont
            connus ; jamais de blocage inventé.

    Returns:
        dict détaillé (USD/t et total, classe retenue, contraintes appliquées,
        provenance) ou ``None`` si ports inconnus/identiques ou tonnage nul.
    """
    o = (origin_locode or "").upper()
    d = (destination_locode or "").upper()
    if o not in PORTS or d not in PORTS or o == d:
        return None
    if tonnes is None or tonnes <= 0:
        return None

    constraints_notes: List[str] = []

    wanted = vessel_class or pick_vessel_class(tonnes, allowed_classes)
    if wanted is None or wanted not in VESSEL_CLASSES:
        return None

    # Plafonnement par les ports (tirant d'eau connu uniquement).
    chosen = wanted
    for locode in (o, d):
        cap = max_vessel_class_for_port(locode)
        attrs = BULK_PORT_ATTRIBUTES.get(locode)
        if attrs is None:
            constraints_notes.append(
                f"{PORTS[locode]['name']} : attributs vrac non vérifiés — aucune "
                "contrainte de tirant d'eau appliquée."
            )
            continue
        if cap is None:
            constraints_notes.append(
                f"{PORTS[locode]['name']} : tirant d'eau ({attrs['max_draft_m']} m) "
                "insuffisant même pour un handysize chargé — escale partielle ou "
                "allègement nécessaires (non chiffrés)."
            )
            cap = "handysize"
        if _CLASS_ORDER.index(chosen) > _CLASS_ORDER.index(cap):
            constraints_notes.append(
                f"{PORTS[locode]['name']} : classe plafonnée à "
                f"{VESSEL_CLASSES[cap]['label']} (tirant d'eau "
                f"{attrs['max_draft_m']} m, non vérifié)."
            )
        chosen = _cap_class(chosen, cap)
        if required_terminal and attrs.get("bulk_terminals"):
            if required_terminal not in attrs["bulk_terminals"]:
                constraints_notes.append(
                    f"{PORTS[locode]['name']} : terminal « {required_terminal} » non "
                    "recensé parmi les équipements connus "
                    f"({', '.join(attrs['bulk_terminals'])}) — manutention non "
                    "spécialisée probable, cadence et coût dégradés."
                )

    spec = VESSEL_CLASSES[chosen]
    voyages = max(1, math.ceil(tonnes / spec["max_parcel_t"]))
    if voyages > 1:
        constraints_notes.append(
            f"Lot de {round(tonnes):,} t supérieur à l'emport d'un "
            f"{spec['label']} : {voyages} voyages nécessaires.".replace(",", " ")
        )

    dist_nm = _sea_distance_nm(o, d)
    ocean_usd_per_t = model_bulk_freight_usd_per_t(dist_nm, chosen)
    market_override = freight_market_override(chosen)
    load_usd_per_t = BULK_PORT_HANDLING_USD_PER_T_LOAD
    discharge_usd_per_t = BULK_PORT_HANDLING_USD_PER_T_DISCHARGE
    total_usd_per_t = round(ocean_usd_per_t + load_usd_per_t + discharge_usd_per_t, 2)
    total_usd = round(total_usd_per_t * tonnes, 2)

    # Délais modélisés : mer à vitesse commerciale + opérations portuaires
    # (cadences vrac moyennes ~12 000 t/j au chargement, ~8 000 t/j au
    # déchargement), par voyage.
    per_voyage_t = tonnes / voyages
    sea_days = dist_nm / (_BULK_SPEED_KNOTS * 24.0)
    load_days = max(1.0, per_voyage_t / 12_000.0)
    discharge_days = max(1.0, per_voyage_t / 8_000.0)
    transit_min = max(3, int(math.ceil(sea_days + 0.8 * (load_days + discharge_days))))
    transit_max = max(
        transit_min + 2, int(math.ceil(1.15 * sea_days + load_days + discharge_days + 4))
    )

    pa, pb = PORTS[o], PORTS[d]
    return {
        "origin_locode": o,
        "destination_locode": d,
        "origin_port": pa["name"],
        "destination_port": pb["name"],
        "origin_country": pa["iso"],
        "destination_country": pb["iso"],
        "distance_nm": dist_nm,
        "vessel_class": chosen,
        "vessel_class_label": spec["label"],
        "vessel_class_requested": wanted,
        "voyages_needed": voyages,
        "parcel_tonnes": round(float(tonnes), 1),
        "ocean_freight_usd_per_t": ocean_usd_per_t,
        "port_load_usd_per_t": load_usd_per_t,
        "port_discharge_usd_per_t": discharge_usd_per_t,
        "total_usd_per_t": total_usd_per_t,
        "total_cost_usd": total_usd,
        "transit_days_min": transit_min,
        "transit_days_max": transit_max,
        "co2_g_per_tkm": spec["co2_g_per_tkm"],
        "co2_source": "IMO 4th GHG Study 2020 / GLEC Framework v3 (ordre de grandeur par classe)",
        "constraints_notes": constraints_notes,
        "is_modeled": True,
        # Fraîcheur : un facteur live (drapeau ``is_live``, posé par l'ETL) date
        # le tarif à sa date de marché — indépendamment de la valeur du facteur,
        # qui peut légitimement valoir 1,0 (marché à sa moyenne glissante).
        "as_of": (
            market_override.get("as_of")
            if market_override and market_override.get("is_live")
            else "calibration moyennes 2024"
        ),
        "calibration_sources": [b["source"] for b in _CALIBRATION_BENCHMARKS],
        "freight_market_override": (
            {
                "vessel_class": chosen,
                "multiplier": market_override["multiplier"],
                "is_live": bool(market_override.get("is_live")),
                # Provenance du facteur : proxy de marché (BDRY) ou, pour
                # compatibilité, un ancien champ ``index`` par classe.
                "proxy": market_override.get("proxy") or market_override.get("index"),
                "as_of": market_override.get("as_of"),
                "source": market_override.get("source"),
            }
            if market_override
            else None
        ),
        "currency": "USD",
        "data_year": 2024,
        "disclaimer": _DISCLAIMER,
    }
