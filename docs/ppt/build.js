const pptxgen = require("pptxgenjs"); const sharp = require("sharp"); const fs = require("fs"); const path = require("path");
const React = require("react"); const RDS = require("react-dom/server"); const Fi = require("react-icons/fi");
const FIG = path.resolve(__dirname, "../figuras"), OLD = path.resolve(__dirname, "../../analysis/figs");
const NAVY = "0B1F3A", TEAL = "0F8F6B", AMB = "E8A900", AMBD = "A86F00", RED = "D9423F", BLUE = "2563B8", INK = "14233A", MUT = "5B6B80", SOFT = "E6ECF2", WH = "FFFFFF", CREAM = "FBF8F1";
const IR = ["Luis Alejandro Castro", "Yessly Poma", "Alan García", "Luis David Morales", "Diego Espinoza", "Christian Guevara"];
const TOTAL = 18; const pres = new pptxgen(); pres.layout = "LAYOUT_16x9"; pres.theme = { headFontFace: "Cambria", bodyFontFace: "Calibri" };
pres.title = "DataSmart — Sustentación final"; pres.author = "Grupo 4";
const guion = []; let n = 0; const cache = {};
async function icon(name, color, px = 256) { const k = name + color; if (cache[k]) return cache[k];
  const svg = RDS.renderToStaticMarkup(React.createElement(Fi[name], { color: "#" + color, size: px, strokeWidth: 2 }));
  const b = await sharp(Buffer.from(svg)).png().toBuffer(); return cache[k] = "image/png;base64," + b.toString("base64"); }
const sh = () => ({ type: "outer", blur: 10, offset: 3, angle: 90, color: "0B1F3A", opacity: 0.14 });
function card(s, x, y, w, h, fill, name) { s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x, y, w, h, fill: { color: fill || WH }, line: { color: fill || WH, width: 0 }, rectRadius: 0.12, shadow: sh(), objectName: name || "tarjeta" }); }
async function circ(s, ic, x, y, d, bg, fg) { s.addShape(pres.shapes.OVAL, { x, y, w: d, h: d, fill: { color: bg }, line: { color: bg, width: 0 } }); s.addImage({ data: await icon(ic, fg), x: x + d * .25, y: y + d * .25, w: d * .5, h: d * .5, altText: ic }); }
async function img(s, f, x, y, w, h, alt) { const p = fs.existsSync(path.join(FIG, f + ".png")) ? path.join(FIG, f + ".png") : fs.existsSync(path.join(__dirname, f)) ? path.join(__dirname, f) : path.join(OLD, f + ".png");
  const m = await sharp(p).metadata(); const r = Math.min(w / m.width, h / m.height); const iw = m.width * r, ih = m.height * r; s.addImage({ path: p, x: x + (w - iw) / 2, y: y + (h - ih) / 2, w: iw, h: ih, altText: alt || f }); }
async function figura(s, f, x, y, w, h, alt) { card(s, x, y, w, h, WH, "marco figura"); await img(s, f, x + .12, y + .12, w - .24, h - .24, alt); }
function T(s, text, o) { s.addText(text, Object.assign({ margin: 0, isTextBox: true, color: INK, fontSize: 14, valign: "top" }, o)); }
function light(s, kicker, title, who) { n++; s.background = { path: path.join(__dirname, "bg_light.png") };
  T(s, kicker, { x: .5, y: .28, w: 7, h: .3, fontSize: 12, bold: true, color: AMBD, charSpacing: 1 });
  T(s, title, { x: .5, y: .55, w: 9, h: .6, fontFace: "Cambria", fontSize: 26, bold: true, color: NAVY, valign: "middle" });
  s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x: .5, y: 5.12, w: 2.6, h: .3, fill: { color: SOFT }, line: { color: SOFT, width: 0 }, rectRadius: .15 });
  T(s, "Expone: " + IR[who], { x: .62, y: 5.12, w: 2.4, h: .3, fontSize: 10, color: MUT, valign: "middle" });
  T(s, `${n} / ${TOTAL}`, { x: 8.5, y: 5.12, w: 1, h: .3, fontSize: 10, color: MUT, align: "right", valign: "middle" }); }
