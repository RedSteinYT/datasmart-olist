"""Entregable 4 - Explicabilidad del clasificador de riesgo de entrega tardía.

* Importancia por permutación agrupada (cada variable completa, con sus columnas one-hot juntas).
* SHAP (librería `shap`, TreeExplainer exacto) en escala de probabilidad (puntos porcentuales).
* LIME (librería `lime`) sobre las 61 columnas, para contrastar con SHAP en casos concretos.
* Cinco casos de estudio: riesgo alto acertado, riesgo bajo acertado, riesgo medio, falsa alarma, caso difícil.
"""
import sys, json, warnings
from pathlib import Path
import numpy as np, pandas as pd, joblib
from scipy.stats import spearmanr
import shap
from lime.lime_tabular import LimeTabularExplainer
from sklearn.metrics import average_precision_score, roc_auc_score

warnings.filterwarnings("ignore")
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from datasmart import features as F

OUT = ROOT / "analysis" / "outputs_s16"
df = pd.read_csv(ROOT / "data/processed/pedidos_modelo.csv")
model = joblib.load(ROOT / "models" / "clasificador_xgb.joblib")
meta = joblib.load(ROOT / "models" / "clasificador_meta.joblib")
X = F.build_X(df, meta["num"], log=True, drop_first=False)
assert list(X.columns) == meta["columns"]
y = df.entrega_tardia.values
Xtr, Xte = X.iloc[meta["itr"]], X.iloc[meta["ite"]]
yte = y[meta["ite"]]
p_te = model.predict_proba(Xte)[:, 1]
grupo = np.array([F.grupo_de(c) for c in X.columns])
nombre_g = lambda g: F.NOMBRES.get(g, g)
rng = np.random.RandomState(42)

# ---------- 1. Importancia por permutación agrupada (caída del AUC-PR en la prueba) ----------
base = average_precision_score(yte, p_te)
filas = []
for g in dict.fromkeys(grupo):
    cols = list(X.columns[grupo == g]); caidas = []
    for _ in range(5):
        Xp = Xte.copy(); perm = rng.permutation(len(Xp)); Xp[cols] = Xp[cols].values[perm]
        caidas.append(base - average_precision_score(yte, model.predict_proba(Xp)[:, 1]))
    filas.append(dict(grupo=g, variable=nombre_g(g), caida_AUC_PR=float(np.mean(caidas))))
perm = pd.DataFrame(filas).sort_values("caida_AUC_PR", ascending=False)
perm.to_csv(OUT / "14_importancia_permutacion.csv", index=False); print(perm.head(8).round(4).to_string(index=False))

# ---------- 2. SHAP en escala de probabilidad ----------
fondo = Xtr.iloc[rng.choice(len(Xtr), 100, replace=False)]
expl = shap.TreeExplainer(model, data=fondo, feature_perturbation="interventional", model_output="probability")
base_prob = float(expl.expected_value)
print("probabilidad media de referencia (fondo):", round(base_prob, 4))
n_glob = 600
ig = rng.choice(len(Xte), n_glob, replace=False)
sv = expl.shap_values(Xte.iloc[ig], check_additivity=False)
sv = np.asarray(sv)
if sv.ndim == 3: sv = sv[..., 1]
adit = np.abs(sv.sum(1) + base_prob - model.predict_proba(Xte.iloc[ig])[:, 1])
print("error máximo de aditividad SHAP:", float(adit.max()))
# agrupar columnas one-hot por variable original
svg = pd.DataFrame({g: sv[:, grupo == g].sum(1) for g in dict.fromkeys(grupo)})
glob = pd.DataFrame({"grupo": svg.columns, "variable": [nombre_g(g) for g in svg.columns],
                     "shap_abs_medio_pp": 100 * svg.abs().mean().values,
                     "shap_medio_pp": 100 * svg.mean().values}).sort_values("shap_abs_medio_pp", ascending=False)
glob.to_csv(OUT / "14_shap_global.csv", index=False); print(glob.head(8).round(3).to_string(index=False))
# nube de puntos tipo "beeswarm" (valor normalizado de la variable vs efecto)
Xg = Xte.iloc[ig]
rows = []
for g in glob.grupo.head(10):
    if g in ("customer_state", "cat"): continue
    v = Xg[g].values; z = (v - np.nanpercentile(v, 2)) / max(np.nanpercentile(v, 98) - np.nanpercentile(v, 2), 1e-9)
    for a, b, c in zip(np.clip(z, 0, 1), svg[g].values * 100, v):
        rows.append((g, round(float(a), 3), round(float(b), 3), round(float(c), 4)))
