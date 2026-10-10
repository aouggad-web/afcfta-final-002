import os
exec(open((os.environ['RG_DIR'] + '/charts1.py')).read().split("names=list(REG)")[0])
import datetime as dt
# g1 : liste grise GAFI, pays africains (dates de plénière)
def d(y,m): return y+(m-1)/12
L=[('Maurice',d(2020,2),d(2021,10),'retirée'),('Maroc',d(2021,2),d(2023,2),'retirée'),('Sénégal',d(2021,2),d(2023,10),'retirée'),('Burkina Faso',d(2021,2),d(2025,10),'retirée'),
   ('Soudan du Sud',d(2021,6),None,'listée'),('Mozambique',d(2022,10),d(2025,10),'retirée'),('RD Congo',d(2022,10),None,'listée'),('Afrique du Sud',d(2023,2),d(2025,10),'retirée'),('Nigeria',d(2023,2),d(2025,10),'retirée'),
   ('Cameroun',d(2023,6),None,'listée'),('Kenya',d(2024,2),None,'listée'),('Namibie',d(2024,2),d(2026,6),'retirée'),('Algérie',d(2024,10),d(2026,6),'retirée'),('Angola',d(2024,10),None,'listée'),('Côte d\'Ivoire',d(2024,10),None,'listée')]
fig,ax=plt.subplots(figsize=(7.3,3.6)); now=d(2026,9.9)
for i,(n,a,b,s) in enumerate(L):
    e=b if b else now; col=TEAL if b else RED
    if n in('Maurice','Algérie'): col=GOLD
    ax.barh(i,e-a,left=a,color=col,height=0.62)
    ax.text(e+0.06,i,('sortie ' + f"{['janv.','févr.','mars','avr.','mai','juin','juil.','août','sept.','oct.','nov.','déc.'][round((b-int(b))*12)]} {int(b)}") if b else 'toujours listé',va='center',fontsize=6.3,color=G)
ax.set_yticks(range(len(L))); ax.set_yticklabels([x[0] for x in L],fontsize=7.4); ax.invert_yaxis()
ax.set_xlim(2019.8,2027.6); ax.set_xticks(range(2020,2028)); ax.axvline(now,color='#999',lw=0.6,ls=':')
ax.grid(axis='x',color='#eceef2'); ax.set_axisbelow(True)
from matplotlib.patches import Patch
ax.legend(handles=[Patch(color=GOLD,label='Pays étudiés (Maurice, Algérie)'),Patch(color=TEAL,label='Période sous surveillance, sortie obtenue'),Patch(color=RED,label='Toujours sous surveillance (sept. 2026)')],frameon=False,fontsize=6.6,loc='upper center',bbox_to_anchor=(0.45,-0.07),ncol=3)
fig.savefig(C+'g1_gafi.png'); plt.close()
# a1 : Algérie facture d'import et couverture
yrs=['2019','2022','2023','2024','2025*']; imp=[2000,1250,718,515,500]; cov=[50,None,70,None,83]
fig,ax=plt.subplots(figsize=(7.3,2.6))
b=ax.bar(yrs,imp,color=[TEAL_L]*4+['#D7EBEF'],edgecolor=[TEAL]*5,linewidth=0.6)
for bb,v in zip(b,imp): ax.text(bb.get_x()+bb.get_width()/2,v+30,f'{v:,}'.replace(',',' '),ha='center',fontsize=7)
ax.set_ylabel('Importations de médicaments (M USD)'); ax.set_ylim(0,2400); ax.grid(axis='y',color='#eceef2'); ax.set_axisbelow(True)
ax2=ax.twinx(); xs=[0,2,4]; ax2.plot(xs,[50,70,83],color=GOLD,marker='o',lw=1.8); ax2.set_ylim(0,100); ax2.set_ylabel('Couverture locale (%)',color=GOLD_D if False else '#8A6414')
for x,v in zip(xs,[50,70,83]): ax2.text(x+0.08,v+4,f'{v} %',fontsize=7,color='#8A6414')
ax2.spines['top'].set_visible(False)
fig.savefig(C+'a1_dza_imp.png'); plt.close()
# m1 : frise Maurice
ev=[(1970,'Loi EPZ'),(1992,'Création du\nFreeport'),(1994,'Suspension du\ncontrôle\ndes changes'),(2004,'Freeport Act\nn° 43'),(2006,'Fin des\ncertificats EPZ'),(2018,'Freeport :\nIS 0 % → 3 %'),
    (2019.75,'Ratification\nZLECAf'),(2020.1,'Liste grise\nGAFI'),(2021.8,'Sortie de la\nliste grise'),(2022.2,'Sortie de la\nliste UE'),(2023.1,'Règlement\nZLECAf 1/2023\n(ZES)'),(2025.6,'Impôt minimum\nPilier 2 (QDMTT)'),(2026.45,'APE UE\napprofondi\n(conclu)'),(2027.3,'Évaluation\nESAAMLG')]
fig,ax=plt.subplots(figsize=(7.4,2.7)); n=len(ev); ax.set_xlim(-0.7,n-0.3); ax.set_ylim(-3.2,3.2); ax.axis('off')
ax.plot([-0.5,n-0.5],[0,0],color=G,lw=1)
for k,(x,t) in enumerate(ev):
    up=1 if k%2==0 else -1; h=up*1.0
    col=RED if ('GAFI' in t or 'grise' in t or 'liste UE' in t or 'ESAAMLG' in t) else (TEAL if ('ZLECAf' in t or 'ZES' in t or 'APE' in t) else GOLD)
    ax.plot([k,k],[0,h],color=col,lw=0.9); ax.plot(k,0,'o',color=col,ms=4)
    ax.text(k,h+0.15*up,(f'{int(x)}\n' if up>0 else '')+t+('' if up>0 else f'\n{int(x)}'),ha='center',va='bottom' if up>0 else 'top',fontsize=6.1,color=G,linespacing=1.15)
    ax.text(k,h+0.15*up,'',)
fig.savefig(C+'m1_mus.png'); plt.close()