function dark(s, plano) { n++; s.background = { path: path.join(__dirname, plano ? "bg_dark_plano.png" : "bg_dark.png") }; }
const INTER = JSON.parse(fs.readFileSync(path.join(__dirname, "interaccion.json"), "utf8"));
function add(s, t, notes, who) { const k = String(guion.length + 1), it = INTER[k];
  let extra = ""; if (it && it.dice) extra = `\n\nMOMENTO INTERACTIVO${it.opcional ? " (opcional, solo si van bien de tiempo)" : ""}:\n${it.dice}` + (it.veran ? `\nLo que verán: ${it.veran}` : "");
  s.addNotes(notes + extra); guion.push({ t, notes, who: IR[who] }); }
async function filas(s, items, x, y, w, rowH, ic, bg, fg, size, tc) { for (let i = 0; i < items.length; i++) { const yy = y + i * rowH; await circ(s, ic, x, yy, .38, bg, fg); T(s, items[i], { x: x + .52, y: yy - .02, w: w - .52, h: rowH, fontSize: size || 14, color: tc || INK }); } }
async function statCard(s, x, y, w, h, ic, col, big, small) { card(s, x, y, w, h); await circ(s, ic, x + .22, y + .22, .5, col, WH);
  T(s, big, { x: x + .22, y: y + .82, w: w - .44, h: .62, fontFace: "Cambria", fontSize: 32, bold: true, color: col, valign: "middle" });
  T(s, small, { x: x + .22, y: y + 1.44, w: w - .44, h: h - 1.55, fontSize: 13, color: MUT }); }
