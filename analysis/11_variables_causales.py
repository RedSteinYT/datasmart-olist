"""Entregable 4 - Variables causales (solo información disponible al momento de la compra).

* Historial del vendedor: días de entrega y % de entregas tardías de los pedidos que el
  vendedor YA había entregado cuando se hizo la compra (suavizado hacia la media de la plataforma
  en ese momento, para que pocos pedidos no den valores extremos).
* Carga relativa de la plataforma: pedidos de los últimos 7 días frente al promedio semanal de
  las 8 semanas previas.
Integra geolocalización y deja el dataset final data/processed/pedidos_modelo.csv (96 469 x 51).
"""
from pathlib import Path
import numpy as np, pandas as pd

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw" / "olist"
PROC = ROOT / "data" / "processed"
OUT = ROOT / "analysis" / "outputs_s16"
OUT.mkdir(parents=True, exist_ok=True)
K_SUAV = 10  # pseudo-observaciones del suavizado

df = pd.read_csv(PROC / "pedidos_procesados.csv",
                 parse_dates=["order_purchase_timestamp", "order_delivered_customer_date"])
geo = pd.read_csv(PROC / "geo_pedidos.csv")
df = df.merge(geo.drop(columns=["seller_principal"]), on="order_id", how="left")
df = df.merge(geo[["order_id", "seller_principal"]], on="order_id", how="left")

# ---------- 1. Historial causal del vendedor ----------
# media de plataforma "hasta ese momento" (pedidos ya entregados)
ent = df.sort_values("order_delivered_customer_date")
cd = ent.dias_entrega.cumsum().values
ct = ent.entrega_tardia.cumsum().values
deliv_t = ent.order_delivered_customer_date.values.astype("datetime64[ns]")
n_glob = np.searchsorted(deliv_t, df.order_purchase_timestamp.values.astype("datetime64[ns]"), side="right")
with np.errstate(invalid="ignore", divide="ignore"):
    g_dias = np.where(n_glob > 0, cd[np.maximum(n_glob - 1, 0)] / np.maximum(n_glob, 1), df.dias_entrega.mean())
    g_tard = np.where(n_glob > 0, ct[np.maximum(n_glob - 1, 0)] / np.maximum(n_glob, 1), df.entrega_tardia.mean())
# con muy pocos pedidos entregados la media global es inestable: usar la media general
g_dias = np.where(n_glob < 200, df.dias_entrega.mean(), g_dias)
g_tard = np.where(n_glob < 200, df.entrega_tardia.mean(), g_tard)
df["_g_dias"], df["_g_tard"] = g_dias, g_tard

n_h = np.zeros(len(df)); s_d = np.zeros(len(df)); s_t = np.zeros(len(df))
pos = {i: k for k, i in enumerate(df.index)}
for sid, g in df.groupby("seller_principal"):
    gd = g.sort_values("order_delivered_customer_date")
    dt = gd.order_delivered_customer_date.values.astype("datetime64[ns]")
    cdias = np.concatenate([[0], gd.dias_entrega.cumsum().values])
    ctard = np.concatenate([[0], gd.entrega_tardia.cumsum().values])
    idx = np.searchsorted(dt, g.order_purchase_timestamp.values.astype("datetime64[ns]"), side="right")
    ii = g.index.values
    n_h[ii] = idx; s_d[ii] = cdias[idx]; s_t[ii] = ctard[idx]
df["vend_hist_n"] = n_h
df["vend_hist_dias"] = (s_d + K_SUAV * df._g_dias) / (n_h + K_SUAV)
df["vend_hist_tardio"] = (s_t + K_SUAV * df._g_tard) / (n_h + K_SUAV)
df = df.drop(columns=["_g_dias", "_g_tard", "seller_principal"])

# ---------- 2. Carga relativa de la plataforma ----------
orders = pd.read_csv(RAW / "olist_orders_dataset.csv", usecols=["order_purchase_timestamp"],
                     parse_dates=["order_purchase_timestamp"])
daily = orders.order_purchase_timestamp.dt.floor("D").value_counts().sort_index()
full = pd.date_range(daily.index.min() - pd.Timedelta(days=70), daily.index.max(), freq="D")
daily = daily.reindex(full, fill_value=0)
last7 = daily.rolling(7).sum().shift(1)                       # días t-7 .. t-1
prev56 = daily.rolling(56).sum().shift(8)                      # días t-63 .. t-8
carga = (last7 / (prev56 / 8)).replace([np.inf, -np.inf], np.nan)
carga[prev56 < 200] = np.nan                                   # historia insuficiente (2016)
day = df.order_purchase_timestamp.dt.floor("D")
df["carga_rel"] = carga.reindex(day).values
print("carga_rel nulos antes de imputar:", int(df.carga_rel.isna().sum()))
df["carga_rel"] = df.carga_rel.fillna(1.0)

# ---------- 3. Verificaciones ----------
assert df.vend_hist_n.min() >= 0
print("vend_hist_n: mediana", df.vend_hist_n.median(), " | pedidos con 0 historial:", int((df.vend_hist_n == 0).sum()))
print("correlación vend_hist_dias vs dias_entrega:", round(df.vend_hist_dias.corr(df.dias_entrega), 3))
print("correlación carga_rel vs dias_entrega:", round(df.carga_rel.corr(df.dias_entrega), 3))
print("forma final:", df.shape)

df.to_csv(PROC / "pedidos_modelo.csv", index=False)
pd.DataFrame({"variable": df.columns}).to_csv(OUT / "11_columnas_dataset_final.csv", index=False)
