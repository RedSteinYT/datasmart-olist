"""Semana 13 - Segmentación de clientes: RFM + K-Means, Hierarchical y DBSCAN."""
from pathlib import Path
import numpy as np, pandas as pd
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import KMeans, AgglomerativeClustering, DBSCAN
from sklearn.metrics import silhouette_score, davies_bouldin_score, calinski_harabasz_score
from sklearn.decomposition import PCA
ROOT=Path(__file__).resolve().parents[1]; OUT=ROOT/"analysis"/"outputs_s13"
df=pd.read_csv(ROOT/"data/processed/pedidos_procesados.csv",parse_dates=["order_purchase_timestamp"])
ref=df.order_purchase_timestamp.max()+pd.Timedelta(days=1)
c=df.groupby("customer_unique_id").agg(
    recencia=("order_purchase_timestamp",lambda s:(ref-s.max()).days),
    frecuencia=("order_id","nunique"), monetario=("valor_pago","sum"),
    ticket_medio=("valor_pago","mean"), review_medio=("review_score","mean"),
    dias_entrega_medio=("dias_entrega","mean"), n_items_medio=("n_items","mean"),
    ratio_flete=("ratio_flete","mean"), estado=("customer_state","first")).reset_index()
c["review_medio"]=c.review_medio.fillna(c.review_medio.median())
c["ratio_flete"]=c.ratio_flete.fillna(c.ratio_flete.median()).clip(upper=c.ratio_flete.quantile(.99))
print("clientes:",len(c)," | 1 sola compra:",(c.frecuencia==1).mean().round(4))
# ---- RFM por scoring (R: menor=mejor; F con rank para evitar empates; M cuantiles)
c["R"]=pd.qcut(c.recencia.rank(method="first"),5,labels=[5,4,3,2,1]).astype(int)
c["F"]=np.where(c.frecuencia>=3,5,np.where(c.frecuencia==2,4,np.where(c.monetario.rank(pct=True)>.5,2,1)))
c["M"]=pd.qcut(c.monetario.rank(method="first"),5,labels=[1,2,3,4,5]).astype(int)
c["RFM_score"]=c.R+c.F+c.M
# ---- ABC por monetario
cs=c.sort_values("monetario",ascending=False); cum=cs.monetario.cumsum()/cs.monetario.sum()
c["ABC"]=pd.Series(np.where(cum<=.8,"A",np.where(cum<=.95,"B","C")),index=cs.index)
print(c.ABC.value_counts(normalize=True).round(3).to_dict(), "ingreso A:",c[c.ABC=="A"].monetario.sum()/c.monetario.sum())
# ---- Features de clustering
feat=["recencia","frecuencia","monetario","review_medio","dias_entrega_medio","ratio_flete"]
X=c[feat].copy()
for k in ["recencia","frecuencia","monetario","dias_entrega_medio","ratio_flete"]: X[k]=np.log1p(X[k])
Xs=StandardScaler().fit_transform(X)
rng=np.random.RandomState(42); samp=rng.choice(len(Xs),8000,replace=False)
# ---- K-Means: elegir k
rows=[]
for k in range(2,9):
    km=KMeans(k,n_init=5,random_state=42).fit(Xs)
    rows.append(dict(k=k,inercia=km.inertia_,silhouette=silhouette_score(Xs[samp],km.labels_[samp]),davies_bouldin=davies_bouldin_score(Xs,km.labels_)))
