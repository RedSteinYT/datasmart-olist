"""Construye el Informe Final (HTML -> PDF con Chrome sin cabeza).
Toda cifra de modelos sale de analysis/outputs_* y web/data/*.json. Dos pasadas: numeración de tablas/figuras y paginación del índice."""
import json, re, subprocess, sys, html
from pathlib import Path
import pandas as pd
from playwright.sync_api import sync_playwright

R = Path(__file__).resolve().parents[1]
A = R / "analysis"
O16, O13, O10 = A / "outputs_s16", A / "outputs_s13", A / "outputs_s10"
FIG = R / "docs" / "figuras"
FIGS_OLD = A / "figs"
WD = R / "web" / "data"
SALIDA = R / "docs" / "Informe_Final_DataSmart_Grupo4.pdf"

cla = json.load(open(WD / "clasificacion.json"))
res = json.load(open(WD / "resumen.json"))
mon = json.load(open(WD / "monitoreo.json"))
txt = json.load(open(WD / "texto.json"))
F = cla["final"]
FF = F["final"]
kpi = res["kpi"]
tmp = json.load(open(O16 / "16_validacion_temporal.json"))
r16 = json.load(open(O16 / "16_resumen.json"))
geo = pd.read_csv(O16 / "10_geo_resumen.csv").set_index("indicador")["valor"]
ex = json.load(open(O16 / "14_resumen.json"))
ing = json.load(open(O16 / "17_resumen.json"))


def f(x, d=0):
    s = f"{x:,.{d}f}"
    return s.replace(",", " ").replace(".", ",")


def pc(x, d=1):
    return f(x * 100, d) + " %"


NUMS = {}
CONT = {"t": 0, "f": 0}
HEADS = []


def ref(k):
    return NUMS.get(k, "?")


def esc(s):
    return html.escape(str(s), quote=False)


def tabla(key, cap, head, rows, ancho=None, pequeno=False):
    CONT["t"] += 1
    NUMS[key] = f"Tabla {CONT['t']}"
    cls = "peq" if pequeno else ""
    th = "".join(f"<th>{h}</th>" for h in head)
    tr = ""
    for r in rows:
        tr += "<tr>" + "".join(f"<td{' class=n' if re.match(r'^[-−+]?[\\d\\u00a0]+([,.]\\d+)?\\s?%?$', str(c)) else ''}>{c}</td>" for c in r) + "</tr>"
    return f'<div class="tabla {cls}"><div class="cap">{NUMS[key]}. {cap}</div><table><thead><tr>{th}</tr></thead><tbody>{tr}</tbody></table></div>'


def fig(key, fichero, cap, ancho=100):
    CONT["f"] += 1
    NUMS[key] = f"Figura {CONT['f']}"
    p = FIG / f"{fichero}.png"
    if not p.exists():
        p = FIGS_OLD / f"{fichero}.png"
    return f'<figure style="width:{ancho}%"><img src="{p.as_uri()}"><figcaption>{NUMS[key]}. {cap}</figcaption></figure>'


def h1(num, t):
    HEADS.append((num, t))
    return f'<h1 id="s{num}">Anexo {num}. {t}</h1>' if str(num) in list("ABCDEF") else f'<h1 id="s{num}">{num}. {t}</h1>'


def h2(t):
    return f"<h2>{t}</h2>"


def p(t):
    return f"<p>{t}</p>"


def ul(items):
    return "<ul>" + "".join(f"<li>{i}</li>" for i in items) + "</ul>"


def nota(t):
    return f'<div class="nota">{t}</div>'


