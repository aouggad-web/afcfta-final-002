import json, glob, os, statistics as st, gzip, collections
OUT=(os.environ['RG_DIR'] + '/')
GROUPS=[
 ("G01","Principes actifs & intermédiaires",["2936","2937","2938","2939","2940","2941"]),
 ("G02","Sang, vaccins, immunologiques",["3001","3002"]),
 ("G03","Médicaments en vrac",["3003"]),
 ("G04","Médicaments dosés (conditionnés)",["3004"]),
 ("G05","Pansements & articles pharmaceutiques",["3005","3006"]),
 ("G06","Réactifs de diagnostic",["3822"]),
 ("G07","Désinfectants & antiseptiques",["380894","220710","220890"]),
 ("G08","Gants & consommables caoutchouc",["401511","401512","401519","4014"]),
 ("G09","Instruments & appareils médicaux",["9018","9019","9020"]),
 ("G10","Orthopédie, implants & prothèses",["9021"]),
 ("G11","Imagerie & radiologie",["9022"]),
 ("G12","Mobilier médical",["9402"]),
 ("G13","Hygiène (serviettes, couches)",["9619"]),
 ("G14","Emballages pharmaceutiques",["701090","701010","392330","392350","392310"]),
 ("G15","Masques & textiles médicaux",["630790","621010"]),
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
    all30=[l['dd_rate'] for l in d['tariff_lines'] if l['hs6'][:2]=='30' and l.get('dd_rate') is not None]
    res['countries'][iso]=dict(
      groups={k:dict(n=len(v),avg=round(st.mean(v),2),mx=max(v),zero=round(100*sum(1 for x in v if x==0)/len(v)),vat=(round(st.mean(gv[k]),1) if gv[k] else None),tot=round(st.mean(gt[k]),1)) for k,v in g.items()},
      ch30_avg=round(st.mean(all30),2) if all30 else None, ch30_max=max(all30) if all30 else None, ch30_zero=round(100*sum(1 for x in all30 if x==0)/len(all30)) if all30 else None,
      vat=sm.get('vat_rate_pct'), status=sm.get('data_status'), rel=sm.get('reliability'), src=sm.get('source_name'), lines=lines)
    c=res['countries'][iso]; print(iso, c['ch30_avg'], c['ch30_max'], c['ch30_zero'], {k:v['avg'] for k,v in sorted(c['groups'].items())}, 'vat3004', c['groups'].get('G04',{}).get('vat'))
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
json.dump(res,open(OUT+'saas_pharma.json','w'),ensure_ascii=False,indent=1)
