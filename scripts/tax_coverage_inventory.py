#!/usr/bin/env python3
"""
Inventaire de couverture fiscale par pays — préalable au rattrapage de collecte.

« Combler les déficits » porte sur **toutes** les taxes publiées par une source
douanière, pas seulement le droit de douane et la TVA : accises, redevances
statistiques, prélèvements communautaires, surtaxes, redevances de
développement. Ce script recense, pays par pays et taxe par taxe, ce que les
fichiers du dépôt portent réellement.

Principe de méthode
-------------------
Les codes de taxes sont canonicalisés par **la fonction du dépôt**
(`services.authentic_tariff_service._canonical_tax_code`), jamais par une
heuristique propre à ce script. C'est délibéré : un inventaire qui classerait
les taxes autrement que le calculateur mesurerait un déficit que la correction
ne comblerait pas. Cinq tentatives de recherche par mots-clés ont produit cinq
résultats différents et faux avant ce choix — dont un comptage de « VALUE ADDED
TAX » comme droit de douane, parce que le libellé contient « ADDED ».

Les colonnes de droits préférentiels (COMESA `D2R`, SADC, EU/UK, EFTA,
MERCOSUR, ZLECAf) sont exclues du recensement des taxes dues : elles décrivent
un régime alternatif, pas un prélèvement NPF.

Trois états par taxe et par position
------------------------------------
* ``LIQUIDABLE`` — taux numérique exploitable, zéro compris quand il est lu dans
  la source.
* ``SPECIFIQUE`` — valeur non exprimable en pourcentage (« 8c/kg ») : la donnée
  est correcte et collectée, elle réclame une quantité pour être liquidée. **Ce
  n'est pas un déficit de collecte.**
* ``SANS_ASSIETTE`` — taux numérique mais aucune assiette documentée : le
  montant ne peut pas être calculé de façon sûre.

Une taxe absente d'une position n'est pas comptée comme due : on ne peut pas
déduire d'un fichier ce qu'une administration lève. Le rapport dit ce que la
source porte ; l'écart avec ce qui est réellement dû est l'objet de la collecte.

Usage
-----
    python3 scripts/tax_coverage_inventory.py
    python3 scripts/tax_coverage_inventory.py --countries ZAF,GHA --detail
    python3 scripts/tax_coverage_inventory.py --out inventaire.json
"""

from __future__ import annotations

import argparse
import collections
import json
import pathlib
import re
import sys
from datetime import datetime, timezone
from typing import Any, Dict, Iterable, List, Optional, Tuple

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
BACKEND = REPO_ROOT / "backend"
for _path in (REPO_ROOT, BACKEND):
    if str(_path) not in sys.path:
        sys.path.insert(0, str(_path))

CRAWLED_DIR = BACKEND / "data" / "crawled"

NUMBER = re.compile(r"-?\d+(?:[.,]\d+)?")

LIQUIDABLE = "LIQUIDABLE"
SPECIFIQUE = "SPECIFIQUE"
SANS_ASSIETTE = "SANS_ASSIETTE"


def _repo_helpers():
    """Canonisation et exclusions : celles du dépôt, pas celles de ce script."""
    from services.authentic_tariff_service import (
        _PREFERENTIAL_RATE_CODES,
        _canonical_tax_code,
    )

    return _canonical_tax_code, set(_PREFERENTIAL_RATE_CODES)


