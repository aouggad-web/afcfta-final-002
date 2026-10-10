import os
import json, collections, matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib import font_manager as fm
import numpy as np
S=(os.environ['RG_DIR'] + '/')
C=S+'charts/'; import os; os.makedirs(C,exist_ok=True)
for f in ['DMSans-Regular','DMSans-Bold','DMSans-Medium']: fm.fontManager.addfont(os.environ['RG_POLICES'] + '/'+f+'.ttf')
plt.rcParams.update({'font.family':'DMSans','font.size':9,'axes.spines.top':False,'axes.spines.right':False,
 'axes.edgecolor':'#9aa5a0','axes.labelcolor':'#2b3a35','xtick.color':'#44524d','ytick.color':'#44524d','axes.titleweight':'bold',
 'axes.titlesize':10,'axes.titlecolor':'#161820','axes.titlelocation':'left','savefig.dpi':220,'savefig.bbox':'tight'})
G='#161820'; G2='#1E8C5A'; G3='#9ED9BC'; GOLD='#C8952B'; SAND='#EFE6D2'; RED='#C0493D'; GREY='#C3C7D1'
s1=json.load(open(S+'saas_stats.json')); s2=json.load(open(S+'saas_stats2.json')); esc=json.load(open(S+'escal.json'))
SEC={sid:name for sid,name,_ in s1['sectors_def']}
REG={'CEDEAO (15)':'CIV','CAE/EAC (7)':'KEN','CEMAC (6)':'CMR','SACU (5)':'ZAF','Algérie':'DZA','Égypte':'EGY','Éthiopie':'ETH','Maroc':'MAR','Maurice':'MUS','Tunisie':'TUN','Somalie':'SOM'}
cs=s1['countries']
# 1 ag vs non-ag
fig,ax=plt.subplots(figsize=(7.2,3.2))
names=list(REG); ag=[cs[REG[n]]['avg_ag'] for n in names]; nag=[cs[REG[n]]['avg_nag'] for n in names]
# Egypt: exclude ch22 peaks for readability
import statistics as st
d=json.load(open('backend/data/EGY_tariffs.json')); eg=[l['dd_rate'] for l in d['tariff_lines'] if l['hs6'][:2]<='24' and l['hs6'][:2]!='22' and l.get('dd_rate') is not None]
ag[names.index('Égypte')]=round(st.mean(eg),1)
x=np.arange(len(names)); w=0.38
b1=ax.bar(x-w/2,ag,w,color=G2,label='Produits agricoles (SH 01-24)'); b2=ax.bar(x+w/2,nag,w,color=GREY,label='Produits non agricoles (SH 25-97)')
for b,v in zip(b1,ag): ax.text(b.get_x()+b.get_width()/2,v+0.6,f'{v:.1f}',ha='center',fontsize=7,color=G)
ax.set_xticks(x); ax.set_xticklabels(names,rotation=30,ha='right'); ax.set_ylabel('Droit de douane moyen simple (%)')
ax.legend(frameon=False,fontsize=8,loc='upper left',ncol=2); ax.set_ylim(0,40); ax.grid(axis='y',color='#e6ebe8'); ax.set_axisbelow(True)
fig.savefig(C+'c1_ag_vs_nag.png'); plt.close()
json.dump({'egy_ex22':ag[names.index('Égypte')]},open(S+'egy.json','w'))
# 2 heatmap regimes x sectors
secs=[s for s,_,_ in s1['sectors_def']]
M=np.array([[cs[REG[n]]['sectors'].get(s,np.nan) for s in secs] for n in names],dtype=float)
M=np.clip(M,0,60)
from matplotlib.colors import LinearSegmentedColormap
cmap=LinearSegmentedColormap.from_list('g',['#F4F1E6',GOLD,'#9C4A2F'])
fig,ax=plt.subplots(figsize=(7.4,4.1))
im=ax.imshow(M,cmap=cmap,aspect='auto',vmin=0,vmax=50)
for i in range(M.shape[0]):
  for j in range(M.shape[1]):
    raw=cs[REG[names[i]]]['sectors'].get(secs[j])
    if raw is None: continue
    ax.text(j,i,f'{raw:.0f}' if raw<100 else f'{raw:.0f}',ha='center',va='center',fontsize=6.5,color='white' if raw>32 else '#2b3a35')
