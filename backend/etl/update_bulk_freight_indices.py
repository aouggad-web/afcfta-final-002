"""
Rafraîchissement des indices de fret vraquier (Baltic) par classe de navire.

Écrit ``data/json/fret_vraquier.json`` (racine du dépôt), lu par
``backend/logistics_bulk_fees_data.py`` en priorité sur son modèle
distance-coût statique. Conçu pour tourner dans GitHub Actions (cron jours
ouvrés) — voir .github/workflows/update_bulk_freight.yml.

Modèle : chaque classe de navire porte un MULTIPLICATEUR de marché =
``niveau d'indice Baltic courant / niveau de référence 2024``. Le backend
multiplie son tarif modélisé par ce facteur. Multiplicateur 1,0 = marché à
la moyenne 2024 (comportement statique).

Discipline « zéro fabrication », identique à update_world_market_prices.py :

  - on n'écrit QU'un multiplicateur calculé à partir d'un niveau d'indice
    effectivement récupéré, avec la date fournie par la source — jamais une
    valeur inventée ni recopiée d'un run précédent ;
  - une classe dont l'indice échoue ou sort des bornes de vraisemblance est
    ramenée à un multiplicateur 1,0 daté « moyenne 2024 » (repli statique
    explicite), jamais un facteur douteux ;
  - les niveaux de référence 2024 sont des ordres de grandeur publiés
    (moyennes annuelles Baltic Exchange), utilisés UNIQUEMENT comme
    dénominateur pour passer d'un niveau d'indice à un facteur relatif.

Source des niveaux courants : à câbler sur le flux Baltic disponible dans
l'environnement CI (``BALTIC_INDEX_URL`` / clé d'API en variable
d'environnement). En l'absence de flux configuré, TOUTES les classes
retombent sur 1,0 et le fichier reste le repli statique daté — aucune
donnée fabriquée.
"""

from __future__ import annotations

import json
import os
import sys
from datetime import datetime, timezone

_OUT_PATH = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "..", "data", "json", "fret_vraquier.json"
)

# Indice Baltic par classe + niveau de référence 2024 (ordre de grandeur,
# moyenne annuelle Baltic Exchange) servant de dénominateur du multiplicateur.
# Ces niveaux sont datés et sourcés ; ils ne sont PAS servis tels quels — seul
# le rapport niveau_courant / référence l'est.
VESSEL_INDICES = {
    "handysize": {
        "index": "BHSI (Baltic Handysize Index)",
        "baseline_2024": 690.0,
        "source": "Baltic Exchange — BHSI, moyenne annuelle 2024 (ordre de grandeur)",
    },
    "supramax": {
        "index": "BSI (Baltic Supramax Index)",
        "baseline_2024": 1230.0,
        "source": "Baltic Exchange — BSI, moyenne annuelle 2024 (ordre de grandeur)",
    },
    "panamax": {
        "index": "BPI (Baltic Panamax Index)",
        "baseline_2024": 1520.0,
        "source": "Baltic Exchange — BPI, moyenne annuelle 2024 (ordre de grandeur)",
    },
    "capesize": {
        "index": "BCI (Baltic Capesize Index)",
        "baseline_2024": 2750.0,
        "source": "Baltic Exchange — BCI, moyenne annuelle 2024 (ordre de grandeur)",
    },
}

# Bornes de vraisemblance du multiplicateur (identiques au backend) : un flux
# cassé hors de cette plage est REJETÉ, la classe reste au repli statique 1,0.
MULTIPLIER_BOUNDS = (0.3, 3.0)


def compute_multiplier(current_index: float, baseline_2024: float) -> float:
    """Multiplicateur de marché = niveau courant / référence 2024.

    Lève ValueError si les entrées sont inexploitables ou si le résultat sort
    des bornes de vraisemblance — on ne devine jamais, on ne borne pas en
    silence.
    """
    if not isinstance(current_index, (int, float)) or current_index <= 0:
        raise ValueError(f"niveau d'indice absent ou invalide: {current_index!r}")
    if not isinstance(baseline_2024, (int, float)) or baseline_2024 <= 0:
        raise ValueError(f"référence 2024 invalide: {baseline_2024!r}")
    mult = round(current_index / baseline_2024, 4)
    lo, hi = MULTIPLIER_BOUNDS
    if not (lo <= mult <= hi):
        raise ValueError(
            f"multiplicateur {mult} hors bornes de vraisemblance [{lo}, {hi}] — "
            "flux probablement cassé, rejeté"
        )
    return mult


