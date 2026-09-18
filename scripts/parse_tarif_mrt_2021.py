#!/usr/bin/env python3
"""
Parseur du tarif douanier national mauritanien 2021 (douanes.mr).

Source : https://www.douanes.mr/uploads/pics/tarif_fr_2021.pdf
SHA-256 : 3585fbe23bf6b7be3c4e9eb963fdb31bf0336b059bf0019e4b471f178829c182

Extrait les 6 129 sous-positions nationales (codes à 10 chiffres) avec :
désignation, unité statistique, DD (droit de douane), RS (redevance
statistique), PC (prélèvement communautaire) — pourcentages ad valorem.

Méthode : positions x/y des mots (PyMuPDF) ; colonnes identifiées par
fenêtres x (code ~93, taux 455-565) ; lignes de taux appariées aux codes
par ordre monotone ; désignations par blocs texte ancrés sur (RS, PC).

Validation intégrée (rapport rendu avec les données) :
  V1 décomptes : 6129 codes = 6129 lignes de taux, unicité, comptage
     indépendant par lignes texte ;
  V2 propreté : exactement 3 tokens numériques par ligne de taux ;
  V3 bornes spatiales : chaque ligne de taux dans son bloc [code i, code i+1) ;
  V5 domaines : DD {0,5,10,20,35}, RS {0,1}, PC {0,0,5} ;
  V6 triplet (DD,RS,PC) consécutif dans le texte brut (1 tolérance :
     unité fusionnée avec le DD sur une même ligne, ex. « u(jeu) 20 »).

Usage : python3 scripts/parse_tarif_mrt_2021.py <tarif_fr_2021.pdf> <sortie.json>
"""
import sys, re, json, hashlib
from collections import Counter
import fitz

CODE_RE = re.compile(r'^\d{4}\.\d{2}\.\d{2}\.\d{2}$')
NUM_RE = re.compile(r'^\d+(?:[.,]\d+)?$')
SHA_ATTENDU = '3585fbe23bf6b7be3c4e9eb963fdb31bf0336b059bf0019e4b471f178829c182'


def cluster_lignes(ws, tol=3.5):
    """Regrouper les mots en lignes (y-cluster). Rend [y, [(x, texte)…]]."""
    lines = []  # chaque entrée : [y, [(x, texte)…]]
    for w in sorted(ws, key=lambda z: (round(z[1], 1), z[0])):
        x0, y0, t = w[0], w[1], w[4]
        if lines and abs(y0 - lines[-1][0]) <= tol:
            lines[-1][1].append((x0, t))
        else:
            lines.append([y0, [(x0, t)]])
    return lines


