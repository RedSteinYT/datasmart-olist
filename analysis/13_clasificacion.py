"""Entregable 4 - Clasificación del riesgo de entrega tardía.

Objetivo: entrega_tardia (1 = llega después de la fecha prometida), conocida solo al final del proceso.
Predictores: variables disponibles antes del despacho (61 columnas: 18 numéricas + estado + categoría).
Compara 5 clasificadores y 5 estrategias de balanceo (ninguno, under, over, SMOTE, ADASYN),
ajusta el modelo final con validación, calcula bandas de riesgo, curvas y calibración.
"""
import sys, json, time, warnings
from pathlib import Path
import numpy as np, pandas as pd, joblib
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier, HistGradientBoostingClassifier
from sklearn.svm import SVC
from sklearn.naive_bayes import GaussianNB
from sklearn.metrics import (roc_auc_score, average_precision_score, precision_recall_curve, roc_curve,
                             brier_score_loss)
from sklearn.model_selection import train_test_split
from sklearn.utils.class_weight import compute_sample_weight
from xgboost import XGBClassifier
from imblearn.under_sampling import RandomUnderSampler
from imblearn.over_sampling import RandomOverSampler, SMOTE, ADASYN

warnings.filterwarnings("ignore")
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from datasmart import features as F

OUT = ROOT / "analysis" / "outputs_s16"
(ROOT / "models").mkdir(exist_ok=True)
df = pd.read_csv(ROOT / "data/processed/pedidos_modelo.csv")
y = df.entrega_tardia.values
NUM = [c for c, _ in F.NUM_FINAL]
X = F.build_X(df, NUM, log=True, drop_first=False)
assert X.shape[1] == 61, X.shape
itr, ite = F.split_clasificacion(df)
Xtr, Xte, ytr, yte = X.iloc[itr], X.iloc[ite], y[itr], y[ite]
print("pedidos:", len(df), "| tardíos:", int(y.sum()), f"({y.mean():.3%}) | variables:", X.shape[1])
sc = StandardScaler().fit(Xtr[NUM])
def esc(A):
    B = A.copy(); B[NUM] = sc.transform(A[NUM]); return B
Xtr_s, Xte_s = esc(Xtr), esc(Xte)


def metricas(yt, s):
    p, r, th = precision_recall_curve(yt, s)
    f1 = 2 * p * r / np.maximum(p + r, 1e-12)
    k = int(np.nanargmax(f1[:-1]))
    return dict(AUC_ROC=roc_auc_score(yt, s), AUC_PR=average_precision_score(yt, s), F1=float(f1[k]),
                precision=float(p[k]), exhaustividad=float(r[k]), umbral=float(th[k]))


# ---------- 1. Comparación de clasificadores (clases ponderadas) ----------
filas = []
sw = compute_sample_weight("balanced", ytr)
gb_w = HistGradientBoostingClassifier(max_iter=250, learning_rate=.06, random_state=42)
gb_w.fit(Xtr, ytr, sample_weight=sw); s = gb_w.predict_proba(Xte)[:, 1]
filas.append(dict(modelo="Gradient Boosting (Hist)", **metricas(yte, s), segundos=0)); print(filas[-1])
rf = RandomForestClassifier(n_estimators=200, max_depth=14, min_samples_leaf=20, class_weight="balanced_subsample", n_jobs=2, random_state=42)
t = time.time(); rf.fit(Xtr, ytr); s = rf.predict_proba(Xte)[:, 1]
filas.append(dict(modelo="Random Forest", **metricas(yte, s), segundos=round(time.time() - t, 1))); print(filas[-1])
lr = LogisticRegression(max_iter=2000, class_weight="balanced", C=1.0)
t = time.time(); lr.fit(Xtr_s, ytr); s = lr.predict_proba(Xte_s)[:, 1]
filas.append(dict(modelo="Regresión logística", **metricas(yte, s), segundos=round(time.time() - t, 1))); print(filas[-1])
sub = np.random.RandomState(7).choice(len(Xtr_s), 15000, replace=False)
svm = SVC(kernel="rbf", C=1.0, gamma="scale", class_weight="balanced")
t = time.time(); svm.fit(Xtr_s.iloc[sub], ytr[sub]); s = svm.decision_function(Xte_s)
filas.append(dict(modelo="SVM (RBF, 15 mil)", **metricas(yte, s), segundos=round(time.time() - t, 1))); print(filas[-1])
nb = GaussianNB()
t = time.time(); nb.fit(Xtr_s, ytr); s = nb.predict_proba(Xte_s)[:, 1]
filas.append(dict(modelo="Naive Bayes (Gauss)", **metricas(yte, s), segundos=round(time.time() - t, 1))); print(filas[-1])
spw = float((ytr == 0).sum() / (ytr == 1).sum())
xg = XGBClassifier(n_estimators=250, learning_rate=.06, max_depth=5, min_child_weight=10, subsample=.8, colsample_bytree=.8,
                   scale_pos_weight=spw, tree_method="hist", n_jobs=2, random_state=42, eval_metric="logloss")
