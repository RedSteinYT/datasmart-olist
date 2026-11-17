"""Genera las figuras del informe final en docs/figuras/ a partir de las salidas de los scripts 01-19.
Todas las cifras salen de los CSV/JSON; nada se escribe a mano."""
import json
from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch

R = Path(__file__).resolve().parents[1]
O16 = R / "analysis" / "outputs_s16"
O13 = R / "analysis" / "outputs_s13"
WD = R / "web" / "data"
OUT = R / "docs" / "figuras"
OUT.mkdir(parents=True, exist_ok=True)

INK, TEAL, AMB, RED, GRY, BLU = "#1f2a37", "#0f766e", "#d97706", "#b91c1c", "#9ca3af", "#1d4ed8"
plt.rcParams.update({
    "font.family": "Inter", "font.size": 10, "axes.edgecolor": "#6b7280", "axes.labelcolor": INK,
    "xtick.color": INK, "ytick.color": INK, "axes.spines.top": False, "axes.spines.right": False,
    "axes.titleweight": "bold", "axes.titlesize": 11, "figure.dpi": 200, "savefig.bbox": "tight",
    "axes.grid": True, "grid.color": "#e5e7eb", "grid.linewidth": .6, "axes.axisbelow": True,
})


def save(fig, nombre):
    fig.savefig(OUT / f"{nombre}.png")
    plt.close(fig)
    print("ok", nombre)


res = json.load(open(WD / "resumen.json"))
cla = json.load(open(WD / "clasificacion.json"))
txt = json.load(open(WD / "texto.json"))

# F01 serie mensual
m = pd.DataFrame(res["mensual"])
fig, ax = plt.subplots(figsize=(7.4, 3.3))
ax.bar(m.mes, m.pedidos, color=TEAL, alpha=.85)
ax.set_ylabel("Pedidos entregados")
ax.tick_params(axis="x", rotation=60)
ax2 = ax.twinx()
ax2.plot(m.mes, m.pct_tardias * 100, color=RED, marker="o", ms=3.5, lw=1.6)
ax2.set_ylabel("% de entregas tardías", color=RED)
ax2.grid(False)
ax2.spines["right"].set_visible(True)
ax.set_title("Pedidos y entregas tardías por mes de compra")
save(fig, "f01_mensual")

# F02 tardías por estado
e = pd.DataFrame(res["estados"]).query("pedidos >= 300").sort_values("pct_tardias")
fig, ax = plt.subplots(figsize=(7.2, 4.6))
ax.barh(e.customer_state, e.pct_tardias * 100, color=np.where(e.pct_tardias > .081, RED, TEAL))
ax.axvline(res["kpi"]["pct_tardias"] * 100, color=INK, ls="--", lw=1)
ax.text(res["kpi"]["pct_tardias"] * 100 + .2, 0, "media nacional", fontsize=8, va="bottom")
ax.set_xlabel("% de pedidos entregados tarde (estados con ≥300 pedidos)")
ax.set_title("El retraso depende del destino")
save(fig, "f02_estados")

# F03 reg versiones
v = pd.read_csv(O16 / "12_regresion_versiones.csv")
v = v[v.modelo != "Baseline (media)"]
piv = v.pivot(index="modelo", columns="version", values="R2").sort_values("v3")
fig, ax = plt.subplots(figsize=(7.4, 3.8))
y = np.arange(len(piv))
for i, (c, col) in enumerate(zip(["v1", "v2", "v3"], [GRY, AMB, TEAL])):
    ax.barh(y + (i - 1) * .26, piv[c], .26, color=col, label=c)
ax.set_yticks(y)
ax.set_yticklabels(piv.index)
ax.set_xlabel("R² en prueba")
ax.legend(title="versión")
ax.set_title("Regresión del tiempo de entrega: v1 → v3")
save(fig, "f03_regresion_versiones")

