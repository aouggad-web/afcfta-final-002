#!/usr/bin/env python3
"""Quels pays ont perdu leurs droits à 0 % en chemin ?

LE DÉFAUT QUE CE SCRIPT CHERCHE. Certaines sources — notamment les miroirs qui
republient un tarif officiel — n'affichent aucun bloc « droit de douane »
quand celui-ci vaut zéro. Le collecteur, fidèle à ce qu'il lit, n'enregistre
rien ; le socle en tire une indisponibilité ; et le calculateur refuse de
liquider une position que le tarif laisse pourtant en franchise.

Découvert sur l'Algérie : `conformepro.dz` supprime le bloc quand le droit est
nul. Le portail officiel de la DGD, lui, publie « D.D 0.00 ». 296 droits
avaient disparu de cette façon.

LA SIGNATURE, ET POURQUOI ELLE EST FIABLE. Un tarif national comporte toujours
des milliers de lignes en franchise. Si un pays présente BEAUCOUP de positions
dont le droit est indisponible et AUCUNE dont le droit vaut zéro, ce n'est pas
un tarif sans franchise : c'est une chaîne incapable de transporter un zéro.

À l'inverse, quand un pays publie des milliers de droits à 0 % ET porte
quelques droits indisponibles, ces derniers sont de VRAIES lacunes. Les
combler serait inventer des franchises.

CE QUE CE SCRIPT NE FAIT PAS. Il n'écrit rien, ne corrige rien, ne suppose
rien. Il mesure, il classe, et il produit l'ordre de travail : la liste exacte
des positions à relire à la source primaire, avec la source que le socle leur
attribue. La relecture, elle, se fait PAYS PAR PAYS — chaque portail a sa
navigation — puis se verse avec un script de fusion dédié, sur le modèle de
`scripts/recolter_dd_manquants_dza.py` et `scripts/fusionner_dd_dgd_dza.py`.

    python3 scripts/diagnostic_zeros_perdus.py
    python3 scripts/diagnostic_zeros_perdus.py --pays ETH --ordre /tmp/ETH.json
"""

from __future__ import annotations

import argparse
import collections
import json
import pathlib

RACINE = pathlib.Path(__file__).resolve().parents[1]
SOCLE = RACINE / "backend" / "socle"
NON_PAYS = {
    "MANIFESTE.json",
    "assiettes_pays.json",
    "devises_pays.json",
    "tva_nationale.json",
}

#: Prélèvement examiné. Le droit de douane est le seul dont l'absence fasse
#: basculer un total en « indisponible » sur la quasi-totalité des tarifs ;
#: les autres se traitent à part, avec leur propre établissement d'assiette.
CODE = "DD"

#: En deçà de ce nombre de droits captés, l'absence de zéro ne prouve rien :
#: un échantillon trop mince peut n'en contenir aucun par hasard.
ASSEZ_DE_DROITS = 500

#: Part des droits captés valant zéro, en deçà de laquelle le doute s'impose
#: sans que rien ne soit prouvé. Le défaut n'est pas toujours total : une
#: source peut transporter le zéro sur une partie de son tarif seulement. Les
#: pays au-dessus de ce seuil vont de 1,7 % (Algérie) à 93 % (Maurice) ; très
#: en dessous, l'écart demande un examen à la main plutôt qu'un verdict.
PART_DE_ZEROS_PLAUSIBLE = 0.01

#: Les trois états qui appellent un examen, par ordre de gravité.
A_EXAMINER = ("ZERO_IMPOSSIBLE", "PART_DE_ZEROS_ANORMALE", "ECHANTILLON_TROP_MINCE")


def _droit(position: dict) -> dict | None:
    for d in position.get("droits") or []:
        if d.get("code") == CODE:
            return d
    return None


def mesurer(chemin: pathlib.Path) -> dict:
    """Le compte des zéros, des indisponibles et des absents d'un pays."""
    donnees = json.loads(chemin.read_text(encoding="utf-8"))
    zeros = indisponibles = captes = sans_ligne = 0
    positions = donnees.get("positions") or {}
    sources: collections.Counter = collections.Counter()

    for p in positions.values():
        if not isinstance(p, dict):
            continue
        d = _droit(p)
        if d is None:
            sans_ligne += 1
            continue
        captes += 1
        if d.get("taux") is None:
            indisponibles += 1
            if d.get("source"):
                sources[d["source"]] += 1
        elif d["taux"] == 0.0:
            zeros += 1

    return {
        "pays": chemin.stem,
        "positions": len(positions),
        "droits_captes": captes,
        "droits_a_zero": zeros,
        "droits_indisponibles": indisponibles,
        "positions_sans_ligne_de_droit": sans_ligne,
        "sources_des_indisponibles": dict(sources.most_common(3)),
    }


def verdict(m: dict) -> str:
    """Trois états, et ils ne se confondent pas."""
    a_combler = m["droits_indisponibles"] + m["positions_sans_ligne_de_droit"]
    if a_combler == 0:
        return "RIEN_A_FAIRE"
    if m["droits_captes"] < ASSEZ_DE_DROITS:
        return "ECHANTILLON_TROP_MINCE"
    if m["droits_a_zero"] == 0:
        return "ZERO_IMPOSSIBLE"
    if m["droits_a_zero"] / m["droits_captes"] < PART_DE_ZEROS_PLAUSIBLE:
        return "PART_DE_ZEROS_ANORMALE"
    return "LACUNE_REELLE"