def cuerpo():
    o = []
    A_ = o.append
    # ---------------------------------------------------------------- 1
    A_(h1(1, "Introducción"))
    A_(p("El presente informe documenta el proyecto de Minería de Datos del Grupo 4 de principio a fin. Parte del Segundo Informe (entregables 2 y 3) y lo "
         "completa con lo realizado en la cuarta etapa: clasificación, minería de textos, explicabilidad, propuesta de monitoreo y mantenimiento, aplicación web con dashboard, "
         "pruebas y documentación. Reúne así, en un solo documento, la comprensión del negocio y de los datos (primer entregable), la preparación y los primeros modelos (segundo), "
         "el modelamiento avanzado (tercero) y el producto final (cuarto)."))
    A_(p("El estudio utiliza el <i>Brazilian E-Commerce Public Dataset by Olist</i>, publicado en Kaggle. Olist es una plataforma brasileña que conecta vendedores con clientes de distintos estados; "
         "el conjunto integra pedidos, clientes, productos, pagos, reseñas, vendedores y geolocalización. El proyecto se enmarca en la propuesta <b>DataSmart: plataforma inteligente para el análisis, "
         "segmentación y predicción de clientes</b>, cuyo producto final es una aplicación web con dashboard, modelos predictivos y documentación técnica."))
    A_(p("<b>Hilo conductor.</b> La logística conecta todos los resultados: un pedido que llega tarde recibe una reseña baja con mucha mayor frecuencia, el segmento de clientes más insatisfecho es el de entrega lenta y "
         "las variables que explican la demora (plazo prometido, carga de la plataforma, distancia y destino) son las mismas que permiten anticiparla. Por eso el modelo central del producto final es un clasificador "
         f"que estima, al momento de la compra, la probabilidad de que un pedido llegue tarde (AUC-ROC {f(FF['AUC_ROC'],3)} en una partición aleatoria) y explica cada predicción."))
    A_(p("Los resultados se presentan con sus límites. En particular, la evaluación en el tiempo (entrenar con el pasado y probar en los meses siguientes) es peor que la aleatoria, "
         "y el reentrenamiento mensual simulado no superó al modelo congelado; ambos hallazgos se explican en las secciones 17 y 20."))

    A_(h1(2, "Planteamiento del problema"))
    A_(p("Las plataformas de comercio electrónico generan grandes volúmenes de registros, pero estos no producen valor por sí solos. Para orientar decisiones se requiere identificar qué categorías generan "
         "mayor ingreso, qué zonas concentran las ventas, cómo se comportan los clientes en el tiempo y qué factores se vinculan con la satisfacción o con la demora de entrega."))
    A_(p("El problema es la falta de una visión integrada del desempeño de Olist a partir de sus pedidos entregados, pagos, productos, clientes y reseñas, que sirva para segmentar clientes, descubrir asociaciones entre categorías, "
         "pronosticar ventas, <b>anticipar los pedidos con riesgo de llegar tarde</b> y explicar por qué el sistema lo considera así, de modo que un equipo no técnico pueda usar la información."))

    A_(h1(3, "Objetivos"))
    A_(p("<b>Objetivo general.</b> Analizar el comportamiento comercial, logístico y de satisfacción de los pedidos entregados en Olist para identificar patrones y oportunidades de mejora, aplicando técnicas de minería de datos "
         "(asociación, clustering, series temporales, grafos, regresión, clasificación y minería de textos) y entregando una plataforma web explicable y con propuesta de monitoreo."))
    A_(p("<b>Objetivos específicos.</b>"))
    A_(ul(["Describir el alcance y las relaciones entre las tablas relevantes y medir ingresos, volumen, tiempo de entrega y satisfacción.",
           "Evaluar la calidad de los datos, documentar el tratamiento de cada problema y construir un dataset integrado a nivel de pedido.",
           "Descubrir reglas de asociación (Apriori, FP-Growth, ECLAT), segmentar clientes (RFM, ABC, clustering) y pronosticar ventas diarias.",
           "Representar las relaciones entre categorías en un grafo y detectar comunidades.",
           "Construir modelos de regresión del tiempo de entrega y un clasificador de entrega tardía, tratando el desbalance de clases.",
           "Analizar los comentarios de las reseñas (sentimiento, aspectos y temas) y relacionarlos con el riesgo logístico.",
           "Explicar las predicciones (importancia por permutación, SHAP y LIME) y proponer la operación del modelo (desempeño, deriva, reentrenamiento, versionado, registro y auditoría).",
           "Integrar todo en una aplicación web desplegable sin costo, con dashboard interactivo, API, pruebas y documentación."]))

    # ---------------------------------------------------------------- 4
    A_(h1(4, "Descripción y alcance del conjunto de datos"))
    A_(p("La fuente es el <i>Brazilian E-Commerce Public Dataset by Olist</i> (Kaggle). El período abarca pedidos realizados entre el 15 de septiembre de 2016 y el 29 de agosto de 2018. "
         "Se trabaja con pedidos en estado «delivered», porque permiten evaluar pago, entrega y reseña. El archivo de pedidos contiene 99 441 registros; al filtrar los entregados quedan 96 478, "
         "cuyos pagos suman R$ 15 422 461,77 (montos en reales brasileños)."))
    A_(p("Las tablas son: pedidos, clientes, ítems, pagos, reseñas, productos, vendedores, geolocalización y traducción de categorías. <i>order_id</i> relaciona pedidos, ítems, pagos y reseñas; <i>customer_id</i> relaciona pedidos con clientes; "
         "<i>product_id</i> e <i>seller_id</i> relacionan ítems con productos y vendedores. Para el modelamiento se construyó un dataset más restrictivo, a nivel de pedido, que concilia la "
         f"{ref('t_conc')} con el universo del análisis exploratorio."))
    A_(tabla("t_conc", "Conciliación del universo de análisis.", ["Etapa", "Pedidos", "Criterio"], [
        ["Pedidos en la tabla principal", "99 441", "Todos los estados"],
        ["Pedidos entregados (universo del EDA)", "96 478", "order_status = delivered"],
        ["Entregados con fecha de entrega válida", "96 470", "Se excluyen 8 pedidos entregados sin fecha de entrega al cliente"],
        ["Dataset procesado (modelamiento)", "96 469", "Se excluye 1 pedido entregado sin registro de pago"]]))
    A_(p("El ingreso del dataset procesado es de R$ 15 421 082,85, es decir, R$ 1 378,92 menos que el universo del EDA, que corresponde a los 9 pedidos excluidos."))

    A_(h1(5, "Preguntas de negocio y KPIs"))
    A_(p("Las preguntas del primer entregable se mantienen como marco: ingreso por categoría y por estado (suma de <i>payment_value</i>), facturación mensual, tiempo de entrega (entrega al cliente menos compra) y satisfacción "
         "(distribución de <i>review_score</i>, con atención a 1–2 y 4–5). La propuesta pide además preguntas que responden los modelos; la tabla siguiente indica dónde se contesta cada una."))
    A_(tabla("t_preg", "Preguntas de negocio y dónde se responden.", ["Pregunta", "Técnica", "Sección"], [
        ["¿Qué categorías se compran juntas y cuáles tienen mayor asociación?", "Reglas de asociación", "12"],
        ["¿Qué segmentos de clientes existen y cuáles tienen mayor valor?", "RFM, ABC, clustering", "13"],
        ["¿Cómo evolucionan las ventas y cuáles serán las de los próximos 7, 30, 60 y 90 días?", "Series temporales", "14"],
        ["¿Qué categorías están fuertemente conectadas? ¿Hay comunidades?", "Grafos", "15"],
        ["¿Cuánto tardará un pedido y qué variables influyen?", "Regresión", "16"],
        ["¿Qué pedidos tienen mayor probabilidad de llegar tarde?", "Clasificación", "17"],
        ["¿Qué variables influyen en esa predicción y por qué?", "Importancia, SHAP, LIME", "18"],
        ["¿Qué temas aparecen en los comentarios y cómo se relacionan con la entrega?", "Minería de textos", "19"],
        ["¿Cómo se mantiene el modelo en operación?", "Monitoreo y versionado", "20"]], pequeno=True))

    A_(h1(6, "Diccionario de datos"))
    A_(p("<b>Pedidos:</b> order_id, customer_id, order_status, order_purchase_timestamp, order_approved_at, order_delivered_customer_date y order_estimated_delivery_date. "
         "<b>Clientes:</b> customer_id (por pedido), customer_unique_id (identifica a quien reaparece), ciudad y estado. <b>Ítems:</b> order_item_id, product_id, seller_id, price y freight_value. "
         "<b>Pagos:</b> medio, cuotas e importe. <b>Productos:</b> categoría, peso y dimensiones. <b>Reseñas:</b> review_score de 1 a 5 y comentarios opcionales. "
         "<b>Vendedores</b> y <b>geolocalización</b> (prefijo postal, latitud, longitud). Las variables derivadas y el diccionario del dataset final (51 columnas) se documentan en la sección 11 y en el Anexo B."))

    # ---------------------------------------------------------------- 7
    A_(h1(7, "Resultados del análisis exploratorio"))
    mx = max(res["mensual"], key=lambda d: d["ingreso"])
    A_(p(f"El ingreso total de los pedidos entregados es de R$ 15,42 millones, con {f(kpi['pedidos'])} pedidos y {f(kpi['clientes'])} clientes únicos; el ticket medio es de R$ {f(kpi['ticket'],2)}. "
         f"La mayor actividad mensual ocurre en noviembre de 2017 (R$ 1,15 millones y 7 289 pedidos), posiblemente por campañas estacionales; como solo hay un noviembre completo, no puede confirmarse su recurrencia. "
         f"La {ref('f_mensual')} muestra el volumen mensual y la proporción de entregas tardías."))
    A_(fig("f_mensual", "f01_mensual", "Pedidos entregados por mes y porcentaje de entregas tardías.", 88))
    A_(p("Las cinco categorías con mayor ingreso son health_beauty (R$ 1,41 millones), watches_gifts (R$ 1,26), bed_bath_table (R$ 1,23), sports_leisure (R$ 1,12) y computers_accessories (R$ 1,03). "
         "Por estado, São Paulo lidera con R$ 5,77 millones (40 501 pedidos), seguido de Río de Janeiro (R$ 2,06) y Minas Gerais (R$ 1,82)."))
    A_(p(f"El tiempo medio de entrega es de {f(kpi['dias_entrega'],2)} días (mediana 10,2) y la puntuación media de reseña es {f(kpi['puntaje'],2)}. "
         "Las calificaciones se concentran en valores altos (57 328 reseñas de 5 estrellas, 57,8 %), pero hay 11 424 de 1 estrella (11,5 %). "
         f"El {pc(kpi['pct_tardias'])} de los pedidos llega después de la fecha prometida, y esas entregas tardías se asocian con una reseña media de 2,57 frente a 4,29 en las puntuales "
         f"(la {ref('f_estados')} muestra que el retraso depende mucho del destino)."))
    A_(fig("f_estados", "f02_estados", "Porcentaje de entregas tardías por estado del comprador.", 82))
    A_(fig("f_review", "s10_review_vs_tardia", "Puntuación de reseña según entrega puntual o tardía (primer entregable).", 80))

    A_(h1(8, "Evaluación de la calidad de datos"))
    A_(p("Hay 2 965 pedidos sin fecha de entrega (coherentes con estados no entregados), 610 productos sin categoría, 87 656 títulos y 58 247 mensajes de reseña vacíos (campos opcionales) y 261 831 filas de "
         "geolocalización duplicadas exactas. Esta última tabla se depuró en la etapa de variables geográficas (sección 11.2). El tratamiento de cada problema se resume en la "
         f"{ref('t_calidad')} (sección 10)."))

    A_(h1(9, "Metodología de trabajo"))
    A_(p(f"Se sigue CRISP-DM. A la fecha de este informe todas las fases están completadas ({ref('t_crisp')}). Todo el trabajo está en scripts de Python reproducibles que guardan sus resultados en CSV y figuras (Anexo A)."))
    A_(tabla("t_crisp", "Estado final de cada fase CRISP-DM.", ["Fase", "Estado", "Evidencia"], [
        ["Comprensión del negocio", "Completada (sem. 7)", "Problema, objetivos, preguntas y KPIs (secciones 2–5)"],
        ["Comprensión de los datos", "Completada (sem. 7)", "Inventario, diccionario, EDA y calidad (secciones 4–8)"],
        ["Preparación de los datos", "Completada (sem. 10 y 16)", "Dataset de 96 469 pedidos × 51 variables; ingeniería de características (secciones 10–11)"],
        ["Modelado", "Completada (sem. 10, 13 y 16)", "Asociación, clustering, series, grafos, regresión, clasificación y textos (secciones 12–19)"],
        ["Evaluación", "Completada", "Comparación de modelos, validación temporal, intervalos de confianza y explicabilidad (secciones 16–18, 22)"],
        ["Despliegue", "Completada", "Aplicación web, API, pruebas y guía de despliegue gratuito (secciones 20–21, anexos C–E)"]], pequeno=True))

    # ---------------------------------------------------------------- 10
    A_(h1(10, "Preparación de datos"))
    A_(p("La preparación se documentó problema por problema."))
    A_(tabla("t_calidad", "Tratamiento de problemas de calidad.", ["Problema", "Hallazgo", "Tratamiento"], [
        ["Registros duplicados", "0 filas duplicadas en pedidos, ítems, pagos, clientes, productos y reseñas", "Verificado; sin acción"],
        ["Reseñas múltiples", "547 pedidos con más de una reseña", "Se conserva la más reciente"],
        ["Fecha de entrega faltante", "2 965 pedidos (todos los estados)", "Se excluyen solo del análisis de entrega"],
        ["Categoría faltante", "610 productos", "Etiqueta «sin_categoria»; traducción al inglés"],
        ["Peso y dimensiones faltantes", "2 productos", "Mediana de su categoría"],
        ["Pagos con valor 0", "9 registros", "Se conservan (vales); no afectan los modelos"],
        ["Inconsistencias", "0 entregas anteriores a la compra; 0 ítems con precio ≤ 0", "Verificado; sin acción"],
        ["Geolocalización", "261 831 duplicados exactos; 42 filas fuera de Brasil", "Promedio por prefijo postal; se descartan las filas fuera de Brasil"]], pequeno=True))
    A_(h2("10.1 Valores atípicos: IQR y Z-score"))
    A_(p(f"Se aplicaron ambos criterios ({ref('t_outl')}). No se eliminan, porque son pedidos reales (un envío de 200 días ocurrió); se winsorizan al percentil 99 solo para la regresión de días de entrega."))
    A_(tabla("t_outl", "Valores atípicos detectados por IQR (1,5×) y por Z-score (|Z| > 3).", ["Variable", "IQR", "Z > 3"], [
        ["Valor pagado", "7 575", "1 698"], ["Días de entrega", "4 895", "1 571"], ["Flete", "9 694", "1 540"], ["Precio", "7 658", "1 660"]], pequeno=True))
    A_(h2("10.2 Integración de fuentes y estadísticos"))
    A_(p("La unidad de análisis es el pedido entregado. Se integraron seis tablas: pedidos, clientes, pagos (valor, cuotas máximas, número de medios y medio principal), ítems (número de ítems, productos y vendedores, precio, flete, peso, "
         "volumen y categoría principal), productos y reseñas (una por pedido). Se formatearon fechas y tipos y se tradujeron las categorías. El resultado inicial es una tabla de 96 469 pedidos × 41 variables."))
    A_(tabla("t_stat", "Estadísticos descriptivos del dataset procesado.", ["Variable", "Media", "Mediana", "Desv. est.", "Máximo"], [
        ["Valor pagado (R$)", "159,86", "105,28", "218,82", "13 664,08"], ["Días de entrega", "12,56", "10,22", "9,55", "209,63"],
        ["Ítems por pedido", "1,14", "1", "0,54", "21"], ["Puntuación de reseña (95 823 pedidos con reseña)", "4,16", "5", "1,28", "5"]], pequeno=True))
    A_(h2("10.3 Codificación de variables categóricas y escalamiento"))
    cod = pd.read_csv(O16 / "19_codificacion_escalamiento.csv")
    A_(p(f"La propuesta pide mostrar One-Hot y Label Encoding, y MinMaxScaler y StandardScaler. Se compararon sobre el mismo problema (entrega tardía, misma partición) en la {ref('t_cod')}. "
         "Con modelos lineales el escalamiento prácticamente no cambia el resultado (diferencia en la tercera cifra decimal), porque la regularización es suave y las variables ya están en escalas manejables tras el logaritmo. "
         "El Label Encoding no afecta a XGBoost, que parte los árboles por umbrales, pero deteriora la regresión logística porque impone un orden artificial entre estados y categorías. "
         "Por ello el modelo final usa One-Hot (estado y 15 categorías principales; el resto, «otras») y no necesita escalamiento."))
    A_(tabla("t_cod", "Efecto de la codificación y del escalamiento (AUC-ROC y AUC-PR en prueba).", ["Modelo", "Codificación", "Escalamiento", "AUC-ROC", "AUC-PR"],
             [[r.modelo, r.codificacion, r.escalamiento, f(r.AUC_ROC, 4), f(r.AUC_PR, 4)] for r in cod.itertuples()], pequeno=True))
    A_(h2("10.4 Balanceo de clases"))
    A_(p("El balanceo se trata en la sección 17, donde se comparan submuestreo, sobremuestreo aleatorio, SMOTE y ADASYN."))

    # ---------------------------------------------------------------- 11
    A_(h1(11, "Ingeniería de características"))
    A_(p("Se construyeron variables derivadas en tres tandas: logísticas y comerciales (Segundo Informe), geográficas y causales (cuarta etapa). El dataset final tiene 51 columnas (Anexo B)."))
    A_(h2("11.1 Variables derivadas iniciales"))
    A_(tabla("t_vars", "Grupos de variables del dataset.", ["Grupo", "Variables"], [
        ["Logística", "dias_entrega, dias_estimados, retraso_dias, entrega_tardia (0/1), dias_aprobacion"],
        ["Comercial", "valor_pago, n_cuotas, n_medios, medio_principal, precio_total, flete_total, ratio_flete, precio_medio_item, n_items, n_productos, n_vendedores"],
        ["Producto", "peso_total_g, volumen_total_cm3, categoria_principal"],
        ["Temporal", "mes, dia_semana, hora, fin_de_semana"],
        ["Cliente y satisfacción", "customer_unique_id, customer_state, customer_city, review_score, resena_baja (≤ 2)"],
        ["Geográficas (11.2)", "distancia_km, mismo_estado"],
        ["Causales (11.3)", "carga_rel, vend_hist_dias, vend_hist_tardio, vend_hist_n"]], pequeno=True))
    A_(h2("11.2 Distancia entre vendedor y comprador"))
    A_(p(f"La tabla de geolocalización tenía {f(geo['filas geolocalización'])} filas, con {f(geo['duplicados exactos'])} duplicados exactos y {f(geo['filas fuera de Brasil (descartadas)'])} puntos fuera de Brasil. "
         f"Tras promediar por prefijo postal quedaron {f(geo['prefijos postales con coordenada'])} prefijos con coordenada. La distancia (fórmula de haversine) se calculó para el {f(geo['cobertura de distancia (% pedidos)'],2)} % de los pedidos; "
         f"la mediana es de {f(geo['distancia mediana (km)'],0)} km, el promedio de {f(geo['distancia promedio (km)'],0)} km y solo el {f(geo['% mismo estado'],0)} % de los pedidos se vende dentro del mismo estado. "
         f"La correlación de Spearman con los días de entrega es de {f(geo['Spearman distancia vs días de entrega'],2)}."))
    A_(h2("11.3 Variables causales con información disponible al comprar"))
    A_(p("Para predecir el retraso con lo que se sabe al momento de la compra se añadieron: <b>días estimados</b> (plazo prometido al cliente), <b>carga relativa</b> de la plataforma (pedidos de los últimos 7 días frente al promedio de las 8 semanas previas), "
         "y el historial del vendedor medido <b>solo con pedidos anteriores</b>: días de entrega medios, porcentaje de entregas tardías y número de pedidos previos. Este cuidado evita fuga de información del futuro. "
         "Una salvedad honesta: <i>dias_aprobacion</i> se conoce cuando se aprueba el pago, no estrictamente al comprar."))
    A_(h2("11.4 Eliminación de colinealidad"))
    A_(p(f"Se calculó el factor de inflación de la varianza (VIF) de las 18 variables numéricas: el máximo es {f(ing['vif_max'],2)} (precio), de modo que ninguna supera el umbral de 5. "
         f"La mayor correlación absoluta es {f(ing['corr_max'],3)} entre peso y volumen. No fue necesario eliminar variables; el resultado se muestra en la {ref('f_vifpca')}."))
    A_(h2("11.5 Reducción de dimensionalidad y selección por importancia"))
    A_(p(f"El PCA necesita {ing['k90']} de las {ing['n_num']} componentes para explicar el 90 % de la varianza, lo que indica poca redundancia. "
         "La selección por importancia se hizo con la permutación: las seis variables numéricas principales son " + ", ".join(ing["seleccion"]) + "."))
    A_(fig("f_vifpca", "f13_vif_pca", "VIF de las variables numéricas y varianza acumulada del PCA.", 90))
    A_(h2("11.6 LDA y QDA"))
    ci = pd.read_csv(O16 / "17_comparacion_ingenieria.csv")
    A_(p(f"Se compararon la regresión logística con todas las variables, con la selección y con PCA, y los discriminantes lineal y cuadrático ({ref('t_ing')}). "
         "Ningún reductor mejora al modelo completo: la información está repartida y los discriminantes suponen distribuciones normales que no se cumplen. "
         "Por eso la reducción no se usa en el modelo final; se documenta como experimento con resultado negativo."))
    A_(tabla("t_ing", "Comparación de alternativas de ingeniería de características (clasificación de entrega tardía).", ["Modelo", "Variables", "AUC-ROC", "AUC-PR"],
             [[r.modelo, r.n_variables, f(r.AUC_ROC, 4), f(r.AUC_PR, 4)] for r in ci.itertuples()], pequeno=True))

    # ---------------------------------------------------------------- 12
    A_(h1(12, "Reglas de asociación"))
    A_(p("Como el 97 % de los clientes compró una sola vez, la canasta se definió como el conjunto de categorías distintas compradas por un cliente único; se analizaron los 2 270 clientes (2,4 %) con al menos dos categorías. "
         "Se implementaron Apriori, FP-Growth y ECLAT con soporte mínimo de 0,4 %, confianza mínima de 5 % e itemsets de hasta tres categorías. Los tres obtienen los mismos 115 itemsets y 105 reglas y difieren solo en tiempo "
         f"({ref('t_alg')})."))
    al = pd.read_csv(O10 / "03_comparacion_algoritmos.csv")
    A_(tabla("t_alg", "Comparación de algoritmos de asociación (tiempos medidos al volver a ejecutar).", ["Algoritmo", "Itemsets", "Reglas", "Tiempo (ms)"],
             [[r.algoritmo, r.itemsets_frecuentes, r.reglas, f(r.tiempo_s * 1000, 0)] for r in al.itertuples()], pequeno=True))
    tr = pd.read_csv(O10 / "04_top_reglas.csv").head(9)
    A_(tabla("t_reglas", "Reglas con mayor lift (2 270 canastas).", ["Antecedente", "Consecuente", "Soporte", "Confianza", "Lift", "Clientes"],
             [[r.antecedente, r.consecuente, f(r.support, 3), f(r.confidence, 3), f(r.lift, 2), r.n_clientes] for r in tr.itertuples()], pequeno=True))
    A_(p("La regla más fuerte vincula bed_bath_table con home_confort: el 74 % de quienes compraron en home_confort también compraron en bed_bath_table (lift 3,1). También hay asociación entre bebé y juguetes. "
         "Cada regla se apoya en entre 10 y 54 clientes, por lo que se consideran hipótesis para ventas cruzadas y no conclusiones definitivas."))
    A_(fig("f_reglas", "s10_reglas_lift", "Reglas de asociación ordenadas por lift.", 78))

    # ---------------------------------------------------------------- 13
    A_(h1(13, "Segmentación de clientes"))
    A_(h2("13.1 RFM y ABC"))
    A_(p("Se calcularon recencia, frecuencia y monto por cliente único (93 349 clientes). Solo el 3 % compró más de una vez. En el análisis ABC por monto, la clase A (45 600 clientes, 48,8 %) concentra el 80 % del ingreso (R$ 12,34 millones), "
         "la B (28 542; 30,6 %) el 15 % y la C (19 207; 20,6 %) el 5 %."))
    A_(h2("13.2 Selección del número de segmentos"))
    A_(p("Se aplicó K-Means sobre recencia, frecuencia, monto, reseña media, días de entrega medios y proporción de flete (logaritmo y estandarización). La silueta es máxima en k = 5 (0,254); "
         f"se eligió k = 4 (0,238) por interpretabilidad de negocio, una decisión de interpretación y no un óptimo estadístico ({ref('f_kmeans')})."))
    A_(fig("f_kmeans", "f14_segmentos_series", "Silueta según k y ventas diarias reales frente a dos pronósticos en la ventana de validación.", 92))
    pf = pd.read_csv(O13 / "03_perfil_clusters.csv")
    nom = {0: "Alto valor satisfecho", 1: "Ticket bajo, flete alto", 2: "Insatisfechos (entrega lenta)", 3: "Recurrentes"}
    A_(tabla("t_perfil", "Perfil de los cuatro segmentos (nombres propuestos por el equipo).", ["Clúster", "Perfil", "Clientes", "% clientes", "% ingreso", "Monto medio (R$)", "Reseña", "Entrega (días)", "Ratio flete"],
             [[int(r.cluster_kmeans), nom[int(r.cluster_kmeans)], f(r.clientes), f(r.pct_clientes, 1), f(r.pct_ingreso, 1), f(r.monetario, 0), f(r.review, 2), f(r.dias_entrega, 1), f(r.ratio_flete, 2)] for r in pf.itertuples()], pequeno=True))
    A_(p("El segmento 2 es el hallazgo más relevante: 15,5 % de los clientes y 17,6 % del ingreso, pero reseña media de 1,66 y 21,2 días de entrega, casi el doble que el segmento 0. Los recurrentes (3 %) tienen el mayor monto por cliente."))
    A_(fig("f_perfil", "s13_perfil", "Participación de cada segmento en clientes e ingreso.", 80))
    A_(h2("13.3 Comparación de algoritmos"))
    cc = pd.read_csv(O13 / "02_clustering_comparacion.csv")
    A_(tabla("t_clus", "Comparación de algoritmos de clustering.", ["Modelo", "Clusters", "Silueta", "Davies-Bouldin", "Calinski-Harabasz", "Ruido", "Muestra"],
             [[r.modelo, r.n_clusters, "—" if pd.isna(r.silhouette) else f(r.silhouette, 3), "—" if pd.isna(r.davies_bouldin) else f(r.davies_bouldin, 2),
               "—" if pd.isna(r.calinski) else f(r.calinski, 0), pc(r.ruido, 1), r.muestra] for r in cc.itertuples()], pequeno=True))
    A_(p("K-Means ofrece el mejor equilibrio y escala a todos los clientes. El jerárquico (Ward) se calculó sobre 8 000 clientes por su costo cuadrático y separa peor. Con DBSCAN se probaron 12 combinaciones: o descarta entre 31 % y 94 % de los puntos "
         "como ruido o deja al menos 94 % en un solo grupo; no sirve como segmentador, aunque podría detectar atípicos. K-Medoids no se implementó; la propuesta exige al menos dos técnicas y se compararon tres."))

    # ---------------------------------------------------------------- 14
    A_(h1(14, "Series temporales: pronóstico de ventas"))
    sc = pd.read_csv(O13 / "07_series_comparacion.csv")
    A_(p("Se pronosticaron las ventas diarias (pagos en R$) del 1 de enero de 2017 al 15 de agosto de 2018 (592 días); se descartó 2016 por su bajo volumen y las últimas dos semanas por estar incompletas. "
         "Los últimos 30 días fueron validación. Se compararon cuatro modelos de referencia, dos de regresión con rezagos (Ridge y Gradient Boosting) y, ejecutados en Google Colab, SARIMA(1,1,1)(1,0,1,7) y Prophet."))
    rows = [[r.modelo, f(r.MAE, 0), f(r.RMSE, 0), f(r.MAPE, 1) + " %"] for r in sc.itertuples()]
    rows += [["Prophet (Colab)", "11 345", "13 041", "24,6 %"], ["SARIMA(1,1,1)(1,0,1,7) (Colab)", "14 114", "15 407", "31,5 %"]]
    rows.sort(key=lambda r: float(r[3].replace(" ", "").replace(",", ".").replace("%", "")))
    A_(tabla("t_series", "Comparación de modelos de pronóstico (validación en los últimos 30 días).", ["Modelo", "MAE (R$)", "RMSE (R$)", "MAPE"], rows, pequeno=True))
    ph = pd.read_csv(O13 / "10_pronostico_horizontes.csv")
    A_(p("El mejor modelo fue Ridge con rezagos (MAPE 11,8 % frente a 20,4 % del modelo ingenuo). SARIMA y Prophet quedaron atrás; el ajuste de SARIMA no convergió por completo. "
         f"El pronóstico a 7, 30, 60 y 90 días se muestra en la {ref('t_horiz')}."))
    A_(tabla("t_horiz", "Pronóstico de ventas por horizonte (promedio diario real de los últimos 30 días: R$ 42 946).", ["Horizonte (días)", "Ventas pronosticadas (R$)", "Promedio diario (R$)"],
             [[int(r.horizonte_dias), f(r.ventas_pronosticadas_BRL, 0), f(r.promedio_diario, 0)] for r in ph.itertuples()], pequeno=True))
    A_(p("El pronóstico es casi plano: con menos de dos años y un solo noviembre, el modelo no aprende la estacionalidad anual ni eventos como Black Friday, y debe leerse como un nivel base."))
    A_(fig("f_pron", "s13_pronostico", "Serie histórica (media móvil de 7 días) y pronóstico a 90 días.", 86))

    # ---------------------------------------------------------------- 15
    A_(h1(15, "Minería de grafos"))
    A_(p("Cada nodo es una categoría y cada arista une dos categorías compradas por al menos 3 clientes en común, ponderada por ese número. El grafo tiene 45 nodos, 218 aristas, densidad 0,22 y es conexo. "
         "Se detectaron comunidades con modularidad voraz y se calcularon grado, intermediación y PageRank."))
    A_(fig("f_grafo", "s13_grafo", "Red de co-compra de categorías (aristas con al menos 8 clientes en común; color por comunidad).", 80))
    A_(tabla("t_comu", "Comunidades detectadas.", ["Comunidad", "Categorías", "Principales"], [
        ["0 (hogar)", "18", "bed_bath_table, furniture_decor, housewares, garden_tools, office_furniture"],
        ["1 (salud, tecnología y deporte)", "17", "health_beauty, sports_leisure, computers_accessories, watches_gifts, telephony, auto"],
        ["2 (bebé y juguetes)", "6", "toys, cool_stuff, baby, musical_instruments"],
        ["3 (otros)", "4", "fashion_bags_accessories, pet_shop, sin_categoria"]], pequeno=True))
    A_(p("La modularidad es de 0,17: la estructura de comunidades es débil, pero los cuatro grupos tienen lectura de negocio. Las categorías más centrales son bed_bath_table (PageRank 0,120), furniture_decor (0,111) y housewares (0,074); "
         "la relación más fuerte es bed_bath_table – furniture_decor, con 153 clientes en común. Es coherente con las reglas de asociación."))

    # ---------------------------------------------------------------- 16
    A_(h1(16, "Regresión: tiempo de entrega"))
    rv = pd.read_csv(O16 / "12_regresion_versiones.csv")
    A_(p("El objetivo numérico es el tiempo de entrega en días. Se excluyeron el retraso y las fechas de entrega para evitar fuga de información; la variable se winsorizó al percentil 99 y se usó partición 80/20. "
         "El modelo se construyó en tres versiones que añaden información: <b>v1</b> (52 variables: lo conocido al despachar), <b>v2</b> (54: se agrega la distancia vendedor–comprador y si están en el mismo estado) y "
         "<b>v3</b> (59: se agregan plazo prometido, carga de la plataforma e historial del vendedor)."))
    v3 = rv[rv.version == "v3"]
    A_(tabla("t_reg3", "Regresión del tiempo de entrega en la versión final (v3, conjunto de prueba).", ["Modelo", "MAE (días)", "RMSE (días)", "R²"],
             [[r.modelo, f(r.MAE, 2), f(r.RMSE, 2), f(r.R2, 3)] for r in v3.itertuples()], pequeno=True))
    best = {v: rv[(rv.version == v) & (rv.modelo == "XGBoost")].iloc[0] for v in ["v1", "v2", "v3"]}
    A_(p(f"El mejor modelo es XGBoost (R² {f(best['v3'].R2,3)}; error medio de {f(best['v3'].MAE,2)} días frente a 6,19 del baseline). La {ref('f_regv')} compara las tres versiones: el R² de XGBoost sube de {f(best['v1'].R2,3)} (v1) a {f(best['v2'].R2,3)} (v2) y a {f(best['v3'].R2,3)} (v3). "
         "El Segundo Informe reportaba R² 0,288 para Gradient Boosting en v1; al volver a ejecutar el script con las librerías actuales se obtuvo 0,294. La diferencia es de la tercera cifra y no cambia ninguna conclusión."))
    A_(fig("f_regv", "f03_regresion_versiones", "R² por modelo en las tres versiones del regresor.", 90))
    imp = pd.read_csv(O16 / "12_regresion_v3_importancia.csv").head(6)
    A_(p("En la versión final, las variables más influyentes por permutación son " + ", ".join(f"{r.variable.lower()} ({f(r.importancia_MAE,2)})" for r in imp.itertuples()) +
         ". En el Segundo Informe el flete y el estado dominaban; al incorporar plazo, carga y distancia, estos desplazan a las variables de producto, lo que confirma que el límite de v1 era la falta de información logística. "
         "El R² de 0,40 sigue siendo moderado: gran parte de la demora depende de eventos que no están en los datos."))

    # ---------------------------------------------------------------- 17
    A_(h1(17, "Clasificación: pedidos con riesgo de entrega tardía"))
    A_(h2("17.1 Planteamiento"))
    A_(p(f"El clasificador estima, con la información disponible al comprar, la probabilidad de que un pedido llegue después de la fecha prometida. La tasa base es de {pc(F['tasa_base'])} ({f(F['n_train'])} pedidos de entrenamiento y {f(F['n_test'])} de prueba, "
         "partición estratificada 80/20, semilla 42). Es un problema desbalanceado: un modelo que dijera siempre «a tiempo» tendría 92 % de exactitud sin servir de nada, por eso se evalúa con AUC-PR, AUC-ROC, F1, precisión, exhaustividad y Brier."))
    A_(h2("17.2 Comparación de modelos"))
    cm = pd.read_csv(O16 / "13_clasificacion_modelos.csv").sort_values("AUC_PR", ascending=False)
    A_(tabla("t_clasif", "Modelos de clasificación (conjunto de prueba; umbral elegido por F1 en validación).", ["Modelo", "AUC-ROC", "AUC-PR", "F1", "Precisión", "Exhaust."],
             [[r.modelo, f(r.AUC_ROC, 3), f(r.AUC_PR, 3), f(r.F1, 3), f(r.precision, 3), f(r.exhaustividad, 3)] for r in cm.itertuples()], pequeno=True))
    A_(p("Los modelos de árboles potenciados lideran; Random Forest, regresión logística, SVM y Naive Bayes quedan por detrás. Se eligió XGBoost porque permite calcular valores SHAP exactos (un Gradient Boosting de histogramas "
         "alcanzó métricas parecidas, pero su explicación no es aditiva en probabilidad). Se afinaron profundidad, peso mínimo de hoja y regularización con validación (AUC-PR 0,309 en la mejor combinación)."))
    A_(h2("17.3 Tratamiento del desbalance"))
    bl = pd.read_csv(O16 / "13_balanceo.csv")
    bx = bl[bl.modelo == "XGBoost"]
    A_(tabla("t_bal", "Técnicas de balanceo con XGBoost (prueba).", ["Técnica", "Pedidos de entrenamiento", "AUC-ROC", "AUC-PR", "F1"],
             [[r.tecnica, f(r.n_entrenamiento), f(r.AUC_ROC, 3), f(r.AUC_PR, 3), f(r.F1, 3)] for r in bx.itertuples()], pequeno=True))
    A_(p("Ninguna técnica de balanceo supera al entrenamiento sin balancear: el submuestreo pierde información y SMOTE y ADASYN, que crean pedidos sintéticos interpolando entre vecinos, <b>empeoran</b> el AUC-PR (0,221 y 0,224 frente a 0,303). "
         "Un riesgo estimado por árboles ya es una probabilidad útil sin balancear; el desbalance se maneja mejor eligiendo el umbral y las bandas de riesgo que alterando los datos."))
    A_(fig("f_modbal", "f06_modelos_balanceo", "Comparación de modelos y de técnicas de balanceo por AUC-PR.", 92))
    A_(h2("17.4 Modelo final y métricas"))
    ic = F["ic95"]
    A_(p(f"El modelo final es XGBoost con {F['hiperparametros']['n_estimators']} árboles, tasa de aprendizaje {f(F['hiperparametros']['learning_rate'],2)}, profundidad {F['hiperparametros']['max_depth']}, submuestreo 0,8 y 61 columnas. "
         f"En prueba obtiene AUC-ROC <b>{f(FF['AUC_ROC'],3)}</b> (IC 95 % {f(ic['AUC_ROC_ic95'][0],3)}–{f(ic['AUC_ROC_ic95'][1],3)}), AUC-PR <b>{f(FF['AUC_PR'],3)}</b> (IC {f(ic['AUC_PR_ic95'][0],3)}–{f(ic['AUC_PR_ic95'][1],3)}; azar = {f(F['tasa_base'],3)}), "
         f"F1 {f(FF['F1'],3)} (precisión {f(FF['precision'],3)}, exhaustividad {f(FF['exhaustividad'],3)}) y Brier {f(F['brier'],4)} (azar = 0,0745). El umbral se fijó en validación ({f(F['umbral_validacion'],3)}). Los intervalos se obtuvieron por bootstrap."))
    A_(fig("f_roc", "f04_roc_pr", "Curvas ROC y precisión–exhaustividad en el conjunto de prueba.", 90))
    A_(h2("17.5 Bandas de riesgo y calibración"))
    bn = pd.DataFrame(cla["bandas"])
    A_(p(f"Para uso operativo se definieron tres bandas con los percentiles 60 y 90 del entrenamiento (probabilidad {f(F['q60'],3)} y {f(F['q90'],3)}). En prueba, la banda <b>Bajo</b> tiene {pc(bn.pct_tarde[0])} de entregas tardías, la <b>Media</b> {pc(bn.pct_tarde[1])} y la <b>Alta</b> {pc(bn.pct_tarde[2])}; "
         f"esta última, con el 10 % de los pedidos, captura {pc(bn.pct_retrasos_capturados[2],0)} de los retrasos y tiene un <i>lift</i> de {f(bn.lift[2],2)}. La calibración es buena en la zona baja y media y subestima algo el riesgo en el decil más alto ({ref('f_cal')})."))
    A_(fig("f_cal", "f05_calibracion_bandas", "Calibración por deciles y tasa real de retraso por banda de riesgo.", 90))
    A_(h2("17.6 Validación en el tiempo"))
    A_(p(f"La partición aleatoria es optimista porque mezcla meses. Se evaluó también entrenando con pedidos de octubre de 2016 a febrero de 2018 y probando en abril–agosto de 2018: el AUC-ROC baja a <b>{f(tmp['AUC_ROC'],3)}</b> y el AUC-PR a {f(tmp['AUC_PR'],3)} "
         f"(tasa base de prueba {pc(tmp['tardias_test'])}). El modelo sobrestima el nivel de retraso (probabilidad media {f(tmp['prob_media'],3)} frente a 0,060 real), porque los picos de noviembre de 2017 y febrero–marzo de 2018 no se repiten. "
         f"El regresor, en el mismo esquema, tiene un MAE de {f(tmp['MAE_regresion'],2)} días. <b>La cifra honesta para anticipar el futuro es la temporal (~0,70), no la aleatoria (0,78).</b>"))
    A_(h2("17.7 Segundo clasificador: reseña baja"))
    sa = pd.read_csv(O16 / "19_satisfaccion.csv")
    A_(p(f"Se probó también predecir la reseña baja (1–2 estrellas; tasa base {pc(sa.tasa_base[0])}). Al comprar, con las mismas variables, el AUC-ROC es {f(sa.AUC_ROC[0],3)} (AUC-PR {f(sa.AUC_PR[0],3)}); "
         f"al entregar, agregando días de entrega y retraso, sube a {f(sa.AUC_ROC[1],3)} (AUC-PR {f(sa.AUC_PR[1],3)}). La sola variable «entrega tardía» da {f(0.6465,3)}. La satisfacción depende de cómo termine la entrega, que no se conoce al comprar; "
         "por eso el producto se centra en el retraso y usa el texto de la reseña como complemento."))

    # ---------------------------------------------------------------- 18
    A_(h1(18, "Explicabilidad de los modelos"))
    A_(p("La propuesta pide mostrar no solo qué predice el modelo sino por qué. Se implementaron tres enfoques complementarios, todos sobre el clasificador final."))
    A_(h2("18.1 Importancia global"))
    pm = pd.DataFrame(cla["perm"])
    sh = pd.DataFrame(cla["shap"])
    A_(p(f"La importancia por permutación (caída de AUC-PR al barajar una variable, agrupando las columnas One-Hot) ubica primero al plazo prometido ({f(pm.caida_AUC_PR[0],3)}), la carga relativa de la plataforma ({f(pm.caida_AUC_PR[1],3)}), "
         f"el estado del comprador ({f(pm.caida_AUC_PR[2],3)}), la distancia ({f(pm.caida_AUC_PR[3],3)}) y los días históricos del vendedor ({f(pm.caida_AUC_PR[4],3)}). "
         f"SHAP (TreeExplainer interventional, en probabilidad, con 100 filas de fondo) coincide en el orden general: |SHAP| medio de {f(sh.shap_abs_medio_pp[0],2)} pp para el plazo, {f(sh.shap_abs_medio_pp[1],2)} para el estado y {f(sh.shap_abs_medio_pp[2],2)} para la carga "
         f"({ref('f_imp')}). La aditividad se verificó: la suma de los aportes más la base reproduce la probabilidad con error máximo de {f(ex['adit_max']*1e7,1)}×10⁻⁷."))
    A_(fig("f_imp", "f07_importancias", "Importancia por permutación y por SHAP (primeras diez variables).", 94))
    A_(fig("f_nube", "f08_shap_nube", "SHAP por pedido: dirección y magnitud del efecto de cada variable.", 82))
    A_(h2("18.2 Explicación de casos y comparación con LIME"))
    ac = pd.DataFrame(cla["acuerdo"])
    A_(p(f"Se analizaron cinco casos representativos ({ref('f_casos')}): un acierto de riesgo alto, un acierto de riesgo bajo, uno medio, una falsa alarma y un caso difícil (llegó tarde con riesgo bajo). "
         "En el primero, la carga relativa de la plataforma aporta +14 pp, mucho más que cualquier otro factor: el pedido se hizo en un período saturado. "
         "Cada caso se explicó con SHAP y con LIME (3 000 muestras). La correlación de Spearman entre ambos rankings fue de " + ", ".join(f(x, 2) for x in ac.corr_shap_lime) +
         ". El acuerdo es moderado y en el caso medio incluso negativo: LIME ajusta un modelo lineal local y puede discrepar cuando el modelo tiene interacciones. Por eso el producto usa SHAP, que es exacto y aditivo, y se reporta LIME como contraste y no como verdad."))
    A_(fig("f_casos", "f09_casos", "Factores principales de tres de los casos analizados (aporte SHAP en puntos porcentuales).", 96))
    A_(h2("18.3 Visualización de decisiones"))
    A_(p("En el panel web, el simulador calcula en el navegador la probabilidad de un pedido descrito por el usuario y muestra el aporte de cada factor (barras rojas suben el riesgo, verdes lo bajan) con una estimación de Shapley, "
         "de modo que la decisión del modelo es visible y no una caja negra (sección 21)."))

    # ---------------------------------------------------------------- 19
    A_(h1(19, "Minería de textos"))
    tm = txt["resumen"]
    A_(p(f"El 42 % de los pedidos tiene comentario; tras la limpieza quedan {f(tm['n_resenas'] if 'n_resenas' in tm else 39661)} reseñas en portugués. El pipeline sigue los pasos pedidos: limpieza (minúsculas, URL y números), normalización de acentos, "
         "tokenización, eliminación de <i>stopwords</i> (lista <i>stopwordsiso</i>, conservando las negaciones «não», «nunca», «nem»), vectorización TF-IDF con unigramas y bigramas (3 000 términos, frecuencia mínima 8, escala sublineal) y tres tareas: sentimiento, aspectos y temas."))
    sm = pd.read_csv(O16 / "15_sentimiento_modelos.csv")
    A_(h2("19.1 Sentimiento"))
    A_(p(f"Se etiquetó como negativo 1–2 estrellas y como positivo 4–5 (se excluye 3). Los tres clasificadores superan con holgura el 91 % de exactitud ({ref('t_sent')}); se eligió la regresión logística por su interpretabilidad y porque el panel puede evaluarla en el navegador "
         "con los mismos coeficientes. La probabilidad media de sentimiento negativo baja de 0,895 con 1 estrella a 0,082 con 5, es decir, el texto y el puntaje cuentan la misma historia."))
    A_(tabla("t_sent", "Clasificación de sentimiento (prueba).", ["Modelo", "Exactitud", "F1 negativa", "F1 macro", "AUC-ROC"],
             [[r.modelo, f(r.exactitud, 3), f(r.F1_negativa, 3), f(r.F1_macro, 3), f(r.AUC_ROC, 3)] for r in sm.itertuples()], pequeno=True))
    A_(h2("19.2 Aspectos y temas"))
    A_(p("Seis diccionarios de expresiones regulares (entrega, calidad, vendedor, precio, empaque y devolución) permiten medir de qué hablan los clientes. La entrega es el aspecto más mencionado (52,9 %), "
         "seguido por la calidad (26,8 %); <b>devolución y reembolso</b> se menciona poco (3,9 %) pero con 75 % de comentarios negativos. Una factorización NMF de 7 temas confirma el patrón: el tema «não recebi» (no recibí) concentra 55 % de comentarios negativos "
         f"({ref('f_texto')})."))
    A_(fig("f_texto", "f10_texto", "Aspectos mencionados en los comentarios y probabilidad de sentimiento negativo según estrellas.", 94))
    A_(h2("19.3 Relación con el riesgo logístico"))
    tv = pd.read_csv(O16 / "15_texto_vs_riesgo.csv")
    A_(p("Los pedidos de la banda de riesgo alto reciben comentarios negativos con mucha más frecuencia: " + ", ".join(f"{r.banda} {pc(r.pct_negativas,0)}" for r in tv.itertuples()) +
         ". Además, el 54 % de los pedidos tardíos termina en reseña baja frente al 9 % de los puntuales. Es el vínculo que cierra el proyecto: el riesgo estimado al comprar anticipa la insatisfacción que luego aparece en el texto."))
    A_(p("<b>Limitación:</b> las traducciones al español de términos en el panel (259 entradas) son un glosario para lectura; el modelo trabaja en portugués."))

    # ---------------------------------------------------------------- 20
    A_(h1(20, "Monitoreo y mantenimiento"))
    A_(p("La propuesta pide una propuesta de operación del modelo con seguimiento de desempeño, deriva de datos, reentrenamiento, versionado, registro y auditoría. No se limita a describirla: se <b>simuló</b> con los datos reales mes a mes, como si el sistema hubiera estado en producción entre noviembre de 2017 y agosto de 2018."))
    A_(h2("20.1 Diseño de la simulación"))
    A_(p(f"El modelo de referencia (v1) se entrena con enero–septiembre de 2017 ({f(r16['n_ref'])} pedidos); su AUC-ROC de referencia es {f(r16['AUC_REF'],3)} y el MAE del regresor {f(r16['MAE_REF'],2)} días. Cada mes se mide el desempeño con los pedidos entregados ese mes, dejando un mes de maduración para que las etiquetas existan. "
         "Se compararon cuatro políticas: <b>A</b> congelado; <b>B</b> reentrenamiento mensual con ventana de 6 meses; <b>C</b> mensual con ventana de 2 meses; <b>D</b> reentrenar solo cuando salta una alerta."))
    A_(h2("20.2 Alertas"))
    A_(p("Se definieron cuatro alertas: caída del AUC mayor a 0,05 respecto a la referencia, calibración (|predicho/real − 1| > 50 %), deriva PSI > 0,25 (índice de estabilidad de la población, 10 percentiles; > 0,10 advertencia) y aumento del MAE mayor a 20 %."))
    A_(fig("f_psi", "f11_psi", "PSI mensual de cada variable frente a la referencia (enero–octubre de 2017).", 92))
    A_(p("El PSI supera 0,25 en los diez meses, sobre todo por la carga relativa de la plataforma y el historial de retrasos de los vendedores, que son variables que por construcción cambian con la dinámica del negocio (más pedidos, más retrasos). "
         "Es una señal legítima de deriva, no un error de medición."))
    A_(h2("20.3 Resultados de las políticas"))
    po = pd.read_csv(O16 / "16_politicas_resumen.csv")
    A_(tabla("t_pol", "Desempeño promedio de las políticas en los 10 meses simulados.", ["Política", "AUC-ROC", "AUC-PR", "Brier", "Meses con alerta", "Reentrenamientos"],
             [[r.politica, f(r.AUC_ROC, 3), f(r.AUC_PR, 3), f(r.Brier, 3), r.meses_alerta, r.reentrenamientos] for r in po.itertuples()], pequeno=True))
    A_(fig("f_mon", "f12_monitoreo", "AUC-ROC mensual del clasificador por política y MAE mensual del regresor.", 96))
    A_(p("<b>Hallazgo.</b> Reentrenar cada mes no superó claramente al modelo congelado (AUC-ROC medio 0,641 con A, 0,630 con B, 0,642 con C, 0,627 con D). Los choques (noviembre de 2017 con 14,3 % de retrasos, febrero–marzo de 2018 con 16–21 % y la huelga de mayo de 2018) "
         "no se aprenden del pasado reciente: un modelo reentrenado justo después de un choque aprende un mundo que ya cambió. La recomendación operativa no es «reentrenar siempre» sino monitorear, alertar y reentrenar con criterio (política D, que usa 7 reentrenamientos en vez de 10), "
         "y agregar variables que anticipen los choques (calendario, huelgas, campañas). Además, en julio–agosto de 2018 hay censura a la derecha: los pedidos más lentos aún no se habían entregado al cortar los datos, por lo que el AUC de esos meses es menos fiable."))
    A_(h2("20.4 Versionado, registro y auditoría"))
    A_(p(f"Cada modelo entrenado en la simulación se registra en <i>models/registro/versiones.json</i> con identificador, política, ventana de entrenamiento, número de pedidos y un <b>hash SHA-256</b> (16 caracteres) del archivo del modelo, de modo que cualquier predicción puede atribuirse a una versión exacta; "
         f"hay {r16['n_versiones']} versiones. Cada evento (referencia, medición mensual, alerta, reentrenamiento) se anota en un registro de auditoría en formato JSON por línea. El panel muestra ambos y la API los expone (<i>/model/versions</i> y <i>/audit</i>)."))
    A_(p("El <b>pipeline de reentrenamiento</b> propuesto es: (1) calcular métricas y PSI cada mes; (2) si hay alerta, entrenar un candidato con la ventana definida; (3) compararlo con el modelo vigente sobre el mes más reciente; (4) si mejora, registrar versión y hash y publicarlo; (5) si no, conservar el vigente y dejar constancia en el registro."))

    # ---------------------------------------------------------------- 21
    A_(h1(21, "Aplicación web"))
    A_(h2("21.1 Arquitectura"))
    A_(p(f"El producto es un panel interactivo y una API. La decisión de diseño central es que <b>el modelo corre en el navegador</b>: se exportan los árboles de XGBoost a JSON y se evalúan en JavaScript, de modo que el panel funciona sin servidor, es gratuito de publicar y no envía datos de nadie. "
         f"Una API Flask opcional ofrece los mismos resultados por HTTP ({ref('f_arq')})."))
    A_(fig("f_arq", "f15_arquitectura", "Arquitectura de DataSmart: del dato al panel, la API y el despliegue.", 94))
    A_(h2("21.2 Panel de diez secciones"))
    A_(tabla("t_secc", "Secciones del panel y la pregunta que responde cada una.", ["Sección", "Qué permite"], [
        ["Inicio", "Cifras clave y seis hallazgos del proyecto en lenguaje cotidiano"],
        ["Panorama", "Ingreso y pedidos por mes, categorías, puntaje de reseñas, y cómo el tiempo y la distancia se relacionan con el retraso"],
        ["Mapa", "Mapa de Brasil por estado de destino (toca un estado para ver sus números), ranking y malla geográfica de pedidos"],
        ["Clientes", "Segmentos, reglas de asociación y red de categorías"],
        ["Pronóstico", "Ventas diarias y pronóstico a 7, 30, 60 y 90 días con comparación de modelos"],
        ["Simulador", "Probabilidad de retraso de un pedido descrito por el usuario, con etiqueta de envío y explicación"],
        ["Modelo", "Métricas, curvas, bandas, balanceo, codificación e ingeniería de variables"],
        ["Explicación", "Importancia, nube SHAP y casos con SHAP frente a LIME"],
        ["Reseñas", "Analizador de texto en vivo, aspectos, temas y términos"],
        ["Monitoreo", "Simulación mensual, PSI, políticas, registro de versiones y auditoría"]], pequeno=True))
    A_(fig("f_web_inicio", "web_inicio", "Sección Inicio del panel (versión de escritorio).", 92))
    A_(fig("f_web_sim", "web_simulador", "Simulador: etiqueta de envío con la probabilidad y explicación de los factores.", 92))
    A_(fig("f_web_mapa", "web_mapa", "Mapa de Brasil por estado.", 92))
    A_(fig("f_web_expl", "web_explicacion", "Sección Explicación.", 92))
    A_(fig("f_web_res", "web_resenas", "Sección Reseñas con analizador de texto.", 92))
    A_(fig("f_web_mon", "web_monitoreo", "Sección Monitoreo.", 92))
    A_(h2("21.3 Experiencia de uso"))
    A_(p("El panel se diseñó para que alguien sin formación en minería de datos lo entienda. Tiene un modo <b>Guiado</b> (explicaciones en lenguaje cotidiano y qué hacer con el resultado) y un modo <b>Experto</b> (métricas, hiperparámetros y detalles técnicos), "
         "tema claro y oscuro, y diseño adaptable a teléfono. El elemento memorable es la <b>etiqueta de envío</b> del simulador: el resultado se presenta como una etiqueta de paquete con ruta, distancia, banda de riesgo y código de barras. "
         "El mapa de Brasil usa el trazado de <i>@svg-maps/brazil</i> (licencia CC BY 4.0). Los gráficos están hechos con D3 v7 sin proceso de compilación."))
    A_(fig("f_web_mov", "web_movil_simulador", "Simulador en un teléfono (390 px de ancho).", 36))
    A_(h2("21.4 API"))
    A_(p("La API (Flask) expone: <i>GET /api/health</i>; <i>POST /api/predict</i> (probabilidad, banda y aportes de factores de un pedido); <i>POST /api/text</i> (sentimiento y aspectos de un comentario); <i>GET /api/monitoring</i>; <i>GET /api/model/versions</i> y <i>GET /api/audit</i>. "
         "También sirve el sitio estático. Para la predicción usa <i>pred_contribs</i> de XGBoost, que entrega los aportes exactos."))
    A_(h2("21.5 Pruebas"))
    A_(p("Hay 23 pruebas automáticas con pytest: comprobaciones de datos (conteos y ausencia de duplicados), variables, modelo, API, monitoreo y, de forma crítica, la <b>paridad entre Python y JavaScript</b>. "
         "Como el modelo se evalúa en dos lenguajes, se verificó que coinciden: sobre 300 pedidos de prueba la diferencia máxima de probabilidad es de 3,3×10⁻⁷ y la del analizador de texto de 2×10⁻⁶. "
         "Lograrlo exigió redondear a 32 bits (<i>Math.fround</i>) los valores y umbrales, porque XGBoost compara en precisión simple; sin ese cuidado la diferencia llegaba a 0,11. "
         "Además, una prueba de humo con navegador abre las diez secciones en escritorio y teléfono y falla ante cualquier error de consola; no se registraron errores."))
    A_(h2("21.6 Despliegue gratuito"))
    A_(p("Se prepararon cuatro vías, descritas paso a paso en el Anexo E y en <i>docs/DESPLIEGUE.md</i>: GitHub Pages (flujo automático), Netlify Drop (arrastrar la carpeta <i>dist</i>), Render (API; el plan gratuito se duerme tras 15 minutos de inactividad) y Docker. "
         "Además se genera un único archivo <i>datasmart.html</i> (1,95 MB) que funciona incluso abriéndolo con doble clic."))

    # ---------------------------------------------------------------- 22
    A_(h1(22, "Evaluación comparativa"))
    A_(tabla("t_comp", "Resumen comparativo de las técnicas.", ["Técnica", "Mejor resultado", "Métrica", "Lectura de negocio"], [
        ["Asociación", "FP-Growth y ECLAT (igual resultado que Apriori, más rápidos)", "105 reglas; lift máx. 3,1", "Ofertas cruzadas entre categorías del hogar y del bebé"],
        ["Clustering", "K-Means, k = 4", "Silueta 0,24", "Segmento de insatisfechos con entrega lenta: 15,5 % de clientes, reseña 1,66"],
        ["Series temporales", "Ridge con rezagos", "MAPE 11,8 %", "Nivel base cercano a R$ 44 mil por día"],
        ["Grafos", "Modularidad voraz", "Modularidad 0,17", "El hogar es el núcleo de las compras cruzadas"],
        ["Regresión", "XGBoost (v3)", "R² 0,405; MAE 4,44 días", "Plazo, carga, distancia y vendedor explican la demora"],
        ["Clasificación", "XGBoost", f"AUC-ROC {f(FF['AUC_ROC'],3)}; AUC-PR {f(FF['AUC_PR'],3)}", "Banda alta: 33 % de retrasos frente a 3 % en la baja"],
        ["Textos", "Regresión logística + TF-IDF", "AUC-ROC 0,973", "La entrega domina lo que dicen los clientes"],
        ["Monitoreo", "Congelado + alertas", "AUC temporal ~0,64–0,70", "Reentrenar no basta; hay que anticipar los choques"]], pequeno=True))
    A_(p("El hallazgo transversal es que la logística conecta los resultados. Estas son asociaciones observadas y no prueban causalidad."))

    # ---------------------------------------------------------------- 23
    A_(h1(23, "Limitaciones"))
    A_(ul(["<b>Evaluación aleatoria frente a temporal.</b> El AUC-ROC es 0,78 en partición aleatoria y 0,70 al probar en meses posteriores; la segunda es la expectativa realista.",
           "<b>Información al comprar.</b> <i>dias_aprobacion</i> se conoce al aprobarse el pago, no al comprar; el resto de variables sí está disponible al comprar.",
           "<b>Historia corta.</b> Menos de dos años de ventas; los modelos de series no aprenden la estacionalidad anual y se valida con una sola ventana de 30 días.",
           "<b>Choques no aprendibles.</b> Noviembre de 2017, febrero–marzo de 2018 y la huelga de mayo de 2018 no se predicen con el pasado reciente; el reentrenamiento no los resuelve.",
           "<b>Censura a la derecha.</b> En julio–agosto de 2018 faltan pedidos lentos aún sin entregar, lo que altera las métricas de esos meses.",
           "<b>Poca recompra y pocas canastas.</b> 97 % de clientes con una compra; solo 2,4 % con dos o más categorías; reglas exploratorias y CLV no estimable.",
           "<b>Explicaciones.</b> LIME y SHAP concuerdan solo moderadamente (Spearman −0,13 a 0,70); se usa SHAP como explicación principal.",
           "<b>Segmentos interpretados.</b> Los nombres y k = 4 son decisión del equipo.",
           "<b>Sin marketing ni navegación.</b> El conjunto no incluye campañas ni visitas.",
           "<b>Alcance.</b> Marketplace brasileño 2016–2018; no generalizar sin nuevos datos.",
           "<b>Modelos no implementados.</b> K-Medoids, LSTM y ARIMAX no se implementaron; la propuesta pide al menos dos técnicas de clustering y alguno de los modelos de series, que sí se cubrieron."]))

    # ---------------------------------------------------------------- 24
    A_(h1(24, "Conclusiones y trabajo futuro"))
    A_(h2("Conclusiones"))
    A_(ul([f"Se construyó un dataset reproducible de 96 469 pedidos con 51 variables, con cada problema de calidad documentado y tratado.",
           "Los tres algoritmos de asociación coinciden (115 itemsets, 105 reglas); la asociación más fuerte es bed_bath_table con home_confort (lift 3,1), apoyada en pocos clientes.",
           "K-Means (k = 4) identificó un segmento de insatisfechos con entrega lenta (15,5 % de los clientes, reseña 1,66) y un segmento de alto valor con el 67 % del ingreso.",
           "Para ventas diarias, Ridge con rezagos obtuvo el menor error (MAPE 11,8 %), pero la historia corta limita el pronóstico a un nivel base.",
           "La regresión del tiempo de entrega mejoró de R² 0,29 a 0,41 al agregar distancia, plazo prometido, carga de la plataforma e historial del vendedor.",
           f"El clasificador de entrega tardía alcanza AUC-ROC {f(FF['AUC_ROC'],3)} con partición aleatoria y {f(tmp['AUC_ROC'],3)} en validación temporal; la banda alta concentra 33 % de retrasos frente a 3 % en la baja. SMOTE y ADASYN empeoraron el resultado.",
           "SHAP muestra que plazo prometido, destino y carga de la plataforma son los factores principales; LIME concuerda solo parcialmente.",
           "La minería de textos confirma que la entrega domina las opiniones (53 % de los comentarios) y que los pedidos de riesgo alto reciben más comentarios negativos (39 % frente a 20 %).",
           "La simulación de monitoreo mostró deriva persistente y que el reentrenamiento mensual no supera al modelo congelado; se recomienda monitorear y reentrenar con criterio.",
           "El producto es un panel web con el modelo en el navegador, API, 23 pruebas y despliegue gratuito."]))
    A_(h2("Trabajo futuro"))
    A_(ul(["Incorporar calendario (feriados, Black Friday), huelgas y campañas para anticipar los choques de demanda.",
           "Obtener más años de datos para modelar estacionalidad anual (SARIMAX, Prophet con regresores, LSTM).",
           "Probar K-Medoids y modelos de supervivencia para el tiempo de entrega.",
           "Calibrar el modelo por estado y evaluar un modelo por región.",
           "Conectar el panel a datos en vivo y automatizar el pipeline de reentrenamiento descrito en la sección 20."]))

    # ---------------------------------------------------------------- 25
    A_(h1(25, "Referencias"))
    refs = ["Olist. Brazilian E-Commerce Public Dataset by Olist. Kaggle. https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce",
            "Chapman, P. et al. CRISP-DM 1.0: Step-by-step data mining guide.",
            "Agrawal, R., y Srikant, R. (1994). Fast algorithms for mining association rules. VLDB.",
            "Han, J., Pei, J., y Yin, Y. (2000). Mining frequent patterns without candidate generation. ACM SIGMOD Record, 29(2).",
            "Zaki, M. J. (2000). Scalable algorithms for association mining. IEEE TKDE, 12(3).",
            "Rousseeuw, P. J. (1987). Silhouettes: a graphical aid to the interpretation and validation of cluster analysis. J. Comput. Appl. Math., 20.",
            "Ester, M., Kriegel, H.-P., Sander, J., y Xu, X. (1996). A density-based algorithm for discovering clusters in large spatial databases with noise. KDD.",
            "Hyndman, R. J., y Athanasopoulos, G. (2021). Forecasting: Principles and Practice (3.ª ed.). OTexts.",
            "Taylor, S. J., y Letham, B. (2018). Forecasting at scale. The American Statistician, 72(1).",
            "Clauset, A., Newman, M. E. J., y Moore, C. (2004). Finding community structure in very large networks. Physical Review E, 70.",
            "Chen, T., y Guestrin, C. (2016). XGBoost: a scalable tree boosting system. KDD.",
            "Lundberg, S. M., y Lee, S.-I. (2017). A unified approach to interpreting model predictions. NeurIPS.",
            "Ribeiro, M. T., Singh, S., y Guestrin, C. (2016). «Why should I trust you?»: explaining the predictions of any classifier. KDD.",
            "Chawla, N. V. et al. (2002). SMOTE: synthetic minority over-sampling technique. JAIR, 16.",
            "He, H., Bai, Y., Garcia, E. A., y Li, S. (2008). ADASYN: adaptive synthetic sampling approach for imbalanced learning. IJCNN.",
            "Lee, D. D., y Seung, H. S. (1999). Learning the parts of objects by non-negative matrix factorization. Nature, 401.",
            "Siddiqi, N. (2006). Credit Risk Scorecards. Wiley (índice de estabilidad de la población, PSI).",
            "Pedregosa, F. et al. (2011). Scikit-learn: machine learning in Python. JMLR, 12.",
            "Hagberg, A. A., Schult, D. A., y Swart, P. J. (2008). Exploring network structure, dynamics, and function using NetworkX. SciPy.",
            "Bostock, M., Ogievetsky, V., y Heer, J. (2011). D³: data-driven documents. IEEE TVCG, 17(12)."]
    A_("<ul class='refs'>" + "".join(f"<li>{esc(r)}</li>" for r in refs) + "</ul>")

    # ---------------------------------------------------------------- Anexos
    A_(h1("A", "Reproducibilidad"))
    A_(p("Los resultados provienen de scripts incluidos en la carpeta <i>analysis</i>. Cada uno guarda sus resultados en CSV, JSON o figuras. Se ejecutan en el orden indicado."))
    A_(tabla("t_scripts", "Scripts del proyecto.", ["Script", "Contenido"], [
        ["00_inventario_olist.py, 01_eda_olist.py", "Inventario de tablas y análisis exploratorio (entregable 1)"],
        ["02_preparacion.py", "Limpieza, integración, variables derivadas y valores atípicos"],
        ["03_asociacion.py", "Apriori, FP-Growth y ECLAT; reglas y comparación"],
        ["04_clustering.py", "RFM, ABC, K-Means, jerárquico y DBSCAN"],
        ["05_series_temporales.py, 05b_sarima_prophet_COLAB.py", "Modelos de referencia, Ridge y GB con rezagos; SARIMA y Prophet (Colab)"],
        ["06_grafos.py", "Grafo de co-compra, comunidades y centralidad"],
        ["07_regresion.py", "Siete modelos de regresión e importancia (v1)"],
        ["08_figuras.py, 09_decks.py", "Figuras y presentaciones de entregables anteriores"],
        ["10_geo_distancia.py", "Depuración de geolocalización y distancia vendedor–comprador"],
        ["11_variables_causales.py", "Plazo prometido, carga de la plataforma e historial del vendedor"],
        ["12_regresion_v3.py", "Regresión en tres versiones (v1, v2, v3)"],
        ["13_clasificacion.py", "Clasificador de entrega tardía, balanceo, bandas y calibración"],
        ["14_explicabilidad.py", "Permutación, SHAP y LIME; casos"],
        ["15_texto.py", "Minería de textos: sentimiento, aspectos y temas"],
        ["16_monitoreo.py", "Simulación de monitoreo, PSI, versionado y auditoría"],
        ["17_ingenieria_extra.py", "VIF, correlación, PCA, selección, LDA y QDA"],
        ["18_export_web.py", "Exportación de modelos y resultados al panel (JSON)"],
        ["19_preproceso_y_satisfaccion.py", "Codificación y escalamiento; clasificador de reseña baja"],
        ["20_figuras_informe.py, 21_capturas_web.py", "Figuras y capturas de este informe"],
        ["docs/construir_informe.py", "Construcción de este informe en PDF"],
        ["tools/construir_sitio.py", "Construcción de dist/ y del archivo único datasmart.html"]], pequeno=True))
    A_(p("Orden recomendado: instalar <i>requirements.txt</i>, colocar los CSV de Olist en <i>data/raw</i> y ejecutar 02, 03, 04, 05, 06, 07, 10, 11, 12, 13, 14, 15, 16, 17, 19 y 18; luego <i>python tools/construir_sitio.py</i> y <i>pytest</i>. La semilla aleatoria es 42 en todos los modelos."))
    A_(h1("B", "Diccionario del dataset final"))
    cols = pd.read_csv(O16 / "11_columnas_dataset_final.csv").variable.tolist()
    A_(p(f"El dataset final tiene {len(cols)} columnas: " + ", ".join(f"<code>{c}</code>" for c in cols) + "."))
    A_(p("Variables nuevas de la cuarta etapa: <code>distancia_km</code> (haversine entre prefijos postales del vendedor y del comprador), <code>mismo_estado</code> (1 si coinciden), <code>dias_estimados</code> (plazo prometido), "
         "<code>carga_rel</code> (pedidos de los últimos 7 días sobre el promedio semanal de las 8 semanas previas), <code>vend_hist_dias</code>, <code>vend_hist_tardio</code> y <code>vend_hist_n</code> (historial del vendedor solo con pedidos anteriores)."))
    A_(h1("C", "API"))
    A_(tabla("t_api", "Puntos de acceso de la API.", ["Método y ruta", "Descripción"], [
        ["GET /api/health", "Estado del servicio"],
        ["POST /api/predict", "Probabilidad de retraso, banda y aportes de factores para un pedido"],
        ["POST /api/text", "Probabilidad de sentimiento negativo y aspectos de un comentario"],
        ["GET /api/monitoring", "Resumen de monitoreo"],
        ["GET /api/model/versions", "Registro de versiones con hash"],
        ["GET /api/audit", "Registro de auditoría"]], pequeno=True))
    A_(h1("D", "Pruebas"))
    A_(p("Archivo <i>tests/test_datasmart.py</i> (23 pruebas) y pruebas de paridad en <i>web/tests</i> (<i>paridad_modelo.js</i>, <i>paridad_texto.js</i>) y <i>humo_navegador.py</i>. Ejecución: <code>pytest -q</code>."))
    A_(h1("E", "Guía de despliegue"))
    A_(p("Los pasos detallados (GitHub Pages, Netlify Drop, Render y Docker, con lista de comprobación) están en <i>docs/DESPLIEGUE.md</i>. Resumen de la vía más sencilla, GitHub Pages: (1) crear un repositorio en GitHub; (2) subir el contenido del proyecto; "
         "(3) en <i>Settings → Pages</i>, elegir <i>GitHub Actions</i> como fuente; (4) el flujo <i>.github/workflows/pages.yml</i> publica la carpeta <i>dist</i> en cada <i>push</i> y da la dirección pública."))
    A_(h1("F", "Matriz de cumplimiento de la propuesta"))
    A_(tabla("t_matriz", "Requisitos de la propuesta y dónde se cumplen.", ["Requisito de la propuesta", "Cumplimiento", "Dónde"], [
        ["Problema, objetivos, preguntas, KPIs, dataset, diccionario, EDA, calidad, metodología", "Cumplido", "Secciones 2–9"],
        ["Preparación: valores faltantes, duplicados, inconsistencias", "Cumplido", "10, Tabla de calidad"],
        ["Outliers: IQR y Z-score", "Cumplido", "10.1"],
        ["Categóricas: One-Hot y Label Encoding", "Cumplido (comparados)", "10.3"],
        ["Escalamiento: MinMaxScaler y StandardScaler", "Cumplido (comparados)", "10.3"],
        ["Balanceo: undersampling, oversampling, SMOTE, ADASYN", "Cumplido (SMOTE y ADASYN empeoran)", "17.3"],
        ["Ingeniería: nuevas variables, integración, formateo", "Cumplido", "10.2, 11.1–11.3"],
        ["Ingeniería: colinealidad, selección, reducción (PCA, LDA, QDA)", "Cumplido (resultado negativo documentado)", "11.4–11.6"],
        ["Asociación: Apriori, FP-Growth, ECLAT; soporte, confianza, lift", "Cumplido", "12"],
        ["Clustering: al menos dos técnicas; RFM, ABC", "Cumplido (K-Means, jerárquico, DBSCAN; RFM y ABC)", "13"],
        ["Series temporales: alguno de ARIMA/SARIMA/Prophet/LSTM", "Cumplido (SARIMA, Prophet, Ridge, Holt-Winters, GB)", "14"],
        ["Minería de grafos: categorías, comunidades, patrones", "Cumplido", "15"],
        ["Regresión: lineal, Ridge, Lasso, Elastic Net, RF, GB, XGBoost", "Cumplido", "16"],
        ["Clasificación: RF, GB, XGBoost, SVM, Naive Bayes; precisión, recall, F1", "Cumplido", "17"],
        ["Minería de textos: pipeline, temas, términos, opiniones", "Cumplido", "19"],
        ["Explicabilidad: SHAP, LIME, importancia, visualización de decisiones", "Cumplido", "18, 21"],
        ["Monitoreo: desempeño, deriva, reentrenamiento, versionado, registro, auditoría", "Cumplido (simulado con datos reales)", "20"],
        ["Producto final: aplicación web con backend y frontend, dashboard", "Cumplido", "21"],
        ["Documentación, presentación y sustentación", "Cumplido (informe, presentación, guion y preguntas)", "Este informe y archivos adjuntos"],
        ["Modelos opcionales: K-Medoids, LSTM, ARIMAX", "No implementados (la propuesta exige solo algunos)", "23"]], pequeno=True))
    return "\n".join(o)


