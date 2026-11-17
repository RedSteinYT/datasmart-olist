"""Entregable 4 - Monitoreo del modelo: simulación mensual (nov-2017 a ago-2018), PSI, alertas y 4 políticas de reentrenamiento.

Reglas: el modelo que puntúa el mes m solo usa pedidos comprados antes de m y ya entregados al inicio de m (etiquetas conocidas).
Referencia: ene-oct 2017. Alertas: AUC-ROC cae > 0.05 vs referencia, calibración |media_pred/obs - 1| > 50 %, PSI > 0.25, MAE +20 % (regresión).
"""
import sys, json, hashlib, warnings, datetime as dt
from pathlib import Path
import numpy as np, pandas as pd, joblib
from xgboost import XGBClassifier, XGBRegressor
from sklearn.metrics import roc_auc_score, average_precision_score, brier_score_loss, mean_absolute_error
from sklearn.model_selection import train_test_split
warnings.filterwarnings("ignore")
ROOT = Path(__file__).resolve().parents[1]; sys.path.insert(0, str(ROOT / "src"))
from datasmart import features as F
OUT = ROOT / "analysis" / "outputs_s16"; REG = ROOT / "models" / "registro"
meta = joblib.load(ROOT / "models/clasificador_meta.joblib")
HP = {k: v for k, v in meta["hiperparametros"].items()}
NUM = meta["num"]; CATS = F.top_categorias(pd.read_csv(ROOT / "data/processed/pedidos_modelo.csv", usecols=["categoria_principal"]))
df = pd.read_csv(ROOT / "data/processed/pedidos_modelo.csv", parse_dates=["order_purchase_timestamp", "order_delivered_customer_date"])
df["mes"] = df.order_purchase_timestamp.dt.to_period("M")
X = F.build_X(df, NUM, log=True, cats=meta.get("cats"), drop_first=False)[meta["columns"]]
y = df.entrega_tardia.values; yd = df.dias_entrega.values
ref_m = pd.period_range("2017-01", "2017-10", freq="M"); sim_m = pd.period_range("2017-11", "2018-08", freq="M")
ini = lambda m: pd.Timestamp(m.start_time)
audit = []
def log(evento, **kw): audit.append(dict(ts=dt.datetime(2026, 11, 17).isoformat(), evento=evento, **kw))

def fit_clf(idx):
    m = XGBClassifier(**HP).fit(X.iloc[idx], y[idx]); p = m.predict_proba(X.iloc[idx])[:, 1]
    return m, float(np.quantile(p, .60)), float(np.quantile(p, .90))
def fit_reg(idx):
    return XGBRegressor(n_estimators=300, learning_rate=.05, max_depth=6, min_child_weight=5, subsample=.8, colsample_bytree=.8, tree_method="hist", n_jobs=2, random_state=42).fit(X.iloc[idx], yd[idx])
def ventana(m, w):
    """Índices de pedidos comprados en los w meses que terminan en m-2 y entregados antes del inicio de m (maduración de 1 mes)."""
    ms = pd.period_range(m - 1 - w, m - 2, freq="M")  # un mes de maduración: las compras de m-1 aún tienen entregas lentas sin registrar
    ok = df.mes.isin(ms) & (df.order_delivered_customer_date < ini(m))
    return np.where(ok)[0]
def huella(model):
    return hashlib.sha256(bytes(model.get_booster().save_raw("json"))).hexdigest()[:16]

# ---------- referencia ----------
ipsi = np.where(df.mes.isin(ref_m))[0]  # referencia de distribuciones (ene-oct 2017)
iref = np.where(df.mes.isin(pd.period_range("2017-01", "2017-09", freq="M")) & (df.order_delivered_customer_date < ini(sim_m[0])))[0]  # entrenamiento v1 (ene-sep; octubre madura)
a, b = train_test_split(iref, test_size=.2, random_state=42, stratify=y[iref])
m0, _, _ = fit_clf(a); p0 = m0.predict_proba(X.iloc[b])[:, 1]
AUC_REF, AP_REF, MEAN_REF = roc_auc_score(y[b], p0), average_precision_score(y[b], p0), float(y[iref].mean())
r0 = fit_reg(a); MAE_REF = mean_absolute_error(yd[b], r0.predict(X.iloc[b]))
print(f"Referencia (entrena ene-sep 2017): n={len(iref)}, tardías {MEAN_REF:.1%}, AUC {AUC_REF:.3f}, AP {AP_REF:.3f}, MAE regresión {MAE_REF:.2f} d")
log("referencia", n=len(iref), auc=AUC_REF, ap=AP_REF, mae=MAE_REF)

