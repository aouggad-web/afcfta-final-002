#!/usr/bin/env python3
"""
Répare l'appariement code/texte des instructions douanières égyptiennes.

Le fichier `backend/data/crawled/EGY_tariffs.json` porte, pour chaque position,
les instructions officielles de la douane égyptienne — préférences tarifaires
(`ر`), formalités administratives (`غ`) et restrictions (`ق`). Le constructeur
appariait ces textes avec le tableau `InstructionCodes` de l'API par `zip`,
c'est-à-dire par position.

Or les deux tableaux que renvoie l'API officielle n'ont ni la même longueur ni
le même ordre. Sur `0101210000`, elle rend onze instructions pour douze codes,
et le tableau des codes contient un doublon. Deux défaillances en découlaient :

* tailles égales — l'appariement par position attribue à chaque texte le code
  d'une autre instruction. Mesuré sur l'API en direct : **1 appariement exact
  sur 15** ;
* tailles inégales — le garde-fou vidait les deux listes, faisant disparaître
  des préférences réellement publiées.

Le code officiel est pourtant inscrit en préfixe de chaque texte. Ce script le
relit et reconstruit `fta_preferences`, `formalities` et `restrictions` à partir
des seuls `official_instructions`, qui sont corrects. Aucune recollecte n'est
nécessaire : la donnée est là, seul son étiquetage était faux.

Le champ `official_instruction_codes` est conservé tel quel — c'est la réponse
brute de la source — mais il ne sert plus de clé d'appariement.

Ce script ne réécrit JAMAIS le fichier collecté sur place. Réparer un fichier
scellé le ferait diverger de ce qui a été collecté, et son sceau d'intégrité
certifierait alors un dérivé au lieu de la collecte. La voie propre est de
reconstruire depuis les fichiers de progression du crawl avec le constructeur
corrigé, puis de resceller — ce qui relève d'une décision de provenance.

Le script mesure par défaut, et n'écrit que dans un fichier distinct nommé
explicitement, pour permettre la comparaison avant cette décision.

Usage :
    python3 scripts/repair_egy_instruction_codes.py
    python3 scripts/repair_egy_instruction_codes.py --out /tmp/EGY_repare.json
"""

from __future__ import annotations

import argparse
import json
import re
from collections import Counter
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
TARIFFS = REPO_ROOT / "backend" / "data" / "crawled" / "EGY_tariffs.json"

INSTRUCTION_CODE_RE = re.compile(r"^\s*([رغق]\d+)")
ZLECAF_MARKER = "افريقية القارية"


def instruction_code(text: str) -> str | None:
    match = INSTRUCTION_CODE_RE.match(str(text or ""))
    return match.group(1) if match else None


