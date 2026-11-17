"""Entregable 4 - Exporta todo lo que necesita el dashboard a web/data/*.json (sin servidor: el sitio es estático)."""
import sys, json, shutil
from pathlib import Path
import numpy as np, pandas as pd, joblib
ROOT = Path(__file__).resolve().parents[1]; sys.path.insert(0, str(ROOT / "src"))
from datasmart import features as F
A = ROOT / "analysis"; D = ROOT / "web" / "data"; D.mkdir(parents=True, exist_ok=True)
def dump(name, obj):
    json.dump(obj, open(D / f"{name}.json", "w"), ensure_ascii=False, separators=(",", ":"), allow_nan=False, default=float)
def rec(csv, nd=4, cols=None):
    t = pd.read_csv(csv);
    if cols: t = t[cols]
    t = t.round(nd).astype(object).where(t.notna(), None); return t.to_dict("records")
def clean(o):
    if isinstance(o, dict): return {k: clean(v) for k, v in o.items()}
    if isinstance(o, list): return [clean(v) for v in o]
    if isinstance(o, float) and (np.isnan(o) or np.isinf(o)): return None
    return o

df = pd.read_csv(ROOT / "data/processed/pedidos_modelo.csv", parse_dates=["order_purchase_timestamp"])
meta = joblib.load(ROOT / "models/clasificador_meta.joblib")
df["mes"] = df.order_purchase_timestamp.dt.to_period("M").astype(str)

# ---- 1. resumen y exploración ----
kpi = dict(pedidos=len(df), clientes=int(df.customer_unique_id.nunique()), ingreso=float(df.valor_pago.sum()), ticket=float(df.valor_pago.mean()),
           puntaje=float(df.review_score.mean()), dias_entrega=float(df.dias_entrega.mean()), pct_tardias=float(df.entrega_tardia.mean()),
           pct_resena_baja=float(df.resena_baja.mean()), distancia_media=float(df.distancia_km.mean()), vendedores=int(pd.read_csv(ROOT/"data/raw/olist/olist_sellers_dataset.csv").shape[0]),
           periodo=[str(df.order_purchase_timestamp.min().date()), str(df.order_purchase_timestamp.max().date())])
mens = df.groupby("mes").agg(pedidos=("order_id", "size"), ingreso=("valor_pago", "sum"), pct_tardias=("entrega_tardia", "mean"), puntaje=("review_score", "mean"), dias=("dias_entrega", "mean")).reset_index()
mens = mens[mens.pedidos >= 100]
cat = df.groupby("categoria_principal").agg(pedidos=("order_id", "size"), ingreso=("valor_pago", "sum"), pct_tardias=("entrega_tardia", "mean"), puntaje=("review_score", "mean")).sort_values("ingreso", ascending=False).head(15).reset_index()
est = df.groupby("customer_state").agg(pedidos=("order_id", "size"), ingreso=("valor_pago", "sum"), pct_tardias=("entrega_tardia", "mean"), puntaje=("review_score", "mean"),
                                       dias=("dias_entrega", "mean"), distancia=("distancia_km", "median"), plazo=("dias_estimados", "median"), lat=("lat", "median"), lng=("lng", "median")).reset_index()
