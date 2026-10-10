import os
exec(open((os.environ['RG_DIR'] + '/charts.py')).read().split('# 1 ag vs non-ag')[0])
import matplotlib.patches as mpatches
from matplotlib.path import Path as MPath
# ---- decode topojson
topo=json.load(open(S+'land-110m.json')); sc,tr=topo['transform']['scale'],topo['transform']['translate']
arcs=[]
for a in topo['arcs']:
    x=y=0; pts=[]
    for dx,dy in a: x+=dx; y+=dy; pts.append((x*sc[0]+tr[0], y*sc[1]+tr[1]))
    arcs.append(pts)
def ring(idx):
    out=[]
    for i in idx:
        pts=arcs[i] if i>=0 else arcs[~i][::-1]
        out.extend(pts if not out else pts[1:])
    return out
polys=[]
for g in topo['objects']['land']['geometries']:
    if g['type']=='Polygon': polys.append([ring(r) for r in g['arcs']])
    else:
        for p in g['arcs']: polys.append([ring(r) for r in p])
fig,ax=plt.subplots(figsize=(7.4,5.3))
ax.set_facecolor('#EEF3F6')
for p in polys:
    xs,ys=zip(*p[0])
    if (max(xs)-min(xs))>300:
        pos=sum(1 for x in xs if x>0)>len(xs)/2
        xs=[(x+360 if (pos and x<-90) else (x-360 if (not pos and x>90) else x)) for x in xs]
    if max(xs)<-30 or min(xs)>130 or max(ys)<-45 or min(ys)>62: continue
    ax.fill(xs,ys,color='#E4DFD3',ec='#C9C2B2',lw=0.4,zorder=1)
W0={'Shanghai':(121.8,31.2),'Singapour':(103.85,1.25),'Colombo':(79.85,6.95),'Bab el-Mandeb':(43.4,12.6),'Suez':(32.35,30.5),'Port-Saïd':(32.3,31.27),'Gibraltar':(-5.6,35.95),
   'Rotterdam':(4.05,51.95),'Las Palmas':(-15.42,28.14),'Port-Louis':(57.5,-20.16),'Le Cap':(18.43,-33.9),'Agulhas':(19.5,-34.83),'Durban':(31.05,-29.88),'Mombasa':(39.66,-4.07),
   'Djibouti':(43.13,11.6),'Tanger Med':(-5.5,35.89),'Abidjan':(-4.02,5.28),'Lagos':(3.4,6.43),'Walvis Bay':(14.5,-22.95),'Dakar':(-17.43,14.68),'Ormuz':(56.25,26.57),'Jeddah':(39.17,21.48),'Novorossiïsk':(37.77,44.72),'Alexandrie':(29.9,31.2)}
W=dict(W0); W['Agulhas']=(19.5,-35.6); W['Walvis Bay']=(14.5,-22.95)
def route(pts,**kw):
    xs=[p[0] for p in pts]; ys=[p[1] for p in pts]; ax.plot(xs,ys,**kw)
SUEZ=[(103.85,1.25),(95,6),(80,5.5),(65,11),(52,12.5),(43.4,12.6),(38.5,20),(34,27.5),(32.35,30.5),(32.3,31.5),(20,34),(10,37.5),(0,37),(-5.6,35.95),(-9.5,37),(-9.8,44),(-5.5,48.5),(2,51),(4.05,51.95)]
CAPE=[(103.85,1.25),(105,-7),(90,-12),(57.5,-20.16),(40,-30),(25,-36),(19.5,-35.6),(14,-30),(12.5,-23),(8,-10),(3,1),(-12,4),(-19,14),(-16.5,28),(-10,36),(-9.8,44),(-5.5,48.5),(2,51),(4.05,51.95)]
route(SUEZ,color=RED,lw=2.2,ls='--',zorder=3,label='Route Suez / Bab el-Mandeb : 8 367 nm')
route(CAPE,color=G2,lw=2.4,zorder=3,label='Route du Cap : 11 855 nm (+42 %, +10,4 j à 14 nœuds)')
route([(37.77,44.72),(36,42.5),(29,41.2),(26,38),(26,35),(32.3,31.5)],color='#6B5B95',lw=1.3,ls=':',zorder=3)
route([(39.66,-4.07),(44,-1),(51.5,10.5),(45,12),(43.4,12.6)],color=RED,lw=1.2,ls=':',zorder=3)
# chokepoints
for n,val in [('Bab el-Mandeb','−65 %'),('Suez','−44 %'),('Ormuz','−96 %'),('Agulhas','+76 %')]:
    x,y=W[n]; ax.scatter(x,y,s=120,color=RED if val.startswith('−') else G2,ec='white',lw=1.2,zorder=5)
    ax.annotate(f'{n if n!="Agulhas" else "Cap de Bonne-Espérance"}\n{val} navires/j', (x,y), xytext=((8,6) if n=='Bab el-Mandeb' else (8,-4)) if n!='Agulhas' else (10,-16), textcoords='offset points',fontsize=6.8,fontweight='bold',color=RED if val.startswith('−') else G2,zorder=6)
ports_g=['Tanger Med','Walvis Bay','Abidjan','Port-Louis']; ports_l=['Djibouti','Jeddah']
for n in ports_g:
    x,y=W[n]; ax.scatter(x,y,s=30,marker='^',color=G2,zorder=5)
    ax.annotate(n,(x,y),xytext=(-6,6) if n!='Port-Louis' else (5,-10),textcoords='offset points',fontsize=6.5,color='#1c5f3f',ha='right' if n in('Tanger Med','Abidjan','Walvis Bay') else 'left')
