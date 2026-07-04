"""
File d'exécution pays par pays pour la collecte tarifaire ZLECAf.

Le but est opérationnel : transformer le manifeste + la couverture réelle en une
liste priorisée de pays à traiter, avec la source à utiliser et la commande de
lancement. La file ne fabrique aucune donnée tarifaire ; elle indique seulement
quoi crawler ensuite, dans quel ordre, et pourquoi.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List, Set

from .coverage import classify_file
from .manifest import Provenance, build_manifest

# Ordre pragmatique : d'abord portails nationaux déjà identifiés, puis blocs
# régionaux où une seule source officielle peut couvrir plusieurs pays, puis MFN
# HS6 WTO/WITS pour les pays sans autre source exploitable à court terme.
PROVENANCE_PRIORITY = {
    Provenance.NATIONAL_CRAWL.value: 10,
    Provenance.REGIONAL_CET.value: 20,
    Provenance.WTO_MFN_HS6.value: 30,
    Provenance.NONE.value: 99,
}

STATUS_PRIORITY = {
    "to_implement": 0,
    "available": 1,
    "available_with_key": 2,
    "ready": 8,
}


def _first_actionable_source(sources: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Sélectionne la première source utile pour démarrer/continuer le crawl."""
    actionable = [s for s in sources if s.get("status") != "ready"]
    if not actionable:
        return sources[0] if sources else {"provenance": Provenance.NONE.value, "status": "none"}
    return sorted(
        actionable,
        key=lambda s: (
            PROVENANCE_PRIORITY.get(s.get("provenance"), 99),
            STATUS_PRIORITY.get(s.get("status"), 9),
        ),
    )[0]


def _next_action(iso3: str, source: Dict[str, Any]) -> str:
    provenance = source.get("provenance")
    status = source.get("status")
    if provenance == Provenance.NATIONAL_CRAWL.value and status == "to_implement":
        return f"Implémenter/brancher le crawler national puis lancer: python backend/scripts/crawl_all_countries.py --run --country {iso3}"
    if provenance == Provenance.REGIONAL_CET.value:
        return "Construire/propager le tarif extérieur commun officiel du bloc, puis valider le fichier pays."
    if provenance == Provenance.WTO_MFN_HS6.value:
        return "Importer les taux MFN appliqués WTO/WITS-TRAINS au niveau HS6 avec clé/API officielle."
    if status == "ready":
        return f"Valider l'ingestion existante: python backend/scripts/crawl_all_countries.py --validate-file {iso3}"
    return "Identifier une source authentique exploitable avant toute ingestion."


def build_collection_queue(countries: List[str] | None = None) -> Dict[str, Any]:
    """Construit une file de collecte priorisée pour tous les pays non complets.

    Args:
        countries: optionnellement, liste ISO3 à inclure dans la file.
    """
    manifest = build_manifest()
    selected: Set[str] | None = {c.upper() for c in countries} if countries else None
    items: List[Dict[str, Any]] = []

    for iso3, descriptor in manifest.items():
        if selected is not None and iso3 not in selected:
            continue
        coverage = classify_file(iso3)
        effective = coverage.get("effective_provenance")
        positions = int(coverage.get("positions") or 0)
        contaminated = bool(coverage.get("contaminated"))

        # Un fichier authentique, non contaminé et non vide est déjà couvert ; il
        # reste validable mais ne doit pas bloquer le démarrage des pays manquants.
        covered = (
            positions > 0
            and not contaminated
            and effective in {
                Provenance.NATIONAL_CRAWL.value,
                Provenance.REGIONAL_CET.value,
                Provenance.WTO_MFN_HS6.value,
            }
        )
        if covered:
            continue

        source = _first_actionable_source(descriptor.get("sources_chain", []))
        priority = (
            PROVENANCE_PRIORITY.get(source.get("provenance"), 99),
            STATUS_PRIORITY.get(source.get("status"), 9),
            descriptor.get("region") or "",
            iso3,
        )
        items.append(
            {
                "iso3": iso3,
                "country_name": descriptor.get("name_fr") or descriptor.get("name_en") or iso3,
                "region": descriptor.get("region"),
                "blocks": descriptor.get("blocks", []),
                "current_provenance": effective,
                "current_positions": positions,
                "contaminated": contaminated,
                "target_provenance": source.get("provenance"),
                "source": source.get("source"),
                "source_url": source.get("source_url"),
                "source_status": source.get("status"),
                "next_action": _next_action(iso3, source),
                "_priority": priority,
            }
        )

    items.sort(key=lambda i: i.pop("_priority"))
    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "total_pending_countries": len(items),
        "countries": items,
    }
