#!/usr/bin/env python3
"""
Parseur du tarif des douanes de Madagascar, édition 2026 (après LFR 2026).

Source : https://www.douanes.gov.mg/srcs/uploads/2026/07/TARIF-DES-DOUANES-2026-MAJ-LFR.pdf
SHA-256 : 9f26e514d5bbbb69e3c45082b49694bb39378c983a975568a46490c02b326e5f

Produit un fichier au modèle de `backend/data/crawled/MRT_tariffs.json` :
sous-positions nationales à 8 chiffres, colonnes DD / TVA / DD APEi.

Méthode : positions x/y des mots (PyMuPDF). Les colonnes changent de page en
page : elles sont donc lues sur l'en-tête `UQN DD TVA APEi` qui précède chaque
sous-table, et non supposées fixes. Seules les sous-tables STANDARD
(`UQN DD TVA APEi`) sont collectées : les sous-tables pétrolières (colonnes
TPP/TVP avec droits spécifiques en Ariary/litre ou Ariary/kg, footnotes (1*)/(2*))
et les sous-tables à colonne DS sont ÉCARTÉES et déclarées, faute d'une lecture
univoque de leur schéma.

Règles de liquidation (assiettes) établies sur texte primaire :
- DD  : valeur transactionnelle + transport/assurance jusqu'au port d'introduction
        (Code des douanes, Loi n° 2006-023, version après LFI 2026, art. 23 §1/§4 c)) → CIF ;
- TVA : valeur des importations, frais et taxes inclus, TVA exclue
        (CGI éd. 2025, art. 06.01.11) → CIF+TOUS_SAUF_TVA.
- `ex` (exonéré) est un zéro publié : rate 0.0, raw « ex ».

Usage : python3 scripts/parse_tarif_mdg_2026.py <tarif.pdf> <sortie.json>
"""
import sys, re, json, hashlib
from collections import Counter
import fitz

PDF_SHA_ATTENDU = "9f26e514d5bbbb69e3c45082b49694bb39378c983a975568a46490c02b326e5f"
PDF_URL = "https://www.douanes.gov.mg/srcs/uploads/2026/07/TARIF-DES-DOUANES-2026-MAJ-LFR.pdf"
STANDARD = ("UQN", "DD", "TVA", "APEi")
LABELS = {"UQN", "DD", "TVA", "TVP", "TPP", "APEi", "APEI", "DS", "Valeur", "TVAPP", "TPPAPEI", "DDAPEi"}
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


def parse(pdf_path):
    doc = fitz.open(pdf_path)
    cols = None
    active = False
    pending = None            # [code, tokens, pno]
    positions = {}            # code -> (tokens, vals, pno)
    dropped = []              # codes écartés et déclarés
    stray = 0

    def finalize(code, tokens, vals, pno):
        if code in positions:
            return  # doublon de reprise de page : première occurrence conservée
        positions[code] = (tokens, vals, pno)

    for pno in range(17, doc.page_count):
        for y, lw in cluster(doc[pno].get_text("words")):
            labels = []
            for w in lw:
                if w[4] in LABELS:
                    labels.append((w[4], w[0]))
            if any(l[0] == "UQN" for l in labels):
                active = tuple(l[0] for l in labels) == STANDARD
                cols = {n: x for n, x in labels if n in ("UQN", "DD", "TVA", "APEi")} if active else None
                if pending is not None:
                    dropped.append((pending[0], "en-tête rencontré avant ses taux", pno))
                    pending = None
                continue
            if not active or cols is None:
                continue

            c1 = [w for w in lw if CODE4.match(w[4]) and w[0] < 140]
            c2 = [w for w in lw if SUF2.match(w[4]) and w[0] < 140]
            code = (c1[0][4].replace(".", "") + c2[0][4]) if (c1 and c2) else None
            heading = bool(c1) and not code
            toks = [w[4] for w in lw if 113 <= w[0] < 378]

            got = {}
            for n, cx in cols.items():
                ts = [w for w in lw if abs(w[0] - cx) <= 7 and (RATE.match(w[4]) or n == "UQN")]
                if ts:
                    got[n] = ts[0][4]
            has = got.get("DD") is not None and bool(RATE.match(got["DD"]))

            if code:
                if pending is not None and has:
                    finalize(pending[0], pending[1], got, pending[2])
                    pending = None
                elif pending is not None and not has:
                    dropped.append((pending[0], "aucun taux publié avant le code suivant", pno))
                    pending = None
                if has:
                    finalize(code, toks, got, pno)
                else:
                    pending = [code, list(toks), pno]
            elif heading:
                if pending is not None and has:
                    finalize(pending[0], pending[1], got, pending[2])
                    pending = None
                elif pending is not None:
                    dropped.append((pending[0], "aucun taux publié avant l'en-tête de position", pno))
                    pending = None
            else:
                if has and pending is not None:
                    finalize(pending[0], pending[1] + list(toks), got, pending[2])
                    pending = None
                elif has and pending is None:
                    stray += 1
                elif pending is not None:
                    pending[1].extend(toks)

    if pending is not None:
        dropped.append((pending[0], "fin de document avant ses taux", None))

    return positions, dropped, stray


