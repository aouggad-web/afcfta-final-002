#!/usr/bin/env python3
"""
Matrice AfCFTA : statut déclaré par l'Union africaine et réciprocité par origine.

Répond à deux questions que les instantanés de barèmes ne posaient pas
séparément : **quels pays ont accepté** un engagement tarifaire, et **quelles
origines sont acceptées** par chacun.

Le portail de l'Union africaine ne qualifie pas ses barèmes d'offres en attente.
Sa notice écrit, pour 45 des 52 entrées, que l'offre « a été adoptée et incluse
dans la directive ministérielle relative à la liste provisoire de concessions
tarifaires ». Cette déclaration est reprise mot pour mot ici : elle est la
position de la source, distincte du verdict du dépôt
(`legal_effect_status=OFFER_ONLY`), qui reste plus strict parce qu'un barème
provisoire adopté au niveau continental ne suffit pas à liquider un droit —
l'effet en droit interne, la date d'entrée en vigueur, la réciprocité bilatérale
et la preuve d'origine sont des conditions distinctes.

Deux faits doivent rester séparés, et cette matrice les sépare :

1. **Statut déclaré** — ce que l'Union africaine dit de l'engagement d'un pays.
2. **Disponibilité de la donnée** — l'existence d'un barème interrogeable. Un
   pays peut être déclaré adopté sans qu'aucun barème ne soit exposé : le
   recensement le dit au lieu de le déduire.

L'origine absente de la carte des origines n'est pas réputée exclue : l'API
renvoie une erreur pour certains couples sans barème réciproque sélectionnable,
et l'absence reste une absence, jamais un zéro.

Usage
-----
    python3 backend/scripts/build_afcfta_status_matrix.py backend/data/official_preferential
"""

from __future__ import annotations

import argparse
import gzip
import json
import re
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

REGIONS_URL = "https://prod-afcfta-api.azurewebsites.net/Region/GetRegions"
PUBLIC_URL = "https://etariff.au-afcfta.org/"

# Qualification du texte de notice, par motifs présents dans la source. L'ordre
# compte : « adoptée et incluse » est plus fort que « soumis ».
STATUS_PATTERNS = (
    ("ADOPTE_PROVISOIREMENT", ("provisionally adopted", "provisoirement adopt")),
    ("ADOPTE_ET_DIRECTIVE", ("adopted and included", "adoptée et incluse")),
    ("LISTE_PROVISOIRE_DIRECTIVE", ("provisional schedule", "liste provisoire")),
    ("SOUMIS", ("submitted", "soumis", "presented", "présent")),
)


def _localized(node: Optional[List[Dict[str, Any]]]) -> Dict[str, str]:
    if not node:
        return {}
    out: Dict[str, str] = {}
    for item in node:
        lang = str(item.get("language") or "").strip()
        text = str(item.get("text") or "").strip()
        if lang in {"en", "fr"} and text:
            out[lang] = text
    return out


def _status_of(statement: Dict[str, str]) -> str:
    joined = " ".join(statement.values()).lower()
    if not joined:
        return "AUCUNE_DECLARATION"
    for label, needles in STATUS_PATTERNS:
        if any(needle in joined for needle in needles):
            return label
    return "AUTRE_DECLARATION"


def _fetch_regions() -> List[Dict[str, Any]]:
    request = urllib.request.Request(REGIONS_URL, headers={"Accept": "application/json"})
    with urllib.request.urlopen(request, timeout=120) as response:
        return json.load(response)


def _local_snapshots(directory: Path) -> Dict[str, Dict[str, Any]]:
    """Cartes des origines déjà collectées, par code d'offre et date."""
    out: Dict[str, Dict[str, Any]] = {}
    for path in sorted(directory.glob("*_afcfta*.json.gz")):
        match = re.match(r"([A-Z]+)_afcfta.*?(\d{4}-\d{2}-\d{2})\.json\.gz$", path.name)
        if not match:
            continue
        offer, collected_at = match.groups()
        payload = json.loads(gzip.decompress(path.read_bytes()).decode("utf-8"))
        origin_map = payload.get("origin_schedule_map") or {}
        out[offer] = {
            "fichier": path.name,
            "collecte_le": payload.get("collected_at", collected_at),
            "destination_interrogee": payload.get("destination_query_code"),
            "revision_source": payload.get("source_revision_date"),
            "barèmes": payload.get("schedule_line_counts") or {},
            "noms_baremes": payload.get("schedule_names") or {},
            "declaration_source": payload.get("source_status_statement") or {},
            "verdict_depot": payload.get("legal_effect_status"),
            "origines_acceptees": origin_map,
            # Le joker « * » signifie qu'un barème unique s'applique à toutes
            # les origines — ZWE, EAC, CEMAC. Le compter 0 faisait dire à la
            # matrice l'inverse de ce que porte origines_acceptees juste
            # au-dessus : aucune origine admise, là où elles le sont toutes.
            "nb_origines_acceptees": ("toutes" if "*" in origin_map else len(origin_map)),
            "couverture_origines": "joker" if "*" in origin_map else "enumeree",
        }
    return out


