"""Entregable 4 - Regresión del tiempo de entrega en tres versiones (v1, v2 con distancia, v3 con variables causales).

Se mantiene la partición 80/20 con semilla 42 del tercer entregable para que las versiones sean comparables.
Salidas en analysis/outputs_s16/12_*.csv
"""
import sys, time
from pathlib import Path
import numpy as np, pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LinearRegression, Ridge, Lasso, ElasticNet
from sklearn.ensemble import RandomForestRegressor, HistGradientBoostingRegressor
from sklearn.dummy import DummyRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from xgboost import XGBRegressor

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from datasmart import features as F

OUT = ROOT / "analysis" / "outputs_s16"
df = pd.read_csv(ROOT / "data/processed/pedidos_modelo.csv")
y = df.dias_entrega.clip(upper=df.dias_entrega.quantile(.99)).values       # winsorizado p99
idx_tr, idx_te = train_test_split(np.arange(len(df)), test_size=.2, random_state=42)

VERS = {"v1": F.NUM_V1, "v2": F.NUM_V2, "v3": F.NUM_V3}


def modelos():
    return {
        "Baseline (media)": (DummyRegressor(), 0),
        "Regresión lineal": (LinearRegression(), 1),
        "Ridge (α=10)": (Ridge(alpha=10), 1),
        "Lasso (α=0.01)": (Lasso(alpha=.01, max_iter=5000), 1),
        "Elastic Net (α=0.01, l1=0.5)": (ElasticNet(alpha=.01, l1_ratio=.5, max_iter=5000), 1),
        "Random Forest": (RandomForestRegressor(n_estimators=80, max_depth=14, min_samples_leaf=5, n_jobs=2, random_state=42), 0),
        "Gradient Boosting (Hist)": (HistGradientBoostingRegressor(max_iter=300, learning_rate=.08, random_state=42), 0),
        "XGBoost": (XGBRegressor(n_estimators=400, learning_rate=.05, max_depth=6, min_child_weight=10, subsample=.8, colsample_bytree=.8, tree_method="hist", n_jobs=2, random_state=42), 0),
    }


rows, best_pred, gb_v3 = [], {}, None
for v, num in VERS.items():
    X = F.build_X(df, num, log=(v != "v1"))
    Xtr, Xte = X.iloc[idx_tr], X.iloc[idx_te]
    sc = StandardScaler().fit(Xtr[num])
    Xtr_s, Xte_s = Xtr.copy(), Xte.copy()
    Xtr_s[num] = sc.transform(Xtr[num]); Xte_s[num] = sc.transform(Xte[num])
    for n, (m, esc) in modelos().items():
        t = time.time()
        a, b = (Xtr_s, Xte_s) if esc else (Xtr, Xte)
        m.fit(a, y[idx_tr]); p = m.predict(b)
        r = dict(version=v, modelo=n, n_variables=X.shape[1], MAE=mean_absolute_error(y[idx_te], p),
                 RMSE=mean_squared_error(y[idx_te], p) ** .5, R2=r2_score(y[idx_te], p), segundos=round(time.time() - t, 1))
        rows.append(r); print({k: (round(x, 3) if isinstance(x, float) else x) for k, x in r.items()})
        if n.startswith("Gradient") and v == "v3":
            gb_v3, Xte_v3 = m, Xte
        if n == "XGBoost" and v == "v3":
            xgb_v3 = m
        if n.startswith("Lasso") and v == "v1":
            print("Lasso v1: variables no nulas", int((m.coef_ != 0).sum()), "de", len(m.coef_))
R = pd.DataFrame(rows)
R.to_csv(OUT / "12_regresion_versiones.csv", index=False)

# importancia por permutación agrupada (v3): se permuta cada variable original completa (las dummies juntas)
rng = np.random.RandomState(1)
sub = rng.choice(len(Xte_v3), 6000, replace=False)
Xs, ys = Xte_v3.iloc[sub].reset_index(drop=True), y[idx_te][sub]
base = mean_absolute_error(ys, gb_v3.predict(Xs))
grupos = {}
for c in Xs.columns:
    grupos.setdefault(F.grupo_de(c), []).append(c)
imp = []
for g, cols in grupos.items():
    inc = []
    for k in range(5):
        Xp = Xs.copy()
        perm = rng.permutation(len(Xp))
        Xp[cols] = Xp[cols].values[perm]
        inc.append(mean_absolute_error(ys, gb_v3.predict(Xp)) - base)
    imp.append(dict(grupo=g, variable=F.NOMBRES.get(g, g), importancia_MAE=float(np.mean(inc))))
imp = pd.DataFrame(imp).sort_values("importancia_MAE", ascending=False)
imp.to_csv(OUT / "12_regresion_v3_importancia.csv", index=False)
print(imp.head(8).round(3).to_string(index=False))
pd.DataFrame({"real": y[idx_te][:3000], "pred": gb_v3.predict(Xte_v3)[:3000]}).to_csv(OUT / "12_regresion_v3_real_vs_pred.csv", index=False)
