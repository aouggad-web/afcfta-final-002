import os
exec(open((os.environ['RG_DIR'] + '/charts.py')).read().split('# 1 ag vs non-ag')[0])
r=json.load(open(S+'scan.json'))
ks=['DZA|TUN','KEN|GHA','DZA|GHA','EGY|TUN','MAR|EGY','EGY|GHA','MAR|GHA','ZAF|GHA']
lab=['Algérie — standard','Kenya — Annexe 1','Algérie — réciprocité','Égypte — groupe 5 ans','Maroc — P1','Égypte — groupe 10 ans','Maroc — P2','SACU — partenaires actifs']
secs=[s for s,_,_ in s1['sectors_def']]
M=np.array([[r[k]['bysec'].get(s,[None,None,np.nan])[2] if s in r[k]['bysec'] else np.nan for s in secs] for k in ks],dtype=float)
from matplotlib.colors import LinearSegmentedColormap
cmap=LinearSegmentedColormap.from_list('g',['#F4F6F5','#9ED9BC','#1E8C5A','#0B4D31']); cmap.set_bad('#FFFFFF')
fig,ax=plt.subplots(figsize=(7.4,3.6))
im=ax.imshow(np.ma.masked_invalid(M),cmap=cmap,aspect='auto',vmin=0,vmax=25)
for i in range(M.shape[0]):
  for j in range(M.shape[1]):
    v=M[i,j]
    if np.isnan(v): ax.text(j,i,'n.d.',ha='center',va='center',fontsize=6,color='#8a948f'); continue
    ax.text(j,i,f'{v:.0f}',ha='center',va='center',fontsize=6.8,color='white' if v>13 else '#2b3a35')
ax.set_xticks(range(len(secs))); ax.set_xticklabels([SEC[s] for s in secs],rotation=55,ha='right',fontsize=7)
ax.set_yticks(range(len(ks))); ax.set_yticklabels([f"{l}  ({r[k]['avg_npf']:.0f} → {r[k]['avg_pref']:.0f} %)" if not k.startswith('EGY') else f"{l}" for l,k in zip(lab,ks)],fontsize=7)
ax.spines[:].set_visible(False); ax.tick_params(length=0)
cb=fig.colorbar(im,ax=ax,fraction=0.025,pad=0.01); cb.ax.tick_params(labelsize=7); cb.set_label('Réduction moyenne servie (points)',fontsize=7)
fig.savefig(C+'c11_served.png'); plt.close()
print('ok')
