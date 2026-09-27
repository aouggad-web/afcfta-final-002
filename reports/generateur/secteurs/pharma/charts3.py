import os
exec(open((os.environ['RG_DIR'] + '/charts1.py')).read().split("names=list(REG)")[0])
def d(y,m,dd=15): return y+(m-1)/12+(dd-1)/365
rows=[('Mali',[(d(2025,4,1),d(2026,7,10),'rupture')],[(d(2025,4,1),'Drone abattu,\nrappels','left'),(d(2025,4,7),''),(d(2026,7,10),'Ambassadeurs, espace\naérien rouvert','right'),(d(2026,8,24),''),(d(2026,9,9),'Commission mixte\n(1re depuis 2016)','left')]),
      ('Niger',[(d(2025,4,6),d(2026,2,12),'rupture')],[(d(2026,2,12),'Retour des\nambassadeurs','right'),(d(2026,2,15),''),(d(2026,3,23),'~20 accords dont\nsanté (Niamey)','left')]),
      ('Burkina Faso',[(d(2025,4,6),d(2026,2,15),'rupture2'),(d(2026,2,15),d(2026,9,27),'partiel')],[(d(2026,2,15),'Visite Arkab,\n~88 M USD')])]
fig,ax=plt.subplots(figsize=(7.4,2.6))
for i,(n,spans,ev) in enumerate(rows):
    y=len(rows)-1-i
    for a,b,k in spans:
        ax.barh(y,b-a,left=a,color=RED if k.startswith('rupture') else '#E9B7B0',height=0.34)
        if k=='rupture': ax.barh(y,d(2026,9,27)-b,left=b,color=TEAL,height=0.34)
    for j,e in enumerate(ev):
        x,t=e[0],e[1]; ha=e[2] if len(e)>2 else 'center'
        ax.plot(x,y,'o',color=G,ms=3.5,zorder=3)
        if t: ax.text(x+(0.01 if ha=='left' else (-0.01 if ha=='right' else 0)),y+0.26,t,fontsize=5.8,ha=ha,va='bottom',color=G,linespacing=1.1)
ax.set_yticks(range(len(rows))); ax.set_yticklabels([r[0] for r in rows][::-1],fontsize=8)
ax.set_xlim(d(2025,3,1),d(2026,10,20)); ax.set_ylim(-0.5,2.95)
ax.set_xticks([d(2025,4,1),d(2025,7,1),d(2025,10,1),d(2026,1,1),d(2026,4,1),d(2026,7,1),d(2026,10,1)]); ax.set_xticklabels(['avr. 25','juil. 25','oct. 25','janv. 26','avr. 26','juil. 26','oct. 26'],fontsize=7)
from matplotlib.patches import Patch
ax.legend(handles=[Patch(color=RED,label='Rupture (ambassadeurs rappelés)'),Patch(color='#E9B7B0',label='Réchauffement sans normalisation confirmée'),Patch(color=TEAL,label='Relations normalisées')],frameon=False,fontsize=6.5,ncol=3,loc='upper center',bbox_to_anchor=(0.5,-0.12))
ax.grid(axis='x',color='#eceef2'); ax.set_axisbelow(True)
fig.savefig(C+'s1_sahel.png'); plt.close()