def rebuild(position: dict, source: str) -> dict:
    """Reconstruit les trois blocs depuis les textes d'instruction."""
    paires = [(instruction_code(t), t) for t in (position.get("official_instructions") or [])]

    return {
        "formalities": [
            {
                "code_verbatim": code,
                "text_verbatim": texte,
                "kind": "administrative_instruction(غ)",
                "source": source,
            }
            for code, texte in paires
            if code and code.startswith("غ")
        ],
        "restrictions": [
            {
                "code_verbatim": code,
                "text_verbatim": texte,
                "kind": "restriction(ق)",
                "source": source,
            }
            for code, texte in paires
            if code and code.startswith("ق")
        ],
        "fta_preferences": [
            {
                "code_verbatim": code,
                "text_verbatim": texte,
                "kind": "customs_instruction(ر)",
                "zlecaf": ZLECAF_MARKER in texte,
            }
            for code, texte in paires
            if code and code.startswith("ر")
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[1])
    parser.add_argument(
        "--out",
        type=Path,
        help=(
            "écrire le résultat réparé dans ce fichier. Sans cette option le "
            "script se contente de mesurer. Le fichier collecté n'est jamais "
            "modifié sur place."
        ),
    )
    args = parser.parse_args()

    payload = json.loads(TARIFFS.read_text(encoding="utf-8"))
    positions = payload.get("sub_positions") or []

    stats: Counter = Counter()
    for position in positions:
        source = position.get("source") or ""
        avant_pref = position.get("fta_preferences") or []
        avant_form = position.get("formalities") or []

        # Appariements faux avant réparation : le code annoncé ne correspond
        # pas au code inscrit dans le texte qu'il accompagne.
        for entree in avant_pref + avant_form:
            attendu = instruction_code(entree.get("text_verbatim"))
            if attendu and entree.get("code_verbatim") != attendu:
                stats["appariements_faux_avant"] += 1
            else:
                stats["appariements_exacts_avant"] += 1

        blocs = rebuild(position, source)
        if not avant_pref and blocs["fta_preferences"]:
            stats["positions_preferences_recuperees"] += 1
        stats["preferences_avant"] += len(avant_pref)
        stats["preferences_apres"] += len(blocs["fta_preferences"])
        stats["restrictions_apres"] += len(blocs["restrictions"])

        position.update(blocs)
        position["zlecaf_instruction"] = next(
            (p for p in blocs["fta_preferences"] if p["zlecaf"]), None
        )

    faux = stats["appariements_faux_avant"]
    total = faux + stats["appariements_exacts_avant"]
    print(f"positions            : {len(positions)}")
    print(
        f"appariements avant   : {faux} faux sur {total}"
        + (f" ({100*faux/total:.1f} %)" if total else "")
    )
    print(
        f"préférences          : {stats['preferences_avant']} avant, {stats['preferences_apres']} après"
    )
    print(
        f"positions récupérées : {stats['positions_preferences_recuperees']} (listes vidées à tort)"
    )
    print(f"restrictions exposées: {stats['restrictions_apres']} (champ absent auparavant)")

    if not args.out:
        print("\nMesure seule. Utiliser --out pour écrire une copie réparée.")
        return 0

    # La promesse du script est de ne jamais réécrire le fichier collecté sur
    # place : cela le ferait diverger de ce qui a été collecté, et son sceau
    # d'intégrité certifierait alors un dérivé. Une promesse qu'un chemin de
    # sortie peut contourner n'en est pas une.
    if args.out.resolve() == TARIFFS.resolve():
        raise SystemExit(
            "--out ne peut pas désigner le fichier collecté lui-même "
            f"({TARIFFS}). Ce script en écrit une copie ; pour intégrer la "
            "correction, reconstruire depuis les fichiers de progression avec "
            "backend/scripts/build_egy_tariffs_official.py, puis resceller."
        )

    # Le sceau d'intégrité du fichier source certifie le fichier source, pas
    # ce dérivé. L'emporter dans la copie produirait un document dont le sceau
    # ne vérifie pas — verify_crawled_file le rejetterait — et pire, un sceau
    # d'apparence valide attaché à un contenu qu'il n'a jamais couvert. La copie
    # part donc sans sceau, et déclare ce qu'elle est.
    payload.pop("_integrity_seal", None)
    payload["_derived_from"] = {
        "file": str(TARIFFS.relative_to(REPO_ROOT)),
        "by": "scripts/repair_egy_instruction_codes.py",
        "note": (
            "Copie corrigée, non scellée : le sceau du fichier collecté ne "
            "couvre pas ce dérivé. Pour produire un fichier scellé, "
            "reconstruire depuis les fichiers de progression avec "
            "backend/scripts/build_egy_tariffs_official.py."
        ),
    }

    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(
        json.dumps(payload, ensure_ascii=False, separators=(",", ":")) + "\n", encoding="utf-8"
    )
    print(f"\ncopie réparée écrite : {args.out}")
    print(
        "Le fichier collecté reste intact. Pour intégrer la correction, "
        "reconstruire depuis les fichiers de progression avec "
        "backend/scripts/build_egy_tariffs_official.py, puis resceller."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
