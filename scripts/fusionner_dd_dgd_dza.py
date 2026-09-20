#!/usr/bin/env python3
"""Verse dans le crawl algérien les droits relus à la DGD.

Ce script est la seconde moitié de `recolter_dd_manquants_dza.py` : celui-là
lit la source primaire, celui-ci écrit. Il n'écrit QUE les droits que la DGD
publie, et ne touche à rien d'autre — ni aux taux déjà captés, ni aux
positions dont le droit manque encore.

    python3 scripts/recolter_dd_manquants_dza.py --sortie releve.json
    python3 scripts/fusionner_dd_dgd_dza.py --releve releve.json
    python3 scripts/build_socle.py

CE QU'IL NE FAIT PAS. Il ne pose jamais 0 sur une position dont la DGD ne
publie pas de droit. Sur les 299 positions relevées, trois sont dans ce cas —
le chapitre 98, régimes douaniers particuliers (marchandises d'exposition et
de démonstration) : elles gardent leur lacune, déclarée.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import pathlib

RACINE = pathlib.Path(__file__).resolve().parents[1]
CRAWL = RACINE / "backend" / "data" / "crawled" / "DZA_tariffs.json"
REGISTRE = RACINE / "backend" / "data" / "source_registry_v2.json"
ARCHIVE = RACINE / "data" / "dza" / "releve_dd_dgd.json"

SOURCE = "douane.gov.dz — Tarif douanier (e-service DGD)"
RACINE_URL = "https://www.douane.gov.dz/spip.php?page=tarif_douanier"
NOTE = (
    "Droit relu à la source primaire (e-service DGD). Le miroir conformepro.dz, "
    "dont provient le reste de cette ligne, ne publie aucun bloc « Droit de "
    "douane » quand celui-ci vaut zéro : le taux n'était pas absent du tarif, "
    "il était absent du miroir."
)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--releve", required=True)
    args = parser.parse_args()

    releve = json.loads(pathlib.Path(args.releve).read_text(encoding="utf-8"))
    crawl = json.loads(CRAWL.read_text(encoding="utf-8"))

    versees, ignorees, deja = 0, [], 0
    archive = {}
    par_code = {x["hs_code"]: x for x in crawl["sub_positions"]}

    for code, fiche in releve["positions"].items():
        dgd = (fiche.get("taxes") or {}).get("DD")
        ligne = par_code.get(code)
        if ligne is None:
            ignorees.append(f"{code} : absente du crawl")
            continue
        if dgd is None:
            # La source primaire ne publie pas de droit non plus : la lacune
            # reste une lacune. On ne la comble pas, on la garde nommée.
            ignorees.append(f"{code} : aucun droit publié par la DGD")
            continue
        if "DD" in (ligne.get("taxes") or {}):
            deja += 1
            continue

        ligne.setdefault("taxes", {})["DD"] = {
            "code": "DD",
            "label_published": dgd.get("label_published", "D.D"),
            "rate": dgd["rate"],
            "raw": f"{dgd['rate']}%",
            "source": SOURCE,
            "source_root_url": RACINE_URL,
            "source_url": fiche.get("source_url"),
            "official_dgd_code": dgd.get("official_dgd_code", "D.D"),
            "official_dgd_label": dgd.get("official_dgd_label", "Droits de Douane"),
            "label_verification": "PUBLISHED_BY_DGD",
            "observation": dgd.get("observation"),
            "note": NOTE,
        }
        ligne["source_gaps"] = [g for g in (ligne.get("source_gaps") or []) if g != "DD"]
        archive[code] = {
            "rate": dgd["rate"],
            "label_published": dgd.get("label_published"),
            "observation": dgd.get("observation"),
            "source_url": fiche.get("source_url"),
        }
        versees += 1

    CRAWL.write_text(json.dumps(crawl, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    empreinte = hashlib.sha256(CRAWL.read_bytes()).hexdigest()

    ARCHIVE.parent.mkdir(parents=True, exist_ok=True)
    ARCHIVE.write_text(
        json.dumps(
            {
                "source": SOURCE,
                "source_root_url": RACINE_URL,
                "releve_le": releve.get("releve_le"),
                "motif": NOTE,
                "positions_relues": releve["visees"],
                "droits_verses": versees,
                "sans_droit_a_la_source": releve["droit_absent_a_la_source"],
                "droits": dict(sorted(archive.items())),
            },
            ensure_ascii=False,
            indent=1,
        )
        + "\n",
        encoding="utf-8",
    )

    registre = json.loads(REGISTRE.read_text(encoding="utf-8"))
    entree = registre["countries"]["DZA"]
    entree["sha256"] = empreinte
    entree["organism"] = (
        "Direction Générale des Douanes (DGD) via conformepro.dz, "
        "droits nuls relus sur l'e-service DGD"
    )
    REGISTRE.write_text(json.dumps(registre, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    print(f"droits versés            : {versees}")
    print(f"déjà présents (intacts)  : {deja}")
    print(f"non versés (déclarés)    : {len(ignorees)}")
    for m in ignorees:
        print(f"   {m}")
    print(f"empreinte DZA_tariffs    : {empreinte}")
    print(f"archive du relevé        : {ARCHIVE.relative_to(RACINE)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
