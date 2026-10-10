import os
exec(open((os.environ['RG_DIR'] + '/charts.py')).read().split('# 1 ag vs non-ag')[0])
# fix heatmap
names=list(REG); secs=[s for s,_,_ in s1['sectors_def']]
M=np.array([[cs[REG[n]]['sectors'].get(s,np.nan) for s in secs] for n in names],dtype=float)
from matplotlib.colors import LinearSegmentedColormap
cmap=LinearSegmentedColormap.from_list('g',['#F7F3EA','#E2C27A','#C8952B','#8E3B2E']); cmap.set_bad('#FFFFFF')
fig,ax=plt.subplots(figsize=(7.4,4.1))
im=ax.imshow(np.ma.masked_invalid(np.clip(M,0,50)),cmap=cmap,aspect='auto',vmin=0,vmax=50)
for i in range(M.shape[0]):
  for j in range(M.shape[1]):
    raw=M[i,j]
    if np.isnan(raw): ax.text(j,i,'n.d.',ha='center',va='center',fontsize=6,color='#8a948f'); continue
    ax.text(j,i,'>50*' if raw>50 else f'{raw:.0f}',ha='center',va='center',fontsize=6.5,color='white' if raw>32 else '#2b3a35')
ax.set_xticks(range(len(secs))); ax.set_xticklabels([SEC[s] for s in secs],rotation=55,ha='right',fontsize=7)
ax.set_yticks(range(len(names))); ax.set_yticklabels(names,fontsize=7.5); ax.spines[:].set_visible(False); ax.tick_params(length=0)
cb=fig.colorbar(im,ax=ax,fraction=0.025,pad=0.01); cb.ax.tick_params(labelsize=7); cb.set_label('Droit de douane moyen (%)',fontsize=7)
fig.savefig(C+'c2_heatmap.png'); plt.close()
fao=s2['fao']; mg=s2['margins']
PROD={'S01':('Cattle meat','Viande bovine','kt',1e3),'S03':('Cattle milk','Lait de vache','Mt',1e6),'S05':('Cassava','Manioc','Mt',1e6),
'S06':('Cashew nuts','Noix de cajou (brute)','kt',1e3),'S07':('Coffee','Café vert','kt',1e3),'S08':('Maize (corn)','Maïs','Mt',1e6),
'S09':('Palm oil','Huile de palme brute','kt',1e3),'S10':('Raw cane or beet sugar (centrifugal only)','Sucre brut','kt',1e3),'S11':('Cocoa beans','Fèves de cacao','kt',1e3),
'S12':('Wheat','Blé (intrant)','Mt',1e6),'S13':('Tomatoes','Tomates','Mt',1e6),'S14':('Beer','Bière d\'orge','Mt',1e6),'S15':('Tobacco','Tabac brut','kt',1e3),
'S02':None,'S04':None}
ORD=['TUN','CEMAC','MAR','ZWE','EAC','ZMB','ECOWAS','EGY','SACU (ZAF)']
lab={'TUN':'Tunisie','CEMAC':'CEMAC','MAR':'Maroc','ETH':'Éthiopie','ZWE':'Zimbabwe','EAC':'CAE/EAC','ZMB':'Zambie','ECOWAS':'CEDEAO','EGY':'Égypte','SACU (ZAF)':'SACU'}
out={}
for sid,name,_ in s1['sectors_def']:
    fig,axs=plt.subplots(1,2,figsize=(7.4,2.55),gridspec_kw={'width_ratios':[1,1.15]})
    ax=axs[0]; p=PROD[sid]
    F24=json.load(open(S+'fao2024.json'))
    FR={'South Africa':'Afrique du Sud','Zimbabwe':'Zimbabwe','United Republic of Tanzania':'Tanzanie','Chad':'Tchad','Ethiopia':'Éthiopie','Sudan':'Soudan','Kenya':'Kenya','Egypt':'Égypte','Uganda':'Ouganda','Nigeria':'Nigeria','Democratic Republic of the Congo':'RD Congo','Ghana':'Ghana','Angola':'Angola','Mozambique':'Mozambique',"CÃ´te d'Ivoire":"Côte d'Ivoire",'Benin':'Bénin','Burkina Faso':'Burkina Faso','Central African Republic':'Centrafrique','Guinea':'Guinée','Cameroon':'Cameroun','Gabon':'Gabon','Eswatini':'Eswatini','Zambia':'Zambie','Sierra Leone':'Sierra Leone','Algeria':'Algérie','Morocco':'Maroc','Tunisia':'Tunisie','Malawi':'Malawi'}
    if p:
        c,lb,u,div=p; f=F24[sid]
        top=[x for x in f['top'] if not (sid=='S07' and x[0] in ('Central African Republic','Guinea'))][:5]
        ks=[FR.get(x[0],x[0]) for x in top]; v=[x[1]/div for x in top]
        ax.barh(ks,v,color=GOLD,height=0.6); ax.invert_yaxis()
        for i,val in enumerate(v): ax.text(val*1.01,i,(f'{val:,.1f}' if val<100 else f'{val:,.0f}').replace(',',' ').replace('.',','),va='center',fontsize=7)
        share=f" · {100*f['total']/f['world']:.0f} % du monde" if f.get('world') else ''
        ax.set_title(f"{lb} — top 5 africain {f['year']} ({u}){share}",fontsize=8)
        ax.set_xlim(0,max(v)*1.28); ax.tick_params(labelsize=7)
        out[sid]={'label':lb,'unit':u,'year':f['year'],'tot':f['total']/div,'tot19':f['tot19']/div,'world_share':(100*f['total']/f['world'] if f.get('world') else None),'top':[(FR.get(x[0],x[0]),x[1]/div) for x in top]}
    else:
        # tariff peaks: sector avg by country (40), top 8
        vals=sorted([(k,v['sectors'].get(sid)) for k,v in cs.items() if v['sectors'].get(sid) is not None],key=lambda x:-x[1])
        # dedupe by regime representative
        seen=set(); rows=[]
        for k,v in vals:
            if v in seen and k not in ('DZA','EGY','ETH','MAR','MUS','TUN'): continue
            seen.add(v); rows.append((k,v))
        rows=rows[:7]
        ax.barh([r[0] for r in rows],[r[1] for r in rows],color=RED,height=0.6); ax.invert_yaxis()
        for i,(_,val) in enumerate(rows): ax.text(val+0.5,i,f'{val:.1f}',va='center',fontsize=7)
        ax.set_title('Droits NPF moyens les plus élevés (%)',fontsize=8.3); ax.tick_params(labelsize=7)
        out[sid]={'peaks':rows}
    ax=axs[1]; rows=[(lab[k],mg[k][sid]['mfn'],mg[k][sid]['y2026']) for k in ORD if sid in mg[k]]
    rows.sort(key=lambda r:-r[1]); y=np.arange(len(rows))
    ax.barh(y-0.2,[r[1] for r in rows],0.38,color=GREY,label='NPF'); ax.barh(y+0.2,[r[2] for r in rows],0.38,color=G2,label='ZLECAf 2026')
    for i,r in enumerate(rows): ax.text(r[1]+0.4,i-0.2,f'{r[1]:.0f}',va='center',fontsize=6.3,color='#44524d'); ax.text(r[2]+0.4,i+0.2,f'{r[2]:.0f}',va='center',fontsize=6.3,color=G)
    ax.set_yticks(y); ax.set_yticklabels([r[0] for r in rows],fontsize=7); ax.invert_yaxis(); ax.tick_params(axis='x',labelsize=7)
    ax.set_title('Droit moyen NPF vs offre ZLECAf 2026 (%)',fontsize=8.3); ax.legend(frameon=False,fontsize=6.5,loc='lower right')
    out.setdefault(sid,{})['margins']=rows
    fig.tight_layout(); fig.savefig(C+f'sec_{sid}.png'); plt.close()
json.dump(out,open(S+'sector_charts.json','w'),ensure_ascii=False,indent=1)
for k,v in out.items(): print(k, {a:b for a,b in v.items() if a!='margins'}, v['margins'][:3])