(async () => {
  let s;
  // 1 portada
  s = pres.addSlide(); dark(s);
  await img(s, "logo.png", .55, .42, .62, .72, "Escudo UNMSM");
  T(s, "Universidad Nacional Mayor de San Marcos", { x: 1.3, y: .45, w: 6, h: .32, fontFace: "Cambria", fontSize: 15, bold: true, color: WH });
  T(s, "Facultad de Ingeniería de Sistemas e Informática · Ingeniería de Software", { x: 1.3, y: .78, w: 6.5, h: .3, fontSize: 11, color: "A9BBD1" });
  T(s, "Minería de Datos · Grupo 4 · Proyecto final", { x: .55, y: 1.65, w: 6, h: .35, fontSize: 15, bold: true, color: AMB });
  T(s, [{ text: "Data", options: { color: WH } }, { text: "Smart", options: { color: AMB } }], { x: .55, y: 2.0, w: 6, h: 1.1, fontFace: "Cambria", fontSize: 64, bold: true, valign: "middle" });
  T(s, "Anticipar entregas tardías y explicar por qué", { x: .55, y: 3.15, w: 5.4, h: .8, fontSize: 19, color: "CDD9E7" });
  T(s, "96 469 pedidos reales de Olist (Brasil, 2016–2018)", { x: .55, y: 3.6, w: 5.4, h: .4, fontSize: 13, color: "A9BBD1" });
  s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x: 6.55, y: 1.45, w: 2.95, h: 3.35, fill: { color: CREAM }, line: { color: CREAM, width: 0 }, rectRadius: .14, rotate: 2, shadow: { type: "outer", blur: 18, offset: 6, angle: 90, color: "000000", opacity: .45 }, objectName: "tarjeta QR" });
  s.addImage({ path: path.join(__dirname, "qr.png"), x: 7.1, y: 1.7, w: 1.85, h: 1.85, rotate: 2, altText: "Código QR a redsteinyt.github.io/datasmart-olist" });
  T(s, "Escanea y pruébalo", { x: 6.7, y: 3.65, w: 2.65, h: .4, fontFace: "Cambria", fontSize: 17, bold: true, color: NAVY, align: "center", rotate: 2 });
  T(s, "redsteinyt.github.io/datasmart-olist", { x: 6.7, y: 4.05, w: 2.65, h: .3, fontSize: 11, color: MUT, align: "center", rotate: 2 });
  T(s, "Funciona en el celular", { x: 6.7, y: 4.33, w: 2.65, h: .3, fontSize: 11, bold: true, color: TEAL, align: "center", rotate: 2 });
  T(s, "Castro · Poma de la Cruz · García · Morales · Espinoza · Guevara — Lima, noviembre de 2026", { x: .55, y: 4.95, w: 8.9, h: .3, fontSize: 11, color: "A9BBD1" });
  add(s, "Portada", "Buenos días. Somos el Grupo 4 y presentamos DataSmart: una plataforma que, con datos reales de Olist, estima qué pedidos van a llegar tarde, explica por qué y se puede usar desde el navegador. Vamos a contar el recorrido completo, desde los datos hasta la aplicación, incluyendo lo que no salió tan bien. Si quieren, escaneen el código QR: abre nuestra web en su celular y pueden probarla mientras presentamos.", 0);
  // 2
  s = pres.addSlide(); light(s, "EL PROBLEMA", "La entrega define la satisfacción", 0);
  await statCard(s, .5, 1.35, 2.9, 2.2, "FiPackage", BLUE, "96 469", "pedidos entregados analizados (R$ 15,4 millones)");
  await statCard(s, 3.55, 1.35, 2.9, 2.2, "FiClock", AMBD, "8,1 %", "llega después de la fecha prometida");
  await statCard(s, 6.6, 1.35, 2.9, 2.2, "FiThumbsDown", RED, "54 / 9 %", "de reseñas bajas: pedidos tardíos frente a puntuales");
  card(s, .5, 3.8, 9, 1.05, NAVY, "pregunta");
  T(s, [{ text: "Pregunta central: ", options: { bold: true, color: AMB } }, { text: "¿qué pedidos tienen riesgo de llegar tarde, ya en el momento de la compra? Y que lo entienda alguien que no es técnico.", options: { color: WH } }], { x: .8, y: 3.8, w: 8.4, h: 1.05, fontSize: 16, valign: "middle" });
  add(s, "Problema", "Olist conecta vendedores con compradores en Brasil. Analizamos 96 469 pedidos entregados. El 8,1 % llega tarde, y esos pedidos terminan con reseña baja el 54 % de las veces frente al 9 % de los puntuales. Por eso la pregunta central es anticipar el retraso al momento de comprar, y hacerlo de forma que una persona no técnica lo entienda.", 0);
  // 3
  s = pres.addSlide(); light(s, "METODOLOGÍA", "Cuatro entregables, un solo hilo", 1);
  const fases = [["Negocio y datos", "Semana 7 · EDA, calidad y KPIs", "FiSearch"], ["Preparación", "Semana 10 · dataset de 96 469 pedidos y reglas", "FiDatabase"], ["Modelos", "Semana 13 · clientes, ventas, grafos y regresión", "FiLayers"], ["Producto", "Semana 16 · clasificación, textos, SHAP, monitoreo y web", "FiPackage"]];
  s.addShape(pres.shapes.LINE, { x: 1, y: 2.05, w: 7.8, h: 0, line: { color: "9FB2C9", width: 1.5, dashType: "dash" } });
  for (let i = 0; i < 4; i++) { const x = .5 + i * 2.3, last = i === 3; card(s, x, 1.5, 2.1, 2.8, last ? NAVY : WH, "fase");
    await circ(s, fases[i][2], x + .2, 1.75, .6, last ? AMB : SOFT, last ? NAVY : BLUE);
    T(s, `${i + 1}. ${fases[i][0]}`, { x: x + .2, y: 2.55, w: 1.75, h: .5, fontFace: "Cambria", fontSize: 16, bold: true, color: last ? WH : NAVY });
    T(s, fases[i][1], { x: x + .2, y: 3.05, w: 1.75, h: 1.15, fontSize: 13, color: last ? "CDD9E7" : MUT }); }
  T(s, "CRISP-DM · Python reproducible · 21 scripts · semilla 42", { x: .5, y: 4.5, w: 9, h: .35, fontSize: 14, color: MUT });
  add(s, "Recorrido", "Seguimos CRISP-DM. Los dos primeros entregables fijaron el negocio, los datos y la preparación; el tercero trajo asociación, clustering, series, grafos y regresión; el cuarto, que es el que presentamos hoy, agrega clasificación, minería de textos, explicabilidad, monitoreo y la aplicación web. Todo está en scripts reproducibles.", 1);
  // 4
  s = pres.addSlide(); light(s, "DATOS", "El retraso depende del destino", 1);
  await figura(s, "f02_estados", .5, 1.3, 5.3, 3.65, "Retraso por estado");
  await filas(s, ["Alagoas supera el 24 % de entregas tardías; la media nacional es 8,1 %.", "Solo el 36 % de las ventas queda en el mismo estado; distancia mediana de 434 km.", "Depuramos la geolocalización (261 831 duplicados) para medir distancias."], 6.05, 1.45, 3.45, 1.15, "FiMapPin", SOFT, BLUE, 14);
  add(s, "Destino", "El retraso no se reparte parejo: algunos estados del norte y noreste superan el 20 por ciento. Para medir distancia tuvimos que depurar la tabla de geolocalización, que tenía más de 261 mil duplicados. La distancia mediana vendedor–comprador es de 434 kilómetros y solo el 36 por ciento de las ventas se queda en el mismo estado.", 1);
  // 5
  s = pres.addSlide(); light(s, "INGENIERÍA DE CARACTERÍSTICAS", "Variables con información disponible al comprar", 2);
  const cards = [["Distancia", "Haversine entre prefijos postales; Spearman 0,54 con los días de entrega", "FiNavigation"], ["Plazo prometido", "Días estimados que ve el cliente al comprar", "FiCalendar"], ["Carga de la plataforma", "Pedidos de 7 días frente al promedio de 8 semanas previas", "FiTrendingUp"], ["Historial del vendedor", "Solo con pedidos anteriores, para no mirar el futuro", "FiUser"]];
  for (let i = 0; i < 4; i++) { const x = .5 + (i % 2) * 4.6, y = 1.3 + Math.floor(i / 2) * 1.5; card(s, x, y, 4.4, 1.32); await circ(s, cards[i][2], x + .22, y + .3, .7, SOFT, BLUE);
    T(s, cards[i][0], { x: x + 1.1, y: y + .17, w: 3.1, h: .4, fontFace: "Cambria", fontSize: 17, bold: true, color: NAVY }); T(s, cards[i][1], { x: x + 1.1, y: y + .58, w: 3.1, h: .7, fontSize: 13, color: MUT }); }
  T(s, "Colinealidad revisada: VIF máximo 3,66 (umbral 5). PCA, LDA y QDA no mejoraron al modelo completo.", { x: .5, y: 4.4, w: 9, h: .5, fontSize: 14, color: MUT });
  add(s, "Variables", "Agregamos cuatro familias de variables: distancia, plazo prometido, carga reciente de la plataforma e historial del vendedor, este último calculado solo con pedidos anteriores para no filtrar información del futuro. Revisamos colinealidad con VIF, máximo 3,66, y probamos PCA, LDA y QDA; ninguno mejoró al modelo completo, y lo documentamos como resultado negativo.", 2);
  // 6
  s = pres.addSlide(); light(s, "ENTREGABLES 2 Y 3", "Clientes, categorías y ventas", 2);
  await figura(s, "s13_perfil", .5, 1.3, 4.7, 3.65, "Segmentos");
  await filas(s, ["K-Means (k = 4): 15,5 % de clientes insatisfechos, reseña 1,66 y 21 días de entrega.", "Apriori, FP-Growth y ECLAT dan las mismas 105 reglas; lift máximo 3,1.", "Grafo de 45 categorías: el hogar es el núcleo (modularidad 0,17).", "Ventas: Ridge con rezagos, MAPE 11,8 %."], 5.45, 1.4, 4.05, .9, "FiCheck", SOFT, TEAL, 13);
  add(s, "Clientes", "En el tercer entregable segmentamos con K-Means. El hallazgo clave es un grupo de insatisfechos con entrega lenta: 15 por ciento de clientes, reseña media de 1,66 y 21 días de entrega. Los tres algoritmos de asociación dan los mismos resultados, solo cambia el tiempo. El grafo muestra que el hogar es el núcleo de las compras cruzadas. Y para ventas diarias, un Ridge con rezagos superó a SARIMA y Prophet con 11,8 por ciento de error.", 2);
  // 7
  s = pres.addSlide(); light(s, "REGRESIÓN", "Más información logística, mejor predicción", 3);
  await figura(s, "f03_regresion_versiones", .5, 1.3, 5.6, 3.65, "Regresión v1 a v3");
  await statCard(s, 6.35, 1.3, 3.15, 2.2, "FiTrendingUp", TEAL, "0,29 → 0,41", "R² de XGBoost de v1 a v3");
  card(s, 6.35, 3.7, 3.15, 1.25); T(s, [{ text: "MAE 4,44 días", options: { bold: true, color: NAVY, breakLine: true } }, { text: "frente a 6,19 del baseline", options: { color: MUT } }], { x: 6.57, y: 3.7, w: 2.8, h: 1.25, fontSize: 15, valign: "middle" });
  add(s, "Regresión", "Para predecir cuántos días tardará un pedido construimos tres versiones. Con las variables básicas el R cuadrado era 0,29. Al sumar distancia llegó a 0,32 y con plazo prometido, carga de la plataforma e historial del vendedor, a 0,41. El error medio es de 4,4 días. Es un resultado moderado: mucha de la demora depende de eventos que no están en los datos.", 3);
  // 8
  s = pres.addSlide(); light(s, "CLASIFICACIÓN", "¿Llegará tarde este pedido?", 3);
  await figura(s, "f04_roc_pr", .5, 1.3, 5.6, 2.75, "ROC y PR");
  await statCard(s, 6.35, 1.3, 1.5, 2.75, "FiTarget", TEAL, "0,783", "AUC-ROC (IC 0,769–0,794)");
  await statCard(s, 8.0, 1.3, 1.5, 2.75, "FiCrosshair", AMBD, "0,317", "AUC-PR (azar 0,081)");
  T(s, "XGBoost, 300 árboles, 61 columnas. Brier 0,065 (azar 0,0745). Comparado con Random Forest, regresión logística, SVM y Naive Bayes.", { x: .5, y: 4.25, w: 9, h: .65, fontSize: 14, color: MUT });
  add(s, "Clasificación", "El modelo central es un XGBoost que estima la probabilidad de entrega tardía. Como solo el 8 por ciento llega tarde, usamos AUC-PR además de AUC-ROC. Obtuvimos 0,783 y 0,317, contra 0,081 que daría el azar. Con intervalos de confianza por bootstrap. Lo comparamos con cuatro algoritmos más; los de árboles potenciados fueron los mejores.", 3);
  // 9
  s = pres.addSlide(); light(s, "DESBALANCE DE CLASES", "Balancear los datos no ayudó", 4);
  card(s, .5, 1.3, 5.6, 3.65, WH, "marco gráfico");
  s.addChart(pres.charts.BAR, [{ name: "AUC-PR", labels: ["Sin balanceo", "Oversampling", "Undersampling", "ADASYN", "SMOTE"], values: [0.303, 0.293, 0.275, 0.224, 0.221] }],
    { x: .65, y: 1.4, w: 5.3, h: 3.45, barDir: "bar", chartColors: [TEAL], invertedColors: [TEAL], showValue: true, dataLabelFormatCode: "0.000", dataLabelColor: INK, dataLabelFontSize: 12, dataLabelFontFace: "+mn-lt", catAxisLabelColor: INK, catAxisLabelFontSize: 12, catAxisLabelFontFace: "+mn-lt", valAxisHidden: true, valGridLine: { style: "none" }, catGridLine: { style: "none" }, showLegend: false, showTitle: true, title: "AUC-PR con XGBoost", titleFontSize: 14, titleColor: INK, titleFontFace: "+mn-lt", catAxisOrientation: "maxMin", catAxisLineShow: false });
  await filas(s, ["Ninguna técnica superó al entrenamiento sin balancear.", "SMOTE y ADASYN crean pedidos sintéticos que empeoran el resultado.", "Mejor: elegir bien el umbral y usar bandas de riesgo."], 6.35, 1.45, 3.15, 1.15, "FiAlertTriangle", "FCEFD0", AMBD, 14);
  add(s, "Balanceo", "La propuesta pedía probar undersampling, oversampling, SMOTE y ADASYN. Los probamos todos y el resultado fue claro: ninguno supera al entrenamiento sin balancear, y SMOTE y ADASYN empeoran bastante. Lo reportamos tal cual. En este problema funciona mejor ajustar el umbral y trabajar con bandas de riesgo.", 4);
  // 10
  s = pres.addSlide(); light(s, "USO PRÁCTICO", "Bandas de riesgo que sirven para decidir", 4);
  await figura(s, "f05_calibracion_bandas", .5, 1.3, 5.9, 3.65, "Calibración y bandas");
  const bandas = [["Alta: 33 % de retrasos", "con solo el 10 % de los pedidos", RED], ["Captura el 40 %", "de todos los retrasos (lift 4,06)", AMBD], ["Baja: 3 %", "de pedidos tardíos", TEAL]];
  for (let i = 0; i < 3; i++) { const y = 1.3 + i * 1.25; card(s, 6.6, y, 2.9, 1.1); s.addShape(pres.shapes.OVAL, { x: 6.8, y: y + .38, w: .34, h: .34, fill: { color: bandas[i][2] }, line: { color: bandas[i][2], width: 0 } });
    T(s, [{ text: bandas[i][0], options: { bold: true, color: NAVY, breakLine: true } }, { text: bandas[i][1], options: { color: MUT, fontSize: 12 } }], { x: 7.3, y, w: 2.1, h: 1.1, fontSize: 14, valign: "middle" }); }
  add(s, "Bandas", "Para uso práctico dividimos el riesgo en tres bandas. En la alta, que es el 10 por ciento de los pedidos, el 33 por ciento llega tarde, cuatro veces más que el promedio, y captura el 40 por ciento de todos los retrasos. En la baja solo llega tarde el 3 por ciento. La calibración es buena hasta el riesgo medio.", 4);
  // 11
  s = pres.addSlide(); light(s, "EXPLICABILIDAD", "No solo qué, también por qué", 5);
  await figura(s, "f07_importancias", .5, 1.3, 6.0, 3.65, "Importancias");
  await filas(s, ["Plazo prometido, destino y carga de la plataforma pesan más.", "SHAP exacto: la suma de aportes reproduce la probabilidad (error 3×10⁻⁷).", "LIME concuerda solo en parte: usamos SHAP."], 6.75, 1.45, 2.75, 1.15, "FiZap", SOFT, BLUE, 13);
  add(s, "Explicabilidad", "Mostramos tres miradas: importancia por permutación, SHAP y LIME. Las dos primeras coinciden: plazo prometido, destino y carga de la plataforma. SHAP es exacto, porque la suma de aportes reproduce la probabilidad. LIME coincide solo parcialmente con SHAP, incluso con un caso negativo, así que lo usamos como contraste y no como verdad.", 5);
  // 12
  s = pres.addSlide(); light(s, "MINERÍA DE TEXTOS", "Lo que dicen los clientes", 5);
  await figura(s, "f10_texto", .5, 1.3, 6.0, 3.65, "Texto");
  await filas(s, ["39 661 comentarios; TF-IDF + regresión logística: AUC 0,973.", "La entrega aparece en el 53 % de los comentarios.", "Devolución: poco mencionada, 75 % negativa.", "Riesgo alto: 39 % negativos (bajo: 20 %)."], 6.75, 1.4, 2.75, .9, "FiMessageSquare", SOFT, BLUE, 13);
  add(s, "Textos", "Analizamos casi 40 mil comentarios en portugués. Un clasificador de sentimiento llega a 0,973 de AUC. La entrega es lo que más mencionan, 53 por ciento, y devoluciones es poco frecuente pero muy negativo, 75 por ciento. Y cierra el círculo: los pedidos de riesgo alto reciben 39 por ciento de comentarios negativos contra 20 por ciento en riesgo bajo.", 5);
  // 13
  s = pres.addSlide(); light(s, "MONITOREO", "Un modelo se vigila: simulamos la operación", 0);
  await figura(s, "f12_monitoreo", .5, 1.3, 6.0, 3.0, "Monitoreo");
  card(s, .5, 4.45, 6.0, .55, "FDECEC", "alerta"); T(s, [{ text: "En el tiempo el AUC baja a 0,70 ", options: { bold: true, color: RED } }, { text: "(con partición aleatoria: 0,78)", options: { color: INK } }], { x: .7, y: 4.45, w: 5.7, h: .55, fontSize: 14, valign: "middle" });
  await filas(s, ["PSI > 0,25 en los 10 meses: deriva real.", "Reentrenar cada mes no superó al modelo congelado.", "28 versiones con hash SHA-256 y auditoría."], 6.75, 1.45, 2.75, 1.15, "FiActivity", SOFT, BLUE, 13);
  add(s, "Monitoreo", "No nos quedamos en describir el monitoreo: lo simulamos mes a mes con datos reales. Medimos deriva con PSI, definimos alertas y comparamos cuatro políticas de reentrenamiento. La conclusión es honesta: reentrenar todos los meses no mejora al modelo congelado, porque los choques, como noviembre de 2017 o la huelga de mayo de 2018, no se aprenden del pasado. Y al evaluar en el tiempo el AUC es 0,70, no 0,78. Cada versión queda registrada con hash SHA-256 y auditoría.", 0);
  // 14
  s = pres.addSlide(); light(s, "PRODUCTO", "El modelo corre en tu navegador", 1);
  await figura(s, "web_simulador", .5, 1.3, 5.9, 3.65, "Simulador en escritorio");
  card(s, 5.6, 2.0, 1.5, 3.05, WH, "teléfono"); await img(s, "web_movil_simulador", 5.67, 2.07, 1.36, 2.91, "Simulador en teléfono");
  await filas(s, ["10 secciones, modo Guiado y Experto, tema claro y oscuro.", "Simulador con etiqueta de envío y explicación.", "Publicado gratis en GitHub Pages."], 7.35, 1.45, 2.15, 1.15, "FiMonitor", SOFT, BLUE, 13);
  add(s, "Aplicación", "El producto es un panel web de diez secciones. Lo central es el simulador: describes un pedido y el modelo, que corre en tu propio navegador, calcula la probabilidad y explica qué factores la suben o bajan, presentado como una etiqueta de envío. Hay modo Guiado para no técnicos y modo Experto, y funciona en el celular. Aquí haremos una demostración en vivo.", 1);
  // 15
  s = pres.addSlide(); light(s, "CALIDAD", "Probado y desplegado sin costo", 2);
  await statCard(s, .5, 1.3, 2.9, 2.15, "FiCheckCircle", TEAL, "23", "pruebas automáticas, todas pasan");
  await statCard(s, 3.55, 1.3, 2.9, 2.15, "FiGitMerge", BLUE, "3×10⁻⁷", "diferencia máxima entre Python y JavaScript");
  await statCard(s, 6.6, 1.3, 2.9, 2.15, "FiShield", AMBD, "0", "errores de consola en escritorio y móvil");
  card(s, .5, 3.7, 9, 1.2, NAVY, "despliegue"); await circ(s, "FiGlobe", .75, 3.97, .65, AMB, NAVY);
  T(s, [{ text: "redsteinyt.github.io/datasmart-olist", options: { bold: true, color: WH, breakLine: true } }, { text: "API en Render, código en GitHub, respaldo en Netlify y un archivo HTML que se abre con doble clic.", options: { color: "CDD9E7", fontSize: 13 } }], { x: 1.6, y: 3.7, w: 7.7, h: 1.2, fontSize: 17, valign: "middle" });
  add(s, "Calidad", "Como el modelo se evalúa en dos lenguajes, verificamos que coincidan: la diferencia máxima es de tres por diez a la menos siete. Hay 23 pruebas automáticas y una prueba de navegador sin errores. Está publicado gratis en GitHub Pages, con la API en Render, y también hay un único archivo HTML que se abre con doble clic.", 2);
  // 16
  s = pres.addSlide(); light(s, "HONESTIDAD", "Limitaciones que reconocemos", 3);
  const lim = [["0,78 frente a 0,70", "La evaluación temporal es la expectativa realista", "FiClock"], ["Historia corta", "Menos de dos años: sin estacionalidad anual", "FiCalendar"], ["Poca recompra", "97 % compra una vez: reglas exploratorias", "FiRepeat"], ["Choques", "Noviembre de 2017 y la huelga de 2018 no se predicen", "FiCloudLightning"], ["Asociación", "Lo que mostramos no prueba causalidad", "FiLink"]];
  for (let i = 0; i < 5; i++) { const col = i < 3 ? 3 : 2, row = i < 3 ? 0 : 1, w = row === 0 ? 2.9 : 4.425, x = .5 + (i - (row ? 3 : 0)) * (w + .15), y = 1.3 + row * 1.85; card(s, x, y, w, 1.65);
    await circ(s, lim[i][2], x + .2, y + .22, .5, "FCEFD0", AMBD); T(s, lim[i][0], { x: x + .85, y: y + .25, w: w - 1, h: .45, fontFace: "Cambria", fontSize: 16, bold: true, color: NAVY, valign: "middle" });
    T(s, lim[i][1], { x: x + .2, y: y + .85, w: w - .4, h: .7, fontSize: 13, color: MUT }); }
  add(s, "Limitaciones", "Queremos ser claros con los límites. El número que mejor describe el futuro es 0,70 y no 0,78. La historia es corta, casi todos los clientes compran una vez, los choques no se anticipan con el pasado, y todo lo que mostramos son asociaciones, no causas.", 3);
  // 17
  s = pres.addSlide(); dark(s, true);
  T(s, "Conclusiones", { x: .6, y: .45, w: 8.8, h: .7, fontFace: "Cambria", fontSize: 34, bold: true, color: WH });
  const con = ["La logística conecta todo: entrega tardía, reseña baja y clientes insatisfechos.", "Se puede anticipar el retraso al comprar (0,78 aleatorio; 0,70 temporal) y explicar cada caso.", "Plazo prometido, destino y carga de la plataforma son los factores principales.", "Reentrenar no basta: hay que monitorear y anticipar los choques.", "Producto: panel web gratuito, explicable y probado."];
  await filas(s, con, .6, 1.4, 8.8, .66, "FiCheck", AMB, NAVY, 16, WH);
  T(s, "Trabajo futuro: calendario y huelgas, más años de datos, K-Medoids y modelos de supervivencia.", { x: .6, y: 4.75, w: 8.8, h: .4, fontSize: 14, color: "9FE0D6" });
  add(s, "Conclusiones", "Para cerrar: la logística conecta todos los resultados; se puede anticipar el retraso y explicarlo, aunque con la salvedad temporal; los factores principales son plazo, destino y carga; reentrenar no basta sin monitoreo y variables que anticipen choques; y entregamos un producto gratuito, explicable y probado. Como trabajo futuro, agregar calendario y huelgas y más años de datos. Gracias, quedamos atentos a sus preguntas.", 4);
  // 18
  s = pres.addSlide(); dark(s);
  await img(s, "logo.png", .6, .5, .62, .72, "Escudo UNMSM");
  T(s, "Gracias", { x: .6, y: 1.7, w: 8.8, h: 1.1, fontFace: "Cambria", fontSize: 60, bold: true, color: WH, valign: "middle" });
  T(s, "¿Preguntas?", { x: .6, y: 2.8, w: 8.8, h: .6, fontSize: 26, color: AMB });
  T(s, "Pruébalo: redsteinyt.github.io/datasmart-olist", { x: .6, y: 3.7, w: 5.6, h: .4, fontSize: 16, color: "CDD9E7" });
  s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x: 6.9, y: 1.35, w: 2.5, h: 2.8, fill: { color: CREAM }, line: { color: CREAM, width: 0 }, rectRadius: .14, shadow: { type: "outer", blur: 18, offset: 6, angle: 90, color: "000000", opacity: .45 }, objectName: "tarjeta QR" });
  s.addImage({ path: path.join(__dirname, "qr.png"), x: 7.25, y: 1.55, w: 1.8, h: 1.8, altText: "Código QR a la web" });
  T(s, "Escanea y pruébalo", { x: 6.9, y: 3.5, w: 2.5, h: .4, fontFace: "Cambria", fontSize: 16, bold: true, color: NAVY, align: "center" });
  T(s, "Grupo 4 · Minería de Datos · UNMSM, FISI", { x: .6, y: 4.95, w: 8.8, h: .3, fontSize: 11, color: "A9BBD1" });
  add(s, "Cierre", "Gracias. Estamos atentos a sus preguntas.", 5);
  // dark slides fixed overlay: on light slides chart text etc.
  await pres.writeFile({ fileName: path.resolve(__dirname, "../Presentacion_DataSmart_Grupo4.pptx") });
  fs.writeFileSync(path.resolve(__dirname, "guion.json"), JSON.stringify(guion, null, 1)); console.log("ok", guion.length);
})();
