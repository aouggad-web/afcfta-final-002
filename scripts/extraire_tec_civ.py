"""Lit le tarif officiel de la Côte d'Ivoire (DGD, « TEC CEDEAO 2022 version
SYDAM World », enrichi de la taxation nationale, PDF de 566 pages) et en tire,
par position, le libellé et le taux de chaque colonne.

Les valeurs sont rattachées à leur colonne par leur position horizontale
(centre du mot au plus près du centre de l'en-tête, à 14 points près, sinon
signalées « _ambigu ») et à leur position tarifaire par le quadrillage du
tableau (lignes horizontales du PDF).

    python3 scripts/extraire_tec_civ.py <tarif.pdf> <sortie.json>
"""
import pymupdf, sys, re, json
d = pymupdf.open(sys.argv[1])
COLS = ["DD","TUB","TVA","DUS","TSB","PSV","TUF","TUE","PCC","PCS","PUA","PSS","RST","TAB","TAI","TBG","TCI","TCB","TCT","TFS","TMP","TPQ","TSM","TSS"]
out = {}
num = re.compile(r"^\d+(?:[.,]\d+)?$")
for pno, page in enumerate(d):
    words = page.get_text("words")
    hdr = {}
    for w in words:
        if w[4] in COLS and w[1] < 120 and w[4] not in hdr:
            hdr[w[4]] = ((w[0]+w[2])/2, w[3])
    if len(hdr) < len(COLS):
        print("page", pno+1, "header incomplete", sorted(set(COLS)-set(hdr)), file=sys.stderr); continue
    ybot = max(v[1] for v in hdr.values())
    codex = None
    rows = []
    for w in words:
        if w[1] > ybot and re.fullmatch(r"\d{10}", w[4]):
            rows.append((w[1], w[4], w[0]))
    rows.sort()
    if not rows: continue
    codex = min(r[2] for r in rows)
    lib_right = hdr["DD"][0] - 15
    lignes = sorted({round(r["rect"].y0, 1) for r in page.get_drawings() if r["rect"].height < 2 and r["rect"].width > 200})
    for i, (y, code, x) in enumerate(rows):
        haut = [l for l in lignes if l <= y + 1]
        bas = [l for l in lignes if l > y + 1]
        y1 = haut[-1] if haut else ybot
        y2 = bas[0] if bas else 10_000
        vals = {}
        lib = [w for w in words if y1 <= w[1] < y2 and x + 50 < w[0] < lib_right]
        lib.sort(key=lambda w: (round(w[1]), w[0]))
        vals["_libelle"] = " ".join(w[4] for w in lib)
        for w in words:
            if y1 <= w[1] < y2 and w[0] > lib_right and num.match(w[4]):
                xc = (w[0]+w[2])/2
                col = min(COLS, key=lambda c: abs(hdr[c][0]-xc))
                if abs(hdr[col][0]-xc) > 14:
                    vals.setdefault("_ambigu", []).append((w[4], round(xc)))
                    continue
                vals[col] = float(w[4].replace(",", "."))
        out[code] = vals
json.dump(out, open(sys.argv[2], "w"))
print(len(out))
