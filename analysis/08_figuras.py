from pathlib import Path
import numpy as np, pandas as pd, networkx as nx, matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
ROOT=Path(__file__).resolve().parents[1]; S10=ROOT/"analysis/outputs_s10"; S13=ROOT/"analysis/outputs_s13"; F=ROOT/"analysis/figs"; F.mkdir(exist_ok=True)
T,N,G,GR="#159A9C","#12304D","#8A97A5","#E07A5F"
plt.rcParams.update({"font.family":"DejaVu Sans","axes.spines.top":False,"axes.spines.right":False,"axes.edgecolor":"#B8C2CC","font.size":11})
def save(n): plt.tight_layout(); plt.savefig(F/n,dpi=170,transparent=False,facecolor="white"); plt.close()
df=pd.read_csv(ROOT/"data/processed/pedidos_procesados.csv")
# S10-1 reseña vs entrega tardía
d=df.dropna(subset=["review_score"]); g=d.groupby("entrega_tardia").review_score.agg(["mean","count"]); print(g)
fig,ax=plt.subplots(figsize=(5.2,4)); ax.bar(["A tiempo","Tardía"],g["mean"],color=[T,GR],width=.5)
for i,v in enumerate(g["mean"]): ax.text(i,v+.05,f"{v:.2f}",ha="center",fontweight="bold")
ax.set_ylim(0,5); ax.set_ylabel("Puntuación media de reseña"); save("s10_review_vs_tardia.png")
# S10-2 distribución dias_entrega
fig,ax=plt.subplots(figsize=(5.8,4)); ax.hist(df.dias_entrega.clip(upper=60),bins=50,color=T); ax.axvline(df.dias_entrega.median(),color=N,ls="--"); ax.text(df.dias_entrega.median()+1,ax.get_ylim()[1]*.9,f"mediana {df.dias_entrega.median():.1f} d",color=N)
ax.set_xlabel("Días de entrega (recortado a 60)"); ax.set_ylabel("Pedidos"); save("s10_dist_entrega.png")
# S10-3 top reglas por lift
r=pd.read_csv(S10/"04_top_reglas.csv"); r["par"]=r.antecedente+" → "+r.consecuente; r=r.sort_values("lift").tail(8)
fig,ax=plt.subplots(figsize=(7.2,4.2)); ax.barh(r.par,r.lift,color=T); ax.axvline(1,color=GR,ls=":"); ax.set_xlabel("Lift (>1 = asociación positiva)")
for i,(v,n) in enumerate(zip(r.lift,r.n_clientes)): ax.text(v+.03,i,f"{v:.1f} (n={n})",va="center",fontsize=9)
ax.set_xlim(0,r.lift.max()*1.25); save("s10_reglas_lift.png")
# S10-4 tiempos algoritmos
c=pd.read_csv(S10/"03_comparacion_algoritmos.csv"); fig,ax=plt.subplots(figsize=(4.6,3.8)); ax.bar(c.algoritmo,c.tiempo_s*1000,color=[GR,T,N],width=.5); ax.set_ylabel("Tiempo (ms)")
for i,v in enumerate(c.tiempo_s*1000): ax.text(i,v+3,f"{v:.0f}",ha="center"); save("s10_tiempos.png")
# S13-1 k-means selección
k=pd.read_csv(S13/"01_kmeans_seleccion_k.csv"); fig,ax=plt.subplots(figsize=(5.6,4)); ax.plot(k.k,k.inercia/1000,"o-",color=N); ax.set_xlabel("k"); ax.set_ylabel("Inercia (miles)",color=N)
a2=ax.twinx(); a2.plot(k.k,k.silhouette,"s--",color=T); a2.set_ylabel("Silhouette",color=T); a2.spines["right"].set_visible(True); save("s13_kmeans_k.png")
# S13-2 PCA
p=pd.read_csv(S13/"04_pca_muestra.csv"); fig,ax=plt.subplots(figsize=(5.6,4.4)); cols=[T,N,GR,GR]
cols=[T,GR,GR,GR]
names={0:"0 Alto valor satisfecho",1:"1 Ticket bajo / flete alto",2:"2 Insatisfechos (entrega lenta)",3:"3 Recurrentes"}; pal=[T,"#F2C14E",GR,N]
for i in range(4): s=p[p.cluster==i]; ax.scatter(s.pc1,s.pc2,s=4,alpha=.45,color=["#159A9C","#F2C14E","#E07A5F","#12304D"][i],label=names[i])
ax.legend(markerscale=4,fontsize=8,frameon=False); ax.set_xlabel("PC1"); ax.set_ylabel("PC2"); save("s13_pca.png")
# S13-3 perfil clusters
pf=pd.read_csv(S13/"03_perfil_clusters.csv"); fig,axs=plt.subplots(1,2,figsize=(8.4,3.8)); lab=["0","1","2","3"]; colc=["#159A9C","#F2C14E","#E07A5F","#12304D"]
axs[0].bar(lab,pf.pct_clientes,color=colc); axs[0].set_title("% de clientes",fontsize=11); axs[1].bar(lab,pf.pct_ingreso,color=colc); axs[1].set_title("% del ingreso",fontsize=11)
for a,v in zip(axs,[pf.pct_clientes,pf.pct_ingreso]):
    for i,x in enumerate(v): a.text(i,x+1,f"{x:.0f}%",ha="center")
    a.set_xlabel("Cluster")
