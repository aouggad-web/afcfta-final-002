import os
import json
S=(os.environ['RG_DIR'] + '/')
# Modèle SaaS : TEU = 175 + 0,255 x milles nautiques ; FEU = 1,5 x TEU (logistics_fees_data)
def feu(nm): return 1.5*(175+0.255*nm)
# distances (nm) : Alger via SaaS ; autres : distances portuaires usuelles (hypothèses, via Gibraltar ou Cap en 2026)
routes={'Nouakchott':{'Algérie (Alger)':1746,'Turquie (Mersin)':3350,'Émirats (Jebel Ali, via le Cap)':9700,'Chine (Shanghai, via le Cap)':11900},
        'Tripoli':{'Algérie (Alger)':588,'Turquie (Mersin)':1050,'Émirats (Jebel Ali, via le Cap)':11000,'Chine (Shanghai, via le Cap)':13200},
        'Dakar':{'Algérie (Alger)':1977,'Turquie (Mersin)':3580,'Émirats (Jebel Ali, via le Cap)':9500,'Chine (Shanghai, via le Cap)':11700}}
war={'Émirats (Jebel Ali, via le Cap)':3000,'Chine (Shanghai, via le Cap)':0,'Turquie (Mersin)':0,'Algérie (Alger)':0}
days={'Algérie (Alger)':10,'Turquie (Mersin)':14,'Émirats (Jebel Ali, via le Cap)':32,'Chine (Shanghai, via le Cap)':40}
T=22; P=1100; V=T*P; r=0.12
out={}
for dest,rs in routes.items():
    out[dest]={}
    for o,nm in rs.items():
        f=feu(nm)+war[o]; fin=V*r*(days[o]*1.5)/365; ins=V*0.004
        tot=f+fin+ins
        out[dest][o]=dict(nm=nm,freight=round(f),fin=round(fin),ins=round(ins),per_t=round(tot/T),pct=round(100*tot/V,1))
        print(dest,o,out[dest][o])
# Urée : netback Europe vs Afrique (hypothèses paramétriques MACF)
# intensité : hypothèse 2,0 tCO2e/t d'urée (ammoniac amont inclus) ; prix ETS 70-100 EUR ; part soumise au MACF : 2,5 % (2026), 48,5 % (2030), 100 % (2034)
cb=[]
for share,yr in [(0.025,2026),(0.485,2030),(1.0,2034)]:
    for p in (70,100):
        cb.append(dict(year=yr,share=share,ets=p,cost=round(2.0*p*share,1)))
out['cbam']=cb
json.dump(out,open(S+'cases.json','w'),ensure_ascii=False,indent=1); print(cb)
