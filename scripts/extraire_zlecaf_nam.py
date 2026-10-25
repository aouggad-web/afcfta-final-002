"""Colonne AfCFTA du tarif namibien (Part 1 du Schedule No. 1), pour
data/nam/zlecaf_gn391_2024.json.

Source : Government Notice No. 391 of 2024 (Government Gazette No. 8543 du
20/12/2024), qui substitue la Part 1 entière, six colonnes de droits (General,
EU/UK, EFTA, SADC, MERCOSUR, AfCFTA), puis Government Notice No. 174 of 2026
(Gazette No. 8936 du 04/06/2026), seul amendement de la Part 1 publié depuis.

Les pages du GN 391 sont en paysage : une ligne du tableau est une abscisse,
une colonne une plage d'ordonnées. Les colonnes sont bornées par les centres
des en-têtes de la page ; une ligne commence à l'abscisse de son code et va
jusqu'au code suivant, ce qui rattache à leur code les cellules sur deux
lignes (« 30% or » / « 130c/kg »). Les en-têtes de position et de
sous-position ouvrent aussi une ligne : leur libellé court sur toute la
largeur et ne doit pas tomber dans les colonnes de la ligne précédente. Le pied
de page (« Government Gazette 20 December 2024 8543 ») est écarté par son
ordonnée. Seules les lignes terminales (sans subdivision) sont gardées, et
parmi elles celles qui portent le taux General : 4414.00 et 9401.91.20 sont
imprimées sans lui, à côté des lignes qui les remplacent (4414.10 et 4414.90,
9401.91.21 et 9401.91.29).

    python3 scripts/extraire_zlecaf_nam.py
"""
import collections
import json
import os
import re

import pymupdf

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PDF = os.path.join(REPO, "data", "sources", "NAM", "legislation", "NAM_TarifSch1Part1_GN391-2024_2024-12-20.pdf")
SORTIE = os.path.join(REPO, "data", "nam", "zlecaf_gn391_2024.json")

COLONNES = ["General", "EU", "EFTA", "SADC", "MERCOSUR", "AfCFTA"]
#: Début de ligne : position (« 03.04 »), sous-position (« 0303.9 »,
#: « 0303.99 »), groupe (« 3824.99.3 ») ou ligne nationale (« 0303.99.10 »).
DEBUT = re.compile(r"^\d{2}\.\d{2}$|^\d{4}\.\d{1,2}(\.\d{1,2})?$")
#: Les taux d'une ligne commencent jusqu'à 1,1 point avant son code.
TOLERANCE = 2
#: En dessous de cette ordonnée : pied de page, en marge du tableau.
PIED = 45
#: Au-dessus de cette ordonnée : colonne des codes.
COLONNE_CODES = 700

#: GN 174/2026, items 1 à 5 (en vigueur à la publication, 04/06/2026).
SUPPRIMES_174 = ("03073920", "03073930", "03073940")
REMPLACES_174 = {
    **{c: ("25%", "10%") for c in ("03073220", "03073230", "03073240")},
    **{c: ("436,38c/kg", "436,38c/kg") for c in ("170112", "170113", "170114", "170191", "170199")},
    **{c: ("61,9c/kg", "61,9c/kg") for c in ("100191", "100199")},
    **{c: ("92,85c/kg", "92,85c/kg") for c in ("11010010", "11010020", "11010030", "11010090")},
}


def _cellule(mots):
    """Mots d'une cellule dans l'ordre de lecture : ligne par ligne, puis de
    haut en bas de la page tournée."""
    texte = " ".join(m[4] for m in sorted(mots, key=lambda m: (round(m[0]), -m[3])))
    return re.sub(r"(\d) (\d{3}c/)", r"\1\2", texte)  # « 1 500c/kg »


def lire_gn391(chemin=PDF):
    doc = pymupdf.open(chemin)
    positions = {}
    for pno in range(doc.page_count):
        mots = [m for m in doc[pno].get_text("words") if m[1] > PIED]
        entete = {}
        for m in mots:
            if m[4] in COLONNES and m[4] not in entete:
                entete[m[4]] = (m[1] + m[3]) / 2
        if len(entete) < len(COLONNES):
            continue
        centres = [entete[c] for c in COLONNES]
        bornes = [(a + b) / 2 for a, b in zip(centres, centres[1:])]
        haut = centres[0] + (centres[0] - centres[1]) / 2
        bas = centres[-1] - (centres[-2] - centres[-1]) / 2
        x_entete = max(m[0] for m in mots if m[4] == "AfCFTA")
        codes = sorted(
            (m[0], m[4].replace(".", "")) for m in mots if DEBUT.match(m[4]) and m[1] > COLONNE_CODES and m[0] > x_entete
        )
        cellules = collections.defaultdict(lambda: collections.defaultdict(list))
        for m in mots:
            milieu = (m[1] + m[3]) / 2
            if m[0] <= x_entete or not bas < milieu < haut:
                continue
            rang = [x for x, _ in codes if x <= m[0] + TOLERANCE]
            if not rang:
                continue
            code = codes[len(rang) - 1][1]
            cellules[code][COLONNES[sum(1 for b in bornes if milieu < b)]].append(m)
        for code, cols in cellules.items():
            if len(code) < 6:
                continue
            if code in positions:
                raise ValueError(f"{code} lu deux fois (p. {positions[code]['page']} et {pno + 1})")
            positions[code] = {c: _cellule(cols.get(c, [])) for c in COLONNES} | {"page": pno + 1}
    return positions


def colonne_afcfta():
    sortie = {
        code: {"general": p["General"], "afcfta": p["AfCFTA"], "source": f"GN 391/2024, p. {p['page']}"}
        for code, p in lire_gn391().items()
        if code not in SUPPRIMES_174 and p["General"]
    }
    for code, (general, afcfta) in REMPLACES_174.items():
        sortie[code] = {"general": general, "afcfta": afcfta, "source": "GN 174/2026"}
    # Lignes terminales seulement : 0307.32 est subdivisée par le GN 174/2026.
    return {code: v for code, v in sorted(sortie.items()) if not any(c != code and c.startswith(code) for c in sortie)}


if __name__ == "__main__":
    resultat = colonne_afcfta()
    with open(SORTIE, "w", encoding="utf-8") as f:
        json.dump(resultat, f, ensure_ascii=False, indent=1)
    print(len(resultat), "positions")