sel=pd.DataFrame(rows); sel.to_csv(OUT/"01_kmeans_seleccion_k.csv",index=False); print(sel.round(3).to_string(index=False))
K=4; km=KMeans(K,n_init=10,random_state=42).fit(Xs); c["cluster_kmeans"]=km.labels_
# ---- Hierarchical (muestra 8000 por costo O(n^2))
hc=AgglomerativeClustering(K,linkage="ward").fit(Xs[samp])
# ---- DBSCAN (muestra)
db=DBSCAN(eps=0.9,min_samples=30).fit(Xs[samp]); nd=len(set(db.labels_))-(1 if -1 in db.labels_ else 0)
cmp_=[dict(modelo="K-Means (k=4)",n_clusters=K,silhouette=silhouette_score(Xs[samp],km.labels_[samp]),davies_bouldin=davies_bouldin_score(Xs,km.labels_),calinski=calinski_harabasz_score(Xs,km.labels_),ruido=0.0,muestra="completo (93k)"),
 dict(modelo="Hierarchical Ward (k=4)",n_clusters=K,silhouette=silhouette_score(Xs[samp],hc.labels_),davies_bouldin=davies_bouldin_score(Xs[samp],hc.labels_),calinski=calinski_harabasz_score(Xs[samp],hc.labels_),ruido=0.0,muestra="8,000")]
m=db.labels_!=-1
if nd>=2 and m.sum()>10: cmp_.append(dict(modelo=f"DBSCAN (eps=0.9, min=30)",n_clusters=nd,silhouette=silhouette_score(Xs[samp][m],db.labels_[m]),davies_bouldin=davies_bouldin_score(Xs[samp][m],db.labels_[m]),calinski=calinski_harabasz_score(Xs[samp][m],db.labels_[m]),ruido=float((~m).mean()),muestra="8,000"))
else: cmp_.append(dict(modelo=f"DBSCAN (eps=0.9, min=30)",n_clusters=nd,silhouette=np.nan,davies_bouldin=np.nan,calinski=np.nan,ruido=float((~m).mean()),muestra="8,000"))
cmp_=pd.DataFrame(cmp_); cmp_.to_csv(OUT/"02_clustering_comparacion.csv",index=False); print(cmp_.round(3).to_string(index=False))
# ---- Perfil
prof=c.groupby("cluster_kmeans").agg(clientes=("customer_unique_id","count"),recencia=("recencia","mean"),frecuencia=("frecuencia","mean"),
   monetario=("monetario","mean"),ticket=("ticket_medio","mean"),review=("review_medio","mean"),dias_entrega=("dias_entrega_medio","mean"),ratio_flete=("ratio_flete","mean"),ingreso_total=("monetario","sum")).round(2)
prof["pct_clientes"]=(prof.clientes/len(c)*100).round(1); prof["pct_ingreso"]=(prof.ingreso_total/c.monetario.sum()*100).round(1)
prof.to_csv(OUT/"03_perfil_clusters.csv"); print(prof.to_string())
c.to_csv(ROOT/"data/processed/clientes_segmentados.csv",index=False)
p=PCA(2,random_state=42).fit(Xs); Z=p.transform(Xs[samp]); print("PCA var:",p.explained_variance_ratio_.round(3))
pd.DataFrame({"pc1":Z[:,0],"pc2":Z[:,1],"cluster":km.labels_[samp]}).to_csv(OUT/"04_pca_muestra.csv",index=False)
pd.DataFrame(Xs[:0],columns=feat)
pd.DataFrame({"var_explicada_pc1":[p.explained_variance_ratio_[0]],"var_explicada_pc2":[p.explained_variance_ratio_[1]]}).to_csv(OUT/"04b_pca_varianza.csv",index=False)
print(c.groupby("ABC").agg(n=("monetario","size"),ingreso=("monetario","sum")).assign(pct=lambda d:d.ingreso/d.ingreso.sum()))

# ---- Barrido DBSCAN (para justificar que no sirve como segmentador principal)
g=[]
for eps in [0.4,0.6,0.9,1.2]:
    for ms in [15,30,60]:
        l=DBSCAN(eps=eps,min_samples=ms).fit(Xs[samp]).labels_; n=len(set(l))-(1 if -1 in l else 0)
        g.append(dict(eps=eps,min_samples=ms,n_clusters=n,pct_ruido=round(float((l==-1).mean()),3),
            pct_mayor=round(float(pd.Series(l[l!=-1]).value_counts(normalize=True).max()),3) if n else np.nan))
g=pd.DataFrame(g); g.to_csv(OUT/"05_dbscan_barrido.csv",index=False); print(g.to_string(index=False))
