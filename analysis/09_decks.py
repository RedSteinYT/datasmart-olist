from pathlib import Path
import pandas as pd
from pptx import Presentation
from pptx.util import Emu, Pt
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
ROOT=Path(__file__).resolve().parents[1]; F=ROOT/"analysis/figs"; S10=ROOT/"analysis/outputs_s10"; S13=ROOT/"analysis/outputs_s13"
NAVY,TEAL,PALE,INK,MUT=[RGBColor.from_string(x) for x in ("12304A","159A9C","EAF3F5","1E2933","5B6770")]; WH=RGBColor(255,255,255)
def px(v): return Emu(int(v*9525))
class Deck:
    def __init__(s,tag):
        s.p=Presentation(); s.p.slide_width=px(1280); s.p.slide_height=px(720); s.tag=tag; s.n=0
    def slide(s,bg=None):
        sl=s.p.slides.add_slide(s.p.slide_layouts[6]); s.n+=1
        if bg: sl.background.fill.solid(); sl.background.fill.fore_color.rgb=bg
        return sl
    def text(s,sl,t,l,tp,w,h,size=20,color=INK,bold=False,align=PP_ALIGN.LEFT,anchor=MSO_ANCHOR.TOP):
        tb=sl.shapes.add_textbox(px(l),px(tp),px(w),px(h)); tf=tb.text_frame; tf.word_wrap=True; tf.vertical_anchor=anchor
        for i,line in enumerate(t.split("\n")):
            p=tf.paragraphs[0] if i==0 else tf.add_paragraph(); p.alignment=align; r=p.add_run(); r.text=line
            r.font.size=Pt(size); r.font.bold=bold; r.font.color.rgb=color; r.font.name="Calibri"
        return tb
    def bullets(s,sl,items,l,tp,w,h,size=18):
        tb=sl.shapes.add_textbox(px(l),px(tp),px(w),px(h)); tf=tb.text_frame; tf.word_wrap=True
        for i,t in enumerate(items):
            p=tf.paragraphs[0] if i==0 else tf.add_paragraph(); p.space_after=Pt(8)
            r=p.add_run(); r.text="•  "+t; r.font.size=Pt(size); r.font.color.rgb=INK; r.font.name="Calibri"
    def title(s,sl,t,sub=""):
        s.text(sl,t,70,38,1140,55,32,NAVY,True)
        if sub: s.text(sl,sub,72,98,1140,30,15,MUT)
        r=sl.shapes.add_shape(1,px(70),px(138),px(1140),px(4)); r.fill.solid(); r.fill.fore_color.rgb=TEAL; r.line.fill.background()
        s.text(sl,f"DataSmart | {s.tag} | {s.n}",70,684,1140,18,11,MUT,False,PP_ALIGN.RIGHT)
    def img(s,sl,name,l,tp,w=None,h=None):
        sl.shapes.add_picture(str(F/name),px(l),px(tp),px(w) if w else None,px(h) if h else None)
    def table(s,sl,rows,l,tp,w,h,size=14,colw=None):
        gt=sl.shapes.add_table(len(rows),len(rows[0]),px(l),px(tp),px(w),px(h)); t=gt.table
        if colw:
            for i,cw in enumerate(colw): t.columns[i].width=px(cw)
        for r,row in enumerate(rows):
            for c,v in enumerate(row):
                cell=t.cell(r,c); cell.text=str(v); cell.fill.solid(); cell.fill.fore_color.rgb=NAVY if r==0 else (WH if r%2 else PALE)
                for p in cell.text_frame.paragraphs:
                    for run in p.runs: run.font.size=Pt(size); run.font.name="Calibri"; run.font.bold=(r==0); run.font.color.rgb=WH if r==0 else INK
    def cover(s,t,sub,sub2):
        sl=s.slide(NAVY); s.text(sl,t,80,165,1120,76,53,WH,True,PP_ALIGN.CENTER); s.text(sl,sub,120,255,1040,50,26,RGBColor.from_string("D9F3F1"),False,PP_ALIGN.CENTER)
        s.text(sl,sub2,120,320,1040,40,18,WH,False,PP_ALIGN.CENTER); s.text(sl,"Equipo: Luis Alejandro, Nicolas, Diego y Luis Brenis",120,380,1040,30,16,RGBColor.from_string("BFD8DC"),False,PP_ALIGN.CENTER); return sl
    def notes(s,sl,t): sl.notes_slide.notes_text_frame.text=t
    def save(s,path): s.p.save(path)

