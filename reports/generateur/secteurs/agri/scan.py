import os
import json, datetime, sys, logging, collections, statistics as st
logging.disable(logging.WARNING); sys.path.insert(0,'.')
exec(open((os.environ['RG_DIR'] + '/targets.py')).read().split('TG=[')[0])
exec(open((os.environ['RG_DIR'] + '/analyze.py')).read().split('res={"countries":{}}')[0].split("OUT=")[0]+"\n"+open((os.environ['RG_DIR'] + '/analyze.py')).read().split('SECTORS = ')[1].join(['SECTORS = ','']) if False else '')
SECTORS=[("S01",["01","02","1601","1602"]),("S02",["03","1603","1604","1605"]),("S03",["04"]),("S04",["06"]),("S05",["07"]),("S06",["08"]),("S07",["09"]),("S08",["10","11","23"]),("S09",["12","15"]),("S10",["17"]),("S11",["18"]),("S12",["19","21"]),("S13",["20"]),("S14",["22"]),("S15",["24"])]
def sector_of(hs):
    best=None
    for sid,pre in SECTORS:
        for p in pre:
            if hs.startswith(p) and (best is None or len(p)>best[1]): best=(sid,len(p))
    return best[0] if best else None
CASES=[('MAR','EGY','Maroc — liste P1 (ex. Égypte)'),('MAR','GHA','Maroc — liste P2 (ex. Ghana)'),('EGY','TUN','Égypte — groupe 5 ans (ex. Tunisie)'),('EGY','GHA','Égypte — groupe 10 ans (ex. Ghana)'),
       ('KEN','GHA','Kenya — Annexe 1 (ex. Ghana)'),('ZAF','GHA','SACU — partenaire actif (ex. Ghana)'),('DZA','TUN','Algérie — calendrier standard (ex. Tunisie)'),('DZA','GHA','Algérie — réciprocité (ex. Ghana)')]
res={}
for d,o,lab in CASES:
    T.pop(d,None); npf(d,'01')
    rows=[]
    for hs6,l in T[d].items():
        if hs6[:2]>'24' or l.get('dd_rate') is None: continue
        subs=l.get('sub_positions') or [{'code':hs6,'dd':l['dd_rate']}]
        s=subs[0]; code=s['code']; n=s.get('dd', l['dd_rate'])
        try:
            if d=='DZA': r,src=compute_dza_zlecaf_rate(code,o,n,D)
            elif d=='EGY': r,src=compute_egy_zlecaf_rate(code,o,n,D)
            elif d=='KEN':
                r,src=compute_ken_zlecaf_rate(code.ljust(8,'0') if len(code)<8 else code,o,D)
                if r is None: r=n
            else:
                x=resolve_official_preferential_rate(d,code,o,as_of_year=2026)
                r = n if (x is None or x.get('ad_valorem_rate_pct') is None) else x['ad_valorem_rate_pct']
        except Exception as e:
            r=n
        if n is None or r is None: continue
        r=min(r,n)
        rows.append(dict(hs=code,hs6=hs6,desc=(l.get('description_fr') or '')[:70],npf=n,pref=r,m=round(n-r,2),sec=sector_of(hs6)))
    red=[x for x in rows if x['m']>0]
    bysec=collections.defaultdict(lambda:[0,0,[]])
    for x in rows:
        b=bysec[x['sec']]; b[0]+=1; b[1]+= (x['m']>0); b[2].append(x['m'])
    res[f'{d}|{o}']=dict(label=lab,n=len(rows),n_red=len(red),share=round(100*len(red)/len(rows),1),avg_npf=round(st.mean(x['npf'] for x in rows),1),avg_pref=round(st.mean(x['pref'] for x in rows),1),
        top=sorted(red,key=lambda x:-x['m'])[:40],bysec={k:(v[0],v[1],round(st.mean(v[2]),1)) for k,v in bysec.items() if k})
    print(lab, len(rows), 'réduites', len(red), f"{100*len(red)/len(rows):.0f}%", 'NPF moy', res[f'{d}|{o}']['avg_npf'], '→', res[f'{d}|{o}']['avg_pref'])
json.dump(res,open((os.environ['RG_DIR'] + '/scan.json'),'w'),ensure_ascii=False,indent=1)
