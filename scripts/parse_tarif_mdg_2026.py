#!/usr/bin/env python3
"""
Parseur du tarif des douanes de Madagascar, édition 2026 (après LFR 2026).

Source : https://www.douanes.gov.mg/srcs/uploads/2026/07/TARIF-DES-DOUANES-2026-MAJ-LFR.pdf
SHA-256 : 9f26e514d5bbbb69e3c45082b49694bb39378c983a975568a46490c02b326e5f

Produit un fichier au modèle de `backend/data/crawled/MRT_tariffs.json` :
sous-positions nationales à 8 chiffres, colonnes DD / TVA / DD APEi.

Méthode : positions x/y des mots (PyMuPDF). Les colonnes changent d'une page à
l'autre : elles sont donc lues sur l'en-tête `UQN DD TVA [APEi]` qui précède
chaque sous-table, et non supposées fixes.

DEUX RÈGLES QUE LA PREMIÈRE VERSION AVAIT RATÉES, ET QUI ONT COÛTÉ DES POSITIONS :

1. **Les valeurs d'une ligne peuvent être réparties sur plusieurs lignes.** Une
   désignation qui se replie repousse l'unité et la TVA (voire l'APEi) sur la
   ligne suivante, alors que le DD reste sur la ligne du code. La première
   version finalisait la position dès la ligne du code : cinq TVA publiées
   (4010.31 à 4010.34, 8423.81) sortaient à `null`. On accumule désormais les
   valeurs colonne par colonne jusqu'au code suivant.

2. **Un en-tête non strictement `UQN DD TVA APEi` n'est pas forcément
   spécial.** Sept chapitres (25, 26, 27, 50, 71, 75, 81) disparaissaient parce
   que leur en-tête variait (`UQN DD TVA`, `UQN DD TVA DD`, ou six colonnes avec
   un second `UQN`/`DS`). On collecte les schémas compatibles (`UQN DD TVA`,
   `APEi` optionnel) ; on ÉCARTE et DÉCLARE les schémas non univoques
   (colonnes `TPP`/`TVP` à droits spécifiques en Ariary/litre ou Ariary/kg-net,
   colonnes `DS`), qui ne sont jamais devinées.

Usage : python3 scripts/parse_tarif_mdg_2026.py <tarif.pdf> <sortie.json>
"""
import sys, re, json, hashlib
from collections import Counter
import fitz

PDF_SHA_ATTENDU = "9f26e514d5bbbb69e3c45082b49694bb39378c983a975568a46490c02b326e5f"
PDF_URL = "https://www.douanes.gov.mg/srcs/uploads/2026/07/TARIF-DES-DOUANES-2026-MAJ-LFR.pdf"
SRC_NAME = "Tarif des douanes de Madagascar, édition 2026 (douanes.gov.mg)"

#: Colonnes de taxe reconnues. Les unes situent une colonne, les autres
#: rendent la sous-table NON univoque et sont écartées en bloc.
COLONNES_TAXE = {"DD", "TVA", "TVP", "TPP", "DS", "TVAPP", "TPPAPEI", "DDAPEi"}
COLONNES_APEi = {"APEi", "APEI", "DDAPEi", "TPPAPEI"}
COLONNES_SPECIALES = {"TPP", "TVP", "DS", "TVAPP", "TPPAPEI"}
LABELS = {"UQN", "DD", "TVA", "APEi", "APEI", "DS", "Valeur"} | COLONNES_TAXE
RATE = re.compile(r"^(?:ex|EX|\d{1,3}(?:[.,]\d+)?%?)$")
CODE4 = re.compile(r"^\d{4}\.\d{2}$")
SUF2 = re.compile(r"^\d{2}$")


def cluster(ws, tol=3.0):
    """Regroupe les mots en lignes (y-cluster)."""
    lines = []
    for w in sorted(ws, key=lambda z: (round(z[1], 1), z[0])):
        if lines and abs(w[1] - lines[-1][0]) <= tol:
            lines[-1][1].append(w)
        else:
            lines.append([w[1], [w]])
    return lines


def clean_designation(tokens):
    txt = " ".join(tokens)
    txt = re.sub(r"-{2,}", " ", txt)
    txt = re.sub(r"\s+", " ", txt).strip(" -")
    return txt.strip()


