"""Lit les prélèvements du tarif sud-africain (SACU) dus à l'importation :
Schedule 1 Part 3A (sacs plastiques), 3C (lampes à filament), 3D (CO2 des
véhicules), 3E (pneus), 5A (taxe sur les carburants), 5B (Road Accident Fund)
et 7A (Health Promotion Levy, boissons sucrées).

Chaque article s'écrit sur des lignes successives : numéro d'article à trois
niveaux (« 147.01.01 »), sous-position, libellé, taux. Le taux occupe la ou
les dernières lignes de l'article (« R146.00
per g/km CO2 emissions exceeding 95g/km », « 2,21c/gram of the sugar content
that exceeds 4g/100ml »). La Part 3F (émissions de carbone produites dans la
République) ne porte pas sur des marchandises importées : elle n'est pas lue.

    python3 scripts/extraire_prelevements_zaf.py <dossier ZAF/legislation> <sortie.json>
"""
import hashlib
import json
import os
import re
import sys

import pymupdf

PARTIES = {
    "3A": "ZAF_Sch1_Part3A_2024-04-01.pdf",
    "3C": "ZAF_Sch1_Part3C_2024-04-01.pdf",
    "3D": "ZAF_Sch1_Part3D_2024-04-01.pdf",
    "3E": "ZAF_Sch1_Part3E_2022-06-17.pdf",
    "5A": "ZAF_Sch1_Part5A_2026-07-01.pdf",
    "5B": "ZAF_Sch1_Part5B_2026-04-01.pdf",
    "7A": "ZAF_Sch1_Part7A_2022-10-01.pdf",
}
ARTICLE = re.compile(r"^\d{3}\.\d{2}\.\d{2}$")
SOUS_POSITION = re.compile(r"^\d{4}(?:\.\d{1,2}){0,2}$")
TAUX = re.compile(
    r"^(?:(?P<free>free)$"
    r"|(?P<c>\d[\d ]*(?:,\d+)?)c/(?P<uc>li|bag)$"
    r"|R\s?(?P<r>\d[\d ]*(?:\.\d+)?)\s?/(?P<ur>kg net|lamp)$"
    r"|R\s?(?P<co2>\d[\d ]*(?:\.\d+)?)\s?per g/km CO2 emissions exceeding (?P<seuil_co2>\d+)\s?g/km$"
    r"|(?P<sucre>\d+(?:,\d+)?)c/gram of the sugar content that exceeds (?P<seuil_sucre>\d+)g/100ml$)"
)
UNITES = {"li": "li", "bag": "bag", "kg net": "kg", "lamp": "lamp"}


def nombre(texte):
    return float(texte.replace(" ", "").replace(",", "."))


def taux(texte):
    """Le taux qu'un texte énonce en entier, ou ``None``."""
    m = TAUX.match(" ".join(texte.split()))
    if not m:
        return None
    if m["free"]:
        return {"taux": 0.0, "brut": "free"}
    if m["c"]:
        return {"montant": round(nombre(m["c"]) / 100, 6), "unite": UNITES[m["uc"]], "brut": m.group(0)}
    if m["r"]:
        return {"montant": nombre(m["r"]), "unite": UNITES[m["ur"]], "brut": m.group(0)}
    if m["co2"]:
        return {"par_g_km_co2": nombre(m["co2"]), "seuil_g_km": int(m["seuil_co2"]), "brut": m.group(0)}
    return {"par_gramme_de_sucre": round(nombre(m["sucre"]) / 100, 6), "seuil_g_100ml": int(m["seuil_sucre"]),
            "brut": m.group(0)}


def lire(chemin, partie):
    lignes = [l.strip() for page in pymupdf.open(chemin) for l in page.get_text().split("\n") if l.strip()]
    sortie = []
    for k, ligne in enumerate(lignes):
        if not (ARTICLE.match(ligne) and k + 1 < len(lignes) and SOUS_POSITION.match(lignes[k + 1])):
            continue
        texte = []
        for suite in lignes[k + 2:]:
            if ARTICLE.match(suite) or re.match(r"^\d{3}\.\d{2}$", suite) or suite.startswith("Date:"):
                break
            texte.append(suite)
        # Le taux occupe la ou les dernières lignes de l'article (« 2,21c/gram of
        # the sugar content » / « that exceeds 4g/100ml ») : le lire sur le texte
        # entier lui rattacherait les chiffres du libellé (« Chapter 27 225c/li »).
        lu, n = next(((taux(" ".join(texte[-n:])), n) for n in (1, 2, 3)
                      if len(texte) >= n and taux(" ".join(texte[-n:]))), (None, 0))
        if lu is None:
            continue
        libelle = " ".join(texte[:-n])
        sortie.append({"partie": partie, "article": ligne, "sous_position": lignes[k + 1], "libelle": libelle, **lu})
    return sortie


def date_du_document(chemin):
    m = re.search(r"Date:\s*(\d{4}-\d{2}-\d{2})", " ".join(p.get_text() for p in pymupdf.open(chemin)))
    return m.group(1) if m else None


def main(dossier, sortie):
    articles, documents = [], []
    for partie, nom in PARTIES.items():
        chemin = os.path.join(dossier, nom)
        articles += lire(chemin, partie)
        documents.append({"partie": partie, "fichier": nom, "date": date_du_document(chemin),
                          "sha256": hashlib.sha256(open(chemin, "rb").read()).hexdigest()})
    json.dump({"source": "SARS, Customs and Excise Act 1964, Schedule No. 1 Parts 3, 5 et 7",
               "documents": documents, "articles": articles},
              open(sortie, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    for partie in PARTIES:
        print(partie, sum(a["partie"] == partie for a in articles), "articles")


if __name__ == "__main__":
    main(*sys.argv[1:3])