def positions(payload: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Les quatre conteneurs de positions rencontrés dans le dépôt."""
    for key in ("sub_positions", "positions"):
        if isinstance(payload.get(key), list) and payload[key]:
            return payload[key]
    out: List[Dict[str, Any]] = []
    for line in payload.get("tariff_lines", []) or []:
        out.extend(line.get("sub_positions", []) or [])
    return out


def tax_entries(position: Dict[str, Any]) -> List[Tuple[str, str, Any]]:
    """
    (code brut, libellé, valeur) pour chaque taxe, quel que soit le schéma.

    Six représentations coexistent : dictionnaire indexé par code (Algérie,
    Égypte), dictionnaire indexé par libellé français (Maroc), liste `taxes[]`
    (SACU, Nigeria), liste `taxes_import[]` (Tunisie), liste `taxes_detail[]`
    (EAC), et champ direct `dd` sans collection (Ghana).
    """
    out: List[Tuple[str, str, Any]] = []
    # La collection détaillée passe AVANT la collection compacte. Chez les pays
    # CEDEAO et CEMAC les deux coexistent et portent les mêmes taxes, mais seule
    # `taxes_detail` documente l'assiette : `taxes` y est un dictionnaire de
    # taux nus, `{"DD": 20.0}`. Dédupliquer dans l'autre sens retiendrait le
    # taux sans assiette et classerait en SANS_ASSIETTE des assiettes que la
    # source publie.
    for key in ("taxes_detail", "taxes_import", "taxes"):
        block = position.get(key)
        if isinstance(block, dict):
            for code, value in block.items():
                name = ""
                if isinstance(value, dict):
                    name = str(value.get("name") or value.get("label_published") or "")
                # La clé brute est reprise dans le slot libellé : le Maroc indexe
                # ses taxes par intitulé français, et `_canonical_tax_code` ne
                # reconnaît « Droit d'Importation (DI) » que par le libellé — le
                # code, lui, est normalisé sans espaces et ne matche plus.
                out.append((str(code), f"{name} {code}".strip(), value))
        elif isinstance(block, list):
            for item in block:
                if not isinstance(item, dict):
                    continue
                # Le code d'une entrée-liste n'a pas partout la même clé :
                # `tax_code` chez les 19 pays CEDEAO et CEMAC, `tax` dans le
                # schéma canonique v4, `code` chez SACU, le Nigeria et la
                # Tunisie. N'en lire qu'une rend les autres invisibles — et un
                # code vide n'est pas une taxe non classée, c'est une clé non lue.
                code = str(item.get("code") or item.get("tax_code") or item.get("tax") or "")
                name = str(item.get("name") or item.get("tax_name") or "")
                out.append((code, f"{name} {code}".strip(), item))
    for key in ("dd", "dd_rate"):
        if position.get(key) is not None:
            out.append(("DD", "droit de douane", {"rate": position[key]}))
            break
    return out


def preferential_blocks(position: Dict[str, Any]) -> List[Tuple[str, Any]]:
    """
    Régimes préférentiels portés hors de la collection de taxes.

    Plusieurs sources les publient dans un champ à part, invisible d'un
    recensement qui ne lirait que `taxes` : la Tunisie donne un taux par pays
    partenaire et par accord (`preferences`), l'EAC une franchise
    intra-communautaire (`fiscal_advantages`), l'Algérie des exonérations en
    texte libre (`advantages`), l'Éthiopie sa colonne COMESA.
    """
    out: List[Tuple[str, Any]] = []
    for field in ("preferences", "advantages", "fiscal_advantages", "preferential_rates"):
        block = position.get(field)
        if block:
            out.append((field, block))
    return out


def numeric_rate(value: Any) -> Optional[float]:
    """Taux numérique exploitable. Une chaîne « 2.5 % » en est un ; « 8c/kg » non."""
    if isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, dict):
        for key in ("rate", "rate_pct"):
            candidate = value.get(key)
            if isinstance(candidate, (int, float)) and not isinstance(candidate, bool):
                return float(candidate)
        for key in ("raw", "raw_value"):
            text = value.get(key)
            if isinstance(text, str) and "%" in text:
                match = NUMBER.search(text.replace(",", "."))
                if match:
                    return float(match.group())
        return None
    if isinstance(value, str):
        if "%" not in value:
            return None
        match = NUMBER.search(value.replace(",", "."))
        return float(match.group()) if match else None
    return None


def specific_expression(value: Any) -> Optional[str]:
    if not isinstance(value, dict):
        return None
    for key in ("specific_value", "raw_value", "raw"):
        text = value.get(key)
        if isinstance(text, str) and text.strip() and "%" not in text:
            return text.strip()
    return None


def declared_base(value: Any) -> Optional[str]:
    if not isinstance(value, dict):
        return None
    for key in ("assiette", "base", "base_expr"):
        text = value.get(key)
        if isinstance(text, str) and text.strip():
            return text.strip()
    return None


def inventory(countries: Optional[Iterable[str]] = None) -> Dict[str, Any]:
    canonical, preferential = _repo_helpers()
    wanted = {iso.upper() for iso in countries} if countries else None

    per_country: Dict[str, Any] = {}
    global_tax: Dict[str, collections.Counter] = collections.defaultdict(collections.Counter)
    global_pref: Dict[str, collections.Counter] = collections.defaultdict(collections.Counter)

    for path in sorted(CRAWLED_DIR.glob("*_tariffs.json")):
        iso = path.name.split("_")[0].upper()
        if len(iso) != 3 or not iso.isalpha():
            continue
        if wanted and iso not in wanted:
            continue
        try:
            with path.open(encoding="utf-8") as handle:
                payload = json.load(handle)
        except Exception as exc:
            per_country[iso] = {"erreur": str(exc)[:80]}
            continue

        rows = positions(payload)
        if not rows:
            per_country[iso] = {"lignes": 0, "taxes": {}, "note": "fichier sans position"}
            continue

        stats: Dict[str, collections.Counter] = collections.defaultdict(collections.Counter)
        bases: Dict[str, collections.Counter] = collections.defaultdict(collections.Counter)
        prefer: Dict[str, collections.Counter] = collections.defaultdict(collections.Counter)
        pref_fields: Dict[str, int] = collections.Counter()
        pref_zones: Dict[str, int] = collections.Counter()
        for row in rows:
            for field, block in preferential_blocks(row):
                pref_fields[field] += 1
                # Les zones/accords nommés, quand la source les structure.
                if isinstance(block, list):
                    for item in block:
                        if isinstance(item, dict):
                            zone = item.get("zone") or item.get("name") or item.get("regime")
                            if zone:
                                pref_zones[str(zone)[:40]] += 1
            seen_codes = set()
            for raw_code, label, value in tax_entries(row):
                code = canonical(raw_code, label)
                if code in seen_codes:
                    # `taxes` et `taxes_detail` coexistent chez les pays CEDEAO :
                    # une même taxe y figure deux fois.
                    continue
                seen_codes.add(code)
                if code in preferential:
                    # Régime alternatif, jamais ajouté à la cascade NPF — mais
                    # recensé : pour un outil du commerce intra-africain, les
                    # colonnes préférentielles sont la donnée la plus utile.
                    if numeric_rate(value) is not None:
                        prefer[code]["LIQUIDABLE"] += 1
                        global_pref[code]["LIQUIDABLE"] += 1
                    elif specific_expression(value):
                        prefer[code]["SPECIFIQUE"] += 1
                        global_pref[code]["SPECIFIQUE"] += 1
                    continue
                base = declared_base(value)
                if numeric_rate(value) is not None:
                    state = LIQUIDABLE if base else SANS_ASSIETTE
                elif specific_expression(value):
                    state = SPECIFIQUE
                else:
                    continue  # entrée sans taux ni expression : rien de publié
                stats[code][state] += 1
                bases[code]["avec_assiette" if base else "sans_assiette"] += 1
                global_tax[code][state] += 1

        per_country[iso] = {
            "lignes": len(rows),
            "nb_taxes_distinctes": len(stats),
            "champs_preferentiels": dict(pref_fields),
            "zones_preferentielles": dict(pref_zones.most_common(20)),
            "regimes_preferentiels": {
                code: {
                    "positions_couvertes": sum(counter.values()),
                    "couverture_pct": round(100 * sum(counter.values()) / len(rows), 1),
                    "etats": dict(counter),
                }
                for code, counter in sorted(prefer.items())
            },
            "taxes": {
                code: {
                    "positions_couvertes": sum(counter.values()),
                    "couverture_pct": round(100 * sum(counter.values()) / len(rows), 1),
                    "etats": dict(counter),
                    "assiette": dict(bases[code]),
                }
                for code, counter in sorted(stats.items())
            },
        }

    # Tout code qui n'est ni une taxe NPF connue ni un régime préférentiel listé
    # par le dépôt : c'est là qu'apparaissent les colonnes préférentielles non
    # répertoriées (Agadir, accords arabes, Turquie, AGOA, colonnes du Schedule
    # sud-africain...). Ne jamais détecter un régime par une liste figée : la
    # liste du dépôt sert à exclure de la cascade NPF, pas à découvrir.
    from services.tax_computation import DD_CODES, VAT_CODES

    connus = (
        set(DD_CODES)
        | set(VAT_CODES)
        | {
            "DD",
            "TVA",
            "IDF",
            "RDL",
            "GETFUND",
            "SUR",
            "TCL",
            "NHIL",
        }
    )
    non_classes = {
        code: dict(counter)
        for code, counter in sorted(global_tax.items())
        if code not in connus and code not in preferential
    }

    return {
        "metadata": {
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "canonisation": "services.authentic_tariff_service._canonical_tax_code",
            "exclusions": sorted(preferential),
            "note": (
                "Le rapport décrit ce que les fichiers portent. Une taxe absente n'est "
                "pas réputée non due : l'écart avec les prélèvements réellement levés "
                "est l'objet de la collecte."
            ),
        },
        "par_pays": per_country,
        "par_taxe": {code: dict(counter) for code, counter in sorted(global_tax.items())},
        "par_regime_preferentiel": {
            code: dict(counter) for code, counter in sorted(global_pref.items())
        },
        "codes_non_classes": non_classes,
    }


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[1])
    parser.add_argument("--countries", help="Liste ISO3 séparée par des virgules")
    parser.add_argument("--out", help="Écrire le rapport JSON dans ce fichier")
    parser.add_argument("--detail", action="store_true", help="Détail par taxe sur stdout")
    args = parser.parse_args(argv)

    selected = args.countries.split(",") if args.countries else None
    report = inventory(selected)

    payload = json.dumps(report, ensure_ascii=False, indent=2)
    if args.out:
        pathlib.Path(args.out).parent.mkdir(parents=True, exist_ok=True)
        pathlib.Path(args.out).write_text(payload + "\n", encoding="utf-8")
    else:
        print(payload)

    print("\nTaxes distinctes recensées, tous pays :", file=sys.stderr)
    for code, states in report["par_taxe"].items():
        total = sum(states.values())
        print(f"  {code:<10} {total:>8} occurrences  {dict(states)}", file=sys.stderr)

    print("\nRégimes préférentiels recensés, tous pays :", file=sys.stderr)
    for code, states in report["par_regime_preferentiel"].items():
        total = sum(states.values())
        print(f"  {code:<10} {total:>8} occurrences  {dict(states)}", file=sys.stderr)

    non_classes = report["codes_non_classes"]
    print(
        f"\nCodes non classés ({len(non_classes)}) — à trier entre taxe et "
        f"régime préférentiel :",
        file=sys.stderr,
    )
    for code, states in sorted(non_classes.items(), key=lambda kv: -sum(kv[1].values()))[:40]:
        print(f"  {code:<22} {sum(states.values()):>8}", file=sys.stderr)

    if args.detail:
        for iso, data in report["par_pays"].items():
            if not data.get("taxes"):
                continue
            print(
                f"\n{iso} — {data['lignes']} lignes, " f"{data['nb_taxes_distinctes']} taxes",
                file=sys.stderr,
            )
            for code, info in data["taxes"].items():
                print(
                    f"   {code:<10} {info['couverture_pct']:>5} %  {info['etats']}", file=sys.stderr
                )
    return 0


if __name__ == "__main__":
    sys.exit(main())
