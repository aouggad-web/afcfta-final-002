"""Lit le Tarif extérieur commun de la CEDEAO tel que publié par la DGD de Guinée
(SH 2022, PDF de 414 pages, janvier 2022) et en tire, par position, le libellé
et le taux de chaque colonne : DD, RTL, AC (accises), TVA, PC, CA (centime
additionnel) à l'entrée, DFE à la sortie. « ex » (exonéré) est lu comme 0.

Les valeurs sont rattachées à leur colonne par leur position horizontale
(centre du mot au plus près du centre de l'en-tête de la page, ou de la
dernière page qui en porte un, à 12 points près, 16 pour la colonne DFE, sinon
signalées « _ambigu ») et à la cellule de leur position, qui court
jusqu'au code suivant (40 points au plus après le dernier code d'une page).

    python3 scripts/extraire_tec_gin.py <tarif.pdf> <sortie.json>
"""
import json
import re
import sys

import pymupdf

COLS = ["DD", "RTL", "AC", "TVA", "PC", "CA", "DFE"]
CODE = re.compile(r"^\d{4}\.\d{2}\.\d{2}\.\d{2}$")
VAL = re.compile(r"^(\d+(?:[.,]\d+)?)%?$|^ex$")

doc = pymupdf.open(sys.argv[1])
sortie = {}
dernier = None
for page in doc:
    mots = page.get_text("words")
    # L'en-tête est au-dessus du premier code : un « PC » ou un « TVA » du
    # texte des notes n'en fait pas partie.
    premier = min([w[1] for w in mots if w[0] < 100 and CODE.match(w[4])] or [10_000])
    hdr = {}
    for w in mots:
        if w[4] in COLS + ["Us"] and w[4] not in hdr and w[1] < premier:
            hdr[w[4]] = ((w[0] + w[2]) / 2, w[1])
    if len(hdr) == len(COLS) + 1:
        dernier = hdr
        haut = max(y for _, y in hdr.values())
    elif dernier:
        # Page sans en-tête : les colonnes gardent les abscisses de la précédente.
        hdr, haut = dernier, 0
    else:
        continue
    gauche = hdr["Us"][0] + 8
    lignes = sorted((w[1], w[4], w[2]) for w in mots if w[1] > haut and w[0] < 100 and CODE.match(w[4]))
    for i, (y, code, x_code) in enumerate(lignes):
        y2 = lignes[i + 1][0] if i + 1 < len(lignes) else 10_000
        bande = [w for w in mots if y - 3 <= w[1] < y2 - 3]
        lib = sorted((w for w in bande if x_code < w[0] < hdr["Us"][0] - 30), key=lambda w: (round(w[1]), w[0]))
        garde, vues = [], []
        for w in lib:
            if round(w[1]) not in vues:
                # Une ligne suivante ouverte par un tiret est l'intitulé d'un autre article.
                if vues and w[4].startswith("-"):
                    break
                vues.append(round(w[1]))
            garde.append(w)
        vals = {"_libelle": " ".join(w[4] for w in garde)}
        # Les taux sont centrés dans la cellule de la position, qui court
        # jusqu'au code suivant ; au plus 40 points sous le code, au-delà
        # desquels commencent, en fin de chapitre, les notes du suivant. Un code
        # centré dans une cellule de deux lignes a ses taux sur la première,
        # 4 points au-dessus de lui (1509.20.10.00) : la cellule commence 6
        # points avant le code. Un libellé de plus de quatre lignes porte ses
        # taux plus bas (0304.51.00.00) : faute de taux dans les 40 points, la
        # première ligne d'au moins cinq valeurs avant le code suivant.
        fin = y2 - 6 if i + 1 < len(lignes) else y + 37
        cand = [w for w in mots if w[0] >= gauche and VAL.match(w[4]) and y - 6 <= w[1] < fin]
        retenus = [w for w in cand if w[1] < y + 37]
        if not retenus:
            for y_ligne in sorted({round(w[1]) for w in cand}):
                ligne = [w for w in cand if abs(w[1] - y_ligne) <= 2]
                if len(ligne) >= 5:
                    retenus = ligne
                    break
        for w in retenus:
            m = VAL.match(w[4])
            xc = (w[0] + w[2]) / 2
            col = min(COLS, key=lambda c: abs(hdr[c][0] - xc))
            if abs(hdr[col][0] - xc) > (16 if col == "DFE" else 12):
                vals.setdefault("_ambigu", []).append((w[4], round(xc)))
                continue
            vals[col] = 0.0 if w[4] == "ex" else float(m.group(1).replace(",", "."))
        sortie[code.replace(".", "")] = vals
json.dump(sortie, open(sys.argv[2], "w"), indent=0)
print(len(sortie))
