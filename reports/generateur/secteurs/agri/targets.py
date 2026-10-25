import os
import json, datetime, sys, logging
logging.disable(logging.WARNING)
sys.path.insert(0,'.')
from services.zlecaf_schedule_dza import compute_dza_zlecaf_rate
from services.zlecaf_schedule_egy import compute_egy_zlecaf_rate
from services.zlecaf_schedule_ken import compute_ken_zlecaf_rate
from services.official_preferential_rates import resolve_official_preferential_rate
from services.zlecaf_implementation_registry import implementation_decision
S=(os.environ['RG_DIR'] + '/')
T={}
def npf(dest,hs):
    if dest not in T: T[dest]={l['hs6']:l for l in json.load(open(f'data/{dest}_tariffs.json'))['tariff_lines']}
    l=T[dest].get(hs[:6]); 
    if not l: return None, None
    subs=[s for s in l.get('sub_positions',[]) if s['code'].startswith(hs)]
    return (subs[0]['dd'] if subs else l['dd_rate']), (subs[0]['code'] if subs else hs[:6])
D=datetime.date(2026,9,27)
def pref(o,d,hs):
    n,code=npf(d,hs)
    if d=='DZA': r,src=compute_dza_zlecaf_rate(code,o,n,D)
    elif d=='EGY': r,src=compute_egy_zlecaf_rate(code,o,n,D)
    elif d=='KEN':
        dec=implementation_decision('KEN',o)
        if not dec['applied']: r,src=n,'origine non admise'
        else:
            r,src=compute_ken_zlecaf_rate(code.ljust(8,'0') if len(code)<8 else code,o,D)
            if r is None: r,src=n,'hors barème cat. A (B/C/composite) — NPF'
    else:
        x=resolve_official_preferential_rate(d,code,o,as_of_year=2026)
        if x is None: r,src=n,'non servi (hors liste A / origine non admise) — NPF'
        else: r,src=x.get('ad_valorem_rate_pct'),(x.get('rate_expression') or '')+' '+str(x.get('source_column',''))
    return n,r,src,code
TG=[('EGY','MAR','190219','Pâtes alimentaires'),('TUN','MAR','190219','Pâtes alimentaires'),('EGY','ZAF','190219','Pâtes alimentaires'),('EGY','KEN','190219','Pâtes alimentaires'),
('EGY','MAR','200290','Concentré de tomate'),('EGY','DZA','200290','Concentré de tomate'),('EGY','KEN','200290','Concentré de tomate'),('EGY','ZAF','200290','Concentré de tomate'),
('EGY','MAR','080410','Dattes'),('TUN','MAR','080410','Dattes'),('KEN','DZA','090240','Thé noir'),('UGA','EGY','090111','Café vert'),('UGA','MAR','090111','Café vert'),('ETH','ZAF','090111','Café vert'),
('GHA','KEN','180690','Chocolat'),('GHA','DZA','180690','Chocolat'),('GHA','ZAF','180632','Chocolat'),('GHA','MAR','180690','Chocolat'),('CIV','KEN','080132','Amandes de cajou'),('CIV','MAR','080132','Amandes de cajou'),
('CIV','KEN','151190','Huile de palme raffinée'),('GHA','KEN','151190','Huile de palme raffinée'),('MWI','EGY','170199','Sucre raffiné'),('MWI','KEN','240120','Tabac écôté'),('KEN','ZAF','060311','Roses'),('ETH','MAR','060311','Roses'),
('MAR','EGY','160413','Sardines en conserve'),('GHA','KEN','160414','Thon en conserve'),('UGA','EGY','040210','Lait en poudre'),('KEN','DZA','040221','Lait en poudre'),('EGY','KEN','080510','Oranges'),
('NGA','ZAF','210410','Bouillons'),('EGY','ZAF','170490','Confiserie'),('TCD','MAR','010229','Bovins vivants'),('ZMB','KEN','100590','Maïs'),('EGY','KEN','190531','Biscuits'),('TUN','DZA','190219','Pâtes'),('ZAF','EGY','200870','Pêches au sirop'),('KEN','EGY','080440','Avocats'),('KEN','ZAF','080440','Avocats'),('KEN','DZA','080440','Avocats')]
out=[]
for o,d,hs,lab in TG:
    try: n,r,src,code=pref(o,d,hs)
    except Exception as e: n,r,src,code=None,None,f'ERR {e}',hs
    out.append(dict(o=o,d=d,hs=hs,code=code,lab=lab,npf=n,pref=r,src=src))
    print(f'{o}->{d} {code:10} {lab:22} NPF {n} -> {r} | {src[:90]}')
json.dump(out,open(S+'targets.json','w'),ensure_ascii=False,indent=1)
