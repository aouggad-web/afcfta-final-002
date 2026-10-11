"""Lit le Tarif extérieur commun de la CEDEAO tel que publié pour le Mali (SH
2022, PDF de 448 pages, décembre 2023) et en tire, par position, le taux de
chaque colonne : DD, RS, PC, PCS, ISCP, TVA, TAI, TCI, TCP, AUTRES, ainsi
que le libellé (texte entre le code et la colonne US).

Les valeurs sont rattachées à leur colonne par leur position horizontale
(centre du mot au plus près du centre de l'en-tête de la page, à 9 points
près, sinon signalées « _ambigu ») et à leur position tarifaire par la ligne
qui porte le code, jusqu'au code suivant.

    python3 scripts/extraire_tec_mli.py <tarif.pdf> <sortie.json>
"""
import json
import re
import sys

import pymupdf

COLS = ["DD", "RS", "PC", "PCS", "ISCP", "TVA", "TAI", "TCI", "TCP", "AUTRES"]
CODE = re.compile(r"^\d{4}\.\d{2}\.\d{2}\.\d{2}$")
NUM = re.compile(r"^\d+(?:[.,]\d+)?$")

doc = pymupdf.open(sys.argv[1])
sortie = {}
for page in doc:
    mots = page.get_text("words")
    hdr = {}
    for w in mots:
        if w[4] in COLS + ["US"] and w[4] not in hdr:
            hdr[w[4]] = ((w[0] + w[2]) / 2, w[1])
    if len(hdr) < len(COLS) + 1:
        continue
    gauche = min(hdr[c][0] for c in COLS) - 12
    us = hdr["US"][0] - 8
    haut = max(y for _, y in hdr.values())
    # Pied de page (« Page 62 | 448 ») : hors de la dernière ligne.
    bas = min([w[1] for w in mots if w[4] == "Page" and w[1] > haut] or [10_000])
    # Le code ouvre la ligne, en marge gauche ; cité dans un libellé, il ne compte pas.
    lignes = sorted((w[1], w[4], w[2]) for w in mots if w[1] > haut and w[0] < 150 and CODE.match(w[4]))
    for i, (y, code, x_code) in enumerate(lignes):
        y2 = lignes[i + 1][0] if i + 1 < len(lignes) else bas
        vals = {}
        lib = sorted(
            (w for w in mots if y - 2 <= w[1] < y2 - 2 and x_code < w[0] and w[2] < us and w[0] < us - 14),
            key=lambda w: (round(w[1]), w[0]),
        )
        # Une ligne suivante qui s'ouvre par un tiret est l'intitulé d'un autre
        # article (« - Anes : »), pas la suite du libellé.
        garde, lignes_vues = [], []
        for w in lib:
            if round(w[1]) not in lignes_vues:
                if lignes_vues and w[4].startswith("-"):
                    break
                lignes_vues.append(round(w[1]))
            garde.append(w)
        vals["_libelle"] = " ".join(w[4] for w in garde)
        for w in mots:
            if y - 2 <= w[1] < y2 - 2 and w[0] >= gauche and NUM.match(w[4]):
                xc = (w[0] + w[2]) / 2
                col = min(COLS, key=lambda c: abs(hdr[c][0] - xc))
                if abs(hdr[col][0] - xc) > 9:
                    vals.setdefault("_ambigu", []).append((w[4], round(xc)))
                    continue
                vals[col] = float(w[4].replace(",", "."))
        sortie[code.replace(".", "")] = vals
json.dump(sortie, open(sys.argv[2], "w"), indent=0)
print(len(sortie))