ax.set_xticks(range(len(secs))); ax.set_xticklabels([SEC[s] for s in secs],rotation=55,ha='right',fontsize=7)
ax.set_yticks(range(len(names))); ax.set_yticklabels(names,fontsize=7.5)
ax.spines[:].set_visible(False); ax.tick_params(length=0)
cb=fig.colorbar(im,ax=ax,fraction=0.025,pad=0.01); cb.ax.tick_params(labelsize=7); cb.set_label('% (plafonné à 50 pour l\'échelle)',fontsize=7)
fig.savefig(C+'c2_heatmap.png'); plt.close()
# 3 total landed tax burden by country (39, hors DZA)
b2=json.load(open(S+'burden2.json'))
items=sorted([(k,v[0],v[1]) for k,v in b2.items() if v],key=lambda x:-x[1])
fig,ax=plt.subplots(figsize=(7.4,3.0))
ax.bar([k for k,_,_ in items],[d for _,_,d in items],color=G2,label='Droit de douane (DD)')
ax.bar([k for k,_,_ in items],[v-d for _,v,d in items],bottom=[d for _,_,d in items],color=GOLD,alpha=0.85,label='Prélèvements + TVA (taux normal)')
for i,(k,v,d) in enumerate(items): ax.text(i,v+0.8,f'{v:.0f}',ha='center',fontsize=5.8,color='#44524d')
ax.set_ylabel('% de la valeur CAF'); plt.xticks(rotation=90,fontsize=7); ax.grid(axis='y',color='#e6ebe8'); ax.set_axisbelow(True)
ax.legend(frameon=False,fontsize=7.5,loc='upper right'); ax.set_ylim(0,72)
fig.savefig(C+'c3_total_burden.png'); plt.close()
# 4 preferential margins
mg=s2['margins']; order=['TUN','CEMAC','MAR','ZWE','EAC','ZMB','ECOWAS','EGY','SACU (ZAF)']
lab={'TUN':'Tunisie','CEMAC':'CEMAC','MAR':'Maroc','ETH':'Éthiopie','ZWE':'Zimbabwe','EAC':'CAE/EAC','ZMB':'Zambie','ECOWAS':'CEDEAO','EGY':'Égypte','SACU (ZAF)':'SACU (col. AfCFTA)'}
fig,ax=plt.subplots(figsize=(7.2,3.3)); y=np.arange(len(order))
for i,k in enumerate(order):
    a=mg[k]['ALL']; ax.plot([a['y2026'],a['mfn']],[i,i],color=GREY,lw=2.5,zorder=1)
    ax.scatter(a['mfn'],i,color=GREY,s=40,zorder=2); ax.scatter(a['y2026'],i,color=G2,s=46,zorder=3)
    if a.get('end') is not None and a['end']<a['y2026']: ax.scatter(a['end'],i,color=GOLD,marker='D',s=26,zorder=3)
    ax.text(a['mfn']+0.8,i,f"{a['mfn']:.1f} → {a['y2026']:.1f}",va='center',fontsize=7,color='#44524d')
ax.set_yticks(y); ax.set_yticklabels([lab[k] for k in order]); ax.invert_yaxis(); ax.set_xlim(0,44)
ax.set_xlabel('Droit moyen sur les lignes agricoles (%)')
from matplotlib.lines import Line2D
ax.legend(handles=[Line2D([],[],marker='o',ls='',color=GREY,label='NPF de base'),Line2D([],[],marker='o',ls='',color=G2,label='Taux ZLECAf 2026 (année 6)'),Line2D([],[],marker='D',ls='',color=GOLD,label='Fin de calendrier')],frameon=False,fontsize=7.5,loc='lower right')
ax.grid(axis='x',color='#e6ebe8'); ax.set_axisbelow(True)
fig.savefig(C+'c4_margins.png'); plt.close()
# 5 offer categories stacked
of=s1['offers']; rows=[]
for k,v in of.items():
    code=k.split('|')[0]
    if code=='ZAF': continue
    sch=[x for x in v if x!='meta'][0]; c=v[sch]['ag_cat']; tot=sum(c.values())
    rows.append((lab.get(code,code),100*c.get('A',0)/tot,100*c.get('B',0)/tot,100*c.get('C',0)/tot,100*c.get('UNSPEC',0)/tot))
rows.sort(key=lambda r:-r[1])
fig,ax=plt.subplots(figsize=(7.2,2.9)); y=np.arange(len(rows)); left=np.zeros(len(rows))
for idx,(nm,col) in enumerate([('Catégorie A (libéralisée)',G),('Catégorie B (sensible)',GOLD),('Catégorie C (exclue)',RED),('Non spécifiée / non publiée',GREY)]):
    vals=np.array([r[idx+1] for r in rows]); ax.barh(y,vals,left=left,color=col,label=nm,height=0.62)
    for yi,(l,v) in enumerate(zip(left,vals)):
        if v>=6: ax.text(l+v/2,yi,f'{v:.0f}%',ha='center',va='center',fontsize=7,color='white' if col in (G,RED) else '#2b3a35')
    left+=vals
ax.set_yticks(y); ax.set_yticklabels([r[0] for r in rows]); ax.invert_yaxis(); ax.set_xlim(0,100); ax.set_xlabel('% des lignes tarifaires agricoles (SH 01-24) de l\'offre')
ax.legend(frameon=False,fontsize=7,ncol=4,loc='upper center',bbox_to_anchor=(0.5,-0.2))
fig.savefig(C+'c5_categories.png'); plt.close()
json.dump(rows,open(S+'cats.json','w'),ensure_ascii=False)
# 6 RoO distribution
ro=s1['roo']; cnt=collections.Counter()
for lvl in ['chapters','headings','subheadings']:
    for k,v in ro[lvl].items(): cnt[(lvl,v['code'])]+=1
