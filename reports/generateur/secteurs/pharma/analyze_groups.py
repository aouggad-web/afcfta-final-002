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
