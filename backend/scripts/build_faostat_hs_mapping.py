#!/usr/bin/env python3
"""
Génération du pont SH ↔ commodités FAOSTAT, par correspondance publiée
=======================================================================
Écrit ``backend/etl/faostat_hs_mapping.py`` : la liste des couples
(préfixe SH, libellé de commodité FAOSTAT) qui élargit le pont
SH ↔ production de ``services/production_capacity_service.py``.

POURQUOI UNE GÉNÉRATION, ET PAS UNE TABLE ÉCRITE À LA MAIN
-----------------------------------------------------------
Rattacher une production réelle au mauvais produit échangé est pire que ne
rien rattacher : le module Opportunités raisonnerait sur un débouché qui n'est
pas le bon. Une attribution au jugé, même plausible, est donc exclue.

La chaîne utilisée est entièrement sourcée, en deux maillons publiés :

  1. **item FAOSTAT → code CPC v2.1** — publié par la FAO dans le membre
     ``*_ItemCodes.csv`` du bulk QCL ;
  2. **CPC v2.1 → SH 2017** — table de correspondance officielle de l'UNSD,
     ``CPC21-HS2017.csv``.
     https://unstats.un.org/unsd/classifications/Econ

Relevé du 2026-09-21 : 232 des 233 items non agrégés se résolvent ainsi, vers
294 codes SH6 répartis sur 99 positions SH4.

TROIS RÈGLES DE PRUDENCE
------------------------
* **Additif seulement, et IDEMPOTENT.** Un code SH déjà résolu par la table
  curée de ``production_capacity_service`` n'est jamais réécrit — et la
  comparaison porte sur cette table curée SEULE, jamais sur le pont complet.
  Se comparer au pont complet reviendrait à se comparer à sa propre sortie
  précédente : la deuxième exécution verrait ses entrées comme déjà couvertes
  et écrirait un module vide. Un test rejoue la génération et vérifie qu'elle
  redonne le même résultat.
* **Agrégats écartés.** Les items de code CPC ``F1…`` sont des agrégats
  FAOSTAT (« Cereals, primary », « Meat, Total ») : les rattacher doublerait
  les totaux et placerait un agrégat en tête des classements.
* **Libellés alignés sur la donnée.** Le libellé émis est celui que
  l'ingestion écrit réellement dans ``production_africaine.json`` — table de
  normalisation quand l'item y figure, libellé FAOSTAT publié sinon. Un pont
  qui pointerait vers un libellé absent de la donnée ne résoudrait rien.

Usage :
    python3 scripts/build_faostat_hs_mapping.py [--dry-run]

Prérequis : le bulk FAOSTAT en cache (``engine/sources/``) et la table UNSD,
téléchargée automatiquement si absente.
"""

from __future__ import annotations

import argparse
import collections
import csv
import io
import sys
import urllib.request
import zipfile
from datetime import datetime, timezone
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
BACKEND_DIR = SCRIPT_DIR.parent
sys.path.insert(0, str(BACKEND_DIR))
sys.path.insert(0, str(SCRIPT_DIR))

SOURCES_DIR = BACKEND_DIR / "engine" / "sources"
OUT_MODULE = BACKEND_DIR / "etl" / "faostat_hs_mapping.py"

FAOSTAT_ZIP = SOURCES_DIR / "faostat_production_africa.zip"
UNSD_CSV = SOURCES_DIR / "CPC21-HS2017.csv"
UNSD_URL = (
    "https://unstats.un.org/unsd/classifications/Econ/tables/CPC/" "CPCv21_HS2017/CPC21-HS2017.csv"
)

# Préfixe des codes CPC propres à FAOSTAT : agrégats, à écarter.
CPC_AGGREGATE_PREFIX = "F1"


def _ensure_unsd_table() -> None:
    if UNSD_CSV.exists():
        return
    SOURCES_DIR.mkdir(parents=True, exist_ok=True)
    print(f"   Téléchargement de la table UNSD → {UNSD_CSV.name}")
    req = urllib.request.Request(UNSD_URL, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=180) as resp:  # nosec B310
        UNSD_CSV.write_bytes(resp.read())


