"""Construcción de la matriz de variables para regresión y clasificación (entregable 4).

Una sola definición, usada por los scripts de análisis, la exportación al dashboard y la API,
para que el entrenamiento y la predicción nunca difieran.
"""
import numpy as np
import pandas as pd

# Variables numéricas del modelo final (18). `log=True`: se transforma con log1p (asimétricas).
NUM_FINAL = [
    ("n_items", False), ("n_vendedores", False), ("precio_total", True), ("flete_total", True),
    ("peso_total_g", True), ("volumen_total_cm3", True), ("ratio_flete", False), ("dia_semana", False),
    ("hora", False), ("dias_aprobacion", False), ("n_cuotas", False), ("distancia_km", True),
    ("mismo_estado", False), ("dias_estimados", False), ("vend_hist_dias", False),
    ("vend_hist_tardio", False), ("vend_hist_n", True), ("carga_rel", True),
]
NUM_V1 = ["precio_total", "flete_total", "peso_total_g", "volumen_total_cm3", "n_items", "n_vendedores",
          "ratio_flete", "dia_semana", "hora", "dias_aprobacion", "n_cuotas"]
NUM_V2 = NUM_V1 + ["distancia_km", "mismo_estado"]
NUM_V3 = NUM_V2 + ["dias_estimados", "vend_hist_dias", "vend_hist_tardio", "vend_hist_n", "carga_rel"]
LOG_COLS = {"precio_total", "flete_total", "peso_total_g", "volumen_total_cm3", "distancia_km", "vend_hist_n", "carga_rel"}

NOMBRES = {
    "n_items": "Ítems por pedido", "n_vendedores": "Vendedores en el pedido", "precio_total": "Precio del pedido",
    "flete_total": "Flete", "peso_total_g": "Peso", "volumen_total_cm3": "Volumen", "ratio_flete": "Flete / precio",
    "dia_semana": "Día de la semana de compra", "hora": "Hora de compra", "dias_aprobacion": "Días hasta aprobar el pago",
    "n_cuotas": "Cuotas de pago", "distancia_km": "Distancia vendedor-comprador (km)",
    "mismo_estado": "Vendedor y comprador en el mismo estado", "dias_estimados": "Plazo prometido (días)",
    "vend_hist_dias": "Días de entrega históricos del vendedor", "vend_hist_tardio": "% de entregas tardías históricas del vendedor",
    "vend_hist_n": "Pedidos previos del vendedor",
    "carga_rel": "Carga relativa de la plataforma (7 días vs. 8 semanas previas)",
    "customer_state": "Estado del comprador", "cat": "Categoría del producto",
}


def top_categorias(df, n=15):
    return list(df.categoria_principal.value_counts().head(n).index)


def build_X(df, num, log=False, cats=None, states=None, drop_first=True):
    """Devuelve la matriz de variables (numéricas + estado + categoría one-hot)."""
    d = df.copy()
    cats = cats if cats is not None else top_categorias(d)
    d["cat"] = np.where(d.categoria_principal.isin(cats), d.categoria_principal, "otras")
    X = d[num].astype(float).copy()
    for c in ("dias_aprobacion", "distancia_km", "vend_hist_dias", "vend_hist_tardio", "carga_rel"):
        if c in X:
            X[c] = X[c].fillna(X[c].median())
    if log:
        for c in X.columns:
            if c in LOG_COLS:
                X[c] = np.log1p(X[c].clip(lower=0))
    cs = pd.get_dummies(d[["customer_state", "cat"]], drop_first=drop_first).astype(float)
    return pd.concat([X, cs], axis=1)


def grupo_de(col):
    """Agrupa las columnas one-hot en su variable original (para importancia agrupada)."""
    if col.startswith("customer_state_"):
        return "customer_state"
    if col.startswith("cat_"):
        return "cat"
    return col


def split_clasificacion(df, test_size=0.2, seed=42):
    """Partición estratificada 80/20 por la variable objetivo entrega_tardia."""
    from sklearn.model_selection import train_test_split
    idx = np.arange(len(df))
    return train_test_split(idx, test_size=test_size, random_state=seed, stratify=df.entrega_tardia.values)