# ====================== SEGUNDO ENTREGABLE ======================
lg=pd.read_csv(S10/"01_log_limpieza.csv").set_index("indicador").valor
cmpa=pd.read_csv(S10/"03_comparacion_algoritmos.csv"); par=pd.read_csv(S10/"05_parametros_asociacion.csv").iloc[0]; top=pd.read_csv(S10/"04_top_reglas.csv")
d=Deck("Segundo entregable")
d.cover("DataSmart","Preparación de datos y primeros modelos — Olist","Segundo entregable - Semana 10")
s=d.slide(); d.title(s,"De dónde venimos y qué entregamos hoy","Seguimos CRISP-DM: fase de preparación de datos y primeros modelos")
d.bullets(s,["Semana 7: comprensión del negocio y de los datos (Olist, 99,441 pedidos, 5 KPIs).","Hoy: dataset procesado, ingeniería de características, reglas de asociación (Apriori, FP-Growth, ECLAT), primer prototipo y resultados preliminares.","Unidad de análisis procesada: pedido entregado con ítems, pagos, cliente y reseña integrados.","Semana 13: clustering, series temporales, grafos, regresión y evaluación comparativa."],70,170,1140,420,22)
d.notes(s,"Recordar al profesor el alcance de la semana 7 y presentar el avance de esta semana.")
s=d.slide(); d.title(s,"Preparación de datos","Cada problema de calidad del primer entregable recibió un tratamiento documentado")
rows=[["Problema","Hallazgo","Tratamiento aplicado"],
["Registros duplicados","0 filas duplicadas en las 6 tablas clave","Verificado; sin acción"],
["Reseñas múltiples por pedido",f"{lg['pedidos con >1 reseña']} pedidos","Se conserva la reseña más reciente"],
["Fecha de entrega faltante",f"{int(lg['nulos fecha entrega cliente (todos los estados)']):,} pedidos","Se excluyen solo del análisis de entrega"],
["Categoría faltante",f"{lg['nulos categoría producto']} productos","Categoría «sin_categoria»; traducción al inglés"],
["Dimensiones/peso faltantes","2 productos","Mediana de su categoría"],
["Pagos con valor 0",f"{lg['pagos con valor 0']} registros","Se conservan (vouchers); no afectan el modelo"],
["Outliers (IQR)",f"valor_pago: {int(lg['outliers IQR valor_pago']):,}; entrega: {int(lg['outliers IQR dias_entrega']):,}","No se eliminan; winsorización al p99 solo en regresión"]]
d.table(s,rows,70,165,1140,380,14,[260,400,480])
d.text(s,f"Resultado: {int(lg['filas tras integrar']):,} pedidos entregados y válidos (dataset procesado). No se eliminaron pedidos sin justificación.",70,590,1140,60,18,NAVY,True)
d.notes(s,"Responder a la pregunta típica: los nulos se tratan por análisis, no se borran pedidos completos.")
s=d.slide(); d.title(s,"Ingeniería de características","De 7 tablas a una tabla analítica por pedido con 41 columnas")
d.bullets(s,["Integración de fuentes: pedidos + ítems + pagos + clientes + productos + reseñas.","Logística: días de entrega, días estimados, retraso, entrega tardía (0/1), días de aprobación.","Comercial: precio total, flete total, ratio flete/precio, n.º de ítems, vendedores, medio de pago y cuotas.","Producto: peso y volumen totales, categoría principal (traducida).","Temporales: mes, día de la semana, hora, fin de semana.","Variables categóricas: One-Hot (estado, categoría). Escalamiento: StandardScaler en modelos lineales.","Colinealidad y reducción de dimensionalidad (PCA) se aplican en la semana 13 sobre las variables de clientes."],70,165,1140,480,19)
d.notes(s,"Mencionar que PCA se usa en el clustering de la semana 13.")
s=d.slide(); d.title(s,"Hallazgo preliminar: la entrega tardía castiga la satisfacción","Las variables creadas permiten relacionar logística y experiencia del cliente")
d.img(s,"s10_review_vs_tardia.png",70,165,h=400); d.img(s,"s10_dist_entrega.png",620,165,h=400)
d.text(s,"Pedidos tardíos: reseña media 2.57 vs 4.29 a tiempo (7,660 de 95,823 pedidos con reseña, 8.0%). Es una asociación observada, no prueba causalidad.",70,580,1140,80,18)
d.notes(s,"Cifras calculadas en 02_preparacion.py / 08_figuras.py. Cuidado: es correlación.")
s=d.slide(); d.title(s,"Reglas de asociación: diseño del experimento","Canasta = categorías distintas compradas por un cliente (histórico)")
d.bullets(s,[f"El 97% de los clientes compra una sola vez: solo {int(par.canastas_multicategoria):,} de 93,349 clientes compraron en ≥2 categorías.","Por eso usamos canastas por cliente (no por pedido) y analizamos solo las de ≥2 categorías.",f"Parámetros: soporte mínimo {par.min_support:.1%} (≈9 clientes), confianza mínima {par.min_confidence:.0%}, itemsets de hasta {int(par.max_len)} categorías.","Los tres algoritmos se implementaron y se verificó que producen exactamente los mismos itemsets y reglas."],70,165,1140,260,20)
rows=[["Algoritmo","Itemsets frecuentes","Reglas","Tiempo (ms)"]]+[[r.algoritmo,r.itemsets_frecuentes,r.reglas,f"{r.tiempo_s*1000:.0f}"] for r in cmpa.itertuples()]
d.table(s,rows,70,450,760,170,16); d.text(s,"Apriori es el más lento (recorre la base por nivel); ECLAT y FP-Growth son más rápidos con los mismos resultados.",860,450,350,150,16,MUT)
d.notes(s,"Si preguntan por qué no mlxtend: se implementó cada algoritmo para poder compararlos y verificar equivalencia.")
s=d.slide(); d.title(s,"Reglas de asociación: resultados","Lift > 1 indica que las categorías se compran juntas más de lo esperado por azar")
d.img(s,"s10_reglas_lift.png",70,160,h=420)
d.bullets(s,["bed_bath_table ↔ home_confort: lift 3.1; confianza 74% desde home_confort.","baby ↔ cool_stuff y baby ↔ toys: lift 2.6 y 2.1.","construction_tools_lights → furniture_decor: lift 2.7 (n=18).","Reglas con n pequeño (10–54 clientes): son hipótesis para campañas, no resultados definitivos."],790,175,430,400,16)
d.text(s,"Uso de negocio: ofertas cruzadas entre categorías del hogar y del bebé.",70,600,1140,40,18,NAVY,True)
d.notes(s,"Tabla completa en analysis/outputs_s10/04_top_reglas.csv.")
s=d.slide(); d.title(s,"Primer prototipo","Aplicación Streamlit con los resultados de esta etapa")
d.bullets(s,["Pestañas: Resumen de KPIs, Calidad de datos, Reglas de asociación (filtros por soporte, confianza y lift) y Entrega vs. satisfacción.","Lee los CSV generados por los scripts de analysis/ (sin recalcular), por lo que carga en segundos.","Pendiente para las siguientes semanas: segmentación, pronóstico, grafos, regresión, clasificación, NLP, explicabilidad y monitoreo.","Estructura del repositorio alineada con la propuesta (data/, notebooks/ o analysis/, src/, backend/, frontend/, docs/)."],70,165,1140,420,20)
d.text(s,"[Insertar aquí una captura de pantalla del prototipo ejecutándose — ver guía de pasos humanos]",70,560,1140,60,16,MUT)
d.notes(s,"Antes de exponer, ejecutar 'streamlit run app/app.py' y tomar la captura.")
s=d.slide(); d.title(s,"Resultados preliminares y próximos pasos","Lo que sabemos hoy y lo que falta")
d.bullets(s,["Dataset procesado y reproducible: 96,469 pedidos entregados × 41 variables.","La entrega tardía se asocia a peor satisfacción (2.57 vs 4.29).","Existen asociaciones entre categorías, pero la recompra es baja (97% de clientes compra una vez): la segmentación debe apoyarse en RFM + satisfacción + logística.","Limitación: pocas canastas multi-categoría; las reglas son exploratorias.","Semana 13: clustering (K-Means, jerárquico, DBSCAN), series temporales, grafos, regresión y evaluación comparativa."],70,165,1140,480,21)
d.save(ROOT/"outputs/Segundo_Entregable_Olist_DataSmart.pptx")

