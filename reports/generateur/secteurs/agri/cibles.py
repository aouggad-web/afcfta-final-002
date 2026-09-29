"""Cibles d'export vérifiées : taux servi (calculateurs du SaaS) × marché réel (OEC/BACI).

1. Audit : chaque cible citée dans l'édition précédente reçoit un verdict (verif_cibles).
2. Balayage : toutes les lignes SH6 agricoles (01-24) des 5 destinations appliquées, pour les
   origines admises, sont classées par valeur de marge sur le marché accessible.
Sortie : cibles.json (audit + classement), utilisé par les éditions par profil.
"""
import os
import json, gzip, sys, logging, statistics as stt
logging.disable(logging.WARNING)
sys.path.insert(0, '.')
exec(open(os.environ['RG_DIR'] + '/targets.py').read().split('TG=[')[0])  # npf(), pref(), T, D
import verif_cibles as vc

MARO = json.load(gzip.open('data/official_preferential/MAR_afcfta_etariff_2026-09-13.json.gz'))['schedules']['1']


def pref_ligne(o, d, hs6):
    """Taux NPF et servi pour une SH6, évalués sur TOUTES les lignes nationales (8-10 chiffres).
    Retourne (npf moyen, servi moyen, source, lignes réduites, lignes totales).
    Maroc : lignes de l'offre e-Tariff Book (les codes du barème national ne correspondent pas)."""
    if d == 'MAR':
        lignes = [x for x in MARO if x['hs_code'].startswith(hs6)]
        if not lignes:
            return None, None, 'SH6 absente de l\'offre marocaine', 0, 0
        n, r = [], []
        for x in lignes:
            m = float(x['mfn_rate_expression'])
            y = resolve_official_preferential_rate('MAR', x['hs_code'], o, as_of_year=2026)
            n.append(m)
            r.append(m if (y is None or y.get('ad_valorem_rate_pct') is None) else min(m, y['ad_valorem_rate_pct']))
        k = sum(1 for a, b in zip(n, r) if b < a)
        return round(stt.mean(n), 2), round(stt.mean(r), 2), 'offre marocaine', k, len(lignes)
    if d not in T:
        T[d] = {l['hs6']: l for l in json.load(open(f'data/{d}_tariffs.json'))['tariff_lines']}
    l = T[d].get(hs6)
    if not l:
        return None, None, 'SH6 absente du barème', 0, 0
    subs = [s for s in (l.get('sub_positions') or []) if isinstance(s.get('dd'), (int, float))]
    if not subs:
        if not isinstance(l.get('dd_rate'), (int, float)):
            return None, None, 'droit non ad valorem ou absent', 0, 0
        subs = [{'code': hs6, 'dd': l['dd_rate']}]
    n, r, srcs = [], [], set()
    for s in subs:
        base, code = s['dd'], s['code']
        try:
            if d == 'DZA':
                x, src = compute_dza_zlecaf_rate(code, o, base, D)
            elif d == 'EGY':
                x, src = compute_egy_zlecaf_rate(code, o, base, D)
            elif d == 'KEN':
                if not implementation_decision('KEN', o)['applied']:
                    x, src = base, 'origine non admise'
                else:
                    x, src = compute_ken_zlecaf_rate(code.ljust(8, '0') if len(code) < 8 else code, o, D)
            else:
                y = resolve_official_preferential_rate(d, code, o, as_of_year=2026)
                x, src = (None, 'non servi') if y is None else (y.get('ad_valorem_rate_pct'), 'offre')
        except Exception as e:
            x, src = None, f'erreur {e}'
        x = base if not isinstance(x, (int, float)) else min(x, base)
        n.append(base); r.append(x); srcs.add(str(src)[:40])
    k = sum(1 for a, b in zip(n, r) if b < a)
    return round(stt.mean(n), 2), round(stt.mean(r), 2), ' | '.join(sorted(srcs))[:120], k, len(subs)


FAP = json.load(open(os.environ['RG_REPO'] + '/data/dza/legal_overrides.json'))['measures']
FAP_HS = {}
for mm in FAP:
    for c in mm.get('hs_codes', []):
        FAP_HS.setdefault(c[:6], set()).add(mm['legal_title'].split(':')[-1].strip()[:70])
SEVERES = ('monopole', 'licence', 'autorisation d\'importation', 'autorisation technique', 'usines enregistr', 'registered factor', 'quota', 'contingent')


def mnt(d, hs6):
    """Formalités non tarifaires recensées par le SaaS pour la ligne (F.A.P algériennes, formalités douanières égyptiennes, etc.)."""
    if d == 'DZA':
        docs = sorted(FAP_HS.get(hs6, ()))
    else:
        l = T.get(d, {}).get(hs6) or {}
        docs = sorted({f.get('document_fr') or f.get('document_en') or '' for s in (l.get('sub_positions') or []) for f in (s.get('administrative_formalities') or [])})
    docs = [x for x in docs if x]
    graves = [x for x in docs if any(k in x.lower() for k in SEVERES) and not any(e in x.lower() for e in ('zone franche', 'sans licence'))]
    return docs, graves


