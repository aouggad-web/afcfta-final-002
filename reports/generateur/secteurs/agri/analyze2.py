import json, glob, os, statistics as st, gzip, collections, re
S=(os.environ['RG_DIR'] + '/')
exec(open(S+'analyze.py').read().split('res={"countries":{}}')[0])  # SECTORS, sector_of
def num(x):
    try: return float(str(x).replace('%','').strip())
    except: return None
margins={}
for f in sorted(glob.glob('backend/data/official_preferential/*_etariff_*.json.gz')):
    e=json.load(gzip.open(f)); code=e['offer_code']
    sk=sorted(e['schedules'])[0]; rows=e['schedules'][sk]
    agg=collections.defaultdict(lambda:{'mfn':[],'y2026':[],'end':[]})
    for r in rows:
        hs=str(r['hs_code'])
        if hs[:2]>'24': continue
        m=num(r.get('mfn_rate_expression')); ann=r.get('annual_rate_expressions') or {}
        yrs=sorted(int(y) for y in ann if str(y).isdigit())
        if m is None: continue
        if r.get('category')=='A' and yrs:
            y=min(6,yrs[-1]); v=num(ann[str(y)]); ve=num(ann[str(yrs[-1])])
        else:
            v=m; ve=m   # B/C/non spécifié: pas de réduction en 2026 (hypothèse prudente)
        if v is None: continue
        v=min(v,m); ve=min(ve,m) if ve is not None else ve
        s=sector_of(hs[:6])
        for k in [s,'ALL']:
            if k: agg[k]['mfn'].append(m); agg[k]['y2026'].append(v); agg[k]['end'].append(ve if ve is not None else v)
    margins[code]={k:{'mfn':round(st.mean(v['mfn']),1),'y2026':round(st.mean(v['y2026']),1),'end':round(st.mean(v['end']),1),'n':len(v['mfn'])} for k,v in agg.items()}
    print(code, margins[code]['ALL'])
# ZAF: SARS general vs AfCFTA column
z=json.load(gzip.open('backend/data/official_preferential/ZAF_afcfta_2026-08-06.json.gz'))
zaf_af={l['hs_code'][:6]:l.get('ad_valorem_rate_pct') for l in z['lines'] if l.get('ad_valorem_rate_pct') is not None}
zt=json.load(open('backend/data/ZAF_tariffs.json'))
agg=collections.defaultdict(lambda:{'mfn':[],'y2026':[]})
for l in zt['tariff_lines']:
    hs=l['hs6']
    if hs[:2]>'24' or hs not in zaf_af or l.get('dd_rate') is None: continue
    s=sector_of(hs)
    for k in [s,'ALL']:
        if k: agg[k]['mfn'].append(l['dd_rate']); agg[k]['y2026'].append(zaf_af[hs])
margins['SACU (ZAF)']={k:{'mfn':round(st.mean(v['mfn']),1),'y2026':round(st.mean(v['y2026']),1),'end':None,'n':len(v['mfn'])} for k,v in agg.items()}
print('ZAF',margins['SACU (ZAF)']['ALL'])
# FAOSTAT leaders
d=json.load(open('data/json/production_africaine.json'))
a=[r for r in d['agri_faostat']]
yrs=collections.Counter(r['year'] for r in a)
def leaders(label, year=2023, n=5):
    rows=[r for r in a if r['commodity_label']==label and r['year']==year and r['value']]
    tot=sum(r['value'] for r in rows)
    rows=sorted(rows,key=lambda r:-r['value'])[:n]
    return {'total':tot,'top':[(r['country_iso3'],r['country_name'],r['value']) for r in rows]}
COMMS=['Cattle meat','Chicken meat','Cattle milk','Hen eggs','Natural honey','Cassava','Yam','Onions','Tomatoes','Potatoes','Cashew nuts','Bananas','Oranges','Avocados','Mangoes','Dates','Coffee','Tea','Vanilla','Ginger','Maize (corn)','Rice','Wheat','Sorghum','Millet','Sesame','Groundnuts','Oil palm','Soybeans','Olive oil','Sugarcane','Raw cane or beet sugar (centrifugal only)','Cocoa beans','Tobacco','Wine','Beer of barley, malted','Shea nuts','Cotton lint, ginned','Grapes','Pineapples']
fao={c:{y:leaders(c,y) for y in (2019,2023)} for c in COMMS}
for c in COMMS: print(c, round(fao[c][2023]['total']/1e6,2), [(t[0],round(t[2]/1e6,2)) for t in fao[c][2023]['top'][:4]])
wdi=[r for r in d['value_added_macro'] if r['indicator_code']=='NV.AGR.TOTL.ZS']
va={}
for r in wdi:
    if r['value'] is not None and (r['country_iso3'] not in va or r['year']>va[r['country_iso3']][0]): va[r['country_iso3']]=(r['year'],r['value'],r['country_name'])
print(sorted(va.items(),key=lambda x:-x[1][1])[:10], len(va))
ind=collections.Counter(r['indicator_code'] for r in d['value_added_macro']); print(ind)
atr=json.load(open('data/json/afreximbank_atr2026.json'))
json.dump({'margins':margins,'fao':fao,'agva':va,'atr':atr,'proj':d['agri_projections']},open(S+'saas_stats2.json','w'),ensure_ascii=False,indent=1)
