"""Lit la liste SARS des marchandises prohibées ou réglementées (« Prohibited
and Restricted Imports and Exports list », classeur Excel, feuilles « Imports »
et « Exports ») et en tire, par ligne tarifaire, la mesure publiée : colonnes
« Prohibited or Restricted », « Authority », « Action Required (detain for) »
et « Documentary Requirements », verbatim.

Une ligne est retenue quand elle porte un code tarifaire et au moins une de ces
colonnes. Le code peut être une position (« 04.02 »), un groupe à un tiret
(« 0103.9 »), une sous-position (« 0101.21 ») ou une ligne nationale
(« 0106.33.10 ») : la mesure vaut pour tout ce qu'il couvre. Excel a saisi
quelques positions comme des nombres (« 2942 ») et perdu le
zéro de tête de quelques codes numériques (« 208.3 » pour 0208.3) : il est
rendu. Les mentions qui disent l'absence de contrôle (« Not CITES Listed ») ne
sont pas des mesures. Les notes de chapitre, sans code, ne sont rattachées à
aucune ligne : elles sont comptées, pas servies.

    python3 scripts/extraire_liste_sars_zaf.py <liste.xlsx> <sortie.json>
"""
import hashlib
import json
import re
import sys

import openpyxl

CODE = re.compile(r"^(\d{1,4})\.(\d{1,2})(?:\.(\d{1,2}))?$")
COLONNES = ("restriction", "autorite", "action", "documents")
SANS_CONTROLE = {"Not CITES Listed"}


def _texte(cellule):
    texte = " ".join(str(cellule).split()) if cellule is not None else ""
    return texte or None


def _chiffres(code):
    if re.fullmatch(r"\d{4}", code):  # position saisie comme un nombre (« 2942 »)
        return code
    m = CODE.match(code)
    if not m:
        return None
    tete, milieu, fin = m.groups()
    # Une position s'écrit « 04.02 » ; un code à 3 chiffres de tête a perdu son zéro.
    if len(tete) <= 2 and fin is None and len(milieu) == 2:
        return tete.zfill(2) + milieu
    return tete.zfill(4) + milieu + (fin or "")


def lire(chemin):
    classeur = openpyxl.load_workbook(chemin, read_only=True, data_only=True)
    sortie = {"lignes": [], "notes_sans_code": {}}
    for feuille, sens in (("Imports", "import"), ("Exports", "export")):
        notes = 0
        for ligne in classeur[feuille].iter_rows(values_only=True):
            code = _texte(ligne[0])
            mesure = dict(zip(COLONNES, (_texte(c) for c in ligne[3:7])))
            if not any(mesure.values()):
                continue
            chiffres = _chiffres(code) if code else None
            if chiffres is None:
                notes += 1
                continue
            if not (mesure["autorite"] or mesure["action"] or mesure["documents"]) and (
                mesure["restriction"] in SANS_CONTROLE
            ):
                continue
            sortie["lignes"].append(
                {"sens": sens, "code_sars": code, "chiffres": chiffres, "designation": _texte(ligne[2]), **mesure}
            )
        sortie["notes_sans_code"][sens] = notes
    return sortie


def main():
    chemin, cible = sys.argv[1], sys.argv[2]
    with open(chemin, "rb") as f:
        empreinte = hashlib.sha256(f.read()).hexdigest()
    donnees = {
        "_objet": "Liste SARS des marchandises prohibées ou réglementées, mesures par ligne tarifaire "
                  "(scripts/extraire_liste_sars_zaf.py). Fiche ZAF_liste_sars_2026-10-26.json.",
        "source": "SARS — Prohibited and Restricted Imports and Exports list, 23 October 2026",
        "url": "https://www.sars.gov.za/wp-content/uploads/Docs/ProhibitedGoods/"
               "23-October-2026-Prohibited-and-Restricted-Imports-and-Exports-list.xlsx",
        "sha256": empreinte,
        **lire(chemin),
    }
    with open(cible, "w", encoding="utf-8") as f:
        json.dump(donnees, f, ensure_ascii=False, indent=1)
        f.write("\n")
    for sens in ("import", "export"):
        n = sum(1 for x in donnees["lignes"] if x["sens"] == sens)
        print(f"{sens} : {n} lignes ; notes sans code : {donnees['notes_sans_code'][sens]}")


if __name__ == "__main__":
    main()