def _load_cpc_to_hs() -> dict[str, set[str]]:
    """{code CPC v2.1: {codes SH6}} depuis la table officielle UNSD."""
    mapping: dict[str, set[str]] = collections.defaultdict(set)
    with open(UNSD_CSV, encoding="utf-8-sig") as f:
        for row in csv.DictReader(f):
            hs = (row.get("HS 2017") or "").replace(".", "").strip()
            cpc = (row.get("CPC Ver. 2.1") or "").strip()
            if hs and cpc:
                mapping[cpc].add(hs)
    return mapping


def _load_faostat_items() -> tuple[dict[str, tuple[str, str]], set[str]]:
    """({code item: (code CPC, libellé)}, {codes item avec production}).

    Le code CPC vient du membre de référence ``*_ItemCodes.csv``, mais le
    LIBELLÉ vient du fichier de données. Les deux membres n'orthographient pas
    les items de la même façon — la référence sépare par des points-virgules
    (« Almonds; in shell ») là où les données mettent des virgules
    (« Almonds, in shell »). Prendre le libellé dans la référence produirait
    un pont qui pointe vers des commodités absentes de la donnée.
    """
    with zipfile.ZipFile(FAOSTAT_ZIP) as z:
        codes_name = next(n for n in z.namelist() if n.lower().endswith("_itemcodes.csv"))
        with z.open(codes_name) as f:
            item_rows = list(csv.DictReader(io.TextIOWrapper(f, encoding="utf-8-sig")))
        data_name = next(
            n for n in z.namelist() if "NOFLAG" in n.upper() and n.lower().endswith(".csv")
        )
        with z.open(data_name) as f:
            data_rows = list(
                csv.DictReader(io.TextIOWrapper(f, encoding="utf-8-sig", errors="replace"))
            )

    cpc_by_code = {
        (r.get("Item Code") or "").strip(): (r.get("CPC Code") or "").lstrip("'").strip()
        for r in item_rows
        if (r.get("Item Code") or "").strip()
    }
    label_by_code: dict[str, str] = {}
    produced: set[str] = set()
    for r in data_rows:
        code = (r.get("Item Code") or "").strip()
        if not code:
            continue
        label_by_code.setdefault(code, (r.get("Item") or "").strip())
        if (r.get("Element Code") or "").strip() == "5510":
            produced.add(code)

    items = {
        code: (cpc_by_code.get(code, ""), label_by_code.get(code, "")) for code in label_by_code
    }
    return items, produced


def _resolve_hs(cpc: str, cpc_to_hs: dict[str, set[str]]) -> tuple[list[str], str]:
    """Codes SH6 d'un code CPC, et la façon dont ils ont été obtenus.

    Trois tentatives, de la plus précise à la plus large :
      * le code tel quel ;
      * sa racine avant le point (FAOSTAT descend parfois d'un cran,
        ``01929.07``) et sans suffixe alphabétique propre à FAOSTAT
        (``2351f``) ;
      * à défaut, l'union des classes CPC dont la racine est ce code — cas
        des items rattachés à un GROUPE CPC à 4 chiffres (« Wheat » = 0111)
        là où la table UNSD est indexée sur les classes à 5 chiffres.
    """
    base = cpc.split(".")[0].rstrip("abcdefghijklmnopqrstuvwxyz")
    for key in (cpc, base):
        if key in cpc_to_hs:
            return sorted(cpc_to_hs[key]), "exact"
    if base:
        wider = sorted({h for c, hs in cpc_to_hs.items() if c.startswith(base) for h in hs})
        if wider:
            return wider, "groupe"
    return [], "aucun"


