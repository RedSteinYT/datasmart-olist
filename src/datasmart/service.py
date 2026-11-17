"""Lógica de servicio compartida por la API: predicción de riesgo, texto y lectura de resultados de monitoreo.
Usa exactamente las mismas funciones de variables (features.build_X) que el entrenamiento."""
import json, re
from pathlib import Path
import numpy as np, pandas as pd, joblib
from . import features as F

ROOT = Path(__file__).resolve().parents[2]
CAMPOS_NUM = [n for n, _ in F.NUM_FINAL]
REQUERIDOS = ["customer_state", "categoria_principal", "dias_estimados", "precio_total", "flete_total"]

class Servicio:
    def __init__(self, root=ROOT):
        self.root = Path(root)
        from xgboost import XGBClassifier
        self.modelo = XGBClassifier(); self.modelo.load_model(str(self.root / "models/clasificador_xgb.json"))  # JSON: independiente de la versión de Python
        self.meta = joblib.load(self.root / "models/clasificador_meta.joblib")
        self.cols = self.meta["columns"]
        self.cats = self.meta["cats"]
        self.rangos = None
        t = self.root / "web/data/texto_modelo.json"
        self.texto = json.load(open(t)) if t.exists() else None
        if self.texto:
            self._v = {w: i for i, w in enumerate(self.texto["vocab"])}; self._sw = set(self.texto["stopwords"])
            self._idf = np.array(self.texto["idf"]); self._coef = np.array(self.texto["coef"])

    # ---------- riesgo de entrega ----------
    def _frame(self, p):
        faltan = [k for k in REQUERIDOS if k not in p]
        if faltan: raise ValueError("faltan campos: " + ", ".join(faltan))
        d = {k: p.get(k, np.nan) for k in CAMPOS_NUM}
        d.update(customer_state=p["customer_state"], categoria_principal=p["categoria_principal"])
        d["n_items"] = p.get("n_items", 1); d["n_vendedores"] = p.get("n_vendedores", 1)
        d["ratio_flete"] = p.get("ratio_flete", p["flete_total"] / p["precio_total"] if p["precio_total"] else 0)
        if "mismo_estado" not in p: d["mismo_estado"] = float(p.get("seller_state") == p["customer_state"])
        for k, v in (("peso_total_g", 800), ("volumen_total_cm3", 6000), ("n_cuotas", 2), ("dia_semana", 2), ("hora", 14), ("dias_aprobacion", 0.1),
                     ("vend_hist_dias", 12), ("vend_hist_tardio", 0.05), ("vend_hist_n", 100), ("carga_rel", 1.0), ("distancia_km", 500)):
            if pd.isna(d.get(k, np.nan)): d[k] = v
        return pd.DataFrame([d])

    def predecir(self, p):
        df = self._frame(p)
        X = F.build_X(df, self.meta["num"], log=True, cats=self.cats, drop_first=False)
        X = X.reindex(columns=self.cols, fill_value=0.0)  # estados/categorías ausentes en la fila -> 0
        pr = float(self.modelo.predict_proba(X)[0, 1])
        banda = "Alto" if pr >= self.meta["q90"] else "Medio" if pr >= self.meta["q60"] else "Bajo"
        contrib = self.modelo.get_booster().predict(__import__("xgboost").DMatrix(X), pred_contribs=True)[0][:-1]
        g = pd.Series(contrib, index=self.cols).groupby(F.grupo_de).sum()
        fac = [dict(variable=F.NOMBRES.get(k, k), contribucion_logodds=round(float(v), 4)) for k, v in g.sort_values(key=abs, ascending=False).head(8).items()]
        return dict(probabilidad=round(pr, 4), banda=banda, umbrales=dict(medio=round(self.meta["q60"], 4), alto=round(self.meta["q90"], 4)), factores=fac)

    # ---------- texto (misma limpieza y TF-IDF que el entrenamiento) ----------
    def _limpiar(self, t):
        t = re.sub(r"https?://\S+", " ", t.lower()); t = re.sub(r"\d+", " ", t); t = re.sub(r"(.)\1{2,}", r"\1\1", t, flags=re.S)
        t = re.sub(r"[^a-záàâãéêíóôõúüç\s]", " ", t)
        return [w for w in t.split() if len(w) > 1 and w not in self._sw]

    def analizar_texto(self, txt):
        if not self.texto: raise RuntimeError("modelo de texto no disponible")
        toks = self._limpiar(txt); grams = toks + [a + " " + b for a, b in zip(toks, toks[1:])]
        tf = {}
        for g in grams:
            j = self._v.get(g)
            if j is not None: tf[j] = tf.get(j, 0) + 1
        w = {j: (1 + np.log(c)) * self._idf[j] for j, c in tf.items()}; nrm = np.sqrt(sum(v * v for v in w.values())) or 1.0
        z = self.texto["intercept"] + sum(self._coef[j] * v / nrm for j, v in w.items())
        pneg = float(1 / (1 + np.exp(-z)))
        top = sorted(((self.texto["vocab"][j], float(self._coef[j] * v / nrm)) for j, v in w.items()), key=lambda a: -abs(a[1]))[:6]
        return dict(prob_negativa=round(pneg, 4), etiqueta="negativa" if pneg > .65 else "positiva" if pneg < .35 else "dudosa", terminos=[dict(termino=a, aporte=round(b, 4)) for a, b in top])

    # ---------- monitoreo ----------
    def monitoreo(self):
        o = self.root / "analysis/outputs_s16"
        sim = pd.read_csv(o / "16_simulacion_mensual.csv")
        return dict(resumen=json.load(open(o / "16_resumen.json")), temporal=json.load(open(o / "16_validacion_temporal.json")),
                    politicas=pd.read_csv(o / "16_politicas_resumen.csv").to_dict("records"), meses=sorted(sim.mes.unique().tolist()))
    def versiones(self): return json.load(open(self.root / "models/registro/versiones.json"))
    def auditoria(self, n=50): return [json.loads(l) for l in open(self.root / "analysis/outputs_s16/16_auditoria.jsonl")][-n:]
