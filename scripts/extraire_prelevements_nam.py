"""Fuel levy (Part 5A) et prélèvements environnementaux (Part 3) de la
Schedule No. 1 namibienne, lus dans les Government Gazettes déposées sous
data/sources/NAM/legislation/ (fiche NAM_prelevements_2026-10-25.json) :

- GN 100/2016 (Gazette 6019) : Part 3, Section A — lampes à filament, pneus ;
- GN 225/2019 (Gazette 6967) : Part 5A — fuel levy ;
- GN 226/2019 (même Gazette) : Part 3, Sections B (CO2 des véhicules),
  C (roues équipées de pneus) et D (huiles, sacs plastiques, piles) ;
- GN 131/2020 (Gazette 7239) : pétrole lampant 2710.12.26 ramené à 0.

Une ligne de titre qui porte un taux tout en ayant des sous-positions listées
sous elle (3923.2, 3923.21) ne compte pas : seules les feuilles sont relevées.

    python3 scripts/extraire_prelevements_nam.py data/nam/prelevements_sch1_parts3_5.json
"""
import json
import os
import re
import sys

import pymupdf

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SOURCES = os.path.join(REPO, "data", "sources", "NAM", "legislation")
GN100 = "NAM_EnvironmentalLevy_GN100-2016_2016-05-30.pdf"
GN225_226 = "NAM_FuelLevy_EnvironmentalLevy_GN225-226-2019_2019-08-02.pdf"

#: (fichier, pages de 1 à n, partie) : où chaque partie se lit.
TABLEAUX = (
    (GN100, (2,), "3A"),
    (GN225_226, (2,), "5A"),
    (GN225_226, range(4, 11), "3B"),
    (GN225_226, (10,), "3C"),
    (GN225_226, (11, 12, 13), "3D"),
)
#: GN 131/2020 : « withdrawing the fuel levy of 120 cents per litre imposed on
#: illuminating kerosene under tariff heading “2710.12.26”, reducing the fuel
#: levy to 0 cents per litre with effect from 27 April 2020 ».
GN131_2020 = {"2710.12.26": "0c/li (GN 131/2020, depuis le 27/04/2020)"}

CODE = re.compile(r"\d{4}(?:\.\d{2}(?:\.\d{2})?)?|\d{4}\.\d")
TAUX = re.compile(
    r"N\$\s?(?P<nd>[\d.]+)\s?(?:/|per )(?P<u>lamp|tyre|Li|li|bag)"
    r"|(?P<c>\d+)c/li"
    r"|N\$(?P<co2>\d+) per g/km CO² emissions exceeding (?P<seuil>\d+)g/ ?km"
    r"|(?P<pct>\d+)%"
)


def _codes(cellule):
    # « 8701.10 7 » : le chiffre isolé est la clé de contrôle, pas un code.
    return [c for c in CODE.findall(cellule.replace("4011.0000", "4011").replace("4012.0000", "4012"))]


def _taux(cellule):
    out = []
    for m in TAUX.finditer(cellule.replace("\n", " ")):
        if m.group("nd"):
            unite = {"Li": "li"}.get(m.group("u"), m.group("u"))
            out.append({"montant": float(m.group("nd")), "unite": unite, "brut": m.group(0)})
        elif m.group("c"):
            out.append({"montant": int(m.group("c")) / 100, "unite": "li", "brut": m.group(0)})
        elif m.group("co2"):
            out.append({"par_g_km_co2": float(m.group("co2")), "seuil_g_km": int(m.group("seuil")),
                        "brut": " ".join(m.group(0).split())})
        else:
            out.append({"taux": float(m.group("pct")), "brut": m.group(0)})
    return out


def articles():
    lignes = []
    for fichier, pages, partie in TABLEAUX:
        doc = pymupdf.open(os.path.join(SOURCES, fichier))
        for page in pages:
            for table in doc[page - 1].find_tables().tables:
                for r in table.extract():
                    r = [" ".join((c or "").split()) for c in r]
                    if r[0].startswith(("Fuel Levy", "Environ")):
                        continue
                    codes, taux = _codes(r[1]), _taux(r[3])
                    if partie == "3B" and taux and "g/km" not in taux[0]["brut"]:
                        continue  # le tableau des roues (Section C) partage la page 10
                    if partie == "3C" and taux and "tyre" not in taux[0]["brut"]:
                        continue
                    if partie == "3A" and r[0].startswith("151"):
                        continue  # l'ancienne Section B, remplacée en 2019
                    if not codes or not taux:
                        continue
                    if partie == "3B":
                        # Non liquidé (émissions inconnues) : chaque code garde les taux de sa ligne.
                        bruts = list(dict.fromkeys(t["brut"] for t in taux))
                        taux = [{"brut": " ou ".join(bruts), "par_g_km_co2": True}] * len(codes)
                    elif len({t["brut"] for t in taux}) == 1:
                        taux = taux[:1] * len(codes)  # un même taux répété pour chaque code
                    if len(taux) != len(codes):
                        raise ValueError(f"{fichier} p. {page} : {codes} / {[t['brut'] for t in taux]}")
                    for code, t in zip(codes, taux):
                        lignes.append({"partie": partie, "sous_position": code, "page": page,
                                       "source": fichier, **t})
    # Les feuilles seulement, chacune une fois.
    feuilles, vus = [], set()
    for a in lignes:
        enfants = [b for b in lignes if b is not a and b["partie"] == a["partie"]
                   and b["sous_position"].startswith(a["sous_position"])
                   and b["sous_position"] != a["sous_position"]]
        if enfants or (a["partie"], a["sous_position"]) in vus:
            continue
        vus.add((a["partie"], a["sous_position"]))
        if a["sous_position"] in GN131_2020:
            a = {**a, "montant": 0.0, "brut": GN131_2020[a["sous_position"]]}
        feuilles.append(a)
    return feuilles


if __name__ == "__main__":
    resultat = {"source": "Government Gazettes de Namibie : GN 100/2016, GN 225/2019, GN 226/2019, GN 131/2020",
                "articles": articles()}
    with open(sys.argv[1], "w", encoding="utf-8") as f:
        json.dump(resultat, f, ensure_ascii=False, indent=1)
        f.write("\n")
    print(len(resultat["articles"]), "articles")
