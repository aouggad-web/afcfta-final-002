"""Lit le Legal Notice EAC/160/2026 (Gazette de la CAE, Vol. AT 1 No. 16 du
30/06/2026, data/sources/eac/official/EAC_Vol_AT_1_No_16_2026-06-30.pdf) et
en tire, par position SH et par pays, les droits que les États partenaires
appliquent pour l'exercice 2026/27 à la place du TEC.

Le tableau est lu sur la grille du PDF : les traits horizontaux, propres à
chaque colonne, délimitent les cellules. Une décision fusionnée sur plusieurs
lignes (sucre, « 63 à 66 ») vaut ainsi pour chacune d'elles, ce que le texte
extrait, qui enchaîne les cellules, ne permet pas de dire.

- Table I : décisions rédigées (« Tanzania to stay the application of the EAC
  CET rate of 10% and apply a duty rate of 25% for one year »). Une décision
  est appliquée quand rien ne la restreint entre le taux et « for one year » ;
  sinon (importateur, usage, sous-produit nommé) elle est conditionnelle.
- Table II : une décision par ligne (Ouganda).
- Tables III à VII : positions sous le taux de l'en-tête.
- Tables VIII et IX : équipements « imported by the manufacturers »,
  conditionnelles.
- Table X : amendements du TEC lui-même, valables pour tous les États.

Chaque mesure garde le texte de sa décision. Une décision que le lecteur ne
ramène pas à un pays et à un taux est rendue telle quelle, non appliquée.

    python3 scripts/extraire_mesures_tec_cae_2026.py <gazette.pdf> <sortie.json>
"""
import hashlib
import json
import re
import sys

import pymupdf

PAYS = {
    "Kenya": "KEN", "Uganda": "UGA", "Tanzania": "TZA", "Rwanda": "RWA", "Burundi": "BDI",
    "South Sudan": "SSD",
}
TOUS = sorted(PAYS.values())
#: Code de la colonne « HS CODE » : sous-position à huit chiffres, ou position
#: à quatre (« 20.07 », « 02.01 ») qui vaut pour toutes ses sous-positions.
CODE = re.compile(r"(?<![\d.])(\d{4}\.\d{2}\.\d{2}|\d{2}\.\d{2})(?![\d.])")
TAUX = re.compile(
    r"(?:(?P<pct>\d+(?:\.\d+)?)\s*%)?"
    r"(?:\s*or\s*(?:a\s+specific\s+duty\s+of\s+)?)?"
    r"(?:(?:US\s*\$|USD|\$)\s*(?P<montant>\d[\d,]*(?:\.\d+)?)\s*(?:/|per)\s*(?P<unite>[A-Za-z0-9²]+))?"
    r"(?P<regle>,?\s*whichever\s+is\s+higher)?",
    re.I,
)
UNITES = {"kg": "kg", "mt": "mt", "m3": "m3", "l": "l", "metre": "m", "meter": "m", "sqm": "m2", "m2": "m2", "m²": "m2",
          "liter": "l", "litre": "l", "pair": "paire", "piece": "u", "unit": "u"}


def lire_taux(texte):
    """Taux d'une décision : dict, ou None si illisible."""
    m = TAUX.search(texte)
    while m and not (m.group("pct") or m.group("montant")):
        m = TAUX.search(texte, m.end() + 1)
    if not m:
        return None
    taux = {"taux": float(m.group("pct")) if m.group("pct") else None}
    if m.group("montant"):
        unite = UNITES.get(m.group("unite").lower())
        if unite is None:
            return None
        taux["specifique"] = {"montant": float(m.group("montant").replace(",", "")), "unite_monetaire": "USD",
                              "unite_quantite": unite}
        if taux["taux"] is not None:
            if not m.group("regle"):
                return None
            taux["regle"] = "LE_PLUS_ELEVE"
    taux["expression"] = m.group(0).strip()
    return taux


def pays_de(texte):
    if re.search(r"Partner States", texte, re.I):
        return TOUS
    return [iso for nom, iso in PAYS.items() if re.search(rf"\b{nom}\b", texte, re.I)]


def sans_expression(taux):
    return {k: v for k, v in (taux or {}).items() if k != "expression"}


def rappel_retire(entre):
    """Retirer de « EAC CET … apply » le rappel du taux remplacé."""
    e = re.sub(r"^\s*(?:duty\s+)?rates?\b", "", entre, flags=re.I).strip()
    if re.match(r"of\s", e, re.I):
        e = e[2:].strip()
        t = TAUX.match(e)
        if t and t.group(0).strip():
            e = e[t.end():]
    e = re.sub(r"^(?:\s*(?:and|,)\s*\d+(?:\.\d+)?\s*%)*", "", e)
    e = re.sub(r"^\s*(?:and|,)?\s*(?:to)?\s*$", "", e, flags=re.I)
    return e.strip(" ,")