CSS = """
@page { size: A4; margin: 22mm 20mm 22mm 20mm; }
body { font-family: 'Inter', sans-serif; font-size: 9.6pt; line-height: 1.5; color: #1f2937; }
h1 { font-family: 'Caladea', serif; font-size: 17pt; color: #0f2544; border-bottom: 1.5px solid #0f2544; padding-bottom: 3pt; margin: 20pt 0 8pt; page-break-after: avoid; }
h1.nuevo { page-break-before: always; margin-top: 0; }
h2 { font-family: 'Caladea', serif; font-size: 12.5pt; color: #0f766e; margin: 13pt 0 4pt; page-break-after: avoid; }
p { margin: 0 0 6pt; text-align: justify; hyphens: auto; }
ul { margin: 2pt 0 7pt 15pt; padding: 0; } li { margin-bottom: 2.5pt; text-align: justify; }
ul.refs li { text-align: left; font-size: 9pt; }
code { font-family: 'DejaVu Sans Mono', monospace; font-size: 8.3pt; background: #f3f4f6; padding: 0 2pt; }
figure { margin: 8pt auto; text-align: center; page-break-inside: avoid; } figure img { width: 100%; border: 1px solid #e5e7eb; }
figcaption, .cap { font-size: 8.6pt; color: #4b5563; margin-top: 3pt; font-style: italic; text-align: center; }
.tabla { margin: 8pt 0; page-break-inside: avoid; } .tabla .cap { text-align: left; font-style: normal; font-weight: 600; margin: 0 0 3pt; color: #1f2937; }
table { border-collapse: collapse; width: 100%; font-size: 8.8pt; }
.peq table { font-size: 8.2pt; }
th { background: #0f2544; color: #fff; text-align: left; padding: 3pt 5pt; font-weight: 600; }
td { padding: 2.6pt 5pt; border-bottom: 0.5pt solid #d1d5db; vertical-align: top; } td.n { text-align: right; white-space: nowrap; }
tr:nth-child(even) td { background: #f8fafc; }
.nota { border-left: 3px solid #d97706; background: #fffbeb; padding: 5pt 8pt; margin: 6pt 0; }
.portada { text-align: center; page-break-after: always; padding-top: 2mm; font-family: 'Caladea', serif; color: #111827; }
.portada .u { font-weight: 700; font-size: 17pt; letter-spacing: .4pt; color: #0f2544; }
.portada .f1551 { font-size: 9.5pt; font-style: italic; color: #4b5563; margin: 2pt 0 7mm; }
.portada .fac { font-weight: 700; font-size: 11.5pt; color: #1f2937; line-height: 1.45; }
.portada .escudo { width: 40mm; margin: 9mm auto 9mm; display: block; }
.portada .caja { border: 1.6pt solid #0f2544; border-radius: 3pt; padding: 6mm 8mm; margin: 0 12mm 7mm; }
.portada .t { font-weight: 700; font-size: 19pt; color: #0f2544; letter-spacing: .3pt; }
.portada .st { font-family: 'Inter', sans-serif; font-size: 10pt; color: #0f766e; margin-top: 3pt; }
.portada .curso { font-family: 'Inter', sans-serif; font-size: 10.5pt; font-weight: 600; color: #374151; margin-bottom: 3mm; }
.portada .proy { font-style: italic; font-size: 13pt; margin: 0 14mm 9mm; line-height: 1.35; }
.portada .g { font-weight: 700; font-size: 15pt; margin-bottom: 2mm; color: #0f2544; }
.portada .e { font-size: 11.5pt; line-height: 1.6; }
.portada .lugar { font-size: 11.5pt; margin-top: 10mm; }
.indice { page-break-after: always; } .indice h1 { margin-top: 0; }
.indice .fila { display: flex; font-size: 10pt; margin: 3.2pt 0; } .indice .fila .p { flex: 1; border-bottom: 1px dotted #9ca3af; margin: 0 4pt 3pt; }
"""


