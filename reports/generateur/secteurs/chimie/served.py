import os
import json, sys, collections, statistics as st
sys.path.insert(0,os.environ['RG_DIR'])
exec(open((os.environ['RG_RACINE'] + '/secteurs/agri/targets.py')).read().split('TG=[')[0])
from analyze_groups import group_of, GROUPS
DESTS=['DZA','EGY','KEN','MAR','ZAF','TUN']
ORIG=['DZA','EGY','MAR','TUN','ZAF','KEN','MUS','GHA','NGA','SEN','TZA','CIV']
if os.environ.get('RG_PAYS_FOCUS','DZA') not in ORIG: ORIG.append(os.environ['RG_PAYS_FOCUS'])
res={}
import gzip
MARO=json.load(gzip.open('data/official_preferential/MAR_afcfta_etariff_2026-09-13.json.gz'))['schedules']['1']
for d in DESTS:
    try: npf(d,'30')
    except Exception as e: print('skip',d,e); continue
    for o in ORIG:
        if o==d: continue
        rows=[]
        for hs6,l in T[d].items():
            g=group_of(hs6)
            if not g: continue
            subs=l.get('sub_positions') or [{'code':hs6,'dd':l.get('dd_rate')}]
            code=subs[0]['code']; n=subs[0].get('dd', l.get('dd_rate'))
            if n is None: n=l.get('dd_rate')
            if n is None: continue
            try:
                if d=='DZA': r,src=compute_dza_zlecaf_rate(code,o,n,D)
                elif d=='EGY': r,src=compute_egy_zlecaf_rate(code,o,n,D)
                elif d=='KEN':
                    dec=implementation_decision('KEN',o)
                    if not dec['applied']: r=n
                    else:
                        r,src=compute_ken_zlecaf_rate(code.ljust(8,'0') if len(code)<8 else code,o,D)
                        if r is None: r=n
                elif d=='MAR':
                    oc=[x['hs_code'] for x in MARO if x['hs_code'].startswith(hs6)]
                    vals=[];mf=[]
                    for c in oc:
                        x=resolve_official_preferential_rate(d,c,o,as_of_year=2026)
                        rr=[y for y in MARO if y['hs_code']==c][0]; mf.append(float(rr['mfn_rate_expression']))
                        vals.append(float(rr['mfn_rate_expression']) if (x is None or x.get('ad_valorem_rate_pct') is None) else x['ad_valorem_rate_pct'])
                    if vals: n=round(st.mean(mf),2); r=round(st.mean(vals),2)
                    else: r=n
                else:
                    x=resolve_official_preferential_rate(d,code,o,as_of_year=2026)
                    r = n if (x is None or x.get('ad_valorem_rate_pct') is None) else x['ad_valorem_rate_pct']
            except Exception as e: r=n
            if r is None: r=n
            r=min(r,n); rows.append((hs6,code,g,n,r))
        by=collections.defaultdict(list)
        for x in rows: by[x[2]].append(x)
        res[f'{d}|{o}']={g:dict(n=len(v),npf=round(st.mean(x[3] for x in v),2),pref=round(st.mean(x[4] for x in v),2),red=sum(1 for x in v if x[4]<x[3])) for g,v in by.items()}
        a=[x for x in rows if x[2]=='G04']
        print(d,o,{g:(v['npf'],v['pref']) for g,v in sorted(res[f'{d}|{o}'].items()) if g in ('C01','C04','C07','C11','C12','C15')})
json.dump(res,open((os.environ['RG_DIR'] + '/served.json'),'w'),indent=0)