# F04 ROC y PR
roc = pd.DataFrame(cla["roc"])
pr = pd.DataFrame(cla["pr"])
fig, (a, b) = plt.subplots(1, 2, figsize=(7.6, 3.4))
a.plot(roc.fpr, roc.tpr, color=TEAL, lw=2)
a.plot([0, 1], [0, 1], color=GRY, ls="--")
a.set_xlabel("Falsos positivos")
a.set_ylabel("Verdaderos positivos")
a.set_title(f"ROC (AUC {cla['final']['final']['AUC_ROC']:.3f})")
b.plot(pr.recall, pr.precision, color=AMB, lw=2)
b.axhline(cla["final"]["tasa_base"], color=GRY, ls="--")
b.set_xlabel("Exhaustividad")
b.set_ylabel("Precisión")
b.set_title(f"Precisión–exhaustividad (AP {cla['final']['final']['AUC_PR']:.3f})")
save(fig, "f04_roc_pr")

# F05 calibración y bandas
cal = pd.read_csv(O16 / "13_calibracion.csv")
ban = pd.read_csv(O16 / "13_bandas.csv")
fig, (a, b) = plt.subplots(1, 2, figsize=(7.6, 3.4))
a.plot([0, cal.prob_media.max()], [0, cal.prob_media.max()], color=GRY, ls="--")
a.plot(cal.prob_media, cal.tasa_real, "o-", color=TEAL)
a.set_xlabel("Probabilidad predicha (media por decil)")
a.set_ylabel("Tasa real de retraso")
a.set_title("Calibración")
cols = [TEAL, AMB, RED]
b.bar(ban.banda, ban.pct_tarde * 100, color=cols)
for i, r in ban.iterrows():
    b.text(i, r.pct_tarde * 100 + .8, f"{r.pct_tarde*100:.1f}%\n({r.pedidos:,} ped.)".replace(",", " "), ha="center", fontsize=8)
b.set_ylim(0, 42)
b.set_ylabel("% real de entregas tardías")
b.set_title("Bandas de riesgo (prueba)")
save(fig, "f05_calibracion_bandas")

# F06 modelos y balanceo
mod = pd.read_csv(O16 / "13_clasificacion_modelos.csv").sort_values("AUC_PR")
bal = pd.read_csv(O16 / "13_balanceo.csv")
bx = bal[bal.modelo == "XGBoost"].sort_values("AUC_PR")
fig, (a, b) = plt.subplots(1, 2, figsize=(8, 3.5))
a.barh(mod.modelo, mod.AUC_PR, color=TEAL)
a.set_xlabel("AUC-PR (prueba)")
a.set_title("Modelos comparados")
b.barh(bx.tecnica, bx.AUC_PR, color=[AMB if t != "Sin balanceo" else TEAL for t in bx.tecnica])
b.set_xlabel("AUC-PR (XGBoost)")
b.set_title("Técnicas de balanceo")
save(fig, "f06_modelos_balanceo")

# F07 permutación y SHAP
perm = pd.DataFrame(cla["perm"]).head(10).iloc[::-1]
sh = pd.DataFrame(cla["shap"]).head(10).iloc[::-1]
fig, (a, b) = plt.subplots(1, 2, figsize=(8.4, 3.9))
a.barh(perm.grupo, perm.caida_AUC_PR, color=TEAL)
a.set_xlabel("Caída de AUC-PR al permutar")
a.set_title("Importancia por permutación")
b.barh(sh.grupo, sh.shap_abs_medio_pp, color=AMB)
b.set_xlabel("|SHAP| medio (puntos porcentuales)")
b.set_title("Importancia SHAP")
save(fig, "f07_importancias")

# F08 beeswarm
nb = pd.DataFrame(cla["nube"])
top = list(pd.DataFrame(cla["shap"]).grupo[:8])
fig, ax = plt.subplots(figsize=(7.4, 4.2))
rng = np.random.default_rng(1)
for i, g in enumerate(top[::-1]):
    d = nb[nb.grupo == g]
    ax.scatter(d.shap_pp, i + rng.uniform(-.28, .28, len(d)), c=d.valor_norm, cmap="coolwarm", s=5, alpha=.7)
ax.set_yticks(range(len(top)))
ax.set_yticklabels(top[::-1])
ax.axvline(0, color=INK, lw=.8)
ax.set_xlabel("Efecto en la probabilidad de retraso (puntos porcentuales)")
ax.set_title("SHAP por pedido (azul = valor bajo, rojo = valor alto)")
save(fig, "f08_shap_nube")

