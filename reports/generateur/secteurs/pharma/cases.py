import os
import json
S=(os.environ['RG_DIR'] + '/')
out={}
# Cas 1 : intrants — API importé en Algérie (hors TVA récupérable)
npf=0.17; std=0.02; rcp=0.08
out['be_std']=round(100*((1+npf)/(1+std)-1),1); out['be_rcp']=round(100*((1+npf)/(1+rcp)-1),1)
# protection effective : sortie 3004 (DD5 + PRCT2 = 7 %), intrant API
erp=[]
for a in [0.2,0.35,0.5,0.6]:
    erp.append(dict(a=a, npf=round(100*(0.07-a*npf)/(1-a),1), std=round(100*(0.07-a*std)/(1-a),1), rcp=round(100*(0.07-a*rcp)/(1-a),1)))
out['erp']=erp
# Cas 2 : génériques vers Dakar, Algérie vs Inde, conteneur 40' de 300 000 USD
V=300000; r=0.12
def landed(freight, days, ins, safety):
    fin=V*r*(days+safety)/365
    return dict(freight=freight, ins=round(V*ins), fin=round(fin), total=round(freight+V*ins+fin))
ind=landed(4000,32,0.0035,16); dza=landed(1430,12,0.0025,6)
out['c2']=dict(V=V,ind=ind,dza=dza,adv=ind['total']-dza['total'],adv_pct=round(100*(ind['total']-dza['total'])/V,2))
# sensibilité : fret Inde x jours
sens=[]
for f in [3000,4000,5000,6000]:
    row=[]
    for d in [25,32,40]:
        i=landed(f,d,0.0035,d/2); row.append(round(100*(i['total']-dza['total'])/V,2))
    sens.append((f,row))
out['c2_sens']=sens
# valeur par conteneur : sensibilité à V
out['c2_V']=[(v, round(100*(landed(4000,32,0.0035,16)['total']-landed(1430,12,0.0025,6)['total'])/300000*300000/v,2)) for v in [100000,300000,600000]]
json.dump(out,open(S+'cases.json','w'),indent=1); print(json.dumps(out,indent=1))
