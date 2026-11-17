"""Entregable 4 - (a) Comparación de codificación y escalamiento (One-Hot vs Label; Standard vs MinMax vs ninguno), (b) segundo clasificador:
cliente que dejará una reseña baja (1-2 estrellas), antes y después de conocer la entrega."""
import sys, json, warnings
from pathlib import Path
import numpy as np, pandas as pd
from sklearn.preprocessing import StandardScaler, MinMaxScaler, LabelEncoder
from sklearn.linear_model import LogisticRegression
from sklearn.svm import LinearSVC
from sklearn.calibration import CalibratedClassifierCV
from sklearn.metrics import roc_auc_score, average_precision_score
from xgboost import XGBClassifier
warnings.filterwarnings("ignore")
ROOT = Path(__file__).resolve().parents[1]; sys.path.insert(0, str(ROOT / "src"))
from datasmart import features as F
OUT = ROOT / "analysis" / "outputs_s16"
df = pd.read_csv(ROOT / "data/processed/pedidos_modelo.csv"); NUM = [n for n, _ in F.NUM_FINAL]
itr, ite = F.split_clasificacion(df); y = df.entrega_tardia.values
BASE = dict(n_estimators=250, learning_rate=.06, max_depth=5, min_child_weight=10, subsample=.8, colsample_bytree=.8, tree_method="hist", n_jobs=2, random_state=42)
def ev(m, Xa, Xb, ya, yb): m.fit(Xa, ya); p = m.predict_proba(Xb)[:, 1]; return roc_auc_score(yb, p), average_precision_score(yb, p)
# ---------- (a) codificación y escalamiento sobre la entrega tardía ----------
X1 = F.build_X(df, NUM, log=True, drop_first=False)                       # One-Hot
d = df.copy(); d["cat"] = np.where(d.categoria_principal.isin(F.top_categorias(d)), d.categoria_principal, "otras")
Xl = F.build_X(df, NUM, log=True)[NUM].copy(); Xl["customer_state"] = LabelEncoder().fit_transform(d.customer_state); Xl["cat"] = LabelEncoder().fit_transform(d.cat)  # Label
filas = []
def reg(nombre, enc, esc, modelo, A, B):
    a, p = ev(modelo, A, B, y[itr], y[ite]); filas.append(dict(modelo=nombre, codificacion=enc, escalamiento=esc, AUC_ROC=round(a, 4), AUC_PR=round(p, 4)))
for esc_n, esc in (("ninguno", None), ("StandardScaler", StandardScaler), ("MinMaxScaler", MinMaxScaler)):
    A, B = X1.iloc[itr].values, X1.iloc[ite].values
    if esc: s = esc().fit(A); A, B = s.transform(A), s.transform(B)
    reg("Regresión logística", "One-Hot", esc_n, LogisticRegression(max_iter=3000, class_weight="balanced", C=.5), A, B)
    reg("SVM lineal (calibrado)", "One-Hot", esc_n, CalibratedClassifierCV(LinearSVC(C=.1, class_weight="balanced", max_iter=5000), cv=3), A, B)
reg("XGBoost", "One-Hot", "ninguno", XGBClassifier(**BASE), X1.iloc[itr], X1.iloc[ite])
reg("XGBoost", "Label Encoding", "ninguno", XGBClassifier(**BASE), Xl.iloc[itr], Xl.iloc[ite])
reg("Regresión logística", "Label Encoding", "StandardScaler", LogisticRegression(max_iter=3000, class_weight="balanced", C=.5), *(lambda s: (s.transform(Xl.iloc[itr]), s.transform(Xl.iloc[ite])))(StandardScaler().fit(Xl.iloc[itr])))
t = pd.DataFrame(filas); t.to_csv(OUT / "19_codificacion_escalamiento.csv", index=False); print(t.to_string(index=False))
# ---------- (b) cliente insatisfecho (reseña 1-2) ----------
d2 = df.dropna(subset=["review_score"]).reset_index(drop=True); yy = d2.resena_baja.values
i2, j2 = F.split_clasificacion(d2.assign(entrega_tardia=yy))
Xa = F.build_X(d2, NUM, log=True, drop_first=False)
Xb = Xa.copy(); Xb["dias_entrega"] = d2.dias_entrega.values; Xb["retraso_dias"] = d2.retraso_dias.values; Xb["entrega_tardia"] = d2.entrega_tardia.values
res = []
for nombre, X in (("Al comprar (sin datos de la entrega)", Xa), ("Al entregar (con días de entrega y retraso)", Xb)):
    a, p = ev(XGBClassifier(**BASE), X.iloc[i2], X.iloc[j2], yy[i2], yy[j2]); res.append(dict(momento=nombre, n_variables=X.shape[1], tasa_base=round(float(yy.mean()), 4), AUC_ROC=round(a, 4), AUC_PR=round(p, 4)))
r = pd.DataFrame(res); r.to_csv(OUT / "19_satisfaccion.csv", index=False); print(r.to_string(index=False))
# la entrega tardía por sí sola
a = roc_auc_score(yy[j2], d2.entrega_tardia.values[j2]); print("solo 'entrega_tardia' como predictor, AUC:", round(a, 4))
json.dump(dict(auc_solo_tardia=round(float(a), 4)), open(OUT / "19_resumen.json", "w"))
