"""Entregable 4 - Ingeniería de características adicional: VIF, correlación, PCA, selección, LDA/QDA."""
import sys, json, warnings
from pathlib import Path
import numpy as np, pandas as pd
from sklearn.decomposition import PCA
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegression
from sklearn.discriminant_analysis import LinearDiscriminantAnalysis as LDA, QuadraticDiscriminantAnalysis as QDA
from sklearn.metrics import roc_auc_score, average_precision_score
from statsmodels.stats.outliers_influence import variance_inflation_factor
warnings.filterwarnings("ignore")
ROOT = Path(__file__).resolve().parents[1]; sys.path.insert(0, str(ROOT / "src"))
from datasmart import features as F
OUT = ROOT / "analysis" / "outputs_s16"
df = pd.read_csv(ROOT / "data/processed/pedidos_modelo.csv")
num = [n for n, _ in F.NUM_FINAL]; y = df.entrega_tardia.values
Xn = F.build_X(df, num, log=True, drop_first=False)
cols = [F.grupo_de(c) for c in Xn.columns]
numcols = list(num)
Xnum = Xn[numcols]
# --- VIF y correlación ---
Z = StandardScaler().fit_transform(Xnum)
vif = pd.DataFrame({"variable": [F.NOMBRES.get(c, c) for c in numcols], "col": numcols,
                    "VIF": [variance_inflation_factor(np.c_[np.ones(len(Z)), Z], i + 1) for i in range(Z.shape[1])]}).sort_values("VIF", ascending=False)
vif.to_csv(OUT / "17_vif.csv", index=False); print(vif.round(2).head(8).to_string(index=False))
C = pd.DataFrame(Z, columns=numcols).corr().abs().values.copy(); np.fill_diagonal(C, 0)
i, j = np.unravel_index(C.argmax(), C.shape); print("máx |corr|:", numcols[i], numcols[j], round(C.max(), 3))
pd.DataFrame(Z, columns=numcols).corr().to_csv(OUT / "17_correlacion.csv")
# --- split ---
itr, ite = F.split_clasificacion(df)
def ev(m, Xa, Xb):
    m.fit(Xa[itr], y[itr]); p = m.predict_proba(Xb[ite])[:, 1]
    return roc_auc_score(y[ite], p), average_precision_score(y[ite], p)
Xa = Xn.values.astype(float); sc = StandardScaler().fit(Xa[itr]); Xs = sc.transform(Xa)
Xns = StandardScaler().fit(Xnum.values[itr]).transform(Xnum.values)
# --- PCA ---
pca = PCA().fit(Xns[itr]); cum = np.cumsum(pca.explained_variance_ratio_)
k90 = int(np.searchsorted(cum, .90) + 1); print("componentes para 90%:", k90, "de", Xns.shape[1])
pd.DataFrame({"componente": np.arange(1, len(cum) + 1), "var_expl": pca.explained_variance_ratio_, "acumulada": cum}).to_csv(OUT / "17_pca_varianza.csv", index=False)
load = pd.DataFrame(pca.components_[:3].T, index=[F.NOMBRES.get(c, c) for c in numcols], columns=["PC1", "PC2", "PC3"]); load.to_csv(OUT / "17_pca_cargas.csv")
Zp = PCA(k90).fit(Xns[itr]).transform(Xns)
cat_cols = [c for c in Xn.columns if c not in numcols]
Xpc = np.c_[Zp, Xn[cat_cols].values.astype(float)]
# --- selección: sin las variables con VIF alto ---
imp = pd.read_csv(OUT / '14_importancia_permutacion.csv')
sel = [g for g in imp.grupo if g in numcols][:6]  # 6 numéricas más importantes (permutación)
Xsel = np.c_[StandardScaler().fit(Xnum[sel].values[itr]).transform(Xnum[sel].values), Xn[cat_cols].values.astype(float)]
res = []
LR = lambda: LogisticRegression(max_iter=2000, class_weight="balanced", C=.5)
for nombre, Xm, mod in [
    ("Regresión logística (todas, 61)", Xs, LR()),
    ("Regresión logística (6 numéricas top + categorías)", Xsel, LR()),
    (f"Regresión logística (PCA {k90} + categorías)", np.c_[StandardScaler().fit(Xpc[itr]).transform(Xpc)], LR()),
    ("LDA (numéricas)", Xns, LDA()),
    ("QDA (numéricas)", Xns, QDA(reg_param=0.1)),
    ("LDA (PCA)", Zp, LDA()),
]:
    a, b = ev(mod, Xm, Xm); res.append(dict(modelo=nombre, n_variables=Xm.shape[1], AUC_ROC=round(a, 4), AUC_PR=round(b, 4)))
r = pd.DataFrame(res); r.to_csv(OUT / "17_comparacion_ingenieria.csv", index=False); print(r.to_string(index=False))
json.dump(dict(k90=k90, n_num=len(numcols), vif_max=float(vif.VIF.max()), vif_gt5=vif[vif.VIF > 5].col.tolist(), seleccion=sel,
               corr_max=float(C.max()), par=[numcols[i], numcols[j]]), open(OUT / "17_resumen.json", "w"), indent=1)