# ====================== TERCER ENTREGABLE ======================
pf=pd.read_csv(S13/"03_perfil_clusters.csv"); cc=pd.read_csv(S13/"02_clustering_comparacion.csv"); ts=pd.read_csv(S13/"07_series_comparacion.csv"); gr=pd.read_csv(S13/"13_grafo_resumen.csv").iloc[0]
rg=pd.read_csv(S13/"14_regresion_comparacion.csv"); ph=pd.read_csv(S13/"10_pronostico_horizontes.csv"); ndg=pd.read_csv(S13/"11_grafo_nodos.csv")
d=Deck("Tercer entregable")
d.cover("DataSmart","Modelamiento avanzado — Olist","Tercer entregable - Semana 13")
s=d.slide(); d.title(s,"Qué modelamos esta semana","Cuatro técnicas y una evaluación comparativa sobre los datos procesados")
rows=[["Técnica","Pregunta de negocio","Modelos"],["Clustering","¿Qué tipos de clientes existen?","K-Means, Hierarchical (Ward), DBSCAN; RFM y ABC"],["Series temporales","¿Cuáles serán las ventas de los próximos 7-90 días?","Naive, media móvil, Holt-Winters, Ridge y Gradient Boosting con rezagos"],["Grafos","¿Qué categorías están conectadas?","Red de co-compra, comunidades, centralidad (NetworkX)"],["Regresión","¿Qué factores explican el tiempo de entrega?","Lineal, Ridge, Lasso, Elastic Net, Random Forest, Gradient Boosting"]]
d.table(s,rows,70,170,1140,330,16,[200,420,520]); d.text(s,"Todos los resultados provienen de scripts reproducibles en analysis/ (04 a 07).",70,540,1140,40,16,MUT)
s=d.slide(); d.title(s,"Clustering: selección del número de segmentos","K-Means sobre 6 variables (RFM + reseña + entrega + flete), con log y estandarización")
d.img(s,"s13_kmeans_k.png",70,165,h=400)
d.bullets(s,["Silhouette máximo en k=5 (0.254); k=4 (0.238) con mejor interpretabilidad.","Elegimos k=4 por interpretación de negocio; se declara como decisión, no como óptimo estadístico.","Solo el 3% de clientes compra más de una vez: Frecuencia aporta poca variación.","ABC: el 48.8% de clientes (A) genera el 80% del ingreso."],700,170,510,400,17)
s=d.slide(); d.title(s,"Clustering: perfiles de los 4 segmentos","Los segmentos se distinguen sobre todo por valor, satisfacción y logística")
d.img(s,"s13_perfil.png",70,160,h=330)
rows=[["Cluster","Perfil","Clientes","Monto medio","Reseña","Entrega (d)"]]
nm=["Alto valor satisfecho","Ticket bajo, flete alto","Insatisfechos (entrega lenta)","Recurrentes"]
for i,r in pf.iterrows(): rows.append([int(r.cluster_kmeans),nm[i],f"{int(r.clientes):,}",f"R${r.monetario:.0f}",f"{r.review:.2f}",f"{r.dias_entrega:.1f}"])
d.table(s,rows,70,500,1140,170,14,[90,300,160,200,160,230])
d.img(s,"s13_pca.png",780,150,h=335)
d.notes(s,"Nombres de segmentos = interpretación del equipo sobre los promedios de la tabla.")
s=d.slide(); d.title(s,"Clustering: comparación de algoritmos","No todos los algoritmos sirven igual para este problema")
rows=[["Modelo","Clusters","Silhouette","Davies-Bouldin","Ruido","Muestra"]]+[[r.modelo,int(r.n_clusters),("—" if pd.isna(r.silhouette) else f"{r.silhouette:.3f}"),("—" if pd.isna(r.davies_bouldin) else f"{r.davies_bouldin:.2f}"),f"{r.ruido:.1%}",r.muestra] for r in cc.itertuples()]
d.table(s,rows,70,170,1140,200,16,[360,120,150,180,130,200])
d.bullets(s,["K-Means: mejor equilibrio (silhouette 0.239, DB 1.26) y escala a 93k clientes.","Hierarchical (Ward) se calculó en una muestra de 8,000 por su costo cuadrático; peor separación.","DBSCAN: con eps=0.9 y min_samples=30 forma 1 solo cluster; en el barrido de parámetros o descarta 31–94% como ruido o deja ≥94% en un solo cluster. Útil como detector de atípicos, no como segmentador."],70,400,1140,260,18)
s=d.slide(); d.title(s,"Series temporales: pronóstico de ventas diarias","Serie diaria 2017-01-01 a 2018-08-15; validación en los últimos 30 días")
rows=[["Modelo","MAE (BRL)","RMSE (BRL)","MAPE"]]+[[r.modelo,f"{r.MAE:,.0f}",f"{r.RMSE:,.0f}",f"{r.MAPE:.1f}%"] for r in ts.itertuples()]
d.table(s,rows,70,165,640,290,14,[290,110,130,110]); d.img(s,"s13_holdout.png",730,160,w=480)
d.text(s,"Mejor modelo: Ridge con rezagos (1, 7, 14 d), medias móviles y día de la semana: MAPE 11.8% vs 20.4% del naive.",70,480,1140,50,18,NAVY,True)
d.text(s,"Limitación: una sola ventana de validación de 30 días y menos de 2 años de historia, sin estacionalidad anual aprendible. SARIMA/Prophet se ejecutan en Colab (guía).",70,540,1140,80,16,MUT)
s=d.slide(); d.title(s,"Pronóstico a 7, 30, 60 y 90 días","Salida requerida por la propuesta")
d.img(s,"s13_pronostico.png",70,160,w=700)
rows=[["Horizonte","Ventas (BRL)","Promedio diario"]]+[[f"{int(r.horizonte_dias)} días",f"R${r.ventas_pronosticadas_BRL/1e6:.2f} M" if r.ventas_pronosticadas_BRL>1e6 else f"R${r.ventas_pronosticadas_BRL/1e3:.0f} mil",f"R${r.promedio_diario:,.0f}"] for r in ph.itertuples()]
d.table(s,rows,800,170,410,200,15)
d.text(s,"El pronóstico es casi plano (~R$44 mil/día): el modelo no puede anticipar eventos como Black Friday porque solo hay un noviembre en el rango. Interpretar como nivel base.",800,400,410,200,15,MUT)
s=d.slide(); d.title(s,"Grafos: red de co-compra de categorías","Nodos = categorías; arista = clientes que compraron ambas (≥3 clientes)")
d.img(s,"s13_grafo.png",70,165,h=430)
top3=ndg.head(3).categoria.tolist()
d.bullets(s,[f"{int(gr.nodos)} categorías, {int(gr.aristas)} relaciones, densidad {gr.densidad:.2f}.",f"Modularidad {gr.modularidad:.2f}: estructura de comunidades débil, pero 4 grupos: hogar, salud/tecnología/deporte, bebé/juguetes y otros.",f"Categorías más centrales (PageRank): {', '.join(top3)}.","Arista más fuerte: bed_bath_table – furniture_decor (153 clientes)."],790,170,430,450,15)
s=d.slide(); d.title(s,"Regresión: predecir el tiempo de entrega","Variable objetivo: días de entrega; 52 variables; 80/20 train-test; winsorización p99")
d.img(s,"s13_regresion.png",70,160,h=400)
d.bullets(s,["Mejor: Gradient Boosting (R²=0.29, MAE 4.95 d) vs baseline (MAE 6.19 d).","Los modelos lineales explican ~21%; los de árboles capturan no linealidades.","Lasso conserva 36 de 52 variables.","El poder predictivo es moderado: faltan variables clave (distancia comprador-vendedor, stock del vendedor)."],770,170,450,420,16)
s=d.slide(); d.title(s,"Regresión: qué variables pesan más","Importancia por permutación (Gradient Boosting)")
d.img(s,"s13_importancia.png",70,160,h=400)
d.bullets(s,["Flete y estado de destino (SP) dominan: reflejan distancia y logística.","Volumen y peso del pedido influyen menos.","Anticipa la explicabilidad (SHAP/LIME) de la semana 16."],740,190,470,300,18)
s=d.slide(); d.title(s,"Evaluación comparativa y conclusiones","Qué aprendimos y qué sigue")
rows=[["Técnica","Mejor resultado","Métrica","Lectura de negocio"],["Clustering","K-Means k=4","Silhouette 0.24","Segmento de insatisfechos con entrega lenta (15.5% clientes, reseña 1.66)"],["Series temporales","Ridge con rezagos","MAPE 11.8%","Nivel base ~R$44 mil/día; sin estacionalidad anual"],["Grafos","Greedy modularity","Modularidad 0.17","Hogar es el núcleo de las compras cruzadas"],["Regresión","Gradient Boosting","R² 0.29, MAE 4.95 d","Flete y destino explican la demora"]]
d.table(s,rows,70,165,1140,260,15,[190,260,230,460])
d.bullets(s,["Hallazgo transversal: la logística (entrega lenta) conecta segmentación, satisfacción y regresión.","Semana 16: clasificación (cliente en riesgo), minería de textos, explicabilidad, monitoreo y aplicación web final."],70,450,1140,200,19)
d.save(ROOT/"outputs/Tercer_Entregable_Olist_DataSmart.pptx")
print("ok")