bins = pd.cut(df.dias_entrega, [0, 5, 10, 15, 20, 30, 200], labels=["≤5", "6–10", "11–15", "16–20", "21–30", ">30"])
ent_punt = df.groupby(bins, observed=True).agg(pedidos=("order_id", "size"), puntaje=("review_score", "mean"), pct_baja=("resena_baja", "mean")).reset_index().rename(columns={"dias_entrega": "rango"})
tard_punt = df.groupby("entrega_tardia").agg(pedidos=("order_id", "size"), puntaje=("review_score", "mean"), pct_baja=("resena_baja", "mean")).reset_index()
dist_dec = df.dropna(subset=["distancia_km"]).groupby(pd.qcut(df.distancia_km.dropna(), 10, duplicates="drop"), observed=True).agg(dist=("distancia_km", "median"), pct_tardias=("entrega_tardia", "mean"), dias=("dias_entrega", "mean")).reset_index(drop=True)
pts = df.dropna(subset=["lat", "lng"]).copy(); pts["gx"] = (pts.lng / 0.9).round() * 0.9; pts["gy"] = (pts.lat / 0.9).round() * 0.9
grid = pts.groupby(["gx", "gy"]).agg(n=("order_id", "size"), tard=("entrega_tardia", "mean"), dias=("dias_entrega", "mean")).reset_index(); grid = grid[grid.n >= 8]
dump("resumen", clean(dict(kpi=kpi, mensual=mens.round(4).to_dict("records"), categorias=cat.round(4).to_dict("records"), estados=est.round(4).to_dict("records"),
                           entrega_puntaje=ent_punt.astype({"rango": str}).round(4).to_dict("records"), tardia_puntaje=tard_punt.round(4).to_dict("records"),
                           distancia_deciles=dist_dec.round(4).to_dict("records"), grilla=grid.round(3).to_dict("records"),
                           puntajes=rec(A / "outputs_olist/04_distribucion_puntuacion_resenas.csv"))))
# ---- 2. entregables 2 y 3 ----
cl = A / "outputs_s13"; s10 = A / "outputs_s10"
dump("entregable23", clean(dict(
    reglas=rec(s10 / "04_top_reglas.csv", 4), alg=rec(s10 / "03_comparacion_algoritmos.csv"), param=rec(s10 / "05_parametros_asociacion.csv"),
    k=rec(cl / "01_kmeans_seleccion_k.csv"), clus_comp=rec(cl / "02_clustering_comparacion.csv"), perfil=rec(cl / "03_perfil_clusters.csv", 2), pca=rec(cl / "04_pca_muestra.csv", 3)[:3000],
    dbscan=rec(cl / "05_dbscan_barrido.csv"), serie=rec(cl / "06_serie_diaria.csv", 0), s_comp=rec(cl / "07_series_comparacion.csv", 3), holdout=rec(cl / "08_series_holdout.csv", 0),
    pron=rec(cl / "09_pronostico_90d.csv", 0), pron_h=rec(cl / "10_pronostico_horizontes.csv", 0), nodos=rec(cl / "11_grafo_nodos.csv", 4), aristas=rec(cl / "12_grafo_aristas.csv"),
    grafo=rec(cl / "13_grafo_resumen.csv", 4), reg_v=rec(A / "outputs_s16/12_regresion_versiones.csv", 4), reg_imp=rec(A / "outputs_s16/12_regresion_v3_importancia.csv", 4),
    reg_rp=rec(A / "outputs_s16/12_regresion_v3_real_vs_pred.csv", 2)[:1500])))
# ---- 3. clasificación y explicabilidad ----
o = A / "outputs_s16"; fin = json.load(open(o / "13_final.json"))
dump("clasificacion", clean(dict(final=fin, modelos=rec(o / "13_clasificacion_modelos.csv"), balanceo=rec(o / "13_balanceo.csv"), hiper=rec(o / "13_hiperparametros.csv"),
    roc=rec(o / "13_curva_roc.csv", 4), pr=rec(o / "13_curva_pr.csv", 4), calib=rec(o / "13_calibracion.csv"), bandas=rec(o / "13_bandas.csv"),
    perm=rec(o / "14_importancia_permutacion.csv"), shap=rec(o / "14_shap_global.csv"), nube=rec(o / "14_shap_nube.csv", 3), casos=json.load(open(o / "14_casos.json")),
    acuerdo=rec(o / "14_acuerdo_shap_lime.csv"), res_expl=json.load(open(o / "14_resumen.json")),
    ing=rec(o / "17_comparacion_ingenieria.csv"), vif=rec(o / "17_vif.csv", 3), pca_var=rec(o / "17_pca_varianza.csv"), ing_res=json.load(open(o / "17_resumen.json")), prep=rec(o / "19_codificacion_escalamiento.csv"), satis=rec(o / "19_satisfaccion.csv"), satis_tardia=json.load(open(o / "19_resumen.json")))))
