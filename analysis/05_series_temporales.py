"""Semana 13 - Series temporales: pronóstico de ventas diarias (sin statsmodels; ver 05b para SARIMA/Prophet)."""
from pathlib import Path
import numpy as np, pandas as pd, itertools
from sklearn.linear_model import Ridge
from sklearn.ensemble import GradientBoostingRegressor
ROOT=Path(__file__).resolve().parents[1]; OUT=ROOT/"analysis"/"outputs_s13"
df=pd.read_csv(ROOT/"data/processed/pedidos_procesados.csv",parse_dates=["order_purchase_timestamp"])
df["dia"]=df.order_purchase_timestamp.dt.normalize()
s=df.groupby("dia").agg(ventas=("valor_pago","sum"),pedidos=("order_id","count"))
idx=pd.date_range("2017-01-01","2018-08-15"); s=s.reindex(idx).fillna(0)   # tramo con volumen estable y completo
print(s.tail(3)); s.to_csv(OUT/"06_serie_diaria.csv",index_label="fecha")
y=s.ventas.values; H=30; train,test=y[:-H],y[-H:]
def metr(a,p): return dict(MAE=np.mean(np.abs(a-p)),RMSE=np.sqrt(np.mean((a-p)**2)),MAPE=np.mean(np.abs(a-p)/np.maximum(a,1))*100,sMAPE=np.mean(2*np.abs(a-p)/(np.abs(a)+np.abs(p)+1e-9))*100)
def hw_fit(y,m=7,a=.2,b=.05,g=.2):
    l=y[:m].mean(); t=(y[m:2*m].mean()-y[:m].mean())/m; sea=list(y[:m]-l); sse=0
    for i in range(m,len(y)):
        f=l+t+sea[i-m]; sse+=(y[i]-f)**2
        ln=a*(y[i]-sea[i-m])+(1-a)*(l+t); t=b*(ln-l)+(1-b)*t; sea.append(g*(y[i]-ln)+(1-g)*sea[i-m]); l=ln
    return sse,l,t,sea
def hw_forecast(y,h,m=7):
    best=min(((hw_fit(y,m,a,b,g),(a,b,g)) for a,b,g in itertools.product([.05,.1,.2,.4],[0,.01,.05],[.05,.2,.4])),key=lambda x:x[0][0])
    (sse,l,t,sea),par=best; return np.array([l+(k+1)*t*0.5+sea[len(y)-m+((k)%m)] for k in range(h)]),par   # tendencia amortiguada (0.5)
def lagfeat(y,dates):
    d=pd.DataFrame({"y":y},index=dates); 
    for L in [1,7,14]: d[f"l{L}"]=d.y.shift(L)
    d["ma7"]=d.y.shift(1).rolling(7).mean(); d["ma28"]=d.y.shift(1).rolling(28).mean(); d["dow"]=d.index.dayofweek; d["t"]=np.arange(len(d)); return d.dropna()
def ml_forecast(model,y,dates,h):
    hist=list(y); dts=list(dates); out=[]
    d=lagfeat(np.array(hist),pd.DatetimeIndex(dts)); X=pd.get_dummies(d.drop(columns="y"),columns=["dow"]).astype(float); m=model.fit(X.values,d.y.values); cols=X.columns
    for k in range(h):
        nd=dts[-1]+pd.Timedelta(days=1); hist.append(np.nan); dts.append(nd)
        tmp=pd.DataFrame({"y":hist},index=pd.DatetimeIndex(dts))
        row={f"l{L}":tmp.y.shift(L).iloc[-1] for L in [1,7,14]}; row["ma7"]=tmp.y.shift(1).rolling(7).mean().iloc[-1]; row["ma28"]=tmp.y.shift(1).rolling(28).mean().iloc[-1]; row["t"]=len(hist)-1
        r=pd.DataFrame([row]); 
        for dw in range(7): r[f"dow_{dw}"]=float(nd.dayofweek==dw)
        v=float(m.predict(r.reindex(columns=cols,fill_value=0).values)[0]); hist[-1]=v; out.append(v)
    return np.array(out)
dtr=idx[:-H]; res=[]; preds={}
preds["Naive (último valor)"]=np.repeat(train[-1],H)
preds["Media móvil 28 días"]=np.repeat(train[-28:].mean(),H)
preds["Naive estacional (sem.)"]=np.array([train[-7+(k%7)] for k in range(H)])
preds["Holt-Winters (m=7)"],par=hw_forecast(train,H)
preds["Ridge con rezagos"]=ml_forecast(Ridge(alpha=1.0),train,dtr,H)
preds["Gradient Boosting con rezagos"]=ml_forecast(GradientBoostingRegressor(n_estimators=200,max_depth=3,learning_rate=.05,random_state=42),train,dtr,H)
for k,v in preds.items(): res.append(dict(modelo=k,**metr(test,np.maximum(v,0))))
R=pd.DataFrame(res).sort_values("MAE"); R.to_csv(OUT/"07_series_comparacion.csv",index=False); print(R.round(2).to_string(index=False)); print("HW params",par)
pd.DataFrame({"fecha":idx[-H:],"real":test,**{k:np.maximum(v,0) for k,v in preds.items()}}).to_csv(OUT/"08_series_holdout.csv",index=False)
# Pronóstico a 7/30/60/90 con el mejor modelo (re-entrenado con todo)
best=R.iloc[0].modelo; print("mejor:",best)
fn={"Ridge con rezagos":lambda h:ml_forecast(Ridge(alpha=1.0),y,idx,h),"Holt-Winters (m=7)":lambda h:hw_forecast(y,h)[0],
    "Gradient Boosting con rezagos":lambda h:ml_forecast(GradientBoostingRegressor(n_estimators=200,max_depth=3,learning_rate=.05,random_state=42),y,idx,h),
    "Media móvil 28 días":lambda h:np.repeat(y[-28:].mean(),h),"Naive estacional (sem.)":lambda h:np.array([y[-7+(k%7)] for k in range(h)]),"Naive (último valor)":lambda h:np.repeat(y[-1],h)}[best]
F=np.maximum(fn(90),0); fut=pd.date_range(idx[-1]+pd.Timedelta(days=1),periods=90)
pd.DataFrame({"fecha":fut,"pronostico":F}).to_csv(OUT/"09_pronostico_90d.csv",index=False)
res_h=pd.DataFrame([dict(horizonte_dias=h,ventas_pronosticadas_BRL=F[:h].sum(),promedio_diario=F[:h].mean()) for h in [7,30,60,90]]); res_h.to_csv(OUT/"10_pronostico_horizontes.csv",index=False); print(res_h.round(0).to_string(index=False))
print("promedio diario últimos 30 días reales:",y[-30:].mean().round(0))