t = time.time(); xg.fit(Xtr, ytr); s = xg.predict_proba(Xte)[:, 1]
filas.append(dict(modelo="XGBoost", **metricas(yte, s), segundos=round(time.time() - t, 1))); print(filas[-1])
pd.DataFrame(filas).to_csv(OUT / "13_clasificacion_modelos.csv", index=False)

# ---------- 2. Técnicas de balanceo (solo sobre el conjunto de entrenamiento) ----------
bal = []
tecnicas = {"Sin balanceo": None, "Undersampling": RandomUnderSampler(random_state=42),
            "Oversampling aleatorio": RandomOverSampler(random_state=42),
            "SMOTE": SMOTE(k_neighbors=5, random_state=42), "ADASYN": ADASYN(n_neighbors=5, random_state=42)}
for tn, samp in tecnicas.items():
    if samp is None:
        A, a, As = Xtr, ytr, Xtr_s
    else:
        A, a = samp.fit_resample(Xtr, ytr)
        As = esc(A)
    for mn, mod, usa_esc in [("Regresión logística", LogisticRegression(max_iter=2000), True),
                             ("XGBoost", XGBClassifier(n_estimators=250, learning_rate=.06, max_depth=5, min_child_weight=10, subsample=.8, colsample_bytree=.8, tree_method="hist", n_jobs=2, random_state=42, eval_metric="logloss"), False)]:
        mod.fit(As if usa_esc else A, a)
        s = mod.predict_proba(Xte_s if usa_esc else Xte)[:, 1]
        m = metricas(yte, s); bal.append(dict(tecnica=tn, modelo=mn, n_entrenamiento=len(a), **m))
        print(tn, mn, {k: round(v, 3) for k, v in m.items() if k in ('AUC_ROC', 'AUC_PR', 'F1')})
pd.DataFrame(bal).to_csv(OUT / "13_balanceo.csv", index=False)

# ---------- 3. Modelo final: XGBoost con ajuste de hiperparámetros en validación (sin tocar la prueba) ----------
itr2, iva = train_test_split(np.arange(len(Xtr)), test_size=.2, random_state=1, stratify=ytr)
BASE = dict(n_estimators=300, learning_rate=.05, subsample=.8, colsample_bytree=.8, tree_method="hist", n_jobs=2, random_state=42, eval_metric="logloss")
mejor, mejor_ap, tabla = None, -1, []
for md in (4, 6):
    for mcw in (5, 30):
        for lam in (1., 10.):
            hp = dict(max_depth=md, min_child_weight=mcw, reg_lambda=lam)
            m = XGBClassifier(**BASE, **hp).fit(Xtr.iloc[itr2], ytr[itr2])
            ap = average_precision_score(ytr[iva], m.predict_proba(Xtr.iloc[iva])[:, 1])
            tabla.append(dict(**hp, AUC_PR_val=ap))
            if ap > mejor_ap: mejor_ap, mejor = ap, hp
pd.DataFrame(tabla).sort_values("AUC_PR_val", ascending=False).to_csv(OUT / "13_hiperparametros.csv", index=False)
print("mejores hiperparámetros (validación):", mejor, round(mejor_ap, 4))