def parser(chemin):
    d = fitz.open(chemin)
    codes, raterows = [], []
    for pno in range(d.page_count):
        for y, lw in cluster_lignes(d[pno].get_text("words")):
            c = next((t for x, t in lw if CODE_RE.match(t) and 85 <= x < 120), None)
            if c:
                codes.append((pno, y, c))
            ns = sorted([(x, t) for x, t in lw if 455 < x < 565 and NUM_RE.match(t)])
            if len(ns) == 3:
                xdd = ns[0][0]
                cand = [(x, t) for x, t in lw if x < xdd and x >= xdd - 60]
                unit = sorted(cand)[-1][1] if cand else ''
                raterows.append((unit, ns[0][1], ns[-2][1], ns[-1][1]))
    if len(codes) != 6129:
        raise RuntimeError(f"codes extraits : {len(codes)} (attendu 6129)")
    if len(raterows) != 6129:
        raise RuntimeError(f"lignes de taux : {len(raterows)} (attendu 6129)")
    if len(set(c for _, _, c in codes)) != 6129:
        raise RuntimeError("codes non uniques")

    blocks, cur = {}, None
    for pno in range(d.page_count):
        for ln in d[pno].get_text().splitlines():
            s = ln.strip()
            if CODE_RE.match(s):
                cur = s
                blocks[cur] = []
            elif cur is not None:
                blocks[cur].append(s)

    def designation(c, dd, rs, pc, unit):
        b = [l for l in blocks.get(c, []) if l]
        k = None
        for j in range(len(b) - 1):
            if b[j] == rs and b[j + 1] == pc:
                k = j
        if k is None:
            return ''
        ddline = k - 1
        if ddline >= 0 and (b[ddline] == dd or b[ddline].endswith(' ' + dd)):
            fin = ddline
        else:
            fin = k - 1
        des = [l for l in b[0:fin] if l]
        # retirer l'unité : sur sa propre ligne, ou fusionnée en fin de la
        # dernière ligne de désignation (« … et leurs kg »)
        if des and unit:
            if des[-1] == unit:
                des = des[:-1]
            elif des[-1].endswith(' ' + unit):
                des[-1] = des[-1][:-(len(unit) + 1)].rstrip()
        out = []
        for l in des:
            s = re.sub(r'^-{1,5}\s*', '', l).strip()
            if s.strip('-') == '':
                continue
            out.append(s)
        txt = ''
        for s in out:
            if txt.endswith('-'):
                txt = txt[:-1] + s
            else:
                txt = (txt + ' ' + s).strip()
        return txt

    return [
        {
            'code': c.replace('.', ''),
            'code_brut': c,
            'chapitre': c[:2],
            'designation': designation(c, dd, rs, pc, unit),
            'unite': unit,
            'DD': dd, 'RS': rs, 'PC': pc,
        }
        for (pno_c, y_c, c), (unit, dd, rs, pc) in zip(codes, raterows)
    ]


def verifier(chemin, out):
    """Contre-vérifications indépendantes. Rend un rapport dict."""
    d = fitz.open(chemin)
    txt_codes = set()
    for pno in range(d.page_count):
        for ln in d[pno].get_text().splitlines():
            s = ln.strip()
            if CODE_RE.match(s):
                txt_codes.add(s)
    v1 = len(set(o['code_brut'] for o in out)) == 6129 == len(txt_codes)
    dd = Counter(o['DD'] for o in out)
    rs = Counter(o['RS'] for o in out)
    pc = Counter(o['PC'] for o in out)
    v5 = (set(dd) <= {'0', '5', '10', '20', '35'}
          and set(rs) <= {'0', '1'} and set(pc) <= {'0', '0,5'})
    blocks, cur = {}, None
    for pno in range(d.page_count):
        for ln in d[pno].get_text().splitlines():
            s = ln.strip()
            if CODE_RE.match(s):
                cur = s
                blocks[cur] = []
            elif cur is not None:
                blocks[cur].append(s)
    v6 = 0
    for o in out:
        nums = [l for l in blocks.get(o['code_brut'], []) if l and NUM_RE.match(l)]
        trip = (o['DD'], o['RS'], o['PC'])
        found = any((nums[i], nums[i + 1], nums[i + 2]) == trip
                    for i in range(len(nums) - 2))
        if not found:
            b = [l for l in blocks.get(o['code_brut'], []) if l]
            if not any(l.endswith(' ' + o['DD']) for l in b):
                v6 += 1
    vides = [o['code_brut'] for o in out if not o['designation']]
    return {
        'V1_decomptes': v1,
        'V5_domaines': v5,
        'V6_triplets_non_confirmes': v6,
        'designations_vides': len(vides),
        'DD': dict(dd), 'RS': dict(rs), 'PC': dict(pc),
    }


def main(argv):
    if len(argv) != 3:
        print(__doc__)
        return 2
    src, dst = argv[1], argv[2]
    h = hashlib.sha256(open(src, 'rb').read()).hexdigest()
    if h != SHA_ATTENDU:
        print(f"empreinte différente : {h} (attendu {SHA_ATTENDU}) — "
              "vérifier la source avant de produire une donnée", file=sys.stderr)
        return 1
    data = parser(src)
    rapport = verifier(src, data)
    rapport['_sha256_source'] = h
    json.dump({'tarif': data, 'verification': rapport},
              open(dst, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    print(f"{len(data)} sous-positions — vérification : {rapport}")
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv))