def portada():
    logo = (R / "docs" / "figuras" / "unmsm_transp.png").as_uri()
    return f"""<div class="portada">
<div class="u">UNIVERSIDAD NACIONAL MAYOR DE SAN MARCOS</div><div class="f1551">Universidad del Perú, Decana de América · Fundada en 1551</div>
<div class="fac">FACULTAD DE INGENIERÍA DE SISTEMAS E INFORMÁTICA</div><div class="fac">ESCUELA PROFESIONAL DE INGENIERÍA DE SOFTWARE</div>
<img class="escudo" src="{logo}">
<div class="caja"><div class="t">INFORME FINAL DEL PROYECTO</div><div class="st">Entregable 4 y documentación integral del proyecto (entregables 1 a 4)</div></div>
<div class="curso">Curso: Minería de Datos</div>
<div class="proy">DataSmart: plataforma inteligente para el análisis, segmentación y predicción de clientes — Olist</div>
<div class="g">Grupo 4</div><div class="e"><i>Estudiantes:</i><br>Castro Contreras, Luis Alejandro<br>Poma de la Cruz, Yessly Josselyn<br>García Avalos, Alan Nicolas<br>Morales Brenis, Luis David<br>Espinoza Picon, Diego Steven Martin<br>Guevara Laiza, Christian Piero</div>
<div class="lugar">Lima, noviembre de 2026</div></div>"""


