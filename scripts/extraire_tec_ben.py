"""Lit le tarif douanier officiel du Bénin (DGDDI, « TARIF EXTERIEUR COMMUN
TEC-CEDEAO SH2022 », export Excel en PDF de 392 pages) et en tire, par
position, le libellé, le droit de douane (D.D.) et la redevance statistique
(R.S.).

L'en-tête n'est imprimé qu'en page 1 ; ses abscisses (U.S., D.D., R.S.) valent
pour tout le document. Une valeur est rattachée à la colonne dont l'en-tête est
le plus proche (à 10 points près, sinon signalée « _ambigu ») et à la cellule de
la position : de la ligne du code, moins 5 points, au code suivant.

    python3 scripts/extraire_tec_ben.py <tarif.pdf> <sortie.json>
"""
import json
import re
import sys

import pymupdf

CODE = re.compile(r"^\d{4}\.\d{2}\.\d{2}\.\d{2}$")
NUM = re.compile(r"^\d+(?:[.,]\d+)?$")

doc = pymupdf.open(sys.argv[1])
hdr = {w[4]: (w[0] + w[2]) / 2 for w in doc[0].get_text("words") if w[4] in ("U.S.", "D.D.", "R.S.")}
cols = {"DD": hdr["D.D."], "RS": hdr["R.S."]}
us = hdr["U.S."] - 12
sortie = {}
for page in doc:
    mots = page.get_text("words")
    lignes = sorted((w[1], w[4], w[2]) for w in mots if w[0] < 150 and CODE.match(w[4]))
    for i, (y, code, x_code) in enumerate(lignes):
        y2 = lignes[i + 1][0] if i + 1 < len(lignes) else 10_000
        lib = sorted((w for w in mots if y - 2 <= w[1] < y2 - 2 and x_code < w[0] and w[2] < us), key=lambda w: (round(w[1]), w[0]))
        garde, vues = [], []
        for w in lib:
            if round(w[1]) not in vues:
                # Une ligne suivante ouverte par un tiret est l'intitulé d'un autre article.
                if vues and w[4].startswith("-"):
                    break
                vues.append(round(w[1]))
            garde.append(w)
        vals = {"_libelle": " ".join(w[4] for w in garde)}
        for w in mots:
            # Le D.D. est centré dans la cellule (plusieurs lignes de libellé),
            # quelques points au-dessus du code sur une ligne simple : il
            # appartient à la cellule qui va du code (moins 5 points) au suivant.
            if w[0] < us or not NUM.match(w[4]) or not (y - 5 <= w[1] < y2 - 5):
                continue
            xc = (w[0] + w[2]) / 2
            col = min(cols, key=lambda c: abs(cols[c] - xc))
            if abs(cols[col] - xc) > 10:
                vals.setdefault("_ambigu", []).append((w[4], round(xc)))
                continue
            vals[col] = float(w[4].replace(",", "."))
        sortie[code.replace(".", "")] = vals
json.dump(sortie, open(sys.argv[2], "w"), indent=0)
print(len(sortie))
