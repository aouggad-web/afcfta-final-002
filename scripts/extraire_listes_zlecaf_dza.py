"""Listes officielles A, B et C du schéma de démantèlement ZLECAf à l'importation en Algérie.

Les quatre PDF (« PDF algerie-zlecaf » du Drive de l'exploitant, publiés par la Douane algérienne,
annexes de la circulaire 482/DGD/SP/D.042/24) donnent, ligne par ligne, le taux de base de 2019, la
série annuelle de taux et, dans la colonne « Observations », les lignes gelées faute de règle
d'origine (« régime droit commun »). Ce script lit leurs tableaux (pymupdf.find_tables), contrôle la
lecture contre le dépôt et le calendrier de la circulaire, puis écrit deux fichiers :

- backend/data/zlecaf_dza/frozen_codes.json : les 1 458 lignes gelées (1 136 en liste A, 322 en
  liste B), exactes, là où le code ne les repérait que par plages de positions ;
- backend/data/zlecaf_dza/list_a_base_rates.json : le taux de base 2019 des 15 703 lignes de la liste A,
  regroupées par taux (le calendrier de la liste A se calcule sur ce taux, non sur le taux courant).

Les PDF ne sont pas dans le dépôt (8,6 Mo pour la liste A) : leurs empreintes sont dans la fiche
DZA_listes_a_b_c_verification_2026-11-20.json.

    python3 scripts/extraire_listes_zlecaf_dza.py liste_a_5_ans.pdf liste_b_10_ans.pdf liste_b_13ans.pdf liste_c.pdf
"""
import collections
import json
import os
import re
import sys

import pymupdf

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(REPO, "backend", "data", "zlecaf_dza")
CODE = re.compile(r"\d{4}\.\d{2}\.\d{2}\.\d{2}")

#: Effectifs officiels (schéma général, page 24 de la circulaire).
OFFICIEL = {"A": 15703, "A_gelees": 1136, "B": 1163, "B_gelees": 322, "C": 456, "total": 17322}
#: Part du taux de base encore appliquée : année 2019, puis 2021 à la dernière année du calendrier.
CALENDRIERS = {
    "A5": [1, .8, .6, .4, .2, 0],
    "B10": [1] * 6 + [.8, .6, .4, .2, 0],
    "B13": [1] * 6 + [.875, .75, .625, .5, .375, .25, .125, 0],
}


def _nombre(cellule):
    return float(cellule.replace(",", "."))


def lire(chemin):
    """{code SH10 : (nombres de la ligne, gelée)} d'un PDF de liste."""
    lignes = {}
    for page in pymupdf.open(chemin):
        for table in page.find_tables().tables:
            for r in table.extract():
                r = [" ".join((c or "").split()) for c in r]
                code = next((c for c in r[:3] if CODE.fullmatch(c)), None)
                if code is None:
                    continue
                nombres = [_nombre(c) for c in r[r.index(code) + 1:] if re.fullmatch(r"\d+(?:,\d+)?", c)]
                gelee = bool(re.search(r"droit\s+commun", " ".join(r), re.I))
                lignes[code.replace(".", "")] = (nombres, gelee)
    return lignes


def controler(a, b10, b13, c):
    from_dep = lambda nom: json.load(open(os.path.join(DATA, nom), encoding="utf-8"))  # noqa: E731
    assert len(a) == OFFICIEL["A"], len(a)
    assert len(b10) == len(b13) == OFFICIEL["B"], (len(b10), len(b13))
    assert len(c) == OFFICIEL["C"], len(c)
    assert len(set(a) | set(b13) | set(c)) == OFFICIEL["total"], "A, B et C doivent former les 17 322 lignes"
    assert not (set(a) & set(b13)) and not (set(a) & set(c)) and not (set(b13) & set(c)), "recouvrement entre listes"
    # Les listes B et C du dépôt sont celles des PDF.
    assert set(b10) == set(b13) == set(from_dep("list_b_codes.json")), "liste B du dépôt ≠ PDF"
    assert set(c) == set(from_dep("list_c_codes.json")), "liste C du dépôt ≠ PDF"
    base_b = {k: float(v) for k, v in from_dep("list_b_base_rates.json").items()}
    for nom, liste, cal, duree in (("A5", a, CALENDRIERS["A5"], 5), ("B10", b10, CALENDRIERS["B10"], 10), ("B13", b13, CALENDRIERS["B13"], 13)):
        for code, (nombres, _) in liste.items():
            # La ligne porte la durée du calendrier, le taux de base de 2019, puis un taux par année.
            assert nombres[0] == duree, (nom, code, nombres)
            serie = nombres[1:]
            assert len(serie) == len(cal), (nom, code, nombres)
            assert all(abs(x - serie[0] * f) < 1e-6 for x, f in zip(serie, cal)), (nom, code, serie)
            if nom != "A5":
                assert abs(serie[0] - base_b[code]) < 1e-9, (nom, code, "taux de base ≠ dépôt")
    geles_a = {code for code, (_, g) in a.items() if g}
    geles_b = {code for code, (_, g) in b13.items() if g}
    assert len(geles_a) == OFFICIEL["A_gelees"] and len(geles_b) == OFFICIEL["B_gelees"], (len(geles_a), len(geles_b))
    assert geles_b == {code for code, (_, g) in b10.items() if g}, "lignes gelées de la liste B différentes entre les deux PDF"
    return geles_a, geles_b


def ecrire(a, geles_a, geles_b):
    par_taux = collections.defaultdict(list)
    for code, (nombres, _) in a.items():
        base = nombres[1]
        par_taux[str(int(base)) if base == int(base) else str(base)].append(code)
    sortie = {
        "source": "Listes (A) et (B) officielles de la Douane algérienne (annexes de la circulaire 482/DGD/SP/D.042/24), "
                  "tableaux lus par scripts/extraire_listes_zlecaf_dza.py ; empreintes des PDF dans "
                  "DZA_listes_a_b_c_verification_2026-11-20.json",
        "lignes": sum(len(v) for v in par_taux.values()),
        "par_taux_de_base_2019_pct": {k: sorted(v) for k, v in sorted(par_taux.items(), key=lambda kv: float(kv[0]))},
    }
    with open(os.path.join(DATA, "list_a_base_rates.json"), "w", encoding="utf-8") as f:
        json.dump(sortie, f, ensure_ascii=False, separators=(",", ":"))
        f.write("\n")
    gel = {
        "source": "Colonne « Observations » (« régime droit commun (règle d'origine non déterminée) ») des listes (A) et (B) "
                  "officielles ; les deux listes (B) à 10 et 13 ans portent les mêmes 322 lignes",
        "liste_a": sorted(geles_a),
        "liste_b": sorted(geles_b),
    }
    with open(os.path.join(DATA, "frozen_codes.json"), "w", encoding="utf-8") as f:
        json.dump(gel, f, ensure_ascii=False, separators=(",", ":"))
        f.write("\n")


if __name__ == "__main__":
    chemin_a, chemin_b10, chemin_b13, chemin_c = sys.argv[1:5]
    a, b10, b13, c = lire(chemin_a), lire(chemin_b10), lire(chemin_b13), lire(chemin_c)
    geles_a, geles_b = controler(a, b10, b13, c)
    ecrire(a, geles_a, geles_b)
    print(f"liste A {len(a)} lignes ({len(geles_a)} gelées), liste B {len(b13)} ({len(geles_b)} gelées), liste C {len(c)} ; "
          f"A+B+C = {len(set(a) | set(b13) | set(c))}")