def indice(paginas):
    filas = ""
    for num, t in HEADS:
        etiq = f"Anexo {num}. {t}" if str(num) in list("ABCDEF") else f"{num}. {t}"
        pg = paginas.get(etiq, "")
        filas += f'<div class="fila"><span>{etiq}</span><span class="p"></span><span>{pg}</span></div>'
    return f'<div class="indice"><h1>Índice</h1>{filas}</div>'


def pagina_html(paginas):
    CONT["t"] = CONT["f"] = 0
    HEADS.clear()
    c = cuerpo()
    c = c.replace("<h1 id", "<h1 class='nuevo' id", 1) if False else c
    return f"<html><head><meta charset='utf-8'><style>{CSS}</style></head><body>{portada()}{indice(paginas)}{c}</body></html>"


def render(htmlstr, destino):
    tmp = R / "docs" / "_informe.html"
    tmp.write_text(htmlstr, encoding="utf-8")
    foot = ("<div style=\"font-family:Inter;font-size:8px;color:#6b7280;width:100%;padding:0 20mm;display:flex;justify-content:space-between\">"
            "<span>Grupo 4 — Minería de Datos — Informe final</span><span>Página <span class='pageNumber'></span></span></div>")
    with sync_playwright() as pw:
        b = pw.chromium.launch(executable_path="/usr/bin/google-chrome", args=["--no-sandbox"])
        pg = b.new_page()
        pg.goto(tmp.as_uri())
        pg.wait_for_timeout(1500)
        pg.pdf(path=str(destino), format="A4", print_background=True, display_header_footer=True, header_template="<div></div>", footer_template=foot,
               margin={"top": "22mm", "bottom": "22mm", "left": "20mm", "right": "20mm"})
        b.close()