for n in ports_l:
    x,y=W[n]; ax.scatter(x,y,s=30,marker='v',color=RED,zorder=5)
    ax.annotate(n,(x,y),xytext=(-6,4),textcoords='offset points',fontsize=6.5,color='#8e2f25',ha='right')
for n in ['Shanghai','Singapour','Rotterdam','Mombasa','Durban','Lagos','Dakar','Novorossiïsk']:
    x,y=W[n]; ax.scatter(x,y,s=12,color=G,zorder=5); ax.annotate(n,(x,y),xytext=(4,3),textcoords='offset points',fontsize=6.3,color='#333')
# JWC zones (schematic)
ax.add_patch(mpatches.Polygon([(32,25.5),(45,10.8),(60.25,10.8),(65,26),(56,30),(40,28)],closed=True,fc=RED,alpha=0.10,ec=RED,lw=0.6,ls='--',zorder=2))
ax.text(52,17,'Zones JWC\n(mer Rouge, golfe d\'Aden,\nnord-ouest océan Indien)',fontsize=6,color='#8e2f25',ha='center')
ax.add_patch(mpatches.Polygon([(1.2,6.2),(3,-0.7),(8.7,-0.7),(8.7,4.5),(3,6.5)],closed=True,fc=RED,alpha=0.10,ec=RED,lw=0.6,ls='--',zorder=2))
ax.text(10,1.2,'JWC golfe\nde Guinée',fontsize=5.8,color='#8e2f25')
ax.set_xlim(-25,125); ax.set_ylim(-42,58); ax.set_aspect(1.0)
ax.set_xticks([]); ax.set_yticks([]); ax.spines[:].set_visible(False)
ax.legend(frameon=True,fontsize=7,loc='lower right',facecolor='white',edgecolor='#ddd')
fig.savefig(C+'c12_routes.png'); plt.close()
# ---- chokepoints bar
cp=[('Suez',73.6,41.0),('Bab el-Mandeb',74.6,25.9),('Ormuz',95.6,3.9),('Cap de B.-E.',48.9,86.1),('Gibraltar',146.2,133.3)]
fig,ax=plt.subplots(figsize=(7.2,2.6)); x=np.arange(len(cp)); w=0.38
ax.bar(x-w/2,[c[1] for c in cp],w,color=GREY,label='2023 (janv.-oct., avant crise)'); b=ax.bar(x+w/2,[c[2] for c in cp],w,color=[RED if c[2]<c[1] else G2 for c in cp],label='1-20 sept. 2026')
for i,c in enumerate(cp): ax.text(i+w/2,c[2]+2,f"{(c[2]/c[1]-1)*100:+.0f} %".replace('-','−'),ha='center',fontsize=7.5,fontweight='bold',color=RED if c[2]<c[1] else G2)
ax.set_xticks(x); ax.set_xticklabels([c[0] for c in cp]); ax.set_ylabel('Navires par jour'); ax.legend(frameon=False,fontsize=7.5); ax.grid(axis='y',color='#eee'); ax.set_axisbelow(True)
fig.savefig(C+'c13_chokepoints.png'); plt.close()
# ---- fuel
lab=['T1 24','T2 24','T3 24','T4 24','T1 25','T2 25','T3 25','T4 25','Janv. 26','Févr.','Mars','Avr.','Mai','Juin','Juil.','Août','Sept.*']
brent=[82.92,84.68,80.01,74.66,75.87,68.07,69.03,63.65,66.60,70.89,103.13,117.29,107.14,85.40,83.76,91.08,112.96]
jet=[110.0,103.4,92.4,87.2,93.4,83.9,89.1,88.9,85.3,95.0,155.3,165.0,165.6,127.8,142.9,156.4,184.0]
fig,ax=plt.subplots(figsize=(7.3,2.9)); x=np.arange(len(lab))
ax.axvspan(9.5,16.5,color='#FBEDEA',zorder=0); ax.text(13,196,'Guerre Iran / Ormuz, blocus mer Rouge',ha='center',fontsize=7,color='#8e2f25')
ax.plot(x,jet,color=RED,lw=2,marker='o',ms=3,label='Kérosène US Gulf ($/b)'); ax.plot(x,brent,color=G,lw=2,marker='o',ms=3,label='Brent ($/b)')
ax.annotate('184 $/b\n+107 % vs 2025',(16,184),xytext=(-60,-6),textcoords='offset points',fontsize=7,color=RED,fontweight='bold')
ax.annotate('Pic Brent 130,8 $\nle 15/09/2026',(16,112.96),xytext=(-110,22),textcoords='offset points',fontsize=6.8,color=G,arrowprops=dict(arrowstyle='-',color='#999',lw=0.6))
ax.set_xticks(x); ax.set_xticklabels(lab,fontsize=6.6,rotation=0); ax.set_ylim(40,210); ax.set_ylabel('$ par baril')
ax.axvline(7.5,color='#bbb',lw=0.6,ls=':'); ax.text(3.5,48,'Moyennes trimestrielles',ha='center',fontsize=6.5,color='#777'); ax.text(12.5,48,'Moyennes mensuelles 2026',ha='center',fontsize=6.5,color='#777')
ax.legend(frameon=False,fontsize=7.5,loc='upper left'); ax.grid(axis='y',color='#eee'); ax.set_axisbelow(True)
fig.savefig(C+'c14_fuel.png'); plt.close()
print('ok')