def build_static_entry(vessel_class: str) -> dict:
    """Entrée de repli statique daté (multiplicateur 1,0) pour une classe."""
    spec = VESSEL_INDICES[vessel_class]
    return {
        "multiplier": 1.0,
        "index": spec["index"],
        "as_of": "moyenne 2024",
        "source": f"{spec['source']} (référence de calibration)",
    }


def build_live_entry(vessel_class: str, current_index: float, as_of: str) -> dict:
    """Entrée live pour une classe, ou lève ValueError si le niveau est douteux."""
    spec = VESSEL_INDICES[vessel_class]
    mult = compute_multiplier(current_index, spec["baseline_2024"])
    return {
        "multiplier": mult,
        "index": spec["index"],
        "index_level": round(float(current_index), 2),
        "baseline_2024": spec["baseline_2024"],
        "as_of": as_of,
        "source": f"{spec['source']} → niveau courant {round(float(current_index), 2)}",
    }


def fetch_index_levels() -> dict:
    """Récupère les niveaux d'indices Baltic courants par classe.

    Retourne ``{vessel_class: {"level": float, "as_of": "YYYY-MM-DD"}}``.

    Aucun flux Baltic gratuit fiable n'étant garanti dans l'environnement CI,
    cette fonction lit une source configurée via variable d'environnement
    (``BALTIC_INDEX_JSON`` : chemin d'un JSON déjà récupéré par une étape
    amont, ou vide). En son absence, renvoie un dict vide → repli statique
    intégral. Jamais de niveau inventé.
    """
    src = os.environ.get("BALTIC_INDEX_JSON")
    if not src:
        return {}
    try:
        with open(src, encoding="utf-8") as fh:
            data = json.load(fh)
    except (OSError, ValueError) as exc:
        print(f"SKIP source Baltic ({src}): {exc}", file=sys.stderr)
        return {}
    out = {}
    for cls, entry in (data.get("indices") or {}).items():
        if cls in VESSEL_INDICES and isinstance(entry, dict):
            out[cls] = entry
    return out


def build_payload(live_levels: dict) -> dict:
    """Assemble le contenu de fret_vraquier.json (live si valide, sinon statique)."""
    multipliers = {}
    failures = []
    for cls in VESSEL_INDICES:
        entry = live_levels.get(cls) or {}
        level = entry.get("level")
        as_of = entry.get("as_of")
        if level is not None and as_of:
            try:
                multipliers[cls] = build_live_entry(cls, level, as_of)
                print(f"OK   {cls:10s} -> x{multipliers[cls]['multiplier']} ({as_of})")
                continue
            except ValueError as exc:
                failures.append(f"{cls}: {exc}")
                print(f"SKIP {cls:10s} -> {exc} (repli statique 1,0)", file=sys.stderr)
        multipliers[cls] = build_static_entry(cls)

    return {
        "_meta": {
            "description": "Multiplicateurs de marché du fret vraquier par classe de "
            "navire (indice Baltic courant / référence 2024), appliqués au modèle "
            "distance-coût de backend/logistics_bulk_fees_data.py. Une classe en échec "
            "reste à 1,0 (repli statique daté). Zéro fabrication.",
            "generated_at": datetime.now(tz=timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "generator": "etl/update_bulk_freight_indices.py (GitHub Actions, jours ouvrés)",
            "baseline": "Niveaux d'indices Baltic — moyennes annuelles 2024 (ordre de grandeur)",
            "plausibility_multiplier_bounds": list(MULTIPLIER_BOUNDS),
            "classes_live": sorted(c for c, v in multipliers.items() if v.get("multiplier") != 1.0),
            "classes_failed_or_static": failures,
        },
        "vessel_class_multipliers": multipliers,
    }


def main() -> int:
    payload = build_payload(fetch_index_levels())
    os.makedirs(os.path.dirname(_OUT_PATH), exist_ok=True)
    with open(_OUT_PATH, "w", encoding="utf-8") as fh:
        json.dump(payload, fh, ensure_ascii=False, indent=2)
        fh.write("\n")
    live = payload["_meta"]["classes_live"]
    print(f"\nÉcrit {_OUT_PATH} — {len(live)} classe(s) live, {4 - len(live)} au repli statique.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
