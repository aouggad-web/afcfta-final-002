import os
import json, sys, datetime, collections, logging
logging.disable(logging.WARNING)
sys.path.insert(0,os.environ['RG_REPO'] + '/backend')
from services.zlecaf_schedule_dza import compute_dza_zlecaf_rate, daps_exempt, tariff_list, ACTIVE_PARTNERS, RECIPROCITY_PARTNERS
R=os.environ['RG_REPO'] + '/'
L=json.load(open(R+'data/dza/import_levies.json')); V=json.load(open(R+'data/dza/vat_measures.json')); E=json.load(open(R+'data/dza/excise_measures.json'))
DAPS={h:float(r['rate'].rstrip('%')) for r in L['daps'] for h in r['hs_codes_explicit']}
TCS=set(h for r in L['tcs'] for h in r['hs_codes_explicit'])
VATR={h:float(r['rate'].rstrip('%')) for r in V['vat_rates'] if r['rate']!='19.0%' for h in r['hs_codes_explicit']}
TIC={h:float(r['rate'].rstrip('%')) for r in E['excise_rates'] for h in r['hs_codes_explicit']}
T={l['hs6']:l for l in json.load(open(R+'backend/data/DZA_tariffs.json'))['tariff_lines']}
D=datetime.date(2026,9,27)
def dza_tax(hs6, origin=None):
    l=T[hs6]; sp=(l.get('sub_positions') or [{'code':hs6}])[0]; code=sp['code']; dd=l['dd_rate'] if l.get('dd_rate') is not None else sp.get('dd')
    zl=None
    if origin:
        zl,_=compute_dza_zlecaf_rate(code,origin,dd,D)
    ddr=zl if zl is not None else dd
    daps=DAPS.get(hs6,0.0)
    if origin and daps_exempt(code,origin): daps=0.0
    prct=2.0; tcs=3.0 if hs6 in TCS else 0.0; tic=TIC.get(hs6,0.0); vat=VATR.get(hs6,19.0)
    base=100+ddr+daps+prct+tcs
    ticv=base*tic/100
    tva=(base+ticv)*vat/100
    tot=ddr+daps+prct+tcs+ticv+tva
    return dict(code=code,list=tariff_list(code),dd=ddr,daps=daps,prct=prct,tcs=tcs,tic=round(ticv,2),vat=vat,tva=round(tva,2),total=round(tot,1),total_hors_tva=round(tot-tva,1))
if __name__=='__main__':
    rows=[('090240','Thé noir'),('090210','Thé vert'),('090111','Café vert'),('040221','Lait en poudre'),('040510','Beurre'),('040690','Fromages'),('080390','Bananes'),('080132','Cajou'),('080410','Dattes'),('020230','Viande bovine congelée'),('020714','Poulet congelé'),('070190','Pommes de terre'),('071340','Lentilles'),('071320','Pois chiches'),('100630','Riz'),('100199','Blé'),('170114','Sucre brut'),('170199','Sucre raffiné'),('151190','Huile de palme'),('151219','Huile de tournesol'),('180100','Fèves de cacao'),('180310','Pâte de cacao'),('230990','Aliments du bétail'),('030389','Poisson congelé'),('080510','Oranges'),('200290','Concentré de tomate'),('190219','Pâtes'),('170490','Confiserie')]
    out=[]
    for hs,lab in rows:
        npf=dza_tax(hs); s=dza_tax(hs,'TZA'); rcp=dza_tax(hs,'KEN')
        out.append(dict(hs=hs,lab=lab,npf=npf,std=s,rcp=rcp))
        print(f"{hs} {lab:22} liste {s['list']} | NPF: DD {npf['dd']} DAPS {npf['daps']} TCS {npf['tcs']} TIC {npf['tic']} TVA{npf['vat']} tot {npf['total']} (hors TVA {npf['total_hors_tva']}) | std {s['total_hors_tva']} | récipr {rcp['total_hors_tva']}")
    json.dump(out,open((os.environ['RG_DIR'] + '/dza_tax.json'),'w'),ensure_ascii=False,indent=1)
    c=collections.Counter(); 
    for h,r in DAPS.items():
        if h[:2]<='24': c[(h[:2],r)]+=1
    print(sorted(c.items()))
