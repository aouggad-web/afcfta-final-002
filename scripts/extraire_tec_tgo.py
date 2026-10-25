"""Lit le tarif douanier officiel du Togo (OTR, « TEC CEDEAO actualisé au
10/11/2025 », PDF de 478 pages tiré de Word) et en tire, par position, le
libellé, le droit de douane (D.D.) et la redevance statistique (R.S.).

Le texte du PDF suit l'ordre des cellules : code, libellé, unité, D.D., R.S.
Dans le segment qui va d'un code au suivant, D.D. et R.S. sont la première paire
« taux du TEC (0, 5, 10, 20, 35) suivi de 0 ou 1 » précédée d'un mot non
numérique (l'unité). Deux coquilles du tarif sont tolérées : unité imprimée
« 1 » (2202.91, bière sans alcool) et R.S. imprimée « l » (9405.91 à 9405.99).
Une position sans valeur imprimée (0304.82) reste sans taux.

    python3 scripts/extraire_tec_tgo.py <tarif.pdf> <sortie.json>
"""
import json
import re
import sys

import pymupdf

CODE = re.compile(r"^(\d{4}\.\d{2}\.\d{2}\.\d{2})\b")
NUM = re.compile(r"^\d+(?:,\d+)?$")
DD = {"0", "5", "10", "20", "35"}
RS = {"0", "1"}

lignes = []
for page in pymupdf.open(sys.argv[1]):
    lignes += [ligne.strip() for ligne in page.get_text().split("\n") if ligne.strip()]
debuts = [i for i, ligne in enumerate(lignes) if CODE.match(ligne)]
sortie = {}
for k, i in enumerate(debuts):
    segment = lignes[i:debuts[k + 1] if k + 1 < len(debuts) else len(lignes)]
    code = CODE.match(segment[0]).group(1).replace(".", "")
    mots = " ".join([segment[0][13:]] + segment[1:]).split()
    trouve = None
    for j in range(1, len(mots) - 1):
        if mots[j] in DD and mots[j + 1] in RS and not NUM.match(mots[j - 1]):
            trouve = j
            break
    if trouve is None:
        for j in range(1, len(mots) - 1):
            if mots[j] in DD and mots[j + 1] in RS | {"l"}:
                trouve = j
                break
    if trouve is None:
        sortie[code] = {"_libelle": " ".join(mots).lstrip("- ")}
        continue
    sortie[code] = {
        "_libelle": " ".join(mots[:trouve - 1]).lstrip("- "),
        "DD": float(mots[trouve]),
        "RS": 1.0 if mots[trouve + 1] == "l" else float(mots[trouve + 1]),
    }
json.dump(sortie, open(sys.argv[2], "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print(len(sortie), "positions,", sum(1 for v in sortie.values() if "DD" not in v), "sans valeurs")
