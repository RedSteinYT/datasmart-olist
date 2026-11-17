"""Semana 13 - Regresión: predecir dias_entrega (variable numérica) con variables conocidas al momento de despachar."""
from pathlib import Path
import numpy as np, pandas as pd, time
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LinearRegression, Ridge, Lasso, ElasticNet
from sklearn.ensemble import RandomForestRegressor, HistGradientBoostingRegressor
from sklearn.dummy import DummyRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.inspection import permutation_importance
ROOT=Path(__file__).resolve().parents[1]; OUT=ROOT/"analysis"/"outputs_s13"
df=pd.read_csv(ROOT/"data/processed/pedidos_procesados.csv")
top=df.categoria_principal.value_counts().head(15).index; df["cat"]=np.where(df.categoria_principal.isin(top),df.categoria_principal,"otras")
num=["precio_total","flete_total","peso_total_g","volumen_total_cm3","n_items","n_vendedores","ratio_flete","dia_semana","hora","dias_aprobacion","n_cuotas"]
X=pd.concat([df[num],pd.get_dummies(df[["customer_state","cat"]],drop_first=True)],axis=1).astype(float)
X["dias_aprobacion"]=X.dias_aprobacion.fillna(X.dias_aprobacion.median())
y=df.dias_entrega.clip(upper=df.dias_entrega.quantile(.99)).values   # winsorizado p99 (outliers)
Xtr,Xte,ytr,yte=train_test_split(X,y,test_size=.2,random_state=42)
sc=StandardScaler().fit(Xtr[num]); Xtr_s=Xtr.copy(); Xte_s=Xte.copy(); Xtr_s[num]=sc.transform(Xtr[num]); Xte_s[num]=sc.transform(Xte[num])
models={"Baseline (media)":(DummyRegressor(),0),"Regresión lineal":(LinearRegression(),1),"Ridge (α=10)":(Ridge(alpha=10),1),
 "Lasso (α=0.01)":(Lasso(alpha=.01,max_iter=5000),1),"Elastic Net (α=0.01, l1=0.5)":(ElasticNet(alpha=.01,l1_ratio=.5,max_iter=5000),1),
 "Random Forest":(RandomForestRegressor(n_estimators=80,max_depth=14,min_samples_leaf=5,n_jobs=-1,random_state=42),0),
 "Gradient Boosting (Hist)":(HistGradientBoostingRegressor(max_iter=300,learning_rate=.08,random_state=42),0)}
rows=[]; fitted={}
for n,(m,sc_) in models.items():
    t=time.time(); a,b=(Xtr_s,Xte_s) if sc_ else (Xtr,Xte); m.fit(a,ytr); p=m.predict(b); fitted[n]=(m,b)
    rows.append(dict(modelo=n,MAE=mean_absolute_error(yte,p),RMSE=mean_squared_error(yte,p)**.5,R2=r2_score(yte,p),segundos=round(time.time()-t,1))); print(rows[-1])
R=pd.DataFrame(rows); R.to_csv(OUT/"14_regresion_comparacion.csv",index=False)
lm=fitted["Lasso (α=0.01)"][0]; print("Lasso coef no cero:",(lm.coef_!=0).sum(),"de",len(lm.coef_))
best=R[R.modelo!="Baseline (media)"].sort_values("RMSE").iloc[0].modelo; print("mejor:",best)
m,b=fitted["Gradient Boosting (Hist)"]; idx=np.random.RandomState(1).choice(len(b),5000,replace=False)
pi=permutation_importance(m,b.iloc[idx],yte[idx],n_repeats=5,random_state=42,scoring="neg_mean_absolute_error")
imp=pd.DataFrame({"variable":b.columns,"importancia_MAE":pi.importances_mean}).sort_values("importancia_MAE",ascending=False); imp.head(15).to_csv(OUT/"15_regresion_importancia.csv",index=False); print(imp.head(10).round(3).to_string(index=False))
pd.DataFrame({"real":yte[:3000],"pred":fitted[best][0].predict(fitted[best][1])[:3000]}).to_csv(OUT/"16_regresion_real_vs_pred.csv",index=False)