def build(directory: Path) -> Dict[str, Any]:
    fetched_at = datetime.now(timezone.utc).isoformat()
    regions = _fetch_regions()
    snapshots = _local_snapshots(directory)

    entries = []
    for region in regions:
        statement = _localized(region.get("overview"))
        entries.append(
            {
                "code_iso2": region.get("code"),
                "nom": _localized(region.get("name")).get("en"),
                "est_region": bool(region.get("isRegion")),
                "est_pma": region.get("isLDC"),
                "union_douaniere": region.get("customsUnionCode") or None,
                "revision_source": region.get("lastRevisionDate"),
                "version_sh": region.get("hsVersion") or None,
                "baremes_exposes": len(region.get("schedules") or []),
                "statut_declare": _status_of(statement),
                "declaration_source": statement,
            }
        )

    counts: Dict[str, int] = {}
    for entry in entries:
        counts[entry["statut_declare"]] = counts.get(entry["statut_declare"], 0) + 1

    return {
        "schema_version": 1,
        "source_title": "AfCFTA e-Tariff Book — Region/GetRegions",
        "source_url": PUBLIC_URL,
        "source_api_url": REGIONS_URL,
        "avertissement": (
            "Le statut déclaré est la position de l'Union africaine, citée mot pour "
            "mot. Il ne vaut pas application nationale : l'effet en droit interne, "
            "la date d'entrée en vigueur, la réciprocité bilatérale et la preuve "
            "d'origine restent des conditions distinctes, contrôlées par "
            "zlecaf_implementation_registry.py. Une origine absente d'une carte "
            "n'est pas réputée exclue — l'absence reste une absence."
        ),
        "regions_fetched_at": fetched_at,
        "repartition_statuts": dict(sorted(counts.items())),
        "pays": sorted(entries, key=lambda row: str(row["code_iso2"])),
        "instantanes_locaux": snapshots,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[1])
    parser.add_argument("directory", type=Path, help="Répertoire des instantanés")
    parser.add_argument("--out", type=Path, help="Fichier de sortie (défaut : dans le répertoire)")
    parser.add_argument("--collected-at", required=True, help="Date de collecte (AAAA-MM-JJ)")
    args = parser.parse_args()

    if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", args.collected_at):
        raise SystemExit(f"--collected-at attend AAAA-MM-JJ, reçu {args.collected_at!r}")

    matrix = build(args.directory)
    # La date déclarée ne peut pas réécrire l'instant réel de l'appel : build()
    # interroge Region/GetRegions en direct, et rejouer la commande documentée
    # d'une date passée estamperait une réponse d'aujourd'hui de cette date-là.
    # Les deux sont donc portées séparément, et l'écart est signalé.
    matrix["collected_at"] = args.collected_at
    matrix["regions_fetched_at"] = matrix.get("regions_fetched_at")
    if matrix["regions_fetched_at"] and not matrix["regions_fetched_at"].startswith(
        args.collected_at
    ):
        matrix["provenance_warning"] = (
            f"Les régions ont été interrogées le "
            f"{matrix['regions_fetched_at'][:10]}, alors que --collected-at "
            f"déclare {args.collected_at}. Cette matrice n'est donc pas une "
            f"reproduction de l'instantané du {args.collected_at} : elle mêle "
            f"une réponse d'aujourd'hui à une date passée. Pour reproduire un "
            f"instantané, il faut la réponse archivée de l'époque."
        )

    output = args.out or args.directory / f"afcfta_status_matrix_{args.collected_at}.json"
    output.write_text(json.dumps(matrix, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")

    print(f"{output} — {len(matrix['pays'])} entrées")
    for statut, nombre in matrix["repartition_statuts"].items():
        print(f"  {statut:<28} {nombre}")
    print(f"  instantanés locaux : {', '.join(sorted(matrix['instantanes_locaux']))}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
