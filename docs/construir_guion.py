"""Guion de sustentación y posibles preguntas (PDF). Lee ppt/guion.json generado por ppt/build.js."""
import json, html
from pathlib import Path
from playwright.sync_api import sync_playwright
D = Path(__file__).resolve().parent
g = json.load(open(D / "ppt" / "guion.json"))
QA = [
("¿Por qué eligieron la entrega tardía y no la reseña baja como objetivo?",
 "Porque es lo que se puede anticipar al comprar. Probamos ambos: la reseña baja tiene AUC 0,66 al comprar y sube a 0,77 solo cuando ya se conocen los días de entrega y el retraso. La satisfacción depende de cómo termine la entrega, que no se sabe al comprar. Por eso el modelo central es el retraso y el texto de la reseña se usa como complemento."),
("¿Qué tan bueno es el modelo realmente?",
 "En partición aleatoria, AUC-ROC 0,783 (IC 95 %: 0,769–0,794) y AUC-PR 0,317 frente a 0,081 del azar. Pero al entrenar con el pasado y probar en abril–agosto de 2018, el AUC-ROC baja a 0,704. Esa cifra temporal es la expectativa realista para el futuro, y la reportamos."),
("¿Por qué no usaron SMOTE si hay desbalance?",
 "Sí lo usamos, junto con ADASYN, submuestreo y sobremuestreo aleatorio. Ninguno superó al entrenamiento sin balancear con XGBoost: AUC-PR 0,303 sin balancear frente a 0,221 con SMOTE y 0,224 con ADASYN. Los árboles ya entregan probabilidades útiles; el desbalance se maneja mejor con el umbral y con bandas de riesgo."),
("¿Por qué XGBoost y no otro modelo?",
 "Por desempeño y por explicabilidad. Con AUC-PR 0,302 sin ajustar, igualó o superó a Gradient Boosting de histogramas (0,289), Random Forest (0,247), regresión logística (0,172), SVM (0,174) y Naive Bayes (0,122). Además permite calcular valores SHAP exactos en probabilidad."),
("¿Qué es el AUC-PR y por qué lo usan?",
 "Es el área bajo la curva precisión–exhaustividad. Con solo 8 % de pedidos tardíos, el AUC-ROC puede verse bien aunque el modelo acierte poco en la clase rara. El AUC-PR se compara con la tasa base (0,081): 0,317 es casi cuatro veces mejor que el azar."),
("¿Cómo evitaron fuga de información (data leakage)?",
 "Excluimos las fechas de entrega y el retraso de las variables predictoras. El historial del vendedor y la carga de la plataforma se calculan solo con pedidos anteriores al pedido. Una salvedad que declaramos: los días de aprobación del pago se conocen al aprobarse el pago, no estrictamente al comprar."),
("¿Qué significa que SHAP y LIME no coincidan?",
 "SHAP es exacto y aditivo para árboles; LIME ajusta un modelo lineal local con muestras y puede discrepar si el modelo tiene interacciones. La correlación de Spearman entre ambos fue 0,57, 0,70, −0,13, 0,30 y 0,48 en los cinco casos. Por eso usamos SHAP como explicación principal y LIME como contraste."),
("¿Cuáles son los factores que más influyen en el retraso?",
 "Por permutación: plazo prometido (caída de AUC-PR 0,144), carga relativa de la plataforma (0,112), estado del comprador (0,074), distancia (0,057) y días históricos del vendedor (0,044). SHAP da el mismo orden general."),
("¿Qué es la carga relativa de la plataforma?",
 "Pedidos de los últimos 7 días dividido por el promedio semanal de las 8 semanas previas. Un valor alto indica saturación; en el primer caso explicado aportó +14 puntos porcentuales al riesgo."),
("¿Por qué el R² de la regresión es solo 0,41?",
 "Porque gran parte de la demora depende de eventos que no están en los datos (huelgas, clima, fallas del transportista). Aun así mejoró de 0,29 (v1) a 0,32 (v2, con distancia) y 0,41 (v3, con plazo, carga e historial del vendedor), con error medio de 4,44 días frente a 6,19 del baseline."),
("¿Por qué el pronóstico de ventas es casi plano?",
 "Hay menos de dos años de historia y un solo noviembre; el modelo no puede aprender estacionalidad anual ni Black Friday. Debe leerse como nivel base (alrededor de R$ 44 mil diarios). Ridge con rezagos tuvo MAPE 11,8 % frente a 20,4 % del modelo ingenuo."),
("¿Por qué SARIMA y Prophet salieron peores que Ridge?",
 "Con una serie corta y ruidosa, los modelos de rezagos con media móvil y día de la semana se adaptan mejor. SARIMA no convergió por completo según el optimizador. Se ejecutaron en Google Colab (MAPE 31,5 % y 24,6 %)."),
("¿Por qué k = 4 si la silueta es máxima en k = 5?",
 "La silueta de k = 5 es 0,254 y la de k = 4 es 0,238, una diferencia pequeña. Elegimos k = 4 por interpretabilidad de negocio; es una decisión de interpretación y no un óptimo estadístico, y k = 5 es una alternativa válida."),
("¿Qué utilidad tienen las reglas de asociación si solo el 2,4 % compró en varias categorías?",
 "Son hipótesis exploratorias para ventas cruzadas. Se apoyan en 2 270 clientes y cada regla en 10 a 54 clientes. La más fuerte (bed_bath_table con home_confort) tiene lift 3,1 y es coherente con el grafo, donde el hogar es el núcleo."),
("¿Qué diferencia hay entre Apriori, FP-Growth y ECLAT?",
 "Dan exactamente los mismos resultados (115 itemsets y 105 reglas). Cambia la eficiencia: Apriori genera candidatos nivel por nivel y es el más lento (0,095 s); FP-Growth usa un árbol de prefijos (0,007 s) y ECLAT intersecta listas de transacciones (0,002 s)."),
("¿Cómo funciona el monitoreo? ¿Es real o solo teoría?",
 "Se simuló con datos reales mes a mes entre noviembre de 2017 y agosto de 2018. Se midió AUC, calibración, MAE y deriva con PSI, con alertas definidas, cuatro políticas de reentrenamiento, 28 versiones con hash SHA-256 y un registro de auditoría. No es un sistema en producción, pero la lógica está ejecutada con datos."),
("¿Qué encontraron en la simulación de reentrenamiento?",
 "Reentrenar cada mes no superó al modelo congelado (AUC medio 0,641 con A, 0,630 con B, 0,642 con C y 0,627 con D). Los choques (noviembre de 2017, febrero–marzo de 2018, huelga de mayo de 2018) no se aprenden del pasado reciente. Recomendamos monitorear, alertar y reentrenar con criterio, y agregar variables que anticipen choques."),
("¿Qué es el PSI?",
 "Índice de estabilidad de la población: compara la distribución de una variable en el presente con la de referencia usando 10 percentiles. Entre 0,10 y 0,25 es advertencia y mayor a 0,25 es cambio mayor. Aquí superó 0,25 en los diez meses, sobre todo por la carga relativa y el historial de retrasos de los vendedores."),
("¿Cómo corre el modelo en el navegador? ¿Es el mismo que en Python?",
 "Se exportan los árboles de XGBoost a JSON y se evalúan en JavaScript. Verificamos la paridad con 300 pedidos: diferencia máxima 3,3×10⁻⁷ en probabilidad. Fue necesario redondear a 32 bits (Math.fround) porque XGBoost compara en precisión simple; sin eso la diferencia llegaba a 0,11."),
("¿Qué pasa con la privacidad de quien usa el simulador?",
 "Nada se envía: el cálculo ocurre en el navegador. Solo la API opcional de Flask recibe datos si el equipo decide desplegarla."),
("¿Cómo se despliega gratis?",
 "GitHub Pages con un flujo automático, o arrastrando la carpeta dist a Netlify Drop; también Render (la API se duerme tras 15 minutos de inactividad en el plan gratuito), Docker, o el archivo único datasmart.html que se abre con doble clic. Los pasos están en docs/DESPLIEGUE.md."),
("¿Qué pruebas tiene el proyecto?",
 "23 pruebas con pytest (datos, variables, modelo, API, monitoreo y paridad Python–JavaScript) y una prueba de humo con navegador que abre las diez secciones en escritorio y móvil sin errores de consola."),
("¿Qué limitaciones tiene el estudio?",
 "Evaluación aleatoria (0,78) frente a temporal (0,70); historia corta; 97 % de clientes compra una sola vez; choques no predecibles con el pasado; censura a la derecha en julio–agosto de 2018; asociaciones y no causalidad; y el conjunto no incluye marketing ni navegación."),
("¿Qué no implementaron de la propuesta?",
 "K-Medoids, LSTM y ARIMAX. La propuesta pide al menos dos técnicas de clustering (hicimos K-Means, jerárquico y DBSCAN) y alguno de los modelos de series (hicimos SARIMA, Prophet y modelos de rezagos)."),
("¿Qué mejorarían con más tiempo?",
 "Agregar calendario (feriados, Black Friday), huelgas y campañas; conseguir más años de datos para modelar estacionalidad; probar K-Medoids y modelos de supervivencia; y calibrar por región."),
("¿Cómo se manejaron los datos faltantes y atípicos?",
 "Los faltantes se trataron según el caso (categoría «sin_categoria», mediana por categoría para 2 productos, exclusión solo del análisis de entrega para 2 965 pedidos sin fecha). Los atípicos se detectaron con IQR y Z-score y no se eliminaron, porque son pedidos reales; se winsorizaron al percentil 99 solo para la regresión."),
("¿Por qué no usaron escalamiento en el modelo final?",
 "XGBoost parte por umbrales y no lo necesita. Comparamos MinMaxScaler y StandardScaler con modelos lineales y el AUC no cambió (0,711–0,712). También comparamos One-Hot y Label Encoding: no afecta a XGBoost, pero deteriora la regresión logística (0,677)."),
]
H = "<html><head><meta charset='utf-8'><style>@page{size:A4;margin:20mm}body{font-family:Inter;font-size:10pt;line-height:1.5;color:#1f2937}h1{font-family:Caladea;color:#0f2544;font-size:20pt;border-bottom:1.5px solid #0f2544;padding-bottom:3pt}h2{font-family:Caladea;color:#0f766e;font-size:12.5pt;margin:12pt 0 3pt}.q{page-break-inside:avoid;margin-bottom:9pt}.q b{color:#0f2544}.who{font-size:8.5pt;color:#6b7280}p{margin:0 0 4pt}</style></head><body>"
H += "<h1>Guion de sustentación — DataSmart (Grupo 4)</h1><p>18 diapositivas, unos 15 a 18 minutos. El reparto por diapositiva es una propuesta; cámbienlo según quién domine cada tema. Todos deben conocer todo el proyecto: las preguntas del jurado pueden ir a cualquiera.</p>"
for i, s in enumerate(g, 1):
    H += f"<h2>Diapositiva {i}. {html.escape(s['t'])} <span class='who'>— {html.escape(s['who'])}</span></h2><p>{html.escape(s['notes'])}</p>"
