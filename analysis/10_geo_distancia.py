"""Entregable 4 - Geolocalización y distancia vendedor-comprador (Olist).

Depura la tabla olist_geolocation (261 831 duplicados exactos), toma la mediana de
latitud/longitud por prefijo postal y calcula la distancia de Haversine entre el
comprador y el/los vendedor(es) de cada pedido.
Salidas: data/processed/geo_pedidos.csv, analysis/outputs_s16/10_geo_resumen.csv
"""
from pathlib import Path
import numpy as np, pandas as pd

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw" / "olist"
PROC = ROOT / "data" / "processed"
OUT = ROOT / "analysis" / "outputs_s16"
OUT.mkdir(parents=True, exist_ok=True)
log = []


def L(k, v):
    log.append((k, v)); print(f"{k}: {v}")


# ---------- 1. Depuración de geolocalización ----------
geo = pd.read_csv(RAW / "olist_geolocation_dataset.csv")
L("filas geolocalización", len(geo))
L("duplicados exactos", int(geo.duplicated().sum()))
dentro = geo.geolocation_lat.between(-33.75, 5.28) & geo.geolocation_lng.between(-73.99, -34.79)
L("filas fuera de Brasil (descartadas)", int((~dentro).sum()))
geo = geo[dentro]
zip_xy = (geo.groupby("geolocation_zip_code_prefix")
          .agg(lat=("geolocation_lat", "median"), lng=("geolocation_lng", "median"))
          .reset_index())
L("prefijos postales con coordenada", len(zip_xy))


def haversine(lat1, lng1, lat2, lng2):
    r = 6371.0088
    p1, p2 = np.radians(lat1), np.radians(lat2)
    dphi = p2 - p1
    dl = np.radians(lng2) - np.radians(lng1)
    a = np.sin(dphi / 2) ** 2 + np.cos(p1) * np.cos(p2) * np.sin(dl / 2) ** 2
    return 2 * r * np.arcsin(np.sqrt(a))


# ---------- 2. Pedido -> comprador y vendedores ----------
ped = pd.read_csv(PROC / "pedidos_procesados.csv", usecols=["order_id", "customer_zip_code_prefix", "customer_state"])
items = pd.read_csv(RAW / "olist_order_items_dataset.csv", usecols=["order_id", "order_item_id", "seller_id"])
sell = pd.read_csv(RAW / "olist_sellers_dataset.csv")

ped = ped.merge(zip_xy.rename(columns={"geolocation_zip_code_prefix": "customer_zip_code_prefix",
                                         "lat": "lat", "lng": "lng"}), on="customer_zip_code_prefix", how="left")
sell = sell.merge(zip_xy.rename(columns={"geolocation_zip_code_prefix": "seller_zip_code_prefix",
                                           "lat": "slat", "lng": "slng"}), on="seller_zip_code_prefix", how="left")
L("vendedores sin coordenada", int(sell.slat.isna().sum()))

io = items.merge(sell[["seller_id", "seller_state", "slat", "slng"]], on="seller_id", how="left")
io = io.merge(ped[["order_id", "lat", "lng", "customer_state"]], on="order_id", how="inner")
io["dist"] = haversine(io.lat, io.lng, io.slat, io.slng)

# vendedores distintos por pedido (un mismo vendedor puede aparecer en varios ítems)
uniq = io.drop_duplicates(["order_id", "seller_id"])
agg = uniq.groupby("order_id").agg(distancia_km=("dist", "mean"), distancia_max_km=("dist", "max")).reset_index()
# vendedor principal = el del primer ítem
prim = io.sort_values(["order_id", "order_item_id"]).drop_duplicates("order_id")[
    ["order_id", "seller_id", "seller_state", "customer_state"]].rename(columns={"seller_id": "seller_principal"})
prim["mismo_estado"] = (prim.seller_state == prim.customer_state).astype(int)

res = (ped[["order_id", "lat", "lng"]].merge(agg, on="order_id", how="left")
       .merge(prim[["order_id", "seller_principal", "seller_state", "mismo_estado"]], on="order_id", how="left"))
res.to_csv(PROC / "geo_pedidos.csv", index=False)

cob = res.distancia_km.notna().mean()
L("cobertura de distancia (% pedidos)", round(100 * cob, 2))
L("distancia mediana (km)", round(float(res.distancia_km.median()), 1))
L("distancia promedio (km)", round(float(res.distancia_km.mean()), 1))
L("% mismo estado", round(100 * float(res.mismo_estado.mean()), 1))

# correlación de Spearman con días de entrega
dias = pd.read_csv(PROC / "pedidos_procesados.csv", usecols=["order_id", "dias_entrega"])
m = res.merge(dias, on="order_id").dropna(subset=["distancia_km"])
L("Spearman distancia vs días de entrega", round(float(m.distancia_km.corr(m.dias_entrega, method="spearman")), 3))
pd.DataFrame(log, columns=["indicador", "valor"]).to_csv(OUT / "10_geo_resumen.csv", index=False)
