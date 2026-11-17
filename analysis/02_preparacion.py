"""Semana 10 - Preparación de datos y feature engineering (Olist)."""
from pathlib import Path
import numpy as np, pandas as pd

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT/"data"/"raw"/"olist"; PROC = ROOT/"data"/"processed"; OUT = ROOT/"analysis"/"outputs_s10"
PROC.mkdir(parents=True, exist_ok=True); OUT.mkdir(parents=True, exist_ok=True)
log = []
def L(k, v): log.append((k, v)); print(f"{k}: {v}")

orders = pd.read_csv(RAW/"olist_orders_dataset.csv", parse_dates=[c for c in pd.read_csv(RAW/"olist_orders_dataset.csv", nrows=1).columns if c.endswith(("timestamp","date","at"))])
items = pd.read_csv(RAW/"olist_order_items_dataset.csv")
pay = pd.read_csv(RAW/"olist_order_payments_dataset.csv")
cust = pd.read_csv(RAW/"olist_customers_dataset.csv")
prod = pd.read_csv(RAW/"olist_products_dataset.csv")
rev = pd.read_csv(RAW/"olist_order_reviews_dataset.csv")
tr = pd.read_csv(RAW/"product_category_name_translation.csv")

# ---------- 1. LIMPIEZA ----------
for n, d in [("orders",orders),("items",items),("payments",pay),("customers",cust),("products",prod),("reviews",rev)]:
    L(f"duplicados exactos {n}", int(d.duplicated().sum()))
L("order_id duplicados en orders", int(orders.order_id.duplicated().sum()))
# valores faltantes
L("nulos fecha entrega cliente (todos los estados)", int(orders.order_delivered_customer_date.isna().sum()))
L("nulos categoría producto", int(prod.product_category_name.isna().sum()))
# inconsistencias: entrega antes de compra, pagos 0, precio <=0
inc_fecha = (orders.order_delivered_customer_date < orders.order_purchase_timestamp).sum()
L("inconsistencia entrega < compra", int(inc_fecha))
L("pagos con valor 0", int((pay.payment_value<=0).sum()))
L("ítems con precio <=0", int((items.price<=0).sum()))
# reseñas duplicadas por pedido: nos quedamos con la más reciente
rev["review_answer_timestamp"] = pd.to_datetime(rev.review_answer_timestamp)
L("pedidos con >1 reseña", int((rev.groupby("order_id").size()>1).sum()))
rev1 = rev.sort_values("review_answer_timestamp").drop_duplicates("order_id", keep="last")

prod = prod.merge(tr, on="product_category_name", how="left")
prod["categoria"] = prod.product_category_name_english.fillna(prod.product_category_name).fillna("sin_categoria")
for c in ["product_weight_g","product_length_cm","product_height_cm","product_width_cm"]:
    L(f"nulos {c}", int(prod[c].isna().sum()))
    prod[c] = prod[c].fillna(prod.groupby("categoria")[c].transform("median")).fillna(prod[c].median())

# ---------- 2. INTEGRACIÓN (unidad: pedido entregado) ----------
d = orders[orders.order_status=="delivered"].copy()
d = d[d.order_delivered_customer_date.notna()]
d = d[d.order_delivered_customer_date >= d.order_purchase_timestamp]
L("pedidos entregados válidos", len(d))
pay_o = pay.groupby("order_id").agg(valor_pago=("payment_value","sum"), n_cuotas=("payment_installments","max"),
        n_medios=("payment_type","nunique"), medio_principal=("payment_type", lambda s: s.mode().iloc[0])).reset_index()
it = items.merge(prod[["product_id","categoria","product_weight_g","product_length_cm","product_height_cm","product_width_cm"]], on="product_id", how="left")
it["volumen_cm3"] = it.product_length_cm*it.product_height_cm*it.product_width_cm
it_o = it.groupby("order_id").agg(n_items=("order_item_id","count"), n_productos=("product_id","nunique"), n_vendedores=("seller_id","nunique"),
        precio_total=("price","sum"), flete_total=("freight_value","sum"), peso_total_g=("product_weight_g","sum"),
        volumen_total_cm3=("volumen_cm3","sum"), categoria_principal=("categoria", lambda s: s.mode().iloc[0])).reset_index()
df = (d.merge(cust, on="customer_id", how="left").merge(pay_o, on="order_id", how="left")
        .merge(it_o, on="order_id", how="left").merge(rev1[["order_id","review_score"]], on="order_id", how="left"))
df = df.dropna(subset=["valor_pago","n_items"])
L("filas tras integrar", len(df))

# ---------- 3. FEATURE ENGINEERING ----------
df["dias_entrega"] = (df.order_delivered_customer_date-df.order_purchase_timestamp).dt.total_seconds()/86400
df["dias_estimados"] = (df.order_estimated_delivery_date-df.order_purchase_timestamp).dt.total_seconds()/86400
df["retraso_dias"] = (df.order_delivered_customer_date-df.order_estimated_delivery_date).dt.total_seconds()/86400
df["entrega_tardia"] = (df.retraso_dias>0).astype(int)
df["dias_aprobacion"] = (df.order_approved_at-df.order_purchase_timestamp).dt.total_seconds()/86400
df["mes"] = df.order_purchase_timestamp.dt.to_period("M").astype(str)
df["dia_semana"] = df.order_purchase_timestamp.dt.dayofweek
df["hora"] = df.order_purchase_timestamp.dt.hour
df["fin_de_semana"] = (df.dia_semana>=5).astype(int)
df["ratio_flete"] = df.flete_total/df.precio_total.replace(0,np.nan)
df["precio_medio_item"] = df.precio_total/df.n_items
df["resena_baja"] = (df.review_score<=2).astype(float).where(df.review_score.notna())

# ---------- 4. OUTLIERS (IQR) ----------
def iqr_flags(s):
    q1,q3 = s.quantile([.25,.75]); i=q3-q1
    return (s<q1-1.5*i)|(s>q3+1.5*i)
for c in ["valor_pago","dias_entrega","flete_total","precio_total"]:
    L(f"outliers IQR {c}", int(iqr_flags(df[c]).sum()))
    z = ((df[c]-df[c].mean())/df[c].std()).abs()
    L(f"outliers Z>3 {c}", int((z>3).sum()))
# decisión: no se eliminan; se winsorizan al p99 solo para modelos de regresión
for c in ["valor_pago","flete_total","precio_total","dias_entrega"]:
    df[c+"_w"] = df[c].clip(upper=df[c].quantile(.99))

df.drop(columns=["order_approved_at","order_delivered_carrier_date"], errors="ignore").to_parquet(PROC/"pedidos_procesados.parquet") if False else None
df.to_csv(PROC/"pedidos_procesados.csv", index=False)
pd.DataFrame(log, columns=["indicador","valor"]).to_csv(OUT/"01_log_limpieza.csv", index=False)

# tabla de transacciones (canasta) pedido -> categorías
bask = it.merge(df[["order_id"]], on="order_id")
bask[["order_id","product_id","categoria"]].to_csv(PROC/"canastas_items.csv", index=False)
print(df.shape); print(df[["valor_pago","dias_entrega","retraso_dias","review_score","n_items"]].describe().T)