# ---------- PSI ----------
def psi_num(ref, cur, bins=10):
    e = np.unique(np.nanquantile(ref, np.linspace(0, 1, bins + 1))); e[0], e[-1] = -np.inf, np.inf
    if len(e) < 3: return 0.0
    r = np.histogram(ref[~np.isnan(ref)], e)[0] / max((~np.isnan(ref)).sum(), 1); c = np.histogram(cur[~np.isnan(cur)], e)[0] / max((~np.isnan(cur)).sum(), 1)
    r, c = np.clip(r, 1e-4, None), np.clip(c, 1e-4, None); return float(np.sum((c - r) * np.log(c / r)))
def psi_cat(ref, cur):
    cats = sorted(set(ref) | set(cur)); r = pd.Series(ref).value_counts(normalize=True).reindex(cats).fillna(0).clip(lower=1e-4); c = pd.Series(cur).value_counts(normalize=True).reindex(cats).fillna(0).clip(lower=1e-4)
    return float(np.sum((c - r) * np.log(c / r)))
dcat = np.where(df.categoria_principal.isin(CATS), df.categoria_principal, "otras")
psi_rows = []
def psi_mes(m, score_ref, score_cur):
    cm = np.where(df.mes == m)[0]; r = {"mes": str(m)}
    for c in NUM: r[c] = psi_num(df[c].values[ipsi].astype(float), df[c].values[cm].astype(float))
    r["customer_state"] = psi_cat(df.customer_state.values[ipsi], df.customer_state.values[cm])
    r["cat"] = psi_cat(dcat[ipsi], dcat[cm]); r["score"] = psi_num(score_ref, score_cur); return r

# ---------- simulación ----------
fro, q60f, q90f = fit_clf(iref); fro_id = "v1-referencia"
score_ref = fro.predict_proba(X.iloc[ipsi])[:, 1]
reg_fro = fit_reg(iref)
politicas = ["A. Congelado (ene-sep 2017)", "B. Mensual, ventana 6 meses", "C. Mensual, ventana 2 meses", "D. Solo si hay alerta, ventana 2 meses"]
estado = {p: dict(model=fro, q60=q60f, q90=q90f, version=fro_id) for p in politicas}
estado[politicas[1]]["reg"] = None
filas, versiones, alertas, nver, reg_filas = [], [dict(id=fro_id, politica="todas (inicio)", entrenado_con="ene-sep 2017", n=int(len(iref)), hash=huella(fro), fecha_sim="2017-11-01")], [], 1, []
reg_b = reg_fro; pend_D = False
for m in sim_m:
    cm = np.where(df.mes == m)[0]; yt = y[cm]
    # reentrenamientos previos a puntuar el mes m
    for pol, w in ((politicas[1], 6), (politicas[2], 2)):
        idx = ventana(m, w); mm, q6, q9 = fit_clf(idx); nver += 1; ver = f"v{nver}-{pol[0]}-{m}"
        estado[pol] = dict(model=mm, q60=q6, q90=q9, version=ver)
        versiones.append(dict(id=ver, politica=pol, entrenado_con=f"{w} meses hasta {m-2}", n=int(len(idx)), hash=huella(mm), fecha_sim=f"{m.start_time.date()}"))
        log("reentrenamiento", politica=pol, version=ver, n=int(len(idx)), mes=str(m))
    if pend_D:
        idx = ventana(m, 2); mm, q6, q9 = fit_clf(idx); nver += 1; ver = f"v{nver}-D-{m}"
        estado[politicas[3]] = dict(model=mm, q60=q6, q90=q9, version=ver); pend_D = False
        versiones.append(dict(id=ver, politica=politicas[3], entrenado_con=f"2 meses hasta {m-2} (por alerta)", n=int(len(idx)), hash=huella(mm), fecha_sim=f"{m.start_time.date()}"))
        log("reentrenamiento", politica=politicas[3], version=ver, n=int(len(idx)), mes=str(m), motivo="alerta del mes anterior")
    reg_b = fit_reg(ventana(m, 6))
    for pol in politicas:
        e = estado[pol]; p = e["model"].predict_proba(X.iloc[cm])[:, 1]
        auc, ap, br = roc_auc_score(yt, p), average_precision_score(yt, p), brier_score_loss(yt, p)
        banda = np.where(p >= e["q90"], "Alto", np.where(p >= e["q60"], "Medio", "Bajo"))
        calib = float(p.mean() / yt.mean() - 1)
        fila = dict(mes=str(m), politica=pol, version=e["version"], n=len(cm), pct_tardias=float(yt.mean()), AUC_ROC=auc, AUC_PR=ap, Brier=br,
                    prob_media=float(p.mean()), desv_calibracion=calib,
                    tarde_Bajo=float(yt[banda == "Bajo"].mean()) if (banda == "Bajo").any() else np.nan,
                    tarde_Medio=float(yt[banda == "Medio"].mean()) if (banda == "Medio").any() else np.nan,
                    tarde_Alto=float(yt[banda == "Alto"].mean()) if (banda == "Alto").any() else np.nan,
                    captura_Alto=float(yt[banda == "Alto"].sum() / max(yt.sum(), 1)))
        fila["alerta_AUC"] = bool(AUC_REF - auc > .05); fila["alerta_calibracion"] = bool(abs(calib) > .5)
        filas.append(fila)
        if pol == politicas[0]:
            psi_rows.append(psi_mes(m, score_ref, p))
        if pol == politicas[3] and (fila["alerta_AUC"] or fila["alerta_calibracion"]):
            pend_D = True; log("alerta", politica=pol, mes=str(m), auc=auc, desv_calibracion=calib); alertas.append((str(m), pol))
    # regresión: congelada vs reentrenada
    for nombre, mod in (("Congelado", reg_fro), ("Mensual 6 meses", reg_b)):
        mae = mean_absolute_error(yd[cm], mod.predict(X.iloc[cm])); reg_filas.append(dict(mes=str(m), modelo=nombre, MAE=mae, MAE_ref=MAE_REF, alerta_MAE=bool(mae > 1.2 * MAE_REF), n=len(cm)))
