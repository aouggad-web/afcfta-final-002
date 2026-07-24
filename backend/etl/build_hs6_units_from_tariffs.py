"""
Génère backend/data/hs6_units_derived.json — unité complémentaire par code HS6,
dérivée des tarifs douaniers nationaux réels (backend/data/*_tariffs.json).

Pourquoi : la table curée HS6_SUPPLEMENTARY_UNITS ne couvre que ~715 codes ;
les tarifs nationaux (EAC : KEN/TZA/UGA/RWA/BDI…, SACU : ZAF/BWA/NAM/LSO/SWZ,
plus NGA, ETH) publient l'unité statistique OMD ligne par ligne pour ~5 900
codes HS6. On agrège ces sources par vote majoritaire.

Sources exclues (non informatives) :
- pays dont TOUTES les lignes portent la même unité ("QA" pour la CEDEAO,
  "KG" en remplissage par défaut) — une valeur uniforme n'apporte aucune
  information de différenciation par produit.

Usage :
    cd backend && python -m etl.build_hs6_units_from_tariffs
"""

import json
import logging
from collections import Counter, defaultdict
from pathlib import Path

logging.basicConfig(level=logging.INFO, format="%(message)s")
log = logging.getLogger(__name__)

DATA_DIR = Path(__file__).parent.parent / "data"
OUTPUT_FILE = DATA_DIR / "hs6_units_derived.json"

# Normalisation des libellés bruts des tarifs nationaux vers les unités
# canoniques de hs6_supplementary_units (mêmes clés que _UNIT_LABELS).
RAW_UNIT_MAP = {
    # poids
    "kg": "kg",
    "KG": "kg",
    "Kg": "kg",
    "KGM": "kg",
    "t": "tonnes",
    # volume
    "l": "litres",
    "li": "litres",
    "LTR": "litres",
    "m³": "m³",
    "m3": "m³",
    "MTQ": "m³",
    "m3(*)": "m³",
    "m³/101.3kP": "m³",
    # surface / longueur
    "m²": "m²",
    "m2": "m²",
    "MTK": "m²",
    "m": "mètres",
    # comptage
    "u": "nombre",
    "UNT": "nombre",
    "2u": "paires",
    "NPR": "paires",
    "1000u": "1000 pièces",
    "1000 u": "1000 pièces",
    # divers
    "carat": "carats",
    "1000 KWh": "1000 kWh",
    "1000 kW.h": "1000 kWh",
    "1000kwh": "1000 kWh",
}
# Valeurs ignorées : placeholders, taux, emballages ambigus
IGNORED_RAW = {"QA", "free", "-", "", "10%", "20%", "pack", "u (jue/pack)", "NMP"}

# En cas d'égalité au vote, on préfère l'unité la plus spécifique au produit
# (une unité de comptage/volume est plus informative que le kg générique).
TIE_PRIORITY = [
    "nombre",
    "paires",
    "1000 pièces",
    "litres",
    "m²",
    "m³",
    "mètres",
    "carats",
    "1000 kWh",
    "tonnes",
    "kg",
]


def load_informative_sources():
    """Retourne {country: {hs6: unité_normalisée}} en excluant les pays
    dont les unités sont uniformes (placeholder)."""
    sources = {}
    for fpath in sorted(DATA_DIR.glob("*_tariffs.json")):
        country = fpath.stem.replace("_tariffs", "").upper()
        try:
            with open(fpath, "r", encoding="utf-8") as f:
                data = json.load(f)
        except Exception as e:
            log.warning("Lecture impossible %s : %s", fpath.name, e)
            continue

        raw_units = {}
        for line in data.get("tariff_lines", []):
            hs6 = line.get("hs6", "")
            unit = line.get("unit")
            if hs6 and unit:
                raw_units[hs6] = unit

        distinct = set(raw_units.values())
        if len(distinct) <= 1:
            # Unité uniforme (QA / KG partout) → placeholder, pas une donnée
            continue

        normalized = {}
        for hs6, raw in raw_units.items():
            if raw in IGNORED_RAW:
                continue
            unit = RAW_UNIT_MAP.get(raw)
            if unit:
                normalized[hs6] = unit
        if normalized:
            sources[country] = normalized
    return sources


def build_consensus(sources):
    """Vote majoritaire par HS6 sur l'ensemble des pays informatifs."""
    votes = defaultdict(Counter)
    for units in sources.values():
        for hs6, unit in units.items():
            votes[hs6][unit] += 1

    consensus = {}
    for hs6, counter in votes.items():
        best_count = max(counter.values())
        tied = [u for u, c in counter.items() if c == best_count]
        if len(tied) == 1:
            consensus[hs6] = tied[0]
        else:
            consensus[hs6] = min(tied, key=TIE_PRIORITY.index)
    return consensus


def main():
    sources = load_informative_sources()
    log.info("Pays informatifs : %s", ", ".join(sorted(sources)))
    consensus = build_consensus(sources)
    log.info("Codes HS6 avec unité dérivée : %d", len(consensus))
    log.info("Répartition : %s", Counter(consensus.values()).most_common())

    payload = {
        "_meta": {
            "description": (
                "Unités complémentaires OMD par HS6, dérivées des tarifs "
                "douaniers nationaux africains (vote majoritaire)"
            ),
            "sources": sorted(sources),
            "generator": "etl/build_hs6_units_from_tariffs.py",
            "count": len(consensus),
        },
        "units": dict(sorted(consensus.items())),
    }
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=1)
    log.info("Écrit : %s", OUTPUT_FILE)


if __name__ == "__main__":
    main()