pd.DataFrame(rows, columns=["grupo", "valor_norm", "shap_pp", "valor"]).to_csv(OUT / "14_shap_nube.csv", index=False)

# ---------- 3. Casos de estudio ----------
q60, q90 = meta["q60"], meta["q90"]
cand = pd.DataFrame({"i": np.arange(len(Xte)), "p": p_te, "y": yte})
casos = {
    "Riesgo alto y se cumplió el retraso": cand[(cand.p >= q90) & (cand.y == 1)].sort_values("p").iloc[len(cand[(cand.p >= q90) & (cand.y == 1)]) // 2].i,
    "Riesgo bajo y llegó a tiempo": cand[(cand.p < q60) & (cand.y == 0)].sort_values("p").iloc[len(cand[(cand.p < q60) & (cand.y == 0)]) // 2].i,
    "Riesgo medio": cand[(cand.p >= q60) & (cand.p < q90)].sort_values("p").iloc[len(cand[(cand.p >= q60) & (cand.p < q90)]) // 2].i,
    "Falsa alarma: riesgo alto pero llegó a tiempo": cand[(cand.p >= q90) & (cand.y == 0)].sort_values("p").iloc[-len(cand[(cand.p >= q90) & (cand.y == 0)]) // 3].i,
    "Caso difícil: llegó tarde con riesgo bajo": cand[(cand.p < q60) & (cand.y == 1)].sort_values("p").iloc[len(cand[(cand.p < q60) & (cand.y == 1)]) // 2].i,
}
fondo_l = Xtr.sample(4000, random_state=1)
cat_idx = [i for i, c in enumerate(X.columns) if grupo[i] in ("customer_state", "cat") or c == "mismo_estado"]
lime = LimeTabularExplainer(fondo_l.values, feature_names=list(X.columns), categorical_features=cat_idx,
                            class_names=["a tiempo", "tarde"], discretize_continuous=True, random_state=0)
casos_out, acuerdo = [], []
for nombre, i in casos.items():
    x = Xte.iloc[[int(i)]]
    s1 = np.asarray(expl.shap_values(x, check_additivity=False)); s1 = (s1[..., 1] if s1.ndim == 3 else s1)[0]
    ex = lime.explain_instance(x.values[0], model.predict_proba, num_features=len(X.columns), num_samples=3000, labels=(1,))
    lw = np.zeros(len(X.columns))
    for j, w in ex.as_map()[1]: lw[j] = w
    sg = pd.Series(s1).groupby(grupo).sum(); lg = pd.Series(lw).groupby(grupo).sum()
    sg = sg.reindex(dict.fromkeys(grupo)); lg = lg.reindex(sg.index)
    rho = float(spearmanr(sg.abs(), lg.abs())[0])
    fila_o = df.iloc[meta["ite"][int(i)]]
    detalle = [dict(grupo=g, variable=nombre_g(g), valor=(str(fila_o.get(g, "")) if g not in ("cat",) else str(fila_o.categoria_principal)),
                    shap_pp=float(100 * sg[g]), lime=float(lg[g])) for g in sg.index]
    detalle.sort(key=lambda d: -abs(d["shap_pp"]))
    casos_out.append(dict(caso=nombre, riesgo=float(p_te[int(i)]), real="Llegó tarde" if yte[int(i)] else "A tiempo",
                          corr_shap_lime=rho, base_pp=100 * base_prob,
                          banda=("Alto" if p_te[int(i)] >= q90 else "Medio" if p_te[int(i)] >= q60 else "Bajo"),
                          factores=detalle[:8]))
    acuerdo.append(dict(caso=nombre, riesgo=float(p_te[int(i)]), real=casos_out[-1]["real"], corr_shap_lime=rho))
    print(f"{nombre}: riesgo {p_te[int(i)]:.1%}, real={casos_out[-1]['real']}, rho={rho:.2f}",
          "|", "; ".join(f"{d['variable'][:28]} {d['shap_pp']:+.1f}" for d in detalle[:3]))
pd.DataFrame(acuerdo).to_csv(OUT / "14_acuerdo_shap_lime.csv", index=False)
json.dump(casos_out, open(OUT / "14_casos.json", "w"), ensure_ascii=False, indent=1)
json.dump(dict(base_prob=base_prob, adit_max=float(adit.max()), n_global=n_glob), open(OUT / "14_resumen.json", "w"))