def build(pdf_path, source_sha):
    positions, dropped, stray = parse(pdf_path)
    sub = []
    chapters = set()
    notes = {"ex": "ex = exonéré (mention publiée par le tarif)"}
    for code in sorted(positions):
        toks, vals, pno = positions[code]
        chapters.add(code[:2])
        desig = clean_designation(toks)
        unit = vals.get("UQN") or ""

        def tax(name, raw, note=None):
            if raw is None:
                return {"name": name, "rate": None, "raw": "",
                        "note": "taux non publié par le tarif à cette ligne",
                        "source": SRC_NAME, "source_url": PDF_URL, "source_sha256": source_sha}
            low = raw.strip().lower()
            if low in ("ex", "exempt", "exonere", "exonéré"):
                rate = 0.0
                extra = notes["ex"]
                raw_out = raw
            else:
                try:
                    rate = float(low.replace(",", ".").replace("%", ""))
                except ValueError:
                    rate = None
                extra = None
                raw_out = raw
            d = {"name": name, "rate": rate, "raw": raw_out,
                 "source": SRC_NAME, "source_url": PDF_URL, "source_sha256": source_sha}
            if note:
                d["note"] = note
            if extra:
                d["note"] = extra
            return d

        taxes = {
            "DD": tax("Droit de douane (tarif national 2026)", vals.get("DD")),
            "TVA": tax("Taxe sur la valeur ajoutée (tarif national 2026)", vals.get("TVA")),
        }
        pos = {"hs_code": code, "chapter": code[:2], "name": desig, "description": desig,
               "unit": unit, "taxes": taxes}
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
                "regime": "APEI",
                "rate_pct": rate,
                "raw_value": raw_out,
                "source": SRC_NAME,
                "source_url": PDF_URL,
                "source_sha256": source_sha,
            }]
        sub.append(pos)

    return {
        "country": "MDG",
        "country_name": "Madagascar",
        "source": "Tarif des douanes de Madagascar, édition 2026 (après LFR 2026)",
        "source_name": "Tarif des douanes (basé sur la version 2022 du S.H), édition 2026 — mise à jour LFR 2026",
        "source_url": PDF_URL,
        "source_sha256": source_sha,
        "extracted_at": "2026-09-21T00:00:00+00:00",
        "source_quality": "crawled_authentic_national",
        "stats": {"sections": 0, "chapters": len(chapters), "sub_positions": len(sub), "errors": len(dropped)},
        "calculation_rules": {
            "order": ["DD", "TVA"],
            "bases": {
                "DD": {"basis": "CIF", "type": "ad_valorem"},
                "TVA": {"basis": "CIF+TOUS_SAUF_TVA", "type": "ad_valorem"},
            },
            "source": (
                "Tarif national 2026 (douanes.gov.mg, SHA-256 consigné) : sous-positions "
                "nationales à 8 chiffres, colonnes DD/TVA/DD APEi — remplace la donnée "
                "WITS/UNCTAD-TRAINS (moyenne SH6). Assiettes sur texte primaire : DD = valeur "
                "transactionnelle + transport/assurance jusqu'au port d'introduction (Code des "
                "douanes, Loi n° 2006-023 après LFI 2026, art. 23 §1 et §4 c)) → CIF ; TVA = valeur "
                "des importations, frais et taxes inclus, TVA exclue (CGI éd. 2025, art. 06.01.11) "
                "→ CIF+TOUS_SAUF_TVA. Colonne DD APEi = droit préférentiel APE intérimaire (UE), "
                "servie à part. Les sous-tables pétrolières à droits spécifiques (Ariary/litre ou "
                "Ariary/kg, colonnes TPP/TVP) et les sous-tables à colonne DS sont écartées et "
                "déclarées : " + str(len(dropped)) + " position(s) non collectée(s)."
            ),
        },
        "regimes_registry": [{
            "code": "APEI",
            "name": "Droit préférentiel APE intérimaire (Union européenne)",
            "column_label": "DD APEi",
            "source_url": PDF_URL,
            "source_sha256": source_sha,
        }],
        "non_collected": [
            {"code": c, "reason": r, "page": p} for c, r, p in dropped
        ],
        "sub_positions": sub,
    }


SRC_NAME = "Tarif des douanes de Madagascar, édition 2026 (douanes.gov.mg)"


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
          f"{st['errors']} écartée(s) → {dst}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