def _colonnes(lw):
    """Colonnes d'un en-tête : UQN(1er), DD(1er), TVA, APEi. Rend (cols, active, signature)."""
    labels = [(w[4], w[0]) for w in lw if w[4] in LABELS]
    if not any(l == "UQN" for l, _ in labels):
        return None, None, None
    signature = tuple(l for l, _ in labels)
    cols = {}
    for nom, x in labels:
        if nom == "UQN" and "UQN" not in cols:
            cols["UQN"] = x
        elif nom == "DD" and "DD" not in cols:
            cols["DD"] = x
        elif nom == "TVA" and "TVA" not in cols:
            cols["TVA"] = x
        elif nom in COLONNES_APEi and "APEi" not in cols:
            cols["APEi"] = x
    special = any(l in COLONNES_SPECIALES for l in signature)
    actif = ("UQN" in cols and "DD" in cols and "TVA" in cols and not special)
    return (cols if actif else None), actif, signature


def _valeurs(lw, cols):
    out = {}
    for nom, cx in cols.items():
        for w in lw:
            if abs(w[0] - cx) <= 7 and (RATE.match(w[4]) or nom == "UQN"):
                out[nom] = w[4]
                break
    return out


def parse(pdf_path):
    doc = fitz.open(pdf_path)
    cols = None
    signature = None
    actif = False
    cur = None                 # {"code","tokens","valeurs","page"}
    positions = {}             # code -> record (première occurrence conservée)
    ecartees = []              # (code, motif, page)
    doublons = 0

    def finaliser():
        nonlocal cur, doublons
        if cur is None:
            return
        if not cur["valeurs"].get("DD"):
            ecartees.append((cur["code"], "droit de douane non lu (schéma de ligne)", cur["page"]))
        elif cur["code"] in positions:
            doublons += 1
        else:
            positions[cur["code"]] = cur
        cur = None

    for pno in range(17, doc.page_count):
        for y, lw in cluster(doc[pno].get_text("words")):
            nouvelles, est_actif, sig = _colonnes(lw)
            if sig is not None and "UQN" in sig:
                finaliser()
                actif, cols, signature = est_actif, nouvelles, sig
                continue

            c1 = [w for w in lw if CODE4.match(w[4]) and w[0] < 140]
            c2 = [w for w in lw if SUF2.match(w[4]) and w[0] < 140]
            code = (c1[0][4].replace(".", "") + c2[0][4]) if (c1 and c2) else None
            heading = bool(c1) and not code
            toks = [w[4] for w in lw if 113 <= w[0] < 378]

            if not actif:
                if code:
                    ecartees.append((code, f"sous-table à schéma non standard {signature}", pno))
                elif heading:
                    pass
                continue

            if code:
                finaliser()
                cur = {"code": code, "tokens": list(toks), "valeurs": {}, "page": pno}
                cur["valeurs"].update(_valeurs(lw, cols))
            elif heading:
                finaliser()
            elif cur is not None:
                for k, v in _valeurs(lw, cols).items():
                    cur["valeurs"].setdefault(k, v)
                cur["tokens"].extend(toks)
    finaliser()
    return positions, ecartees, doublons


