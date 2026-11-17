"""Prototipo DataSmart (Semana 10). Ejecutar desde la carpeta del proyecto:  streamlit run app/app.py"""
from pathlib import Path
import pandas as pd, streamlit as st
ROOT = Path(__file__).resolve().parents[1]
S10, E1 = ROOT/"analysis"/"outputs_s10", ROOT/"analysis"/"outputs_olist"
st.set_page_config(page_title="DataSmart Analytics", layout="wide")
st.title("DataSmart Analytics — Olist")
tab1, tab2, tab3, tab4 = st.tabs(["Resumen", "Calidad de datos", "Asociación", "Entrega vs. satisfacción"])

@st.cache_data
def pedidos():
    return pd.read_csv(ROOT/"data"/"processed"/"pedidos_procesados.csv", usecols=["order_id","valor_pago","dias_entrega","entrega_tardia","review_score","mes","customer_state"])

with tab1:
    p = pedidos()
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Pedidos entregados", f"{len(p):,}"); c2.metric("Ingreso (BRL)", f"{p.valor_pago.sum():,.0f}")
    c3.metric("Entrega media (días)", f"{p.dias_entrega.mean():.1f}"); c4.metric("Reseña media", f"{p.review_score.mean():.2f}")
    m = p.groupby("mes").valor_pago.sum()
    st.subheader("Ingreso mensual"); st.line_chart(m)
    st.subheader("Ingreso por estado (top 10)"); st.bar_chart(p.groupby("customer_state").valor_pago.sum().nlargest(10))

with tab2:
    st.dataframe(pd.read_csv(S10/"01_log_limpieza.csv"), use_container_width=True)

with tab3:
    algo = st.selectbox("Algoritmo", ["fpgrowth", "apriori", "eclat"])
    r = pd.read_csv(S10/f"02_reglas_{algo}.csv")
    sup = st.slider("Soporte mínimo", 0.0, 0.05, 0.004, 0.001); conf = st.slider("Confianza mínima", 0.0, 1.0, 0.05, 0.05); lift = st.slider("Lift mínimo", 0.0, 5.0, 1.0, 0.1)
    f = r[(r.support >= sup) & (r.confidence >= conf) & (r.lift >= lift)]
    st.write(f"{len(f)} reglas"); st.dataframe(f, use_container_width=True)
    st.caption("Canastas = categorías compradas por cliente (clientes con ≥2 categorías).")
    st.dataframe(pd.read_csv(S10/"03_comparacion_algoritmos.csv"), use_container_width=True)

with tab4:
    p = pedidos().dropna(subset=["review_score"])
    st.bar_chart(p.groupby("entrega_tardia").review_score.mean().rename({0: "A tiempo", 1: "Tardía"}))
    st.caption("Asociación observada; no implica causalidad.")
