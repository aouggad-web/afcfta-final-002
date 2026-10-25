import os
import json, collections, matplotlib, statistics as st
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib import font_manager as fm
from matplotlib.colors import LinearSegmentedColormap
import numpy as np
A=os.environ['RG_POLICES'] + '/'
S=(os.environ['RG_DIR'] + '/')
C=S+'charts/'; import os; os.makedirs(C,exist_ok=True)
for f in ['DMSans-Regular','DMSans-Bold','DMSans-Medium']: fm.fontManager.addfont(A+f+'.ttf')
plt.rcParams.update({'font.family':'DMSans','font.size':9,'axes.spines.top':False,'axes.spines.right':False,
 'axes.edgecolor':'#9aa5a0','axes.labelcolor':'#2b3a35','xtick.color':'#44524d','ytick.color':'#44524d','axes.titleweight':'bold',
 'axes.titlesize':10,'axes.titlecolor':'#161820','axes.titlelocation':'left','savefig.dpi':220,'savefig.bbox':'tight'})
G='#161820'; TEAL='#1F7A8C'; TEAL_L='#A8D5DE'; GOLD='#C8952B'; RED='#C0493D'; GREY='#C3C7D1'; GREEN='#1E8C5A'
s=json.load(open(S+'saas_pharma.json')); cs=s['countries']; GR={g:n for g,n,_ in s['groups']}
SHORT={'G01':'Principes actifs','G02':'Vaccins & sang','G03':'Médic. en vrac','G04':'Médic. dosés','G05':'Pansements','G06':'Réactifs diag.','G07':'Désinfectants','G08':'Gants','G09':'Instruments','G10':'Orthopédie','G11':'Imagerie','G12':'Mobilier méd.','G13':'Hygiène','G14':'Emballages','G15':'Masques'}
REG={'CEDEAO (15)':'CIV','CAE/EAC (7)':'KEN','CEMAC (6)':'CMR','SACU (5)':'ZAF','Algérie':'DZA','Égypte':'EGY','Éthiopie':'ETH','Maroc':'MAR','Maurice':'MUS','Tunisie':'TUN'}
names=list(REG); gs=[g for g,_,_ in s['groups']]
M=np.array([[cs[REG[n]]['groups'].get(g,{}).get('avg',np.nan) for g in gs] for n in names],dtype=float)
cmap=LinearSegmentedColormap.from_list('t',['#F2F6F7',TEAL_L,TEAL,'#0B3C49'])
fig,ax=plt.subplots(figsize=(7.4,3.9))
im=ax.imshow(M,cmap=cmap,aspect='auto',vmin=0,vmax=35)
for i in range(M.shape[0]):
  for j in range(M.shape[1]):
    v=M[i,j]
    if np.isnan(v): ax.text(j,i,'–',ha='center',va='center',fontsize=6.5,color='#999'); continue
    ax.text(j,i,f'{v:.0f}' if v>=1 or v==0 else f'{v:.1f}',ha='center',va='center',fontsize=6.6,color='white' if v>17 else G)
ax.set_xticks(range(len(gs))); ax.set_xticklabels([SHORT[g] for g in gs],rotation=40,ha='right',fontsize=7)
ax.set_yticks(range(len(names))); ax.set_yticklabels(names,fontsize=7.5)
ax.spines[:].set_visible(False); ax.tick_params(length=0)
cb=fig.colorbar(im,ax=ax,fraction=0.025,pad=0.01); cb.ax.tick_params(labelsize=6.5); cb.set_label('Droit NPF moyen (%)',fontsize=7)
fig.savefig(C+'p1_heat.png'); plt.close()
# p2 : escalade principes actifs vs médicaments vs seringues
cty=[('Algérie','DZA'),('Maroc','MAR'),('Égypte','EGY'),('Tunisie','TUN'),('Éthiopie','ETH'),('CEMAC','CMR'),('CEDEAO','CIV'),('CAE/EAC','KEN'),('SACU','ZAF'),('Maurice','MUS')]
def line(iso,h):
    l=cs[iso]['lines'].get(h); return l['dd'] if l else np.nan
series=[('Antibiotiques (2941)',lambda i: st.mean([cs[i]['lines'][h]['dd'] for h in cs[i]['lines'] if h.startswith('2941')]) if any(h.startswith('2941') for h in cs[i]['lines']) else np.nan,GREY),
        ('Médicaments dosés (3004)',lambda i: cs[i]['groups']['G04']['avg'],TEAL),
        ('Seringues (901831)',lambda i: line(i,'901831'),GOLD),
        ('Gants chirurgicaux (4015)',lambda i: cs[i]['groups'].get('G08',{}).get('avg',np.nan),RED)]
