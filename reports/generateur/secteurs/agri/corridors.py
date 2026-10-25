import os
exec(open((os.environ['RG_DIR'] + '/charts.py')).read().split('# 1 ag vs non-ag')[0])
E={'GHA': 10, 'KEN': 10, 'CMR': 10, 'ZAF': 10, 'NAM': 10, 'NGA': 10, 'SWZ': 10, 'BWA': 10, 'MAR': 5, 'RWA': 5, 'TZA': 5, 'MUS': 5, 'TUN': 5, 'DZA': 5, 'BDI': 5, 'LSO': 5, 'MWI': 5, 'GMB': 5, 'UGA': 5}
M={'BDI': 5, 'BFA': 5, 'CAF': 5, 'COD': 5, 'COM': 5, 'DZA': 5, 'EGY': 5, 'ETH': 5, 'GIN': 5, 'GMB': 5, 'GNB': 5, 'LSO': 5, 'MLI': 5, 'MRT': 5, 'MUS': 5, 'MWI': 5, 'NER': 5, 'RWA': 5, 'SEN': 5, 'SLE': 5, 'SYC': 5, 'TCD': 5, 'TGO': 5, 'TUN': 5, 'TZA': 5, 'UGA': 5, 'ZMB': 5, 'BWA': 10, 'CIV': 10, 'CMR': 10, 'COG': 10, 'CPV': 10, 'GAB': 10, 'GHA': 10, 'GNQ': 10, 'KEN': 10, 'NAM': 10, 'NGA': 10, 'SWZ': 10, 'ZAF': 10}
K=['BFA', 'CAF', 'CIV', 'CMR', 'COD', 'COG', 'CPV', 'EGY', 'GAB', 'GHA', 'GIN', 'GMB', 'GNB', 'GNQ', 'LBR', 'MDG', 'MLI', 'MRT', 'MUS', 'MWI', 'NER', 'NGA', 'SEN', 'SLE', 'SYC', 'TCD', 'TGO', 'ZMB']
Z=['BDI', 'CMR', 'DZA', 'EGY', 'ETH', 'GHA', 'GMB', 'KEN', 'MAR', 'NGA', 'RWA', 'SLE', 'TUN', 'UGA']
A=['CMR', 'EGY', 'GHA', 'KEN', 'MUS', 'RWA', 'TUN', 'TZA', 'ZAF']
dest=[('Égypte',{k:(1 if v==5 else 2) for k,v in E.items()}),('Maroc',{k:(1 if v==5 else 2) for k,v in M.items()}),('Kenya (CAE)',{k:3 for k in K}),('SACU',{k:3 for k in Z}),('Algérie',{k:3 for k in A})]
origins=sorted(set().union(*[set(d) for _,d in dest]),key=lambda o:(-sum(1 for _,d in dest if o in d),o))
import numpy as np
Mx=np.zeros((len(dest),len(origins)))
for i,(_,d) in enumerate(dest):
    for j,o in enumerate(origins): Mx[i,j]=d.get(o,0)
from matplotlib.colors import ListedColormap
cm=ListedColormap(['#F3F4F6','#1E8C5A','#9ED9BC','#C8952B'])
fig,ax=plt.subplots(figsize=(7.5,2.35))
ax.imshow(Mx,cmap=cm,vmin=0,vmax=3,aspect='auto')
ax.set_xticks(range(len(origins))); ax.set_xticklabels(origins,rotation=90,fontsize=6.3)
ax.set_yticks(range(len(dest))); ax.set_yticklabels([d for d,_ in dest],fontsize=7.5)
ax.set_xticks(np.arange(-.5,len(origins),1),minor=True); ax.set_yticks(np.arange(-.5,len(dest),1),minor=True)
ax.grid(which='minor',color='white',lw=1.2); ax.tick_params(which='both',length=0); ax.spines[:].set_visible(False)
cnt=[int(sum(1 for _,d in dest if o in d)) for o in origins]
for j,c in enumerate(cnt): ax.text(j,-0.85,str(c),ha='center',fontsize=6,color='#5E6273')
from matplotlib.patches import Patch
ax.legend(handles=[Patch(color='#1E8C5A',label='Admis — calendrier 5 ans'),Patch(color='#9ED9BC',label='Admis — calendrier 10 ans'),Patch(color='#C8952B',label='Admis (liste unique)')],
          frameon=False,fontsize=6.8,ncol=3,loc='upper center',bbox_to_anchor=(0.5,-0.32))
fig.savefig(C+'c10_corridors.png'); plt.close()
print([(o,c) for o,c in zip(origins,cnt)][:15], len(origins))