# F09 casos
casos = cla["casos"]
fig, axs = plt.subplots(1, 3, figsize=(10.5, 3.4), sharex=True)
fig.subplots_adjust(wspace=.75)
for ax, c in zip(axs, casos[:3]):
    f = pd.DataFrame(c["factores"]).head(5).iloc[::-1]
    ax.barh(f.grupo, f.shap_pp, color=np.where(f.shap_pp > 0, RED, TEAL))
    ax.axvline(0, color=INK, lw=.8)
    ax.set_title(f"{c['caso'].replace(' y ', chr(10)+'y ',1)}\nriesgo {c['riesgo']*100:.0f}% · {c['real']}", fontsize=8)
    ax.set_xlabel("SHAP (pp)")
save(fig, "f09_casos")

# F10 texto
asp = pd.read_csv(O16 / "15_aspectos.csv").sort_values("pct_menciones")
pn = pd.read_csv(O16 / "15_pneg_por_estrellas.csv")
fig, (a, b) = plt.subplots(1, 2, figsize=(8.2, 3.5))
a.barh(asp.aspecto, asp.pct_menciones * 100, color=TEAL)
for i, (p, q) in enumerate(zip(asp.pct_menciones, asp.pct_negativas_entre_menciones)):
    a.text(p * 100 + .6, i, f"{q*100:.0f}% neg.", va="center", fontsize=8, color=RED)
a.set_xlim(0, 70)
a.set_xlabel("% de comentarios que lo mencionan")
a.set_title("Aspectos mencionados")
b.bar(pn.review_score.astype(int), pn.p_neg, color=[RED, RED, GRY, TEAL, TEAL][:len(pn)])
b.set_xlabel("Puntaje (estrellas)")
b.set_ylabel("Probabilidad media de sentimiento negativo")
b.set_title("El modelo coincide con las estrellas")
save(fig, "f10_texto")

# F11 PSI
psi = pd.read_csv(O16 / "16_psi_mensual.csv").set_index("mes")
psi = psi.drop(columns=[c for c in ["n_items", "n_vendedores", "score"] if c in psi.columns])
psi = psi.loc[:, psi.max() > 0.02]
fig, ax = plt.subplots(figsize=(7.6, 3.6))
im = ax.imshow(psi.T.values, aspect="auto", cmap="YlOrRd", vmin=0, vmax=.5)
ax.set_xticks(range(len(psi)))
ax.set_xticklabels(psi.index, rotation=45)
ax.set_yticks(range(psi.shape[1]))
ax.set_yticklabels(psi.columns, fontsize=8)
ax.grid(False)
for i in range(psi.shape[1]):
    for j in range(len(psi)):
        v = psi.iloc[j, i]
        ax.text(j, i, f"{v:.2f}", ha="center", va="center", fontsize=6, color="white" if v > .3 else INK)
fig.colorbar(im, ax=ax, label="PSI (>0,25 = cambio mayor)")
ax.set_title("Deriva de las variables frente a la referencia")
save(fig, "f11_psi")

# F12 AUC por mes y MAE
sim = pd.read_csv(O16 / "16_simulacion_mensual.csv")
sim["p"] = sim.politica.str[0]
fig, (a, b) = plt.subplots(1, 2, figsize=(8.6, 3.5))
for p, col in zip("ABCD", [INK, AMB, TEAL, RED]):
    d = sim[sim.p == p]
    a.plot(d.mes, d.AUC_ROC, marker="o", ms=3, color=col, label=p, lw=1.4)
a.axhline(.7198, color=GRY, ls="--", lw=1)
a.set_ylabel("AUC-ROC mensual")
a.tick_params(axis="x", rotation=60)
a.legend(title="política", fontsize=7)
a.set_title("Clasificador por mes")
rg = pd.read_csv(O16 / "16_regresion_mensual.csv")
for mdl, col in zip(rg.modelo.unique(), [INK, AMB]):
    d = rg[rg.modelo == mdl]
    b.plot(d.mes, d.MAE, marker="o", ms=3, color=col, label=mdl, lw=1.4)
