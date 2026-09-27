import os
import json, matplotlib, statistics as st
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib import font_manager as fm
from matplotlib.colors import LinearSegmentedColormap
from matplotlib.patches import Patch
import numpy as np
A=os.environ['RG_POLICES'] + '/'
S=(os.environ['RG_DIR'] + '/')
C=S+'charts/'; os.makedirs(C,exist_ok=True)
for f in ['DMSans-Regular','DMSans-Bold','DMSans-Medium']: fm.fontManager.addfont(A+f+'.ttf')
plt.rcParams.update({'font.family':'DMSans','font.size':9,'axes.spines.top':False,'axes.spines.right':False,'axes.edgecolor':'#9aa5a0','axes.labelcolor':'#2b3a35',
 'xtick.color':'#44524d','ytick.color':'#44524d','savefig.dpi':220,'savefig.bbox':'tight'})
G='#161820'; TEAL='#1F7A8C'; TEAL_L='#A8D5DE'; GOLD='#C8952B'; RED='#C0493D'; GREY='#C3C7D1'; GREEN='#1E8C5A'; VIO='#6B4FA0'
s=json.load(open(S+'saas_chimie.json')); cs=s['countries']
SHORT={'C01':'Chimie inorg.','C02':'Chimie org. base','C03':'Chimie fine','C04':'Engrais','C05':'Peintures','C06':'Parfums, HE','C07':'Maquillage, soins','C08':'Capillaires','C09':'Bucco-dentaire','C10':'Rasage, déo','C11':'Savons','C12':'Détergents','C13':'Javel, désinf.','C14':'Chimie divers','C15':'Plastiques prim.','C16':'Hyg. papier'}
REG={'CEDEAO (15)':'CIV','CAE/EAC (7)':'KEN','CEMAC (6)':'CMR','SACU (5)':'ZAF','Algérie':'DZA','Égypte':'EGY','Éthiopie':'ETH','Maroc':'MAR','Maurice':'MUS','Tunisie':'TUN'}
names=list(REG); gs=[g for g,_,_ in s['groups']]
M=np.array([[cs[REG[n]]['groups'].get(g,{}).get('avg',np.nan) for g in gs] for n in names],dtype=float)
cmap=LinearSegmentedColormap.from_list('t',['#F2F6F7',TEAL_L,TEAL,'#0B3C49'])
fig,ax=plt.subplots(figsize=(7.4,3.9)); im=ax.imshow(np.clip(M,0,45),cmap=cmap,aspect='auto',vmin=0,vmax=45)
for i in range(M.shape[0]):
  for j in range(M.shape[1]):
    v=M[i,j]
    if np.isnan(v): ax.text(j,i,'–',ha='center',va='center',fontsize=6.5,color='#999'); continue
    ax.text(j,i,(f'{v:.0f}*' if v>45 else f'{v:.0f}'),ha='center',va='center',fontsize=6.4,color='white' if v>22 else G)
ax.set_xticks(range(len(gs))); ax.set_xticklabels([SHORT[g] for g in gs],rotation=40,ha='right',fontsize=7)
ax.set_yticks(range(len(names))); ax.set_yticklabels(names,fontsize=7.5); ax.spines[:].set_visible(False); ax.tick_params(length=0)
cb=fig.colorbar(im,ax=ax,fraction=0.025,pad=0.01); cb.ax.tick_params(labelsize=6.5); cb.set_label('Droit NPF moyen (%)',fontsize=7)
fig.savefig(C+'k1_heat.png'); plt.close()
# k2 : charge algérienne hors TVA
T=json.load(open(S+'dza_tax.json'))
sel=['Soins de la peau','Parfums et eaux de toilette','Shampooings','Dentifrices','Savons de toilette','Détergents (autres)','Préparations tensioactives au détail','Désinfectants','Hypochlorites (javel)','Papier hygiénique','Couches','Peintures (acryliques)','Urée','Méthanol','Soude caustique solide','Polyéthylène']
R=[t for n in sel for t in T if t['lab']==n]
fig,ax=plt.subplots(figsize=(7.4,4.2)); y=np.arange(len(R)); h=0.27
ax.barh(y-h,[r['npf']['total_hors_tva'] for r in R],h,color=GREY,label='NPF (DD + DAPS + PRCT + TCS)')
ax.barh(y,[r['rcp']['total_hors_tva'] for r in R],h,color=GOLD,label='ZLECAf, réciprocité (Afrique du Sud, Cameroun, Ghana, Kenya)')
ax.barh(y+h,[r['std']['total_hors_tva'] for r in R],h,color=TEAL,label='ZLECAf, calendrier standard (Égypte, Maurice, Rwanda, Tanzanie, Tunisie)')
for i,r in enumerate(R):
    ax.text(r['npf']['total_hors_tva']+1.2,i-h,f"{r['npf']['total_hors_tva']:.0f}",va='center',fontsize=6)
    ax.text(r['std']['total_hors_tva']+1.2,i+h,f"{r['std']['total_hors_tva']:.0f}",va='center',fontsize=6,color=TEAL)