def decisions(texte):
    """Découper une décision en sous-décisions (a), (b)… ; chacune en mesure."""
    texte = texte.replace("\xad ", "").replace("\xad", "")  # césures conditionnelles du PDF
    morceaux = re.split(r"\(([a-h])\)\s", texte)
    if len(morceaux) == 1:
        morceaux = ["", "", texte]
    sortie = []
    for i in range(2, len(morceaux), 2):
        d = morceaux[i].strip().rstrip(";").removesuffix("; and").removesuffix(" and").strip(" ;")
        if re.match(r"Assigned the items? as [Ss]ensitive", d):
            continue  # classement en produit sensible : pas un taux
        m = re.search(r"^(?P<qui>.*?)\b(?:to\s+stay|a\s+stay)\b.*?apply\s+(?:(?:a|an|the)\s+)?(?:import\s+)?(?:duty\s+rate\s+of\s+)?"
                      r"(?P<reste>\d.*|US.*|\$.*)$", d, re.I | re.S)
        if not m:
            sortie.append({"decision": d, "lu": False})
            continue
        reste = m.group("reste")
        taux = lire_taux(reste)
        # Entre « EAC CET » et « apply » : le seul rappel du taux remplacé est
        # admis ; tout autre texte (« on Cane Sugar imported under a permit »,
        # « to investors approved by ») restreint la mesure.
        avant = re.search(r"\bEAC\s+CET\b(?P<entre>.*?)\bapply\b", d, re.I | re.S)
        entre = rappel_retire(avant.group("entre") if avant else "")
        exclusions = re.findall(r"\d{4}\.\d{2}\.\d{2}", " ".join(re.findall(r"except[^;]*", d, re.I)))
        fin = re.search(r"\bfor\s+one\s+year\b", reste, re.I)
        apres = reste[len(taux["expression"]) if taux else 0:fin.start() if fin else len(reste)]
        # « 25% instead of 100% or US$ 460 / MT whichever is higher » : rappel
        # du taux remplacé, pas une restriction.
        apres = re.sub(r"^\s*instead\s+of\s+.*$", "", apres).strip(" ;,.")
        pays = pays_de(m.group("qui"))
        restriction = " ; ".join(x for x in (entre.strip(" ,"), apres) if x) or None
        if restriction and exclusions and re.fullmatch(r"except\b.*", restriction, re.I | re.S):
            restriction = None  # « except HS Code 5205.23.00 » : exclusion lue, pas une condition
        sortie.append({"decision": d, "lu": taux is not None and bool(pays), "pays": pays,
                       "droit": sans_expression(taux), "restriction": restriction,
                       **({"exclusions": exclusions} if exclusions else {})})
    return sortie


def segments(page):
    traits = set()
    for dessin in page.get_drawings():
        for item in dessin["items"]:
            if item[0] == "l" and abs(item[1].y - item[2].y) < 1:
                traits.add((round(item[1].y), round(min(item[1].x, item[2].x)), round(max(item[1].x, item[2].x))))
            elif item[0] == "re" and item[1].height < 2:
                traits.add((round(item[1].y0), round(item[1].x0), round(item[1].x1)))
    return traits


def lignes_de_tableau(document, premiere, derniere):
    """(table, textes des colonnes) par ligne de tableau, sur les pages données."""
    lignes, table = [], None
    for numero in range(premiere, derniere):
        page = document[numero]
        mots = page.get_text("words")
        titres = []
        for m in mots:
            if m[4] == "TABLE" and m[0] < 200:
                suite = " ".join(w[4] for w in mots if abs(w[1] - m[1]) < 2 and w[0] >= m[0])
                t = re.match(r"TABLE ([IVX]+):", suite)
                if t:
                    titres.append((m[1], t.group(1)))
        titres.sort()
        bornes = [y for y, _ in titres] + [page.rect.height]
        traits = segments(page)
        regions = [(None, 0, bornes[0])] + [(t, y, bornes[i + 1]) for i, (y, t) in enumerate(titres)]
        for nom, haut, bas in regions:
            if nom:
                table = nom
            if table is None:
                continue
            dans = [t for t in traits if haut <= t[0] < bas]
            colonnes = sorted({(x0, x1) for _, x0, x1 in dans if x1 - x0 < 500})
            if len(colonnes) < 2:
                continue
            seps = {c: sorted({y for y, x0, x1 in dans if x0 <= c[0] + 2 and x1 >= c[1] - 2}) for c in colonnes}

            def cellule(c, y):
                ys = seps[c]
                for a, b in zip(ys, ys[1:]):
                    if a <= y < b:
                        return a, b
                return None

            def texte(c, cel):
                a, b = cel
                choisis = [m for m in mots if c[0] - 1 <= m[0] < c[1] - 1 and a <= (m[1] + m[3]) / 2 < b]
                return " ".join(m[4] for m in sorted(choisis, key=lambda m: (round(m[1]), m[0])))

            ys = seps[colonnes[0]]
            for a, b in zip(ys, ys[1:]):
                milieu = (a + b) / 2
                cellules = [texte(c, cellule(c, milieu)) if cellule(c, milieu) else "" for c in colonnes]
                if not any(cellules) or re.match(r"S\s*/\s*N", cellules[0]):
                    continue
                lignes.append({"table": table, "page": numero + 1, "cellules": cellules})
    return lignes


