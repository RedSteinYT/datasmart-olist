"""Entregable 4 - Minería de textos sobre las reseñas en portugués de Olist.

Limpieza -> TF-IDF (1-2 gramas) -> sentimiento (LR / Naive Bayes / SVM lineal) -> aspectos por diccionario
-> temas NMF -> términos asociados a reseñas negativas -> relación con las bandas de riesgo de entrega.
"""
import sys, re, json, unicodedata, warnings
from pathlib import Path
import numpy as np, pandas as pd, joblib
import stopwordsiso
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.naive_bayes import ComplementNB
from sklearn.svm import LinearSVC
from sklearn.decomposition import NMF
from sklearn.metrics import accuracy_score, f1_score, roc_auc_score, confusion_matrix
warnings.filterwarnings("ignore")
ROOT = Path(__file__).resolve().parents[1]; sys.path.insert(0, str(ROOT / "src"))
from datasmart import features as F
OUT = ROOT / "analysis" / "outputs_s16"; WEB = ROOT / "analysis" / "web_data"; WEB.mkdir(exist_ok=True)

df = pd.read_csv(ROOT / "data/processed/pedidos_modelo.csv")
rv = pd.read_csv(ROOT / "data/raw/olist/olist_order_reviews_dataset.csv").sort_values("review_answer_timestamp").drop_duplicates("order_id", keep="last")
rv["texto_raw"] = (rv.review_comment_title.fillna("") + ". " + rv.review_comment_message.fillna("")).str.strip(" .")
rv = rv[rv.texto_raw.str.len() > 0][["order_id", "texto_raw"]]
d = df.reset_index().merge(rv, on="order_id", how="inner")
print("pedidos entregados:", len(df), "| con comentario:", len(d), f"({len(d)/len(df):.1%})")

NEG_KEEP = {"não", "nao", "nem", "nunca", "sem", "jamais", "nenhum", "nada", "mais", "muito", "pouco", "melhor", "pior", "bem", "mal"}
SW = set(stopwordsiso.stopwords("pt")) - NEG_KEEP
def limpiar(t):
    t = t.lower(); t = re.sub(r"https?://\S+", " ", t); t = re.sub(r"\d+", " ", t)
    t = re.sub(r"(.)\1{2,}", r"\1\1", t)  # "ótimooo" -> "ótimoo"
    t = re.sub(r"[^a-záàâãéêíóôõúüç\s]", " ", t)
    return " ".join(w for w in t.split() if w not in SW and len(w) > 1)
d["texto"] = d.texto_raw.map(limpiar)
d = d[d.texto.str.len() > 0].reset_index(drop=True)
d["sent"] = np.where(d.review_score <= 2, "negativa", np.where(d.review_score >= 4, "positiva", "neutra"))
print(d.sent.value_counts(normalize=True).round(3).to_dict(), "| long. media (palabras):", round(d.texto.str.split().str.len().mean(), 1))

# partición: la misma 80/20 del clasificador (para relacionar luego con el riesgo de entrega)
itr_set = set(joblib.load(ROOT / "models/clasificador_meta.joblib")["itr"])
d["train"] = d["index"].isin(itr_set)
tr, te = d[d.train], d[~d.train]
vec = TfidfVectorizer(ngram_range=(1, 2), min_df=8, max_features=3000, sublinear_tf=True)
Xtr = vec.fit_transform(tr.texto); Xte = vec.transform(te.texto); Xall = vec.transform(d.texto)
voc = np.array(vec.get_feature_names_out()); print("vocabulario:", len(voc))

# ---------- sentimiento: negativa (1-2) vs positiva (4-5); las de 3 estrellas no se usan para entrenar ----------
mtr, mte = tr.sent != "neutra", te.sent != "neutra"
ytr = (tr.sent[mtr] == "negativa").astype(int).values; yte = (te.sent[mte] == "negativa").astype(int).values
res, modelos = [], {
    "Regresión logística": LogisticRegression(max_iter=2000, C=2, class_weight="balanced"),
    "Naive Bayes (complemento)": ComplementNB(alpha=.3),
    "SVM lineal": LinearSVC(C=.3, class_weight="balanced"),
}
for n, m in modelos.items():
    m.fit(Xtr[mtr.values], ytr); pr = m.predict(Xte[mte.values])
    sc = m.decision_function(Xte[mte.values]) if hasattr(m, "decision_function") else m.predict_proba(Xte[mte.values])[:, 1]
    res.append(dict(modelo=n, exactitud=accuracy_score(yte, pr), F1_negativa=f1_score(yte, pr), F1_macro=f1_score(yte, pr, average="macro"), AUC_ROC=roc_auc_score(yte, sc)))
res = pd.DataFrame(res).round(4); res.to_csv(OUT / "15_sentimiento_modelos.csv", index=False); print(res.to_string(index=False))
lr = modelos["Regresión logística"]
cm = confusion_matrix(yte, lr.predict(Xte[mte.values])); pd.DataFrame(cm, index=["real positiva", "real negativa"], columns=["pred positiva", "pred negativa"]).to_csv(OUT / "15_sentimiento_matriz.csv")
# ¿la probabilidad de LR crece con las estrellas?
d["p_neg"] = lr.predict_proba(Xall)[:, 1]
est = d[~d.train].groupby("review_score").p_neg.mean().round(3); est.to_csv(OUT / "15_pneg_por_estrellas.csv"); print("P(negativa) media por estrellas (prueba):", est.to_dict())
coef = pd.Series(lr.coef_[0], index=voc).sort_values()
pd.DataFrame({"termino": coef.index, "coef": coef.values}).to_csv(OUT / "15_coeficientes.csv", index=False)
print("más negativos:", list(coef.index[-12:][::-1])); print("más positivos:", list(coef.index[:12]))