ax.set_yticks(y); ax.set_yticklabels([f"{r['lab']} (liste {r['std']['list']})" for r in R],fontsize=7); ax.invert_yaxis()
ax.set_xlabel('Charge à l\'importation hors TVA (% de la valeur CAF)'); ax.legend(frameon=False,fontsize=6.5,loc='upper center',bbox_to_anchor=(0.4,-0.12))
ax.grid(axis='x',color='#eee'); ax.set_axisbelow(True)
fig.savefig(C+'k2_dza_tax.png'); plt.close()
# k3 : exportations algériennes 2024 vs demande africaine
B=json.load(open(S+'dza_baci.json'))
prods=[('310210','Urée'),('281410','Ammoniac'),('280429','Hélium'),('290511','Méthanol'),('390120','Polyéthylène HD'),('390210','Polypropylène'),('330499','Soins de la peau'),('340220','Détergents au détail'),('961900','Couches, serviettes')]
exp=[B[h]['exportations'].get('2024',[0])[0]/1e6 for h,_ in prods]; afr=[(B[h].get('exportations_afrique',{}).get('2024',0) or 0)/1e6 for h,_ in prods]; dem=[B[h]['demande_afrique'].get('2024',0)/1e6 for h,_ in prods]
fig,ax=plt.subplots(figsize=(7.4,3.1)); x=np.arange(len(prods)); w=0.28
ax.bar(x-w,exp,w,color=TEAL_L,label='Exportations algériennes, monde'); ax.bar(x,afr,w,color=TEAL,label='dont vers l\'Afrique'); ax.bar(x+w,dem,w,color=GOLD,label='Importations africaines (hors Algérie)')
for i in range(len(prods)):
    ax.text(x[i]-w,exp[i]+25,f'{exp[i]:,.0f}'.replace(',',' '),ha='center',fontsize=5.8,rotation=90,va='bottom')
    ax.text(x[i]+w,dem[i]+25,f'{dem[i]:,.0f}'.replace(',',' '),ha='center',fontsize=5.8,rotation=90,va='bottom',color='#8A6414')
ax.set_xticks(x); ax.set_xticklabels([p for _,p in prods],fontsize=7,rotation=25,ha='right'); ax.set_ylabel('M USD (2024)'); ax.set_ylim(0,2700)
ax.legend(frameon=False,fontsize=6.8,ncol=3,loc='upper center',bbox_to_anchor=(0.5,1.13)); ax.grid(axis='y',color='#eee'); ax.set_axisbelow(True)
fig.savefig(C+'k3_dza_gap.png'); plt.close()
# k4 : offres, part des lignes B/C par segment cosmétique/hygiène
order=[('CEMAC','CEMAC'),('EGY','Égypte'),('ETH','Éthiopie'),('TUN','Tunisie'),('EAC','CAE'),('ECOWAS','CEDEAO'),('ZMB','Zambie'),('ZWE','Zimbabwe'),('MAR','Maroc')]
segs=['C06','C07','C08','C09','C10','C11','C12','C13','C16']
fig,ax=plt.subplots(figsize=(7.4,3.2))
Mx=np.full((len(order),len(segs)),np.nan); lab=[['']*len(segs) for _ in order]
for i,(o,_) in enumerate(order):
    v=list(s['offers'][o]['sch'].values())[0]['cat']
    for j,g in enumerate(segs):
        c=v.get(g)
        if not c: continue
        t=sum(c.values()); bc=c.get('B',0)+c.get('C',0); un=c.get('UNSPEC',0)
        Mx[i,j]=100*bc/t if bc else (-1 if un==t else 100*bc/t)
        lab[i][j]=f'{bc}/{t}' if bc else ('n.r.' if un==t else ('0' if not un else f'0 ({un} n.r.)'))
cm2=LinearSegmentedColormap.from_list('r',['#F4F6F8','#E9B7B0',RED])
ax.imshow(np.where(Mx<0,np.nan,Mx),cmap=cm2,vmin=0,vmax=100,aspect='auto')
for i in range(len(order)):
    for j in range(len(segs)):
        ax.text(j,i,lab[i][j] or '–',ha='center',va='center',fontsize=6.2,color=G)
