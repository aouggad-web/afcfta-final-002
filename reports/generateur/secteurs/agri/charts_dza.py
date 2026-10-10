import os
exec(open((os.environ['RG_DIR'] + '/charts.py')).read().split('# 1 ag vs non-ag')[0])
L=json.load(open(S+'dza_lists.json'))['sec']
secs=[s for s,_,_ in s1['sectors_def'] if s in L]
rows=[]
for s in secs:
    c=L[s]; t=sum(c.values()); rows.append((SEC[s],100*c.get('A',0)/t,100*c.get('B',0)/t,100*c.get('C',0)/t,t))
fig,ax=plt.subplots(figsize=(7.3,3.4)); y=np.arange(len(rows)); left=np.zeros(len(rows))
for i,(lab,col) in enumerate([('Liste A — 0 % (standard) / −60 % (réciprocité) en 2026',G2),('Liste B — −20 % / −12,5 % en 2026',GOLD),('Liste C — droit commun',RED)]):
    v=np.array([r[i+1] for r in rows]); ax.barh(y,v,left=left,color=col,label=lab,height=0.66)
    for yi,(l0,vv) in enumerate(zip(left,v)):
        if vv>=7: ax.text(l0+vv/2,yi,f'{vv:.0f}%',ha='center',va='center',fontsize=6.6,color='white')
    left+=v
ax.set_yticks(y); ax.set_yticklabels([f'{r[0]} ({r[4]})' for r in rows],fontsize=7); ax.invert_yaxis(); ax.set_xlim(0,100)
ax.legend(frameon=False,fontsize=6.8,ncol=3,loc='upper center',bbox_to_anchor=(0.45,-0.08)); ax.set_xlabel('')
fig.savefig(C+'a1_lists.png'); plt.close()
T=json.load(open(S+'dza_tax.json'))
sel=['Sucre brut','Sucre raffiné','Pâtes','Viande bovine congelée','Cajou','Thé noir','Huile de tournesol','Poulet congelé','Poisson congelé','Aliments du bétail','Pâte de cacao','Lait en poudre','Riz','Concentré de tomate','Pommes de terre','Beurre']
R=[t for s in sel for t in T if t['lab']==s]
fig,ax=plt.subplots(figsize=(7.4,4.0)); y=np.arange(len(R)); h=0.27
ax.barh(y-h,[r['npf']['total_hors_tva'] for r in R],h,color=GREY,label='NPF (DD + DAPS + PRCT + TCS + TIC)')
ax.barh(y,[r['rcp']['total_hors_tva'] for r in R],h,color=GOLD,label='ZLECAf — calendrier de réciprocité (Afrique du Sud, Cameroun, Ghana, Kenya)')
ax.barh(y+h,[r['std']['total_hors_tva'] for r in R],h,color=G2,label='ZLECAf — calendrier standard (Égypte, Maurice, Rwanda, Tanzanie, Tunisie)')
for i,r in enumerate(R):
    ax.text(r['npf']['total_hors_tva']+1.5,i-h,f"{r['npf']['total_hors_tva']:.0f}",va='center',fontsize=6)
    ax.text(r['std']['total_hors_tva']+1.5,i+h,f"{r['std']['total_hors_tva']:.0f}",va='center',fontsize=6,color=G2)
ax.set_yticks(y); ax.set_yticklabels([f"{r['lab']} (liste {r['std']['list']})" for r in R],fontsize=7); ax.invert_yaxis()
ax.set_xlabel('Charge fiscale à l\'importation hors TVA récupérable (% de la valeur CAF)'); ax.legend(frameon=False,fontsize=6.5,loc='upper center',bbox_to_anchor=(0.4,-0.13),ncol=1); ax.grid(axis='x',color='#eee'); ax.set_axisbelow(True)
fig.savefig(C+'a2_tax.png'); plt.close()
B=json.load(open(S+'dza_baci.json'))
lab={'310210':'Urée','080410':'Dattes','170199':'Sucre raffiné','110100':'Farine de blé','190219':'Pâtes','190531':'Biscuits','220210':'Boissons sucrées','110311':'Semoule','151219':'Huile de tournesol','180690':'Préparations au chocolat','210390':'Sauces, condiments'}
ks=[k for k in lab]
fig,ax=plt.subplots(figsize=(7.3,3.2)); y=np.arange(len(ks))
ax.barh(y,[B[k]['da']/1e6 for k in ks],0.6,color=SAND,ec='#d8cba8',label='Importations africaines 2024 (hors Algérie)')
ax.barh(y,[(B[k]['ea'] or 0)/1e6 for k in ks],0.6,color=G2,label='Exportations algériennes vers l\'Afrique 2024')
for i,k in enumerate(ks):
    sh=100*(B[k]['ea'] or 0)/B[k]['da']; ax.text(B[k]['da']/1e6*1.05,i,f"{B[k]['da']/1e6:,.0f} M$ · part DZ {sh:.1f} %".replace(',',' ').replace('.',','),va='center',fontsize=6.6)
ax.set_xscale('log'); ax.set_xlim(0.3,30000); ax.set_yticks(y); ax.set_yticklabels([lab[k] for k in ks],fontsize=7.2); ax.invert_yaxis()
ax.set_xlabel('M USD (échelle logarithmique)'); ax.legend(frameon=False,fontsize=6.8,loc='lower center',bbox_to_anchor=(0.45,1.0),ncol=2)
fig.savefig(C+'a3_demand.png'); plt.close()
# urea sensitivity
prem=np.linspace(0,10,41); hull=28e6; t=55000
dza=450+35.7; gulf=450+26.2+hull*prem/100/t
fig,ax=plt.subplots(figsize=(7.2,2.7))
ax.plot(prem,gulf-dza,color=G2,lw=2); ax.axhline(0,color='#999',lw=0.8)
be=(35.7-26.2)/(hull/100/t); ax.axvline(be,color=GOLD,ls='--',lw=1); ax.text(be+0.15,-12,f'Point mort ≈ {be:.1f} %'.replace('.',','),fontsize=7,color=GOLD_D if False else '#8A6414')
ax.axvspan(6,10,color='#FBEDEA'); ax.text(8,5,'Niveau sept. 2026\n(6-10 %)',ha='center',fontsize=7,color='#8e2f25')
ax.set_xlabel('Surprime de guerre à Ormuz (% de la valeur de coque, par transit)'); ax.set_ylabel('Avantage urée algérienne ($/t)')
ax.grid(color='#eee'); ax.set_axisbelow(True)
fig.savefig(C+'a4_urea.png'); plt.close()
print('ok', be)