def paginar(pdf):
    n = int(re.search(r"Pages:\s+(\d+)", subprocess.run(["pdfinfo", str(pdf)], capture_output=True, text=True).stdout).group(1))
    out = {}
    for i in range(3, n + 1):
        t = subprocess.run(["pdftotext", "-f", str(i), "-l", str(i), "-layout", str(pdf), "-"], capture_output=True, text=True).stdout
        lineas = [l.strip() for l in t.splitlines()]
        for num, tit in HEADS:
            etiq = f"{num}. {tit}" if str(num) not in list("ABCDEF") else f"Anexo {num}. {tit}"
            if etiq not in out and any(l == etiq for l in lineas):
                out[etiq] = i
    return out, n


if __name__ == "__main__":
    NUMS.clear()
    pagina_html({})          # primera pasada: numeración
    html1 = pagina_html({})
    render(html1, SALIDA)
    pgs, n = paginar(SALIDA)
    html2 = pagina_html(pgs)
    render(html2, SALIDA)
    pgs2, n2 = paginar(SALIDA)
    if pgs2 != pgs:
        render(pagina_html(pgs2), SALIDA)
        pgs2, n2 = paginar(SALIDA)
    faltan = [f"{a}. {b}" for a, b in HEADS if (f"{a}. {b}" if str(a) not in list("ABCDEF") else f"Anexo {a}. {b}") not in pgs2]
    print("páginas:", n2, "| títulos sin página:", faltan)