def build() -> tuple[list[tuple[str, str]], dict]:
    """Couples (préfixe SH, libellé) à ajouter, plus un rapport de génération."""
    # La table de normalisation est importée du script d'ingestion lui-même,
    # et non recopiée : le pont doit pointer vers le libellé que l'ingestion
    # écrit réellement. Deux copies dériveraient au premier ajout.
    from build_production_faostat_usgs import FAOSTAT_ITEM_TO_COMMODITY
    from services.production_capacity_service import HS_TO_COMMODITY_CURATED, _match_commodity

    _ensure_unsd_table()
    cpc_to_hs = _load_cpc_to_hs()
    items, produced = _load_faostat_items()

    entries: dict[str, str] = {}
    stats = collections.Counter()
    unresolved: list[tuple[str, str]] = []
    reachable: set[str] = set()
    unreachable: list[str] = []

    # Un même SH6 revendiqué par deux items est ambigu : notre granularité de
    # commodité est alors plus fine que celle du SH. On le repère d'abord, pour
    # ne l'attribuer à personne plutôt qu'au premier arrivé.
    claims: dict[str, set[str]] = collections.defaultdict(set)
    resolved: dict[str, tuple[str, list[str]]] = {}
    for item_code in sorted(produced):
        cpc, raw_label = items.get(item_code, ("", ""))
        if not raw_label or cpc.startswith(CPC_AGGREGATE_PREFIX):
            if raw_label:
                stats["agrégats écartés"] += 1
            continue
        hs_codes, how = _resolve_hs(cpc, cpc_to_hs)
        if not hs_codes:
            unresolved.append((cpc, raw_label))
            stats["sans correspondance"] += 1
            continue
        stats[f"résolus ({how})"] += 1
        label = FAOSTAT_ITEM_TO_COMMODITY.get(raw_label, raw_label)
        resolved[item_code] = (label, hs_codes)
        for hs in hs_codes:
            claims[hs].add(label)

    for label, hs_codes in resolved.values():
        emitted = False
        for hs in hs_codes:
            # Contre la table CURÉE seule. Interroger le pont complet
            # reviendrait à se comparer à la sortie de la génération
            # précédente : la deuxième exécution verrait ses propres entrées
            # comme « déjà couvertes » et écrirait un module vide.
            existing = _match_commodity(hs, table=HS_TO_COMMODITY_CURATED)
            if existing is not None:
                # Déjà résolu par la table curée. Si c'est vers NOTRE libellé,
                # l'item est atteignable sans rien ajouter ; sinon on n'y
                # touche pas, le pont existant prime.
                if existing[1] == label:
                    emitted = True
                else:
                    stats["déjà couverts par la table curée"] += 1
                continue
            if len(claims[hs]) > 1:
                stats["SH revendiqués par plusieurs items"] += 1
                continue
            entries[hs] = label
            emitted = True
        if emitted:
            reachable.add(label)
        else:
            unreachable.append(label)

    # Point décisif : un libellé qu'aucun code SH n'atteint ne doit PAS être
    # ingéré. L'invariant du dépôt (tests/test_hs_commodity_mapping.py) veut
    # que toute commodité présente soit joignable par un code SH — sans quoi
    # sa donnée est invisible au module Opportunités.
    report = {
        "stats": dict(stats),
        "unresolved": unresolved,
        "hs_added": len(entries),
        "labels_added": len(set(entries.values())),
        "reachable_labels": sorted(reachable),
        "unreachable_labels": sorted(set(unreachable) - reachable),
    }
    return sorted(entries.items()), report