EXPLICATION = {
    "ZERO_IMPOSSIBLE": (
        "Aucun droit à 0 % sur un tarif entier : la chaîne ne sait pas "
        "transporter un zéro. À RELIRE à la source primaire."
    ),
    "PART_DE_ZEROS_ANORMALE": (
        "Le zéro passe, mais si rarement que la chaîne en perd "
        "vraisemblablement une partie. À EXAMINER à la main, sans conclure."
    ),
    "LACUNE_REELLE": (
        "Le pays publie des droits à 0 % que la chaîne transporte : les "
        "indisponibles sont de vraies lacunes. NE PAS les combler."
    ),
    "ECHANTILLON_TROP_MINCE": (
        "Trop peu de droits captés pour conclure : l'absence de zéro peut "
        "n'être qu'un effet du petit nombre. À examiner à la main."
    ),
    "RIEN_A_FAIRE": "Aucun droit manquant.",
}


def ordre_de_travail(chemin: pathlib.Path) -> dict:
    """La liste exacte des positions à relire, et ce que le socle en sait."""
    donnees = json.loads(chemin.read_text(encoding="utf-8"))
    a_relire = []
    for code, p in (donnees.get("positions") or {}).items():
        if not isinstance(p, dict):
            continue
        d = _droit(p)
        if d is not None and d.get("taux") is not None:
            continue
        a_relire.append(
            {
                "code": code,
                "designation": (p.get("designation") or "")[:160],
                "chapitre": p.get("chapitre"),
                "motif_actuel": (d or {}).get("note") or "aucune ligne de droit",
                "source_declaree": (d or {}).get("source") or p.get("source"),
                "autres_prelevements": [
                    x.get("code") for x in p.get("droits") or [] if x.get("code") != CODE
                ],
            }
        )
    return {
        "pays": chemin.stem,
        "prelevement": CODE,
        "a_relire": len(a_relire),
        "consigne": (
            "Relire CHAQUE position à la source primaire du pays. Ne verser "
            "un taux que si la source le publie. Une position dont la source "
            "primaire ne publie aucun droit garde sa lacune, déclarée : ne "
            "jamais poser 0 par régularité avec les autres."
        ),
        "positions": sorted(a_relire, key=lambda x: x["code"]),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pays", help="code ISO3 ; sans lui, tous les pays sont mesurés")
    parser.add_argument("--ordre", help="fichier où écrire l'ordre de travail (avec --pays)")
    args = parser.parse_args()

    if not SOCLE.exists():
        print("socle absent : python3 scripts/build_socle.py")
        return 1

    fichiers = sorted(f for f in SOCLE.glob("*.json") if f.name not in NON_PAYS)
    if args.pays:
        fichiers = [f for f in fichiers if f.stem == args.pays.upper()]
        if not fichiers:
            print(f"{args.pays} : absent du socle")
            return 1

    mesures = [mesurer(f) for f in fichiers]
    a_traiter = [m for m in mesures if verdict(m) in ("ZERO_IMPOSSIBLE", "ECHANTILLON_TROP_MINCE")]

    largeur = max((len(m["pays"]) for m in mesures), default=4)
    print(f"{'pays':{largeur}} {'à 0 %':>9} {'indispo.':>9} {'captés':>9}  verdict")
    for m in sorted(mesures, key=lambda m: -(m["droits_indisponibles"])):
        if verdict(m) == "RIEN_A_FAIRE" and not args.pays:
            continue
        manquants = m["droits_indisponibles"] + m["positions_sans_ligne_de_droit"]
        part = m["droits_a_zero"] / m["droits_captes"] * 100 if m["droits_captes"] else 0.0
        print(
            f"{m['pays']:{largeur}} {m['droits_a_zero']:9} {part:7.1f}% {manquants:9} "
            f"{m['droits_captes']:9}  {verdict(m)}"
        )

    print()
    for etat in A_EXAMINER + ("LACUNE_REELLE",):
        concernes = [m["pays"] for m in mesures if verdict(m) == etat]
        if concernes:
            print(f"{etat} ({len(concernes)}) — {EXPLICATION[etat]}")
            print(f"   {', '.join(concernes)}\n")

    if a_traiter:
        print("Sources déclarées des droits manquants, pour savoir où aller relire :")
        for m in a_traiter:
            for source, n in m["sources_des_indisponibles"].items():
                print(f"   {m['pays']} — {n} × {source}")

    if args.ordre:
        if not args.pays:
            print("\n--ordre exige --pays : un ordre de travail se fait pays par pays.")
            return 1
        ordre = ordre_de_travail(fichiers[0])
        pathlib.Path(args.ordre).write_text(
            json.dumps(ordre, ensure_ascii=False, indent=1) + "\n", encoding="utf-8"
        )
        print(f"\nordre de travail : {ordre['a_relire']} positions → {args.ordre}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