def regrouper(lignes):
    """Une ligne sans numéro prolonge la précédente (saut de page)."""
    sortie = []
    for ligne in lignes:
        sn = re.match(r"^\s*(\d+)\.?\s*$", ligne["cellules"][0])
        meme = sortie and sortie[-1]["table"] == ligne["table"] and len(sortie[-1]["cellules"]) == len(
            ligne["cellules"])
        if sn or not meme:
            sortie.append({**ligne, "sn": int(sn.group(1)) if sn else None})
        else:
            sortie[-1]["cellules"] = [(x + " " + y).strip() for x, y in zip(sortie[-1]["cellules"],
                                                                             ligne["cellules"])]
    return sortie


def entete(document, premiere, derniere, nom):
    for numero in range(premiere, derniere + 1):
        texte = " ".join(document[numero].get_text().split())
        m = re.search(rf"TABLE {nom}:\s*(.*?)\s*S\s*/\s*N", texte)
        if m:
            return m.group(1)
    return ""


document = pymupdf.open(sys.argv[1])
premiere = next(n for n in range(len(document)) if "Legal Notice No. EAC/160/2026" in document[n].get_text())
derniere = next(n for n in range(len(document)) if "Legal Notice No. EAC/161/2026" in document[n].get_text())
# La page où commence l'EAC/161 porte encore la fin de la Table X : on la lit
# jusqu'au titre de l'avis suivant.
lignes = regrouper(lignes_de_tableau(document, premiere, derniere))
mesures, entetes = [], {}
for ligne in lignes:
    t, cel = ligne["table"], ligne["cellules"]
    codes = CODE.findall(cel[1]) if len(cel) > 1 else []
    mesure = {"table": t, "sn": ligne["sn"], "page": ligne["page"], "positions": codes}
    if t == "I":
        mesure["decisions"] = decisions(cel[-1]) if codes else []
        mesure["description"] = cel[2] if len(cel) > 3 else ""
    elif t == "II":
        mesure["decisions"] = decisions(cel[-1])
    elif t in ("III", "IV", "V", "VI", "VII"):
        tete = entete(document, premiere, derniere, t)
        m = re.search(r"APPLY\s+(?:A|THE)\s+(.*)", tete, re.I)
        taux = lire_taux(m.group(1)) if m else None
        pays = pays_de(tete)
        entetes[t] = tete
        mesure["decisions"] = [{"decision": f"en-tête de la Table {t}", "lu": bool(taux and pays), "pays": pays,
                                "droit": sans_expression(taux), "restriction": None}]
    elif t in ("VIII", "IX"):
        mesure["decisions"] = [{"decision": cel[-1], "lu": False,
                                "restriction": "imported by the manufacturers"}]
    elif t == "X":
        m = re.search(r"to\s*[“\"](.*?)[”\"]", cel[-1])
        taux = lire_taux(m.group(1)) if m else None
        mesure["decisions"] = [{"decision": cel[-1], "lu": taux is not None, "pays": TOUS,
                                "droit": sans_expression(taux), "restriction": None}]
    mesures.append(mesure)

json.dump({
    "source": "Legal Notice No. EAC/160/2026, EAC Gazette Vol. AT 1 No. 16 du 30/06/2026 (exercice 2026/27)",
    "pdf_sha256": hashlib.sha256(open(sys.argv[1], "rb").read()).hexdigest(),
    "entetes": entetes,
    "mesures": mesures,
}, open(sys.argv[2], "w", encoding="utf-8"), ensure_ascii=False, indent=0)
appliquees = sum(1 for r in mesures for d in r["decisions"] if d.get("lu") and not d.get("restriction"))
print(len(mesures), "lignes ;", sum(len(r["decisions"]) for r in mesures), "décisions ;", appliquees,
      "appliquées sans condition ;", sum(1 for r in mesures for d in r["decisions"] if not d.get("lu")),
      "non lues")
