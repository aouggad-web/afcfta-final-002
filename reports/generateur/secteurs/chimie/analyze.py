import json, glob, os, statistics as st, gzip, collections
OUT=(os.environ['RG_DIR'] + '/')
GROUPS=[
 ("C01","Chimie inorganique de base",["28"]),
 ("C02","Chimie organique de base",["29%02d"%i for i in range(1,16)]),
 ("C03","Chimie organique fine & intermédiaires",["29%02d"%i for i in range(16,36)]+["2942"]),
 ("C04","Engrais",["31"]),
 ("C05","Peintures, vernis, encres, colorants",["32"]),
 ("C06","Huiles essentielles & parfums",["3301","3302","3303"]),
 ("C07","Maquillage & soins de la peau",["3304"]),
 ("C08","Produits capillaires",["3305"]),
 ("C09","Hygiène bucco-dentaire",["3306"]),
 ("C10","Rasage, déodorants & bain",["3307"]),
 ("C11","Savons",["3401"]),
 ("C12","Détergents & tensioactifs",["3402"]),
 ("C13","Javel, désinfectants & entretien des surfaces",["2828","3808","3405"]),
 ("C14","Produits chimiques divers",["38"]),
 ("C15","Matières plastiques primaires",["39%02d"%i for i in range(1,15)]),
 ("C16","Articles d'hygiène (papier, couches, brosses)",["4818","9619","960321"]),
]
def group_of(hs):
    best=None
    for gid,_,pre in GROUPS:
        for p in pre:
            if hs.startswith(p) and (best is None or len(p)>best[1]): best=(gid,len(p))
    return best[0] if best else None
res={"countries":{},"groups":GROUPS}
for f in sorted(glob.glob('backend/data/*_tariffs.json')):
    iso=os.path.basename(f)[:3]
    d=json.load(open(f)); sm=d.get('summary',{})
    g=collections.defaultdict(list); gv=collections.defaultdict(list); gt=collections.defaultdict(list); lines={}
    for l in d['tariff_lines']:
        if l.get('dd_rate') is None: continue
        k=group_of(l['hs6'])
        if not k: continue
        g[k].append(l['dd_rate']); 
        if l.get('vat_rate') is not None: gv[k].append(l['vat_rate'])
        gt[k].append(l.get('total_taxes_pct') or 0)
        lines[l['hs6']]=dict(dd=l['dd_rate'],vat=l.get('vat_rate'),tot=l.get('total_taxes_pct'),desc=(l.get('description_fr') or '')[:90])
    all30=[l['dd_rate'] for l in d['tariff_lines'] if l['hs6'][:2]=='33' and l.get('dd_rate') is not None]
    res['countries'][iso]=dict(
      groups={k:dict(n=len(v),avg=round(st.mean(v),2),mx=max(v),zero=round(100*sum(1 for x in v if x==0)/len(v)),vat=(round(st.mean(gv[k]),1) if gv[k] else None),tot=round(st.mean(gt[k]),1)) for k,v in g.items()},
      ch30_avg=round(st.mean(all30),2) if all30 else None, ch30_max=max(all30) if all30 else None, ch30_zero=round(100*sum(1 for x in all30 if x==0)/len(all30)) if all30 else None,
      vat=sm.get('vat_rate_pct'), status=sm.get('data_status'), rel=sm.get('reliability'), src=sm.get('source_name'), lines=lines)
    c=res['countries'][iso]; print(iso, c['ch30_avg'], c['ch30_max'], c['ch30_zero'], {k:v['avg'] for k,v in sorted(c['groups'].items())})
# Offers categories for health lines
offers={}
for f in sorted(glob.glob('backend/data/official_preferential/*etariff*.json.gz')):
    e=json.load(gzip.open(f)); code=e['offer_code']
    o={}
    for sk,rows in e['schedules'].items():
        cat=collections.defaultdict(collections.Counter); tf=collections.defaultdict(collections.Counter); mfn=collections.defaultdict(list); exc=[]
        for r in rows:
            hs=str(r.get('hs_code','')); k=group_of(hs[:6])
            if not k: continue
            c=r.get('category') or 'UNSPEC'; cat[k][c]+=1; tf[k][str(r.get('time_frame_years'))]+=1
            try: mfn[k].append(float(r.get('mfn_rate_expression')))
            except: pass
            if c in('B','C'): exc.append((hs,c,r.get('mfn_rate_expression'),(r.get('description') or '')[:70]))
        o[sk]=dict(cat={k:dict(v) for k,v in cat.items()},tf={k:dict(v) for k,v in tf.items()},mfn={k:round(st.mean(v),1) for k,v in mfn.items() if v},exc=exc)
    offers[code]=dict(meta=dict(rev=e.get('source_revision_date'),hs=e.get('hs_version'),map=e.get('origin_schedule_map')),sch=o)
    for sk,v in o.items(): print(code,sk,{k:v['cat'][k] for k in sorted(v['cat'])}, 'B/C lines', len(v['exc']))
res['offers']=offers
json.dump(res,open(OUT+'saas_chimie.json','w'),ensure_ascii=False,indent=1)