NOMS = {'DZA': 'Algérie', 'EGY': 'Égypte', 'KEN': 'Kenya', 'MAR': 'Maroc', 'ZAF': 'Afrique du Sud', 'TUN': 'Tunisie', 'GHA': 'Ghana',
        'CMR': 'Cameroun', 'CIV': "Côte d'Ivoire", 'NGA': 'Nigeria', 'SEN': 'Sénégal', 'TZA': 'Tanzanie', 'RWA': 'Rwanda', 'MUS': 'Maurice',
        'UGA': 'Ouganda', 'ETH': 'Éthiopie', 'MWI': 'Malawi', 'ZMB': 'Zambie', 'MRT': 'Mauritanie'}

# Cibles publiées dans l'édition T3 2026 (synthèse + chapitre 7), à auditer une par une
AUDIT = [('EGY', 'MAR', '070190'), ('EGY', 'MAR', '080510'), ('EGY', 'MAR', '190219'), ('TUN', 'MAR', '190219'), ('EGY', 'MAR', '190531'),
         ('EGY', 'DZA', '020714'), ('TZA', 'DZA', '080132'), ('RWA', 'DZA', '090240'), ('TZA', 'DZA', '090240'), ('TZA', 'DZA', '151219'),
         ('TZA', 'DZA', '060311'), ('MWI', 'MAR', '240120'), ('TUN', 'DZA', '230990'), ('GHA', 'KEN', '180690'), ('CMR', 'KEN', '180690'),
         ('CIV', 'KEN', '080132'), ('EGY', 'KEN', '190531'), ('EGY', 'KEN', '200290'), ('EGY', 'KEN', '200911'), ('EGY', 'KEN', '070310'),
         ('EGY', 'KEN', '020714'), ('MWI', 'KEN', '240120'), ('ZMB', 'KEN', '240120'), ('KEN', 'DZA', '090240'), ('KEN', 'DZA', '080440'),
         ('GHA', 'KEN', '160414'), ('NGA', 'KEN', '210410'), ('NGA', 'ZAF', '210410'), ('GHA', 'ZAF', '180632'), ('EGY', 'ZAF', '220299'),
         ('ZAF', 'EGY', '200911'), ('SEN', 'MAR', '030389'), ('CIV', 'KEN', '151190'), ('GHA', 'KEN', '151190')]

DESTS = ['DZA', 'EGY', 'KEN', 'MAR', 'ZAF']
ORIGS = ['EGY', 'MAR', 'TUN', 'DZA', 'ZAF', 'KEN', 'MUS', 'GHA', 'NGA', 'SEN', 'TZA', 'CIV', 'CMR', 'RWA', 'UGA', 'ETH', 'MWI', 'ZMB', 'MRT']

m = vc.Marches()
res = {'audit': [], 'classement': [], 'seuils': {'marche': vc.SEUIL_MARCHE, 'offre': vc.SEUIL_OFFRE, 'annees': vc.ANNEES}}
for o, d, hs in AUDIT:
    n, r, src, k, nl = pref_ligne(o, d, hs)
    v, motifs, ind = vc.verdict(o, d, hs, n, r, m, (k, nl))
    docs, graves = mnt(d, hs)
    res['audit'].append(dict(o=o, d=d, hs=hs, npf=n, pref=r, src=src, lignes=f'{k}/{nl}', verdict=v, motifs=motifs, mnt=docs, mnt_graves=graves, **ind))
    print(f'{v:8} {o}->{d} {hs} {n}->{r} [{k}/{nl}] imp {ind["imp_dest"]/1e6:7.1f} exp_d {ind["exp_dest"]/1e6:7.1f} exp_o {ind["exp_orig"]/1e6:8.1f} {"; ".join(motifs)}')

# Intrants strictement agricoles (SH 2017). Exclus volontairement : 8701.20 (tracteurs ROUTIERS pour semi-remorques),
# 8424.10 (extincteurs), 8433.11/19 (tondeuses à gazon), 3808.94 (désinfectants), 3808.99 (autres, non spécifiques).
INTRANTS = ['3102', '3103', '3104', '3105', '2309', '2304', '120991', '120999', '120921', '120929', '070110', '100510', '100710', '100310', '100110', '100191',
            '380891', '380892', '380893', '8432', '843320', '843330', '843340', '843351', '843352', '843353', '843359', '8434', '8436', '843780', '842441', '842449', '842482',
            '870110', '870130', '870191', '870192', '870193', '870194', '870195', '871620']