fig,ax=plt.subplots(figsize=(7.3,3.0)); x=np.arange(len(cty)); w=0.2
for k,(lab,f,col) in enumerate(series):
    v=[f(i) for _,i in cty]; b=ax.bar(x+(k-1.5)*w,v,w,color=col,label=lab)
    for bb,vv in zip(b,v):
        if not np.isnan(vv) and vv>0: ax.text(bb.get_x()+bb.get_width()/2,vv+0.6,f'{vv:.0f}',ha='center',va='bottom',fontsize=5.8,color=G,rotation=90)
ax.set_xticks(x); ax.set_xticklabels([c for c,_ in cty],fontsize=7.5); ax.set_ylabel('Droit NPF (%)'); ax.set_ylim(0,34)
ax.legend(frameon=False,fontsize=7,ncol=4,loc='upper center',bbox_to_anchor=(0.5,1.12)); ax.grid(axis='y',color='#eceef2'); ax.set_axisbelow(True)
fig.savefig(C+'p2_escal.png'); plt.close()
# p3 : demande africaine 300490 (BACI) top importateurs
B=json.load(open(S+'dza_baci_pharma.json'))
imp=B['300490']['importateurs_afrique_2024'][:14]
fig,ax=plt.subplots(figsize=(7.3,3.0))
names3=[r[1].replace('Democratic Republic of the Congo','RD Congo') for r in imp]; vals=[r[2]/1e6 for r in imp]
FR={'Egypt':'Égypte','South Africa':'Afrique du Sud','Morocco':'Maroc','Kenya':'Kenya','Nigeria':'Nigeria','Tunisia':'Tunisie','Ethiopia':'Éthiopie','Libya':'Libye','Cote d\'Ivoire':'Côte d\'Ivoire','Ghana':'Ghana','Tanzania':'Tanzanie','Senegal':'Sénégal','Uganda':'Ouganda','Sudan':'Soudan','Cameroon':'Cameroun','Zambia':'Zambie','Angola':'Angola','Mozambique':'Mozambique','Zimbabwe':'Zimbabwe','Botswana':'Botswana','Namibia':'Namibie','Mali':'Mali','Burkina Faso':'Burkina Faso','RD Congo':'RD Congo','Benin':'Bénin','Madagascar':'Madagascar','Rwanda':'Rwanda','Mauritius':'Maurice','Malawi':'Malawi','Guinea':'Guinée','Niger':'Niger','Mauritania':'Mauritanie','Togo':'Togo'}
names3=[FR.get(n,n) for n in names3]
b=ax.bar(range(len(vals)),vals,color=[TEAL if i<6 else TEAL_L for i in range(len(vals))])
for bb,v in zip(b,vals): ax.text(bb.get_x()+bb.get_width()/2,v+25,f'{v:,.0f}'.replace(',',' '),ha='center',fontsize=6.3)
ax.set_xticks(range(len(vals))); ax.set_xticklabels(names3,rotation=35,ha='right',fontsize=7.2); ax.set_ylabel('M USD (2024)')
ax.grid(axis='y',color='#eceef2'); ax.set_axisbelow(True)
fig.savefig(C+'p3_demand.png'); plt.close()
json.dump({'imp300490':imp,'tot':B['300490']['demande_afrique']},open(S+'demand.json','w'))
# p4 : exportations algériennes de médicaments (BACI)
yrs=[str(y) for y in range(2016,2025)]
tot=[sum(B[h]['exportations'].get(y,[0])[0] for h in ['300410','300450','300490'])/1e6 for y in yrs]
afr=[sum((B[h].get('exportations_afrique',{}).get(y,0) or 0) for h in ['300410','300450','300490'])/1e6 for y in yrs]
fig,ax=plt.subplots(figsize=(7.3,2.5))
ax.bar(yrs,tot,color=TEAL_L,label='Exportations de médicaments dosés (SH 300410, 300450, 300490), total')
ax.bar(yrs,afr,color=TEAL,label='dont vers l\'Afrique')
for i,(t,a) in enumerate(zip(tot,afr)): ax.text(i,t+0.4,f'{t:.1f}',ha='center',fontsize=6.8)
ax.set_ylabel('M USD'); ax.legend(frameon=False,fontsize=7,loc='upper left'); ax.grid(axis='y',color='#eceef2'); ax.set_axisbelow(True)
fig.savefig(C+'p4_dza_exp.png'); plt.close()
print('tot',[round(t,2) for t in tot],'afr',[round(a,2) for a in afr])