# ---- 4. texto y monitoreo ----
dump("texto", clean(dict(modelos=rec(o / "15_sentimiento_modelos.csv"), matriz=rec(o / "15_sentimiento_matriz.csv"), aspectos=rec(o / "15_aspectos.csv"), temas=rec(o / "15_temas.csv"),
    terminos=rec(o / "15_terminos_negativos.csv", 3)[:25], pneg=rec(o / "15_pneg_por_estrellas.csv"), riesgo=rec(o / "15_texto_vs_riesgo.csv"), resumen=json.load(open(o / "15_resumen.json")),
    coef_top=rec(o / "15_coeficientes.csv", 3)[:18] + rec(o / "15_coeficientes.csv", 3)[-18:])))
shutil.copy(A / "web_data/texto_modelo.json", D / "texto_modelo.json")
dump("monitoreo", clean(dict(sim=rec(o / "16_simulacion_mensual.csv", 4), psi=rec(o / "16_psi_mensual.csv", 4), pol=rec(o / "16_politicas_resumen.csv"), reg=rec(o / "16_regresion_mensual.csv", 3),
    versiones=json.load(open(ROOT / "models/registro/versiones.json")), resumen=json.load(open(o / "16_resumen.json")), temporal=json.load(open(o / "16_validacion_temporal.json")),
    auditoria=[json.loads(l) for l in open(o / "16_auditoria.jsonl")][:40], nombres={k: v for k, v in F.NOMBRES.items()})))
# ---- 5. modelo para el simulador (árboles XGBoost compactos) ----
mj = json.load(open(ROOT / "models/clasificador_xgb.json")); trees = mj["learner"]["gradient_booster"]["model"]["trees"]
base = float(mj["learner"]["learner_model_param"]["base_score"].strip("[]"))
compact = [dict(f=t["split_indices"], c=t["split_conditions"], l=t["left_children"], r=t["right_children"], d=t["default_left"]) for t in trees]
cols = meta["columns"]; X = F.build_X(df, meta["num"], log=True, drop_first=False)
assert list(X.columns) == cols
NUM = meta["num"]; q = df[NUM].quantile([.01, .5, .99]).T
rng = {c: dict(min=float(q.loc[c, .01]), med=float(q.loc[c, .5]), max=float(q.loc[c, .99])) for c in NUM}
ruta = df.groupby(["seller_state", "customer_state"]).agg(n=("order_id", "size"), dist=("distancia_km", "median"), plazo=("dias_estimados", "median"), tarde=("entrega_tardia", "mean")).reset_index()
ruta = ruta[ruta.n >= 15]
rs = np.random.RandomState(7); ibg = rs.choice(meta["itr"], 100, replace=False)
casos = []
ite = np.array(meta["ite"]); sel = rs.choice(len(ite), 300, replace=False)
dump("modelo", clean(dict(
    base_margin=float(np.log(base / (1 - base))), trees=compact, columns=cols, num=NUM, log_cols=sorted(F.LOG_COLS), cats=sorted(set(c[4:] for c in cols if c.startswith("cat_"))),
    states=sorted(set(c[15:] for c in cols if c.startswith("customer_state_"))), rangos=rng, q60=meta["q60"], q90=meta["q90"], umbral=meta["umbral_val"], nombres=F.NOMBRES,
    medianas_fill={c: float(df[c].median()) for c in ("dias_aprobacion", "distancia_km", "vend_hist_dias", "vend_hist_tardio", "carga_rel")},
    rutas=ruta.round(3).to_dict("records"), fondo=X.iloc[ibg].round(6).values.tolist(),
    prueba_X=X.iloc[ite[sel]].values.tolist(),
    prueba_p=[float(v) for v in joblib.load(ROOT / "models/clasificador_xgb.joblib").predict_proba(X.iloc[ite[sel]])[:, 1]])))
print({p.name: round(p.stat().st_size / 1024) for p in sorted(D.glob("*.json"))}, "KB")
