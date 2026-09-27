import json, glob, os, statistics as st, gzip, collections
OUT=(os.environ['RG_DIR'] + '/')
SECTORS = [
 ("S01","Animaux vivants & viandes",["01","02","1601","1602"]),
 ("S02","Pêche & aquaculture",["03","1603","1604","1605"]),
 ("S03","Lait, œufs & miel",["04"]),
 ("S04","Horticulture & fleurs coupées",["06"]),
 ("S05","Légumes, tubercules & légumineuses",["07"]),
 ("S06","Fruits & fruits à coque",["08"]),
 ("S07","Café, thé & épices",["09"]),
 ("S08","Céréales, minoterie & alim. bétail",["10","11","23"]),
 ("S09","Oléagineux & huiles végétales",["12","15"]),
 ("S10","Sucre & confiserie",["17"]),
 ("S11","Cacao & chocolat",["18"]),
 ("S12","Produits céréaliers & prép. alimentaires",["19","21"]),
 ("S13","Conserves de fruits & légumes",["20"]),
 ("S14","Boissons",["22"]),
 ("S15","Tabac",["24"]),
]
def sector_of(hs):
    best=None
    for sid,_,pre in SECTORS:
        for p in pre:
            if hs.startswith(p) and (best is None or len(p)>best[1]): best=(sid,len(p))
    return best[0] if best else None
res={"countries":{}}
for f in sorted(glob.glob('backend/data/*_tariffs.json')):
    iso=os.path.basename(f)[:3]
    d=json.load(open(f))
    lines=[l for l in d['tariff_lines'] if l.get('hs6','')[:2]<='24' and l.get('dd_rate') is not None]
    allines=[l for l in d['tariff_lines'] if l.get('dd_rate') is not None]
    ag=[l['dd_rate'] for l in lines]; nag=[l['dd_rate'] for l in allines if l['hs6'][:2]>'24']
    sec=collections.defaultdict(list); sect=collections.defaultdict(list)
    for l in lines:
        s=sector_of(l['hs6'])
        if s: sec[s].append(l['dd_rate']); sect[s].append(l.get('total_taxes_pct') or 0)
    top=sorted(lines,key=lambda l:-l['dd_rate'])[:5]
    sm=d.get('summary',{})
    res['countries'][iso]={
      "n_ag":len(ag),"avg_ag":round(st.mean(ag),2) if ag else None,"avg_nag":round(st.mean(nag),2) if nag else None,
      "max_ag":max(ag) if ag else None,"zero_share":round(100*sum(1 for x in ag if x==0)/len(ag),1) if ag else None,
      "peak_share":round(100*sum(1 for x in ag if x>=20)/len(ag),1) if ag else None,
      "vat":sm.get('vat_rate_pct'),"other":sm.get('other_taxes_pct'),
      "avg_total_ag":round(st.mean([l.get('total_taxes_pct') or 0 for l in lines]),1) if lines else None,
      "sectors":{s:round(st.mean(v),1) for s,v in sec.items()},
      "sectors_total":{s:round(st.mean(v),1) for s,v in sect.items()},
      "status":sm.get('data_status'),"reliability":sm.get('reliability'),"source":sm.get('source_name'),
      "top":[(l['hs6'],(l.get('description_fr') or '')[:60],l['dd_rate']) for l in top],
      "distinct_rates":sorted(set(ag)),
    }
    print(iso, res['countries'][iso]['n_ag'], res['countries'][iso]['avg_ag'], res['countries'][iso]['avg_nag'], res['countries'][iso]['max_ag'], sm.get('data_status'), sm.get('reliability'), (sm.get('source_name') or '')[:50], res['countries'][iso]['distinct_rates'][:12])
# RoO
ro=json.load(open('backend/data/zlecaf_rules_of_origin.json'))
roo={"chapters":{c:ro['chapters'][c] for c in ro['chapters'] if c<='24'},
     "headings":{h:v for h,v in ro['headings'].items() if h[:2]<='24'},
     "subheadings":{h:v for h,v in ro['subheadings'].items() if h[:2]<='24'}}
res['roo']=roo
# Offers
offers={}
for f in sorted(glob.glob('backend/data/official_preferential/*.json.gz')):
    e=json.load(gzip.open(f)); code=e.get('offer_code') or os.path.basename(f).split('_')[0]
    sch=e.get('schedules',{})
    o={"meta":{k:e.get(k) for k in ['legal_effect_status','source_revision_date','hs_version','origin_schedule_map','collected_at']}}
    for sk,rows in (sch.items() if isinstance(sch,dict) else []):
        cat=collections.Counter(); catsec=collections.defaultdict(collections.Counter); tf=collections.Counter(); mfn=[]
        for r in rows:
            hs=str(r.get('hs_code',''))
            if hs[:2]>'24' or not hs[:2].isdigit(): continue
            c=r.get('category') or 'UNSPEC'; cat[c]+=1
            s=sector_of(hs[:6]); 
            if s: catsec[s][c]+=1
            tf[r.get('time_frame_years')]+=1
            try: mfn.append(float(r.get('mfn_rate_expression')))
            except: pass
        allcat=collections.Counter((r.get('category') or 'UNSPEC') for r in rows)
        o[sk]={"ag_cat":dict(cat),"all_cat":dict(allcat),"tf":{str(k):v for k,v in tf.items()},"sectors":{k:dict(v) for k,v in catsec.items()},"avg_mfn_ag":round(st.mean(mfn),2) if mfn else None}
    offers[code+"|"+os.path.basename(f)]=o
    print(code, {k:(v.get('ag_cat'),v.get('tf'),v.get('avg_mfn_ag')) for k,v in o.items() if k!='meta'})
res['offers']=offers
res['status_matrix']=json.load(open('backend/data/official_preferential/afcfta_status_matrix_2026-09-13.json'))
res['sectors_def']=SECTORS
json.dump(res,open(OUT+'saas_stats.json','w'),ensure_ascii=False,indent=1)
