"""Lit les droits d'accise du tarif sud-africain (SACU) : Schedule 1 Part 2A
(accises spécifiques) et Part 2B (accises ad valorem), publiés par SARS, et en
tire, par sous-position, le taux tel que le tableau l'imprime.

Chaque article du tableau s'écrit, dans le texte du PDF, sur des lignes
successives : numéro d'article (« 104.10.20 »), sous-position (« 2203.00.90 »),
libellé, taux (« R149.98/li aa », « 34,7c/kg », « 9% », « (See Note 2 to this
Part) »). Les lignes d'intertitre portent un numéro d'article à deux niveaux
(« 104.15 ») et pas de taux.

Unités lues (Part 2A) : c/kg, R/kg, R/kg net, c/li, R/li, R/li aa (litre
d'alcool absolu), R/10cigarettes, R/<n>sticks, R/ml. Le montant est rendu en
rands (« 34,7c/kg » vaut 0,347).

    python3 scripts/extraire_accises_zaf.py <Part2A.pdf> <Part2B.pdf> <sortie.json>
"""
import hashlib
import json
import re
import sys

import pymupdf

ARTICLE = re.compile(r"^\d{3}\.\d{2}\.\d{2}$")
SOUS_POSITION = re.compile(r"^\d{4}(?:\.\d{1,2}){0,2}$")
TAUX = re.compile(
    r"^(?:free|(?P<pct>\d+(?:,\d+)?)%|(?P<note>\(See Note \d+ to this Part\))"
    r"|(?P<c>\d[\d ]*(?:,\d+)?)c/(?P<uc>kg|li)"
    r"|R\s?(?P<r>\d[\d ]*(?:\.\d+)?)/(?P<ur>li aa|li|kg net|kg|\d+\s?cigarettes|\d+\s?sticks|ml))$"
)
UNITES = {"kg net": "kg", "kg": "kg", "li": "li", "li aa": "li aa", "ml": "ml"}


def nombre(texte):
    return float(texte.replace(" ", "").replace(",", "."))


def taux(texte):
    m = TAUX.match(texte)
    if not m:
        return None
    if texte == "free":
        return {"taux": 0.0}
    if m["pct"]:
        return {"taux": nombre(m["pct"])}
    if m["note"]:
        return {"renvoi": m["note"]}
    if m["c"]:
        return {"montant": round(nombre(m["c"]) / 100, 6), "unite": m["uc"]}
    unite = re.sub(r"\s+", "", m["ur"]) if m["ur"][0].isdigit() else UNITES[m["ur"]]
    return {"montant": nombre(m["r"]), "unite": unite}


def lire(chemin, partie):
    lignes = [l.strip() for page in pymupdf.open(chemin) for l in page.get_text().split("\n") if l.strip()]
    sortie, k = [], 0
    while k < len(lignes):
        if ARTICLE.match(lignes[k]) and k + 1 < len(lignes) and SOUS_POSITION.match(lignes[k + 1]):
            article, sous_position, libelle = lignes[k], lignes[k + 1], []
            j = k + 2
            while j < len(lignes) and taux(lignes[j]) is None and not ARTICLE.match(lignes[j]):
                libelle.append(lignes[j])
                j += 1
            if j < len(lignes) and taux(lignes[j]) is not None:
                sortie.append({"partie": partie, "article": article, "sous_position": sous_position,
                               "libelle": " ".join(libelle), "brut": lignes[j], **taux(lignes[j])})
                k = j + 1
                continue
        k += 1
    return sortie


def date_du_document(chemin):
    m = re.search(r"Date:\s*(\d{4}-\d{2}-\d{2})", pymupdf.open(chemin)[0].get_text())
    return m.group(1) if m else None


def main(p2a, p2b, sortie):
    articles = lire(p2a, "2A") + lire(p2b, "2B")
    codes = [a["sous_position"] for a in articles]
    assert len(codes) == len(set(codes)), "sous-position lue deux fois"
    json.dump({
        "source": "SARS, Customs and Excise Act 1964, Schedule No. 1 Part 2A et Part 2B",
        "documents": [{"partie": partie, "date": date_du_document(chemin),
                       "sha256": hashlib.sha256(open(chemin, "rb").read()).hexdigest()}
                      for partie, chemin in (("2A", p2a), ("2B", p2b))],
        "articles": articles,
    }, open(sortie, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(len([a for a in articles if a["partie"] == "2A"]), "articles 2A ;",
          len([a for a in articles if a["partie"] == "2B"]), "articles 2B")


if __name__ == "__main__":
    main(*sys.argv[1:4])