H += "<h1 style='page-break-before:always'>Posibles preguntas y respuestas</h1><p>Todas las cifras provienen de los resultados del proyecto (informe final).</p>"
for q, a in QA:
    H += f"<div class='q'><p><b>{html.escape(q)}</b></p><p>{html.escape(a)}</p></div>"
H += "<h2>Consejos para la sustentación</h2><p>1) Si no saben una respuesta, digan lo que sí saben y reconozcan el límite; el informe ya declara las limitaciones. 2) Practiquen la demostración del simulador con el escenario «Fin de año con alta carga» y con «Pedido típico» para mostrar el contraste. 3) Lleven el archivo datasmart.html en una memoria USB por si falla internet. 4) Tengan abiertas las secciones Explicación y Monitoreo por si piden evidencia.</p></body></html>"
(D / "_guion.html").write_text(H, encoding="utf-8")
with sync_playwright() as p:
    b = p.chromium.launch(executable_path="/usr/bin/google-chrome", args=["--no-sandbox"]); pg = b.new_page(); pg.goto((D / "_guion.html").as_uri()); pg.wait_for_timeout(800)
    pg.pdf(path=str(D / "Guion_y_Preguntas_DataSmart_Grupo4.pdf"), format="A4", print_background=True, margin={"top": "20mm", "bottom": "20mm", "left": "20mm", "right": "20mm"}); b.close()
print("ok", len(QA))
