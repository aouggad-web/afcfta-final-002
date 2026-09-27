import os
exec(open((os.environ['RG_DIR'] + '/charts1.py')).read().split("names=list(REG)")[0])
fig,(a1,a2)=plt.subplots(1,2,figsize=(7.4,2.9),gridspec_kw={'width_ratios':[1,1.25]})
sup=[('Inde',3.84),('France',2.31),('Suisse',1.55),('Belgique',1.51),('Allemagne',1.16),('États-Unis',0.58),('Royaume-Uni',0.58),('Afrique (intra)',0.79)]
sup=sorted(sup,key=lambda x:x[1])
a1.barh([s[0] for s in sup],[s[1] for s in sup],color=[GOLD if s[0].startswith('Afrique') else TEAL for s in sup],height=0.6)
for i,s in enumerate(sup): a1.text(s[1]+0.05,i,f"{s[1]:.2f}".replace('.',','),va='center',fontsize=6.8)
a1.set_title('Fournisseurs de l\'Afrique, SH 30, 2024 (Md USD)',fontsize=8); a1.set_xlim(0,4.6); a1.tick_params(labelsize=7)
imp=[('Égypte',3521),('Afrique du Sud',2423),('Algérie',1970),('Maroc',1073),('Kenya',705),('Éthiopie*',677),('Tunisie',661),('Nigeria',643),('Côte d\'Ivoire',531),('Tanzanie',359),('RD Congo',358),('Sénégal',353)]
a2.bar(range(len(imp)),[v for _,v in imp],color=[GOLD if n=='Algérie' else TEAL_L for n,_ in imp],edgecolor=TEAL,linewidth=0.4)
for i,(n,v) in enumerate(imp): a2.text(i,v+40,f'{v:,}'.replace(',',' '),ha='center',fontsize=5.8,rotation=90,va='bottom')
a2.set_xticks(range(len(imp))); a2.set_xticklabels([n for n,_ in imp],rotation=45,ha='right',fontsize=6.6); a2.set_ylim(0,4300)
a2.set_title('Premiers importateurs africains, SH 30, 2024 (M USD)',fontsize=8); a2.tick_params(axis='y',labelsize=6.5)
for a in (a1,a2): a.grid(axis='x' if a is a1 else 'y',color='#eceef2'); a.set_axisbelow(True)
fig.tight_layout(); fig.savefig(C+'k1_market.png'); plt.close()