save("s13_perfil.png")
# S13-4 series
h=pd.read_csv(S13/"08_series_holdout.csv",parse_dates=["fecha"]); s=pd.read_csv(S13/"06_serie_diaria.csv",parse_dates=["fecha"]); fc=pd.read_csv(S13/"09_pronostico_90d.csv",parse_dates=["fecha"])
fig,ax=plt.subplots(figsize=(7.6,3.8)); ax.plot(h.fecha,h.real/1000,color=N,lw=2,label="Real"); ax.plot(h.fecha,h["Ridge con rezagos"]/1000,color=T,lw=2,label="Ridge con rezagos"); ax.plot(h.fecha,h["Naive (último valor)"]/1000,color=GR,ls="--",label="Naive"); ax.set_ylabel("Ventas diarias (miles BRL)"); ax.legend(frameon=False); plt.xticks(rotation=25); save("s13_holdout.png")
fig,ax=plt.subplots(figsize=(8,3.8)); ax.plot(s.fecha,s.ventas.rolling(7).mean()/1000,color=N,label="Real (media móvil 7 d)"); ax.plot(fc.fecha,fc.pronostico.rolling(7,min_periods=1).mean()/1000,color=T,lw=2,label="Pronóstico 90 d"); ax.axvline(s.fecha.max(),color=GR,ls=":"); ax.set_ylabel("Miles BRL por día"); ax.legend(frameon=False); save("s13_pronostico.png")
# S13-5 grafo
nd=pd.read_csv(S13/"11_grafo_nodos.csv"); ed=pd.read_csv(S13/"12_grafo_aristas.csv"); Gx=nx.Graph(); 
for _,r in nd.iterrows(): Gx.add_node(r.categoria,com=int(r.comunidad),sz=r.clientes)
for _,r in ed[ed.clientes_en_comun>=8].iterrows():
    if r.origen in Gx and r.destino in Gx: Gx.add_edge(r.origen,r.destino,w=r.clientes_en_comun)
Gx.remove_nodes_from([n for n in list(Gx) if Gx.degree(n)==0]); pos=nx.spring_layout(Gx,weight="w",k=.9,seed=7,iterations=200)
fig,ax=plt.subplots(figsize=(8.4,5.2)); cc=["#159A9C","#12304D","#F2C14E","#E07A5F"]
nx.draw_networkx_edges(Gx,pos,width=[.4+Gx[u][v]["w"]/30 for u,v in Gx.edges],edge_color="#C5CDD6",ax=ax)
nx.draw_networkx_nodes(Gx,pos,node_size=[60+Gx.nodes[n]["sz"]/18 for n in Gx],node_color=[cc[Gx.nodes[n]["com"]%4] for n in Gx],ax=ax)
nx.draw_networkx_labels(Gx,pos,font_size=7,ax=ax,bbox=dict(boxstyle="round,pad=0.15",fc="white",ec="none",alpha=.8)); ax.axis("off"); save("s13_grafo.png")
# S13-6 regresión
rg=pd.read_csv(S13/"14_regresion_comparacion.csv"); fig,ax=plt.subplots(figsize=(7.2,4)); rr=rg.sort_values("RMSE",ascending=False)
ax.barh(rr.modelo,rr.RMSE,color=[GR if "Baseline" in m else (T if ("Forest" in m or "Boosting" in m) else N) for m in rr.modelo]); ax.set_xlabel("RMSE en test (días) — menor es mejor"); ax.set_xlim(6,8.6)
for i,(v,r2) in enumerate(zip(rr.RMSE,rr.R2)): ax.text(v+.03,i,f"R²={r2:.2f}",va="center",fontsize=9)
save("s13_regresion.png")
im=pd.read_csv(S13/"15_regresion_importancia.csv").head(8).iloc[::-1]; fig,ax=plt.subplots(figsize=(6,3.8)); ax.barh(im.variable,im.importancia_MAE,color=T); ax.set_xlabel("Aumento de MAE al permutar (días)"); save("s13_importancia.png")