S = pd.DataFrame(filas); S.to_csv(OUT / "16_simulacion_mensual.csv", index=False)
P = pd.DataFrame(psi_rows); P.to_csv(OUT / "16_psi_mensual.csv", index=False)
R = pd.DataFrame(reg_filas); R.to_csv(OUT / "16_regresion_mensual.csv", index=False)
res = S.groupby("politica").agg(AUC_ROC=("AUC_ROC", "mean"), AUC_PR=("AUC_PR", "mean"), Brier=("Brier", "mean"), abs_calib=("desv_calibracion", lambda s: s.abs().mean()),
                                captura_Alto=("captura_Alto", "mean"), meses_alerta=("alerta_AUC", "sum")).round(4)
res["reentrenamientos"] = [0, len(sim_m), len(sim_m), sum(1 for v in versiones if v["politica"] == politicas[3]) - 0]
res["reentrenamientos"] = res.index.map({politicas[0]: 0, politicas[1]: len(sim_m), politicas[2]: len(sim_m), politicas[3]: sum(1 for v in versiones if v["politica"] == politicas[3])})
res.to_csv(OUT / "16_politicas_resumen.csv"); print(res.to_string())
print("\nAUC por mes y política:\n", S.pivot(index="mes", columns="politica", values="AUC_ROC").round(3).to_string())
print("\ndesviación de calibración (obs vs pred) por mes:\n", S.pivot(index="mes", columns="politica", values="desv_calibracion").round(2).to_string())
pc = P.set_index("mes"); print("\nPSI máximo por mes:", pc.max(axis=1).round(2).to_dict()); print("variable de mayor PSI por mes:", pc.idxmax(axis=1).to_dict())
print("MAE regresión:\n", R.pivot(index="mes", columns="modelo", values="MAE").round(2).to_string(), "\nref", round(MAE_REF, 2))
json.dump(versiones, open(REG / "versiones.json", "w"), ensure_ascii=False, indent=1)
with open(OUT / "16_auditoria.jsonl", "w") as f:
    for a_ in audit: f.write(json.dumps(a_, ensure_ascii=False) + "\n")
json.dump(dict(AUC_REF=AUC_REF, AP_REF=AP_REF, MAE_REF=MAE_REF, tardias_ref=MEAN_REF, n_ref=int(len(iref)), n_versiones=len(versiones), alertas_D=alertas), open(OUT / "16_resumen.json", "w"), indent=1)

# ---------- validación temporal (contraste con la partición aleatoria 80/20) ----------
itr_t = np.where((df.mes <= pd.Period("2018-02")) & (df.order_delivered_customer_date < pd.Timestamp("2018-04-01")))[0]
ite_t = np.where(df.mes >= pd.Period("2018-04"))[0]
mt, _, _ = fit_clf(itr_t); pt = mt.predict_proba(X.iloc[ite_t])[:, 1]
mae_t = mean_absolute_error(yd[ite_t], fit_reg(itr_t).predict(X.iloc[ite_t]))
vt = dict(entrena="oct-2016..feb-2018 (entregados antes de abr-2018)", prueba="abr-ago 2018", n_train=int(len(itr_t)), n_test=int(len(ite_t)),
          tardias_train=float(y[itr_t].mean()), tardias_test=float(y[ite_t].mean()), AUC_ROC=float(roc_auc_score(y[ite_t], pt)), AUC_PR=float(average_precision_score(y[ite_t], pt)),
          Brier=float(brier_score_loss(y[ite_t], pt)), prob_media=float(pt.mean()), MAE_regresion=float(mae_t))
print("\nValidación temporal:", {k: (round(v, 4) if isinstance(v, float) else v) for k, v in vt.items()})
json.dump(vt, open(OUT / "16_validacion_temporal.json", "w"), ensure_ascii=False, indent=1)