def render(entries: list[tuple[str, str]], report: dict) -> str:
    generated_at = datetime.now(timezone.utc).isoformat()
    body = "\n".join(f'    ("{hs}", "agri", "{label}"),' for hs, label in entries)
    stats = "\n".join(f"#   {k:38} {v}" for k, v in sorted(report["stats"].items()))
    reachable = "\n".join(f'    "{lbl}",' for lbl in report["reachable_labels"])
    unreachable = "\n".join(f"#   {lbl}" for lbl in report["unreachable_labels"])
    return f'''"""
Pont SH → commodités FAOSTAT, dérivé de correspondances publiées.

GÉNÉRÉ AUTOMATIQUEMENT par ``scripts/build_faostat_hs_mapping.py`` — NE PAS
ÉDITER À LA MAIN.

Chaîne de dérivation, deux maillons publiés :
  1. item FAOSTAT → CPC v2.1  (membre ``*_ItemCodes.csv`` du bulk FAOSTAT)
  2. CPC v2.1 → SH 2017       (table officielle UNSD ``CPC21-HS2017.csv``,
     https://unstats.un.org/unsd/classifications/Econ)

Aucune attribution au jugé : rattacher une production au mauvais produit
échangé tromperait le module Opportunités plus sûrement qu'une absence.

Cette liste est ADDITIVE. Les codes SH que la table curée de
``services/production_capacity_service.py`` résout déjà n'y figurent pas :
le pont existant garde son comportement, tests compris.

Généré le : {generated_at}
Bilan de génération :
{stats}
#   codes SH ajoutés                       {report["hs_added"]}
#   libellés distincts atteints            {report["labels_added"]}
"""

from __future__ import annotations

from typing import FrozenSet, List, Tuple

#: (préfixe SH, dataset, libellé de commodité) — même format que
#: ``production_capacity_service.HS_TO_COMMODITY``, dont cette liste est
#: l'extension générée.
FAOSTAT_HS_TO_COMMODITY: List[Tuple[str, str, str]] = [
{body}
]

#: Commodités FAOSTAT qu'AU MOINS un code SH atteint — soit par une entrée
#: ci-dessus, soit parce que la table curée y pointait déjà.
#:
#: L'ingestion s'en sert comme FILTRE : une commodité absente de cet ensemble
#: n'entre pas dans ``production_africaine.json``. L'invariant du dépôt
#: (tests/test_hs_commodity_mapping.py) est ainsi tenu par construction, et non
#: par vigilance — toute commodité ingérée est joignable par un code SH, donc
#: exploitable par le module Opportunités.
FAOSTAT_REACHABLE_COMMODITIES: FrozenSet[str] = frozenset({{
{reachable}
}})

# Commodités écartées faute de code SH qui leur soit propre. La cause n'est pas
# une lacune de la correspondance : ce sont des cas où UN code SH recouvre
# PLUSIEURS commodités FAOSTAT — le SH 0201 « viande de bovins » vaut pour les
# bovins et les buffles, le SH 0205 pour les chevaux et les ânes. Le pont
# n'associe qu'un libellé par préfixe ; trancher reviendrait à attribuer une
# production au mauvais produit. Elles restent donc hors ingestion, en
# attendant que le pont sache exprimer une relation un-à-plusieurs.
#
{unreachable}
'''


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--dry-run", action="store_true", help="N'écrit pas le module")
    args = ap.parse_args()

    print("Génération du pont SH ↔ commodités FAOSTAT")
    print("=" * 52)
    entries, report = build()
    for key, value in sorted(report["stats"].items()):
        print(f"   {key:40} {value}")
    print(f"   {'codes SH ajoutés':40} {report['hs_added']}")
    print(f"   {'libellés distincts atteints':40} {report['labels_added']}")
    print(f"   {'libellés atteignables par un code SH':40} {len(report['reachable_labels'])}")
    print(f"   {'libellés NON atteignables (à écarter)':40} {len(report['unreachable_labels'])}")
    if report["unresolved"]:
        print(f"   non résolus : {report['unresolved']}")
    if report["unreachable_labels"]:
        print(f"   non atteignables : {report['unreachable_labels'][:10]}")

    if args.dry_run:
        print("\n(--dry-run) Module NON écrit.")
        return
    OUT_MODULE.write_text(render(entries, report), encoding="utf-8")
    print(f"\n✅ Écrit : {OUT_MODULE.relative_to(BACKEND_DIR)}")


if __name__ == "__main__":
    main()