print(cnt)
rules=collections.Counter()
# Effective rule by chapter (24 ch) share
chap=collections.Counter(v['code'] for v in ro['chapters'].values())
head=collections.Counter(v['code'] for v in ro['headings'].values())
sub=collections.Counter(v['code'] for v in ro['subheadings'].values())
json.dump({'chap':chap,'head':head,'sub':sub},open(S+'roo_counts.json','w'))
print(chap,head,sub)
lbl={'WO':'Entièrement obtenu (WO)','CTH':'Changement de position (CTH)','CTSH':'Changement de sous-position','VA60':'Valeur non orig. ≤ 60 %','VA40':'Valeur ≤ 40 %','VA50':'Valeur ≤ 50 %','CC':'Changement de chapitre','SP':'Processus spécifique','YTB':'En négociation'}
allc=head+sub
fig,axs=plt.subplots(1,2,figsize=(7.4,2.7))
for ax,(t,c) in zip(axs,[('Règle de chapitre (24 chapitres)',chap),(f'Règles spécifiques par position/sous-position ({sum(allc.values())})',allc)]):
    it=c.most_common(); ax.barh([lbl.get(k,k) for k,_ in it],[v for _,v in it],color=[G if k=='WO' else (GOLD if k.startswith('VA') else G2) for k,_ in it])
    ax.invert_yaxis(); ax.set_title(t,fontsize=8.5)
    for i,(_,v) in enumerate(it): ax.text(v+0.3,i,str(v),va='center',fontsize=7)
    ax.tick_params(axis='y',labelsize=7)
fig.tight_layout(); fig.savefig(C+'c6_roo.png'); plt.close()
# 7 ATR intra-african trade top 15
atr=s2['atr']['intra_african_trade_by_country']; top=sorted(atr.items(),key=lambda kv:-kv[1]['intra_african_2025_busd'])[:15]
fig,ax=plt.subplots(figsize=(7.2,3.0))
ax.bar([k for k,_ in top],[v['intra_african_2025_busd'] for _,v in top],color=[GOLD if i==0 else G2 for i in range(15)])
for i,(_,v) in enumerate(top): ax.text(i,v['intra_african_2025_busd']+0.5,f"{v['intra_african_2025_busd']:.1f}",ha='center',fontsize=7)
ax.set_ylabel('Mds USD (2025)'); ax.grid(axis='y',color='#e6ebe8'); ax.set_axisbelow(True)
fig.savefig(C+'c7_atr.png'); plt.close()
# 8 ag VA % GDP
va=s2['agva']; it=sorted(va.items(),key=lambda kv:-kv[1][1])
fig,ax=plt.subplots(figsize=(7.4,2.9))
ax.bar([k for k,_ in it],[v[1] for _,v in it],color=[G if v[1]>=25 else (G2 if v[1]>=15 else G3) for _,v in it])
plt.xticks(rotation=90,fontsize=6.3); ax.set_ylabel('% du PIB'); ax.grid(axis='y',color='#e6ebe8'); ax.set_axisbelow(True)
ax.axhline(np.median([v[1] for _,v in it]),color=GOLD,lw=1,ls='--'); ax.text(len(it)-1,np.median([v[1] for _,v in it])+1,f"médiane {np.median([v[1] for _,v in it]):.1f} %",ha='right',fontsize=7,color='#8a6d1f')
fig.savefig(C+'c8_agva.png'); plt.close()
# 9 escalation small multiples (4 chains) for selected regimes
chains=['Cacao','Café','Blé','Lait','Tomate','Sucre']
regs=['CEDEAO','CAE (EAC)','CEMAC','SACU','Algérie','Égypte','Maroc','Tunisie']
fig,axs=plt.subplots(2,3,figsize=(7.4,4.4),sharey=False)
for ax,ch in zip(axs.flat,chains):
    for r,col in zip(regs,[G,G2,G3,GOLD,RED,'#6B5B95','#3E6E8E','#9C4A2F']):
        st_=esc[r][ch]; xs=[i for i,s in enumerate(st_) if s[2] is not None]; ys=[s[2] for s in st_ if s[2] is not None]
        ax.plot(xs,ys,marker='o',ms=3,lw=1.3,color=col,label=r)
    ax.set_xticks(range(len(esc['CEDEAO'][ch]))); ax.set_xticklabels([s[0] for s in esc['CEDEAO'][ch]],fontsize=7)
    ax.set_title(ch,fontsize=8.5); ax.grid(axis='y',color='#eef2ef'); ax.tick_params(axis='y',labelsize=7)
h,l=axs[0,0].get_legend_handles_labels(); fig.legend(h,l,ncol=8,fontsize=6.8,frameon=False,loc='lower center',bbox_to_anchor=(0.5,-0.02))
fig.tight_layout(rect=(0,0.05,1,1)); fig.savefig(C+'c9_escalation.png'); plt.close()
print('ok')