# ---------- aspectos por diccionario ----------
ASP = {
    "Entrega y plazo": r"\b(entreg\w*|prazo|chegou|chegar|chegada|atras\w*|demor\w*|correio\w*|transportadora|rastre\w*|receb\w*)",
    "Calidad del producto": r"\b(qualidade|defeito\w*|quebr\w*|funcion\w*|estragad\w*|danific\w*|original|falsific\w*|ruim|péssim\w*|pessim\w*|excelente|ótim\w*|otim\w*)",
    "Empaque y estado": r"\b(embalag\w*|caixa|amassad\w*|lacrad\w*|aberto|violad\w*)",
    "Vendedor y atención": r"\b(vendedor\w*|loja|atendiment\w*|contato|resposta|respond\w*|sac|suporte)\b",
    "Precio": r"\b(preço|preco|valor|barat\w*|caro|cara|custo|econom\w*)\b",
    "Devolución y reembolso": r"\b(devol\w*|reembols\w*|estorn\w*|troca\w*|cancel\w*|dinheiro volta)",
}
txt = d.texto.str.replace(r"$", " ", regex=True)
rows = []
for a, pat in ASP.items():
    m = txt.str.contains(pat, regex=True)
    d["asp_" + a] = m
    rows.append(dict(aspecto=a, pct_menciones=m.mean(), n=int(m.sum()), pct_negativas_entre_menciones=(d.sent[m] == "negativa").mean(), puntaje_medio=d.review_score[m].mean()))
asp = pd.DataFrame(rows).round(4); asp.to_csv(OUT / "15_aspectos.csv", index=False); print(asp.to_string(index=False))

# ---------- términos asociados a reseñas negativas (razón de momios suavizada) ----------
Xb = (vec.transform(d.texto) > 0).astype(int); neg = (d.sent == "negativa").values
cn = np.asarray(Xb[neg].sum(0)).ravel(); cp = np.asarray(Xb[~neg].sum(0)).ravel()
lo = np.log((cn + 1) / (neg.sum() + 2)) - np.log((cp + 1) / ((~neg).sum() + 2))
lift = pd.DataFrame({"termino": voc, "n_neg": cn, "n_resto": cp, "log_razon": lo})
lift = lift[(lift.n_neg + lift.n_resto) >= 40].sort_values("log_razon", ascending=False)
lift.to_csv(OUT / "15_terminos_negativos.csv", index=False)
print("términos más asociados a negativas:", list(lift.termino.head(15)))

# ---------- temas NMF ----------
Xn = vec.transform(d.texto)
nmf = NMF(n_components=7, init="nndsvda", random_state=0, max_iter=400); W = nmf.fit_transform(Xn)
d["tema"] = W.argmax(1)
tem = []
for k in range(7):
    top = voc[np.argsort(nmf.components_[k])[::-1][:10]]
    m = d.tema == k
    tem.append(dict(tema=k + 1, terminos=", ".join(top), pct_reseñas=m.mean(), puntaje_medio=d.review_score[m].mean(), pct_negativas=(d.sent[m] == "negativa").mean()))
tem = pd.DataFrame(tem).round(4); tem.to_csv(OUT / "15_temas.csv", index=False); print(tem.to_string(index=False))

# ---------- relación con el riesgo de entrega (conjunto de prueba) ----------
meta = joblib.load(ROOT / "models/clasificador_meta.joblib"); mod = joblib.load(ROOT / "models/clasificador_xgb.joblib")
X = F.build_X(df, meta["num"], log=True, drop_first=False)
p = pd.Series(mod.predict_proba(X.iloc[meta["ite"]])[:, 1], index=meta["ite"])
t = d[~d.train].copy(); t["riesgo"] = t["index"].map(p)
t["banda"] = pd.cut(t.riesgo, [-1, meta["q60"], meta["q90"], 2], labels=["Bajo", "Medio", "Alto"])
t["tarde"] = df.entrega_tardia.values[t["index"]]
rel = t.groupby("banda").agg(n=("riesgo", "size"), pct_negativas=("sent", lambda s: (s == "negativa").mean()),
                              puntaje_medio=("review_score", "mean"), pct_menciona_entrega=("asp_Entrega y plazo", "mean")).round(4)
rel.to_csv(OUT / "15_texto_vs_riesgo.csv"); print(rel)
tt = df.copy(); sinc = tt.groupby("entrega_tardia").resena_baja.mean(); print("reseña baja según llegó tarde:", sinc.round(3).to_dict())
d.drop(columns=["texto_raw"]).to_csv(ROOT / "data/processed/resenas_procesadas.csv", index=False)

# ---------- exportación para el analizador de texto en el navegador ----------
json.dump(dict(vocab=voc.tolist(), idf=np.round(vec.idf_, 5).tolist(), coef=np.round(lr.coef_[0], 5).tolist(),
               intercept=float(lr.intercept_[0]), ngram=[1, 2], stopwords=sorted(SW),
               aspectos={k: v for k, v in ASP.items()}), open(WEB / "texto_modelo.json", "w"), ensure_ascii=False)
json.dump(dict(n_resenas=len(d), pct_con_comentario=len(d) / len(df), vocabulario=len(voc),
               sentimiento=res.set_index("modelo").to_dict("index")), open(OUT / "15_resumen.json", "w"), ensure_ascii=False, indent=1)
