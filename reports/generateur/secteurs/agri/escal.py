import os
import json,statistics as st
S=(os.environ['RG_DIR'] + '/')
REG={'CEDEAO':'CIV','CAE (EAC)':'KEN','CEMAC':'CMR','SACU':'ZAF','Algérie':'DZA','Égypte':'EGY','Éthiopie':'ETH','Maroc':'MAR','Maurice':'MUS','Tunisie':'TUN'}
CHAINS=[('Cacao',[('Fèves','1801'),('Pâte/beurre','1803'),('Chocolat','1806')]),
 ('Café',[('Vert','090111'),('Torréfié','090121'),('Soluble','2101')]),
 ('Blé',[('Grain','1001'),('Farine','1101'),('Pâtes','1902')]),
 ('Lait',[('Lait frais','0401'),('Poudre','0402'),('Fromage','0406')]),
 ('Tomate',[('Fraîche','0702'),('Concentré','2002')]),
 ('Sucre',[('Canne/brut','1701'),('Confiserie','1704')]),
 ('Arachide/huile',[('Graines','1202'),('Huile','1508')]),
 ('Noix de cajou',[('Brute en coque','080131'),('Décortiquée','080132')]),
]
out={}
for reg,iso in REG.items():
    d=json.load(open(f'backend/data/{iso}_tariffs.json'))
    L=[l for l in d['tariff_lines'] if l.get('dd_rate') is not None]
    out[reg]={}
    for ch,stages in CHAINS:
        out[reg][ch]=[]
        for lab,p in stages:
            v=[l['dd_rate'] for l in L if l['hs6'].startswith(p)]
            out[reg][ch].append((lab,p,round(st.mean(v),1) if v else None))
    print(reg, {c:[x[2] for x in s] for c,s in out[reg].items()})
json.dump(out,open(S+'escal.json','w'),ensure_ascii=False)