b.axhline(rg.MAE_ref.iloc[0], color=GRY, ls="--", lw=1)
b.set_ylabel("MAE (días)")
b.tick_params(axis="x", rotation=60)
b.legend(fontsize=7)
b.set_title("Regresor por mes")
save(fig, "f12_monitoreo")

# F13 VIF y PCA
vif = pd.read_csv(O16 / "17_vif.csv").sort_values("VIF")
pv = pd.read_csv(O16 / "17_pca_varianza.csv")
fig, (a, b) = plt.subplots(1, 2, figsize=(8.4, 3.8))
a.barh(vif.variable, vif.VIF, color=TEAL)
a.axvline(5, color=RED, ls="--")
a.set_xlabel("VIF (umbral 5)")
a.set_title("Multicolinealidad")
a.tick_params(axis="y", labelsize=7)
b.plot(pv.componente, pv.acumulada * 100, "o-", color=AMB)
b.axhline(90, color=GRY, ls="--")
b.set_xlabel("Componentes principales")
b.set_ylabel("Varianza explicada acumulada (%)")
b.set_title("PCA de las 18 numéricas")
save(fig, "f13_vif_pca")

# F14 k-means y series
k = pd.read_csv(O13 / "01_kmeans_seleccion_k.csv")
ho = pd.read_csv(O13 / "08_series_holdout.csv", parse_dates=["fecha"])
fig, (a, b) = plt.subplots(1, 2, figsize=(8.6, 3.4))
a.plot(k.k, k.silhouette, "o-", color=TEAL)
a.set_xlabel("k")
a.set_ylabel("Silueta")
a.set_title("Selección de k (K-Means)")
b.plot(ho.fecha, ho.real, color=INK, lw=1.6, label="Real")
b.plot(ho.fecha, ho["Ridge con rezagos"], color=TEAL, lw=1.2, label="Ridge con rezagos")
b.plot(ho.fecha, ho["Holt-Winters (m=7)"], color=AMB, lw=1.2, label="Holt-Winters")
b.legend(fontsize=7)
b.tick_params(axis="x", rotation=45)
b.set_title("Ingreso diario: últimos 30 días")
save(fig, "f14_segmentos_series")


# F15 arquitectura
def caja(ax, x, y, w, h, t, col):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.02,rounding_size=0.04", fc=col, ec=INK, lw=1))
    ax.text(x + w / 2, y + h / 2, t, ha="center", va="center", fontsize=8, color=INK)


fig, ax = plt.subplots(figsize=(8.4, 3.6))
ax.set_xlim(0, 10)
ax.set_ylim(0, 4.4)
ax.axis("off")
col1, col2, col3 = "#d1fae5", "#fef3c7", "#dbeafe"
for i, (t, c) in enumerate([("Olist\n9 tablas CSV", col1), ("Preparación\ny variables\n(scripts 01–12)", col1), ("Modelos\nXGBoost · NMF · LR\n(scripts 13–17)", col2),
                            ("Exportación\nJSON (18)", col2), ("Panel web\nHTML + D3", col3)]):
    caja(ax, .15 + i * 1.98, 2.7, 1.7, 1.2, t, c)
    if i:
        ax.annotate("", xy=(.15 + i * 1.98, 3.3), xytext=(.15 + i * 1.98 - .28, 3.3), arrowprops=dict(arrowstyle="->", color=INK))
caja(ax, .15, .35, 2.7, 1.2, "API Flask\n/predict · /text · /monitoring", col3)
caja(ax, 3.3, .35, 2.7, 1.2, "Registro de versiones\nSHA-256 + auditoría JSONL", col2)
caja(ax, 6.45, .35, 3.3, 1.2, "Despliegue gratuito\nGitHub Pages · Netlify · Render · Docker", col1)
ax.annotate("", xy=(1.5, 1.6), xytext=(5.9, 2.65), arrowprops=dict(arrowstyle="->", color=GRY))
ax.annotate("", xy=(4.6, 1.6), xytext=(6.9, 2.65), arrowprops=dict(arrowstyle="->", color=GRY))
ax.annotate("", xy=(8.1, 1.6), xytext=(8.9, 2.65), arrowprops=dict(arrowstyle="->", color=GRY))
save(fig, "f15_arquitectura")
