"""Pruebas automáticas: datos, variables, modelo, API, paridad con el navegador y monitoreo. Ejecutar: python -m pytest -q"""
import json, sys, subprocess
from pathlib import Path
import numpy as np, pandas as pd, pytest
ROOT = Path(__file__).resolve().parents[1]; sys.path.insert(0, str(ROOT / "src")); sys.path.insert(0, str(ROOT / "app"))
from datasmart import features as F
from datasmart.service import Servicio

@pytest.fixture(scope="module")
def df():
    f = ROOT / "data/processed/pedidos_modelo.csv"
    if not f.exists(): pytest.skip("falta data/processed (se genera con los scripts 02, 10 y 11)")
    return pd.read_csv(f)
@pytest.fixture(scope="module")
def svc(): return Servicio()
@pytest.fixture(scope="module")
def cli():
    from api import crear_app
    return crear_app().test_client()

# ---- datos ----
def test_cantidad_de_pedidos(df): assert len(df) == 96469 and df.order_id.is_unique
def test_ingreso_total(df): assert round(df.valor_pago.sum(), 2) == 15421082.85
def test_tasa_de_tardios(df): assert abs(df.entrega_tardia.mean() - 0.0811) < 5e-4
def test_distancia_valida(df): assert df.distancia_km.dropna().between(0, 4500).all()
def test_vendedor_historial_causal(df):
    d = df.sort_values("order_purchase_timestamp"); assert d.vend_hist_tardio.between(0, 1).all() and (d.vend_hist_n >= 0).all()
# ---- variables ----
def test_build_x_mismas_columnas(df):
    meta = __import__("joblib").load(ROOT / "models/clasificador_meta.joblib")
    X = F.build_X(df.head(500), meta["num"], log=True, cats=meta["cats"], drop_first=False).reindex(columns=meta["columns"], fill_value=0)
    assert list(X.columns) == meta["columns"] and not X.isna().any().any()
def test_split_estratificado(df):
    a, b = F.split_clasificacion(df); assert len(set(a) & set(b)) == 0 and abs(df.entrega_tardia.values[a].mean() - df.entrega_tardia.values[b].mean()) < 2e-3
# ---- modelo ----
def test_metricas_guardadas():
    f = json.load(open(ROOT / "analysis/outputs_s16/13_final.json")); assert f["final"]["AUC_ROC"] > 0.77 and f["final"]["AUC_PR"] > 0.30
def test_probabilidad_en_rango(svc):
    r = svc.predecir(dict(customer_state="SP", categoria_principal="health_beauty", dias_estimados=24, precio_total=100, flete_total=15)); assert 0 < r["probabilidad"] < 1 and r["banda"] in ("Bajo", "Medio", "Alto")
def test_plazo_corto_sube_riesgo(svc):
    b = dict(customer_state="RJ", categoria_principal="toys", precio_total=100, flete_total=20, seller_state="SP", distancia_km=400)
    assert svc.predecir({**b, "dias_estimados": 10})["probabilidad"] > svc.predecir({**b, "dias_estimados": 30})["probabilidad"]
def test_python_igual_a_navegador(svc):
    """El JSON exportado al navegador y el modelo de Python dan la misma probabilidad."""
    r = subprocess.run(["node", str(ROOT / "web/tests/paridad_modelo.js")], capture_output=True, text=True); assert r.returncode == 0, r.stdout + r.stderr
def test_texto_python_igual_a_navegador():
    r = subprocess.run(["node", str(ROOT / "web/tests/paridad_texto.js")], capture_output=True, text=True); assert r.returncode == 0, r.stdout + r.stderr
def test_texto_python_vs_sklearn(svc):
    if not (ROOT / "web/tests/texto_paridad.json").exists(): pytest.skip("sin datos de paridad")
    casos = json.load(open(ROOT / "web/tests/texto_paridad.json"))[:100]
    for c in casos: assert abs(svc.analizar_texto(c["texto"])["prob_negativa"] - c["p_neg"]) < 1e-3
def test_texto_negativo_vs_positivo(svc):
    assert svc.analizar_texto("não recebi o produto péssimo")["prob_negativa"] > 0.8 > 0.2 > svc.analizar_texto("produto excelente recomendo")["prob_negativa"]
# ---- API ----
def test_api_health(cli): r = cli.get("/api/health"); assert r.status_code == 200 and r.json["estado"] == "ok"
def test_api_predict_ok(cli):
    r = cli.post("/api/predict", json=dict(customer_state="BA", categoria_principal="auto", dias_estimados=20, precio_total=80, flete_total=30)); assert r.status_code == 200 and "factores" in r.json
def test_api_predict_error(cli):
    assert cli.post("/api/predict", json={"customer_state": "SP"}).status_code == 422 and cli.post("/api/predict", data="no es json").status_code == 400
def test_api_text(cli):
    assert cli.post("/api/text", json={"texto": "entrega demorada, péssimo"}).json["etiqueta"] == "negativa"; assert cli.post("/api/text", json={}).status_code == 422
def test_api_monitoreo_y_versiones(cli):
    assert cli.get("/api/monitoring").status_code == 200; v = cli.get("/api/model/versions").json; assert len(v) >= 20 and all(len(x["hash"]) == 16 for x in v)
def test_api_sirve_tablero(cli): r = cli.get("/"); assert r.status_code == 200 and b"DataSmart" in r.data
# ---- monitoreo ----
def test_monitoreo_cubre_diez_meses():
    s = pd.read_csv(ROOT / "analysis/outputs_s16/16_simulacion_mensual.csv"); assert s.mes.nunique() == 10 and s.politica.nunique() == 4
def test_monitoreo_sin_fuga_temporal():
    """El entrenamiento v1 solo usa compras hasta sep-2017."""
    v = json.load(open(ROOT / "models/registro/versiones.json")); assert v[0]["entrenado_con"] == "ene-sep 2017"
def test_auditoria_jsonl_valida():
    for l in open(ROOT / "analysis/outputs_s16/16_auditoria.jsonl"): assert "evento" in json.loads(l)