def balayage(marches, garder=lambda hs: True):
    out = []
    for d in DESTS:
        imp = marches.imp(d)
        lignes = [h for h, v in imp.items() if v >= vc.SEUIL_MARCHE and garder(h)]
        for o in ORIGS:
            if o == d:
                continue
            exp_o = marches.exp(o)
            for hs in lignes:
                if exp_o.get(hs, 0) < vc.SEUIL_OFFRE:
                    continue
                n, r, src, k, nl = pref_ligne(o, d, hs)
                v, motifs, ind = vc.verdict(o, d, hs, n, r, marches, (k, nl))
                if v == 'REJETÉE':
                    continue
                docs, graves = mnt(d, hs)
                out.append(dict(o=o, d=d, hs=hs, npf=n, pref=r, src=src, lignes=f'{k}/{nl}', verdict=v, motifs=motifs, score=vc.score(ind),
                                mnt=docs, mnt_graves=graves, **ind))
    return sorted(out, key=lambda x: -x['score'])


res['classement'] = balayage(m)
mi = vc.Marches(chapitres=['12', '23', '31', '38', '84', '87', '07', '10'])
res['intrants'] = balayage(mi, lambda hs: hs.startswith(tuple(INTRANTS)))
res['intrants_marches'] = {d: {h: v for h, v in mi.imp(d).items() if h.startswith(tuple(INTRANTS))} for d in DESTS + ['NGA', 'ETH', 'GHA', 'CIV', 'SEN', 'TZA', 'TUN']}
json.dump(res, open(os.environ['RG_DIR'] + '/cibles.json', 'w'), ensure_ascii=False, indent=1)
print('candidats retenus/créneaux :', len(res['classement']), 'intrants :', len(res['intrants']))
for x in res['classement'][:25] + [None] + res['intrants'][:25]:
    if x is None:
        print('--- intrants'); continue
    print(f"{x['verdict']:8} {x['o']}->{x['d']} {x['hs']} {x['npf']}->{x['pref']} [{x['lignes']}] imp {x['imp_dest']/1e6:6.1f} exp_o {x['exp_orig']/1e6:7.1f} bil {x['bilat']/1e6:5.1f} score {x['score']/1e6:5.2f} | MNT {len(x['mnt'])} {'; '.join(x['mnt_graves'])[:80]}")

# Tableau des régimes appliqués aux intrants clés : NPF et taux servi à une origine représentative admise
REP = {'DZA': 'TUN', 'EGY': 'TUN', 'KEN': 'EGY', 'MAR': 'EGY', 'ZAF': 'GHA'}
CLES = ['310210', '310530', '310520', '310420', '230990', '230400', '100510', '070110', '120991', '380891', '380893', '870192', '843351', '842482']
res['intrants_tarifs'] = {}
for hs in CLES:
    res['intrants_tarifs'][hs] = {}
    for d in DESTS:
        n, r, src, k, nl = pref_ligne(REP[d], d, hs)
        res['intrants_tarifs'][hs][d] = dict(npf=n, pref=r, lignes=f'{k}/{nl}', orig=REP[d])
json.dump(res, open(os.environ['RG_DIR'] + '/cibles.json', 'w'), ensure_ascii=False, indent=1)
for hs, v in res['intrants_tarifs'].items():
    print(hs, {d: (x['npf'], x['pref']) for d, x in v.items()})

# Pays focus exportateur : ses premières exportations agricoles (et les produits cités dans son module) dans chaque destination appliquée,
# avec verdict complet (y compris rejets, pour corriger les tableaux « produits du pays → destinations »).
F = os.environ.get('RG_PAYS_FOCUS', 'DZA').upper()
EXTRAS = {'DZA': ['080410', '110311', '190219', '190531', '070190', '200290', '121292', '220110', '220210', '170199', '180690']}
top = [h for h, v in sorted(m.exp(F).items(), key=lambda x: -x[1]) if v >= 1e6][:20]
res['focus'] = {'pays': F, 'exportations': []}
for hs in list(dict.fromkeys(top + EXTRAS.get(F, []))):
    for d in DESTS:
        if d == F:
            continue
        n, r, src, k, nl = pref_ligne(F, d, hs)
        v, motifs, ind = vc.verdict(F, d, hs, n, r, m, (k, nl))
        res['focus']['exportations'].append(dict(o=F, d=d, hs=hs, npf=n, pref=r, src=src, lignes=f'{k}/{nl}', verdict=v, motifs=motifs, **ind))
json.dump(res, open(os.environ['RG_DIR'] + '/cibles.json', 'w'), ensure_ascii=False, indent=1)
for x in res['focus']['exportations']:
    print(f"FOCUS {x['verdict']:8} {x['d']} {x['hs']} {x['npf']}->{x['pref']} [{x['lignes']}] imp {x['imp_dest']/1e6:6.1f} exp_o {x['exp_orig']/1e6:6.1f} {'; '.join(x['motifs'])[:90]}")
