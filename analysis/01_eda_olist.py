"""EDA inicial reproducible para el primer entregable con Olist."""
from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw" / "olist"
OUT = ROOT / "analysis" / "outputs_olist"
OUT.mkdir(exist_ok=True)

orders = pd.read_csv(RAW / "olist_orders_dataset.csv", parse_dates=[
    "order_purchase_timestamp", "order_delivered_customer_date"
])
items = pd.read_csv(RAW / "olist_order_items_dataset.csv")
payments = pd.read_csv(RAW / "olist_order_payments_dataset.csv")
customers = pd.read_csv(RAW / "olist_customers_dataset.csv")
products = pd.read_csv(RAW / "olist_products_dataset.csv")
reviews = pd.read_csv(RAW / "olist_order_reviews_dataset.csv")
translation = pd.read_csv(RAW / "product_category_name_translation.csv")

# Se trabaja con pedidos entregados para medir resultados comerciales cerrados.
delivered = orders.loc[orders["order_status"] == "delivered"].copy()
delivered["mes"] = delivered["order_purchase_timestamp"].dt.to_period("M").astype(str)

payment_by_order = payments.groupby("order_id", as_index=False)["payment_value"].sum()
order_revenue = delivered.merge(payment_by_order, on="order_id", how="left")
monthly = order_revenue.groupby("mes", as_index=False).agg(
    pedidos=("order_id", "nunique"), ingreso_brl=("payment_value", "sum")
)
monthly.to_csv(OUT / "01_ingresos_y_pedidos_mensuales.csv", index=False)

category_map = products.merge(translation, on="product_category_name", how="left")
item_categories = items.merge(category_map[["product_id", "product_category_name_english"]], on="product_id", how="left")
item_categories = item_categories.merge(delivered[["order_id"]], on="order_id", how="inner")
category = item_categories.assign(
    categoria=item_categories["product_category_name_english"].fillna("sin_categoria"),
    ingreso_brl=item_categories["price"] + item_categories["freight_value"],
).groupby("categoria", as_index=False)["ingreso_brl"].sum().nlargest(10, "ingreso_brl")
category.to_csv(OUT / "02_top_categorias_ingreso.csv", index=False)

state_orders = delivered.merge(customers[["customer_id", "customer_state"]], on="customer_id", how="left")
state_orders = state_orders.merge(payment_by_order, on="order_id", how="left")
states = state_orders.groupby("customer_state", as_index=False).agg(
    pedidos=("order_id", "nunique"), ingreso_brl=("payment_value", "sum")
).nlargest(10, "ingreso_brl")
states.to_csv(OUT / "03_top_estados_pedidos_ingreso.csv", index=False)

score = reviews.groupby("review_score", as_index=False).agg(resenas=("review_id", "count"))
score.to_csv(OUT / "04_distribucion_puntuacion_resenas.csv", index=False)

delivery = delivered.dropna(subset=["order_delivered_customer_date"]).copy()
delivery["dias_entrega"] = (
    delivery["order_delivered_customer_date"] - delivery["order_purchase_timestamp"]
).dt.total_seconds() / 86400
delivery[["order_id", "dias_entrega"]].to_csv(OUT / "05_tiempo_entrega_por_pedido.csv", index=False)

summary = pd.DataFrame([
    ["Pedidos entregados", delivered["order_id"].nunique()],
    ["Ingreso en pagos de pedidos entregados (BRL)", order_revenue["payment_value"].sum()],
    ["Fecha inicial", delivered["order_purchase_timestamp"].min()],
    ["Fecha final", delivered["order_purchase_timestamp"].max()],
    ["Tiempo medio de entrega (días)", delivery["dias_entrega"].mean()],
], columns=["indicador", "valor"])
summary.to_csv(OUT / "resumen_eda_olist.csv", index=False)
print(summary.to_string(index=False))