ax.set_xticks(range(len(segs))); ax.set_xticklabels([SHORT[g] for g in segs],rotation=30,ha='right',fontsize=7); ax.set_yticks(range(len(order))); ax.set_yticklabels([o[1] for o in order],fontsize=7.5)
ax.spines[:].set_visible(False); ax.tick_params(length=0)
fig.savefig(C+'k4_offers.png'); plt.close()
print('ok')
# k5 : importations africaines par chapitre et part intra-africaine (OEC)
O=json.load(open(S+'oec_africa.json'))
labs=list(O); tot=[O[l]['tot']/1e9 for l in labs]; intra=[O[l]['intra']/1e9 for l in labs]
fig,ax=plt.subplots(figsize=(7.4,2.9)); x=np.arange(len(labs))
ax.bar(x,tot,color=TEAL_L,label='Importations africaines, toutes origines'); ax.bar(x,intra,color=TEAL,label='dont origine africaine')
for i,l in enumerate(labs): ax.text(i,tot[i]+0.4,f"{tot[i]:.1f}".replace('.',',')+f"\n({100*intra[i]/tot[i]:.0f} %)",ha='center',fontsize=6.4)
ax.set_xticks(x); ax.set_xticklabels(labs,rotation=25,ha='right',fontsize=7); ax.set_ylabel('Md USD (2024)'); ax.set_ylim(0,36)
ax.legend(frameon=False,fontsize=7,loc='upper left'); ax.grid(axis='y',color='#eee'); ax.set_axisbelow(True)
fig.savefig(C+'k5_africa.png'); plt.close()
# k6 : marchés de proximité de l'Algérie (OEC via module SaaS SH6 x pays)
H=json.load(open(S+'oec_hs6.json'))
mk=[('LBY','Libye'),('MAR','Maroc'),('EGY','Égypte'),('NGA','Nigeria'),('TUN','Tunisie'),('SEN','Sénégal'),('MLI','Mali'),('MRT','Mauritanie'),('CIV','Côte d\'Ivoire'),('NER','Niger')]
cols=[('3304','Maquillage, soins',VIO),('3401','Savons',GOLD),('3402','Détergents',TEAL)]
def v(k):
    r=H.get(k,{}); rows=r.get('chart_rows',[])
    return (rows[-1]['imports']/1e6) if rows else 0
mk=sorted(mk,key=lambda m:-sum(v(f'{m[0]}|{c}') for c,_,_ in cols))
fig,ax=plt.subplots(figsize=(7.4,2.8)); left=np.zeros(len(mk)); y=np.arange(len(mk))
for c,l,col in cols:
    vals=np.array([v(f'{m}|{c}') for m,_ in mk]); ax.barh(y,vals,left=left,color=col,label=l,height=0.62); left+=vals
for i,t in enumerate(left): ax.text(t+2,i,f'{t:.0f}',va='center',fontsize=6.6)
ax.set_yticks(y); ax.set_yticklabels([n for _,n in mk],fontsize=7.5); ax.invert_yaxis(); ax.set_xlabel('Importations 2024 (M USD)')
ax.legend(frameon=False,fontsize=7,ncol=3,loc='lower right'); ax.grid(axis='x',color='#eee'); ax.set_axisbelow(True)
fig.savefig(C+'k6_markets.png'); plt.close()
# k7 : Libye, importations 2024 par position (module SH x pays du SaaS)
L=[('3923','Emballages plastiques'),('9619','Couches, serviettes'),('3208','Peintures (solvant)'),('3402','Détergents'),('3105','Engrais NPK'),('3901','Polyéthylène'),('3304','Soins, maquillage'),('3305','Capillaires'),
   ('3307','Rasage, déodorants'),('3401','Savons'),('3209','Peintures (eau)'),('3808','Insecticides, désinfectants'),('3303','Parfums'),('3902','Polypropylène'),('4818','Papier hygiénique'),('3102','Engrais azotés'),('3306','Bucco-dentaire'),('2828','Javel'),('3405','Cirages, entretien')]
vals=[(n,v(f'LBY|{c}')) for c,n in L]; vals=sorted(vals,key=lambda x:-x[1])
fig,ax=plt.subplots(figsize=(7.3,3.6)); y=np.arange(len(vals))
ax.barh(y,[x[1] for x in vals],color=[VIO if any(k in x[0] for k in ('Soins','Capill','Rasage','Parfum','Bucco')) else (TEAL if any(k in x[0] for k in ('Détergent','Savon','Javel','Cirage','Insect','Couches','Papier')) else GOLD) for x in vals],height=0.66)
for i,(n,x) in enumerate(vals): ax.text(x+1,i,f'{x:.0f}',va='center',fontsize=6.5)
ax.set_yticks(y); ax.set_yticklabels([x[0] for x in vals],fontsize=7); ax.invert_yaxis(); ax.set_xlabel('Importations libyennes 2024 (M USD)')
ax.legend(handles=[Patch(color=VIO,label='Cosmétiques'),Patch(color=TEAL,label='Hygiène et entretien'),Patch(color=GOLD,label='Chimie, plastiques, engrais, peintures')],frameon=False,fontsize=7,loc='lower right')
ax.grid(axis='x',color='#eee'); ax.set_axisbelow(True)
fig.savefig(C+'k7_libye.png'); plt.close()