def build(pdf_path, source_sha):
    positions, ecartees, doublons = parse(pdf_path)
    sub = []
    chapters = set()
    for code in sorted(positions):
        rec = positions[code]
        chapters.add(code[:2])
        vals = rec["valeurs"]
        desig = clean_designation(rec["tokens"])
        unit = vals.get("UQN") or ""

        def tax(name, raw):
            if raw is None:
                return {"name": name, "rate": None, "raw": "",
                        "note": "taux non publié par le tarif à cette ligne",
                        "source": SRC_NAME, "source_url": PDF_URL, "source_sha256": source_sha}
            low = raw.strip().lower()
            if low in ("ex", "exempt", "exonere", "exonéré"):
                return {"name": name, "rate": 0.0, "raw": raw, "note": "ex = exonéré (mention publiée par le tarif)",
                        "source": SRC_NAME, "source_url": PDF_URL, "source_sha256": source_sha}
            try:
                rate = float(low.replace(",", ".").replace("%", ""))
            except ValueError:
                rate = None
            return {"name": name, "rate": rate, "raw": raw,
                    "source": SRC_NAME, "source_url": PDF_URL, "source_sha256": source_sha}

        pos = {
            "hs_code": code, "chapter": code[:2], "name": desig, "description": desig,
            "unit": unit,
            "taxes": {
                "DD": tax("Droit de douane (tarif national 2026)", vals.get("DD")),
                "TVA": tax("Taxe sur la valeur ajoutée (tarif national 2026)", vals.get("TVA")),
            },
        }
        ap = vals.get("APEi")
        if ap is not None:
            low = ap.strip().lower()
            if low in ("ex", "exempt", "exonere", "exonéré"):
                rate, raw_out = 0.0, ap
            else:
                try:
                    rate = float(low.replace(",", ".").replace("%", ""))
                except ValueError:
                    rate = None
                raw_out = ap
            pos["preferential_rates"] = [{
                "regime": "APEI", "rate_pct": rate, "raw_value": raw_out,
                "source": SRC_NAME, "source_url": PDF_URL, "source_sha256": source_sha,
            }]
        sub.append(pos)

    par_motif = Counter(r for _, r, _ in ecartees)
    return {
        "country": "MDG",
        "country_name": "Madagascar",
        "source": "Tarif des douanes de Madagascar, édition 2026 (après LFR 2026)",
        "source_name": "Tarif des douanes (basé sur la version 2022 du S.H), édition 2026 — mise à jour LFR 2026",
        "source_url": PDF_URL,
        "source_sha256": source_sha,
        "extracted_at": "2026-09-21T00:00:00+00:00",
        "source_quality": "crawled_authentic_national",
        "stats": {"sections": 0, "chapters": len(chapters), "sub_positions": len(sub),
                  "errors": len(ecartees), "duplicates": doublons},
        "calculation_rules": {
            "order": ["DD", "TVA"],
            "bases": {
                "DD": {"basis": "CIF", "type": "ad_valorem"},
                "TVA": {"basis": "CIF+TOUS_SAUF_TVA", "type": "ad_valorem"},
            },
            "source": (
                "Tarif national 2026 (douanes.gov.mg, SHA-256 consigné) : sous-positions "
                "nationales à 8 chiffres, colonnes DD/TVA/DD APEi — remplace la donnée "
                "WITS/UNCTAD-TRAINS (moyenne SH6). Assiettes sur texte primaire : DD = CIF "
                "(Code des douanes, Loi n° 2006-023 après LFI 2026, art. 23 §1 et §4 c)) ; TVA = "
                "CIF+TOUS_SAUF_TVA (CGI éd. 2025, art. 06.01.11). Colonne DD APEi = droit "
                "préférentiel APE intérimaire (UE), servie à part. Les sous-tables à schéma non "
                "univoque (colonnes TPP/TVP à droits spécifiques Ariary/litre ou Ariary/kg-net, "
                "colonnes DS) sont écartées et énumérées dans `non_collected` — "
                + str(len(ecartees)) + " position(s)."
            ),
        },
        "regimes_registry": [{
            "code": "APEI", "name": "Droit préférentiel APE intérimaire (Union européenne)",
            "column_label": "DD APEi", "source_url": PDF_URL, "source_sha256": source_sha,
        }],
        "non_collected": [{"code": c, "reason": r, "page": p} for c, r, p in ecartees],
        "non_collected_summary": {
            "total": len(ecartees),
            "par_motif": dict(par_motif),
            "chapitres": dict(Counter(c[:2] for c, _, _ in ecartees)),
        },
        "sub_positions": sub,
    }


def main(argv):
    if len(argv) != 3:
        print(__doc__)
        return 2
    src, dst = argv[1], argv[2]
    h = hashlib.sha256(open(src, "rb").read()).hexdigest()
    if h != PDF_SHA_ATTENDU:
        print(f"empreinte différente : {h} (attendu {PDF_SHA_ATTENDU}) — "
              "vérifier la source avant de produire une donnée", file=sys.stderr)
        return 1
    data = build(src, h)
    with open(dst, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=1)
    st = data["stats"]
    print(f"{st['sub_positions']} sous-positions, {st['chapters']} chapitres, "
          f"{st['errors']} écartée(s) ({data['non_collected_summary']['par_motif']}) "
          f"→ {dst}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