# umbral elegido en validación (modelo ajustado en train2) y luego aplicado a la prueba
mv = XGBClassifier(**BASE, **mejor).fit(Xtr.iloc[itr2], ytr[itr2])
umbral_val = metricas(ytr[iva], mv.predict_proba(Xtr.iloc[iva])[:, 1])["umbral"]
final = XGBClassifier(**BASE, **mejor).fit(Xtr, ytr)
p_te = final.predict_proba(Xte)[:, 1]; p_tr = final.predict_proba(Xtr)[:, 1]
mf = metricas(yte, p_te)
pred = p_te >= umbral_val
tp = int((pred & (yte == 1)).sum()); fp = int((pred & (yte == 0)).sum()); fn = int((~pred & (yte == 1)).sum())
prec_v, rec_v = tp / max(tp + fp, 1), tp / max(tp + fn, 1)
print("FINAL:", {k: round(v, 3) for k, v in mf.items()}, "| azar AP:", round(yte.mean(), 3))
print(f"Umbral de validación {umbral_val:.3f} -> precisión {prec_v:.3f}, exhaustividad {rec_v:.3f}, F1 {2*prec_v*rec_v/(prec_v+rec_v):.3f}")

# intervalos de confianza por bootstrap (prueba)
rng = np.random.RandomState(0); aucs, aps = [], []
for _ in range(300):
    b = rng.randint(0, len(yte), len(yte))
    aucs.append(roc_auc_score(yte[b], p_te[b])); aps.append(average_precision_score(yte[b], p_te[b]))
ic = dict(AUC_ROC_ic95=[float(np.percentile(aucs, 2.5)), float(np.percentile(aucs, 97.5))],
          AUC_PR_ic95=[float(np.percentile(aps, 2.5)), float(np.percentile(aps, 97.5))])
print("IC95%:", ic)

# ---------- 4. Bandas de riesgo (percentiles 60 y 90 del entrenamiento) ----------
q60, q90 = np.percentile(p_tr, [60, 90])
banda = np.where(p_te >= q90, "Alto", np.where(p_te >= q60, "Medio", "Bajo"))
tot_tard = int(yte.sum()); filas_b = []
for b in ("Bajo", "Medio", "Alto"):
    m_ = banda == b; n = int(m_.sum()); t_ = int(yte[m_].sum())
    filas_b.append(dict(banda=b, pedidos=n, tardios=t_, pct_tarde=t_ / n, pct_retrasos_capturados=t_ / tot_tard, lift=(t_ / n) / yte.mean()))
bandas = pd.DataFrame(filas_b); bandas.to_csv(OUT / "13_bandas.csv", index=False); print(bandas.round(3).to_string(index=False))

# ---------- 5. Curvas y calibración ----------
fpr, tpr, _ = roc_curve(yte, p_te); pr, rc, _ = precision_recall_curve(yte, p_te)
g = np.linspace(0, 1, 201)
pd.DataFrame({"fpr": g, "tpr": np.interp(g, fpr, tpr)}).to_csv(OUT / "13_curva_roc.csv", index=False)
o = np.argsort(rc); pd.DataFrame({"recall": g, "precision": np.interp(g, rc[o], pr[o])}).to_csv(OUT / "13_curva_pr.csv", index=False)
cb = pd.qcut(p_te, 10, duplicates="drop")
cal = pd.DataFrame({"p": p_te, "y": yte, "b": cb}).groupby("b", observed=True).agg(prob_media=("p", "mean"), tasa_real=("y", "mean"), n=("y", "size"))
cal.to_csv(OUT / "13_calibracion.csv", index=False); print("Brier:", round(brier_score_loss(yte, p_te), 4), "| Brier del azar:", round(yte.mean() * (1 - yte.mean()), 4))

final.save_model(str(ROOT / "models" / "clasificador_xgb.json")); joblib.dump(final, ROOT / "models" / "clasificador_xgb.joblib")
joblib.dump(dict(columns=list(X.columns), num=NUM, cats=F.top_categorias(df), q60=float(q60), q90=float(q90),
                 umbral_val=float(umbral_val), hiperparametros={**BASE, **mejor}, itr=itr.tolist(), ite=ite.tolist()), ROOT / "models" / "clasificador_meta.joblib")
json.dump(dict(final=mf, ic95=ic, umbral_validacion=umbral_val, precision_val=prec_v, exhaustividad_val=rec_v,
               q60=float(q60), q90=float(q90), brier=float(brier_score_loss(yte, p_te)), tasa_base=float(yte.mean()),
               n_train=len(itr), n_test=len(ite), hiperparametros={**BASE, **mejor}), open(OUT / "13_final.json", "w"), indent=2)
