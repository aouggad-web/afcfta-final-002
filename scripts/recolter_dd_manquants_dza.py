#!/usr/bin/env python3
"""Les 299 droits algériens que le miroir n'a pas publiés, lus à la source.

LE DÉFAUT. La collecte algérienne s'appuie sur `conformepro.dz`, qui republie
les données de la DGD. Ce miroir **n'affiche aucun bloc « Droit de douane »
quand le droit vaut zéro**. Vérifié sur trois pages, à la main :

    01.01.2111.00 (cheval de pur-sang, droit 5 %)  → bloc « Droit de douane 5% »
    10.01.1100.00 (blé dur de semence)             → AUCUN bloc
    27.10.1224.00 (pétrole lampant / kérosène)     → AUCUN bloc

Le collecteur est fidèle à ce qu'il lit : c'est la source republiée qui est
lacunaire. Conséquence mesurée sur le socle : **0 droit de douane à 0 % sur
16 927 captés**. Un tarif national de 17 226 lignes sans une seule ligne en
franchise n'existe pas.

Le portail officiel de la DGD, lui, publie le zéro. Sur cette même position :

    Taxes Ad-Valorem : D.D 0.00 | PRCT 2.00 | T.C.S 3.00 | T.V.A 19.00

CE QUE FAIT CE SCRIPT. Il relit à la source primaire, position par position,
les seules lignes dont le droit manque — et n'écrit rien d'autre. Il ne
suppose JAMAIS qu'une absence vaut zéro : si le portail officiel ne publie pas
davantage, la lacune reste une lacune et le script la compte comme telle.

    python3 scripts/recolter_dd_manquants_dza.py --sortie /tmp/DZA_dd_officiels.json
"""

from __future__ import annotations

import argparse
import collections
import json
import pathlib
import sys

RACINE = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RACINE / "backend"))

CRAWL = RACINE / "backend" / "data" / "crawled" / "DZA_tariffs.json"


def positions_sans_droit(crawl: dict) -> list[dict]:
    return [x for x in crawl["sub_positions"] if "DD" not in (x.get("taxes") or {})]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--sortie", required=True)
    parser.add_argument("--delai", type=float, default=0.3)
    args = parser.parse_args()

    from crawlers.countries.algeria_dgd_official_scraper import DgdOfficialScraper

    crawl = json.loads(CRAWL.read_text(encoding="utf-8"))
    cibles = positions_sans_droit(crawl)
    par_code = {x["hs_code"]: x for x in cibles}
    print(f"positions sans droit de douane dans le miroir : {len(cibles)}", flush=True)

    # Regroupées par position tarifaire (« heading ») : l'e-service de la DGD
    # se parcourt par niveaux, et une seule descente sert toutes les feuilles
    # d'une même position.
    par_heading: dict[tuple[str, str], list[str]] = collections.defaultdict(list)
    for x in cibles:
        par_heading[(x["chapter"], x["heading"])].append(x["hs_code"])
    print(f"positions tarifaires à descendre : {len(par_heading)}", flush=True)

    scraper = DgdOfficialScraper(delay=args.delai)
    sections = scraper.chapter_sections()
    print(f"chapitres découverts à la source : {len(sections)}", flush=True)

    lues: dict[str, dict] = {}
    echecs: list[str] = []
    for i, ((chapitre, heading), codes) in enumerate(sorted(par_heading.items()), 1):
        section = sections.get(chapitre)
        if section is None:
            echecs.append(f"{heading} : chapitre {chapitre} absent de la navigation DGD")
            continue
        try:
            feuilles = scraper.leaves(section, chapitre, headings=[heading])
        except Exception as exc:  # noqa: BLE001 — l'échec est compté, pas masqué
            echecs.append(f"{heading} : {exc}")
            continue
        voulues = {c for c in codes}
        for feuille in feuilles:
            if feuille["sub_position"] not in voulues:
                continue
            try:
                detail = scraper.leaf_detail(feuille)
            except Exception as exc:  # noqa: BLE001
                echecs.append(f"{feuille['sub_position']} : {exc}")
                continue
            lues[feuille["sub_position"]] = detail
        print(
            f"[{i}/{len(par_heading)}] {heading} — {len(voulues)} visée(s), "
            f"{sum(1 for c in voulues if c in lues)} lue(s)",
            flush=True,
        )

    # BILAN. Trois issues, et elles ne se confondent pas : le droit est publié
    # (quelle que soit sa valeur, zéro compris), la fiche est lue mais ne
    # publie aucun droit, ou la fiche n'a pas pu être lue.
    avec_droit = {c: d for c, d in lues.items() if "DD" in (d.get("taxes") or {})}
    sans_droit = sorted(set(lues) - set(avec_droit))
    non_lues = sorted(set(par_code) - set(lues))
    valeurs = collections.Counter(d["taxes"]["DD"]["rate"] for d in avec_droit.values())

    bilan = {
        "source": "douane.gov.dz — Tarif douanier (e-service DGD)",
        "visees": len(par_code),
        "lues": len(lues),
        "droit_publie": len(avec_droit),
        "droit_absent_a_la_source": sans_droit,
        "non_lues": non_lues,
        "valeurs_du_droit": {str(k): v for k, v in sorted(valeurs.items())},
        "erreurs": echecs,
        "positions": lues,
    }
    pathlib.Path(args.sortie).write_text(
        json.dumps(bilan, ensure_ascii=False, indent=1), encoding="utf-8"
    )

    print("\n— BILAN —", flush=True)
    print(f"visées                    : {len(par_code)}")
    print(f"fiches lues à la source   : {len(lues)}")
    print(f"droit de douane publié    : {len(avec_droit)}")
    print(f"valeurs du droit          : {dict(sorted(valeurs.items()))}")
    print(f"droit absent à la source  : {len(sans_droit)}")
    print(f"fiches non lues           : {len(non_lues)}")
    print(f"erreurs                   : {len(echecs)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
