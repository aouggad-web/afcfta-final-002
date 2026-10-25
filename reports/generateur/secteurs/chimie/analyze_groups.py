import json, glob, os, statistics as st, gzip, collections
OUT=(os.environ['RG_DIR'] + '/')
GROUPS=[
 ("C01","Chimie inorganique de base",["28"]),
 ("C02","Chimie organique de base",["29%02d"%i for i in range(1,16)]),
 ("C03","Chimie organique fine & intermédiaires",["29%02d"%i for i in range(16,36)]+["2942"]),
 ("C04","Engrais",["31"]),
 ("C05","Peintures, vernis, encres, colorants",["32"]),
 ("C06","Huiles essentielles & parfums",["3301","3302","3303"]),
 ("C07","Maquillage & soins de la peau",["3304"]),
 ("C08","Produits capillaires",["3305"]),
 ("C09","Hygiène bucco-dentaire",["3306"]),
 ("C10","Rasage, déodorants & bain",["3307"]),
 ("C11","Savons",["3401"]),
 ("C12","Détergents & tensioactifs",["3402"]),
 ("C13","Javel, désinfectants & entretien des surfaces",["2828","3808","3405"]),
 ("C14","Produits chimiques divers",["38"]),
 ("C15","Matières plastiques primaires",["39%02d"%i for i in range(1,15)]),
 ("C16","Articles d'hygiène (papier, couches, brosses)",["4818","9619","960321"]),
]
def group_of(hs):
    best=None
    for gid,_,pre in GROUPS:
        for p in pre:
            if hs.startswith(p) and (best is None or len(p)>best[1]): best=(gid,len(p))
    return best[0] if best else None
