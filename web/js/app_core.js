/* DataSmart - tablero (sin compilación). Secciones 1-5 y utilidades. */
const $ = (s, r = document) => r.querySelector(s), $$ = (s, r = document) => [...r.querySelectorAll(s)];
let D = {}; const SEC = [];
const guarda = (k, v) => { try { localStorage.setItem(k, v); } catch (e) { } }, lee = k => { try { return localStorage.getItem(k); } catch (e) { return null; } };
const G = t => `<div class="callout guia"><b>Cómo leerlo</b>${t}</div>`, X = t => `<div class="callout experto"><b>Detalle técnico</b>${t}</div>`, AL = t => `<div class="callout alerta"><b>Ojo</b>${t}</div>`;
const tabla = (cols, rows, mx) => `<div class="scroll" ${mx ? `style="max-height:${mx}px"` : ''}><table><thead><tr>${cols.map(c => `<th class="${c.n ? 'n' : ''}">${c.h}</th>`).join('')}</tr></thead><tbody>${rows.map(r => `<tr>${cols.map(c => `<td class="${c.n ? 'n' : ''}">${c.f(r)}</td>`).join('')}</tr>`).join('')}</tbody></table></div>`;
const kpi = (v, l, tag) => `<div class="card kpi"><div class="v">${v}</div><div class="l">${l}</div>${tag || ''}</div>`;
const ESTADOS = { AC: 'Acre', AL: 'Alagoas', AM: 'Amazonas', AP: 'Amapá', BA: 'Bahía', CE: 'Ceará', DF: 'Distrito Federal', ES: 'Espírito Santo', GO: 'Goiás', MA: 'Maranhão', MG: 'Minas Gerais', MS: 'Mato Grosso do Sul', MT: 'Mato Grosso', PA: 'Pará', PB: 'Paraíba', PE: 'Pernambuco', PI: 'Piauí', PR: 'Paraná', RJ: 'Río de Janeiro', RN: 'Río Grande do Norte', RO: 'Rondônia', RR: 'Roraima', RS: 'Río Grande do Sul', SC: 'Santa Catarina', SE: 'Sergipe', SP: 'São Paulo', TO: 'Tocantins' };
const CAT_ES = { health_beauty: 'Salud y belleza', watches_gifts: 'Relojes y regalos', bed_bath_table: 'Cama, baño y mesa', sports_leisure: 'Deportes y ocio', computers_accessories: 'Informática y accesorios', furniture_decor: 'Muebles y decoración', housewares: 'Artículos del hogar', cool_stuff: 'Novedades', auto: 'Automotor', toys: 'Juguetes', garden_tools: 'Herramientas de jardín', perfumery: 'Perfumería', telephony: 'Telefonía', baby: 'Bebés', stationery: 'Papelería', otras: 'Otras categorías', electronics: 'Electrónica', fashion_bags_accessories: 'Moda: bolsos y accesorios', pet_shop: 'Mascotas', office_furniture: 'Muebles de oficina', home_confort: 'Confort del hogar', luggage_accessories: 'Equipaje', consoles_games: 'Consolas y juegos', construction_tools_construction: 'Construcción' };
const cat = c => CAT_ES[c] || c.replace(/_/g, ' ');
const MESES = d3.timeParse('%Y-%m');

/* ---------- utilidades del simulador ---------- */
function haversine(a, b) { const r = x => x * Math.PI / 180, dl = r(b[0] - a[0]), dg = r(b[1] - a[1]), h = Math.sin(dl / 2) ** 2 + Math.cos(r(a[0])) * Math.cos(r(b[0])) * Math.sin(dg / 2) ** 2; return 12742 * Math.asin(Math.sqrt(h)); }
function rutaInfo(o, d) {
  const r = D.modelo.rutas.find(x => x.seller_state === o && x.customer_state === d);
  if (r) return { dist: r.dist, plazo: r.plazo, tarde: r.tarde, n: r.n, fuente: 'historial real' };
  const E = Object.fromEntries(D.resumen.estados.map(s => [s.customer_state, s])), a = E[o], b = E[d];
  return { dist: a && b ? haversine([a.lat, a.lng], [b.lat, b.lng]) : 600, plazo: b ? b.plazo : 23, tarde: null, n: 0, fuente: 'estimada por distancia entre estados' };
}
function entrada(o) { const R = D.modelo.rangos, i = {}; D.modelo.num.forEach(n => i[n] = R[n].med); Object.assign(i, { customer_state: 'SP', cat: 'health_beauty', seller_state: 'SP' }, o); i.mismo_estado = i.seller_state === i.customer_state ? 1 : 0; return i; }
function simular(inp, perm = 200) { const M = D.modelo, x = Modelo.vector(M, inp), p = Modelo.prob(M, x); return { p, banda: Modelo.banda(M, p), shap: perm ? Modelo.shapley(M, inp, perm, 1) : null }; }
const BANDA_TAG = { Bajo: 'ok', Medio: 'warn', Alto: 'bad' };
function medidor(p) { const M = D.modelo, mx = .4, a = M.q60 / mx * 100, b = M.q90 / mx * 100; return `<div class="medidor" style="background:linear-gradient(90deg,var(--lago) 0 ${a}%,var(--sol) ${a}% ${b}%,var(--brasa) ${b}%)"><i style="left:${Math.min(p, mx) / mx * 100}%"></i></div><div class="legend"><span>Bajo (&lt; ${fP(M.q60, 1)})</span><span>Medio</span><span>Alto (≥ ${fP(M.q90, 1)})</span></div>`; }
function etiqueta(inp, r, ruta) {
  const base = D.clasificacion.final.tasa_base;
  return `<div class="etiqueta" aria-live="polite"><div class="ruta"><span>${inp.seller_state}<i>${ESTADOS[inp.seller_state] || ''}</i></span><span style="font-size:1rem;color:var(--suave)">⟶ ${fN(inp.distancia_km)} km ⟶</span><span style="text-align:right">${inp.customer_state}<i>${ESTADOS[inp.customer_state] || ''}</i></span></div>
  <div style="display:flex;gap:16px;align-items:center;margin-top:10px"><div class="gran">${fP(r.p, 1)}</div><div><span class="tag ${BANDA_TAG[r.banda]}">Riesgo ${r.banda.toLowerCase()}</span><div class="mut" style="font-size:.88rem;margin-top:4px">de cada 100 pedidos como este, unos ${Math.round(r.p * 100)} llegarían tarde (promedio general: ${Math.round(base * 100)}).</div></div></div>${medidor(r.p)}<div class="barcode" aria-hidden="true"></div></div>`;
}
const selEstados = (id, v, lista) => `<select id="${id}" aria-label="${id}">${(lista || Object.keys(ESTADOS)).map(k => `<option value="${k}" ${k === v ? 'selected' : ''}>${k} · ${ESTADOS[k]}</option>`).join('')}</select>`;


function portadaProyecto() {
  const k = D.resumen.kpi;
  const eq = [['Luis Alejandro', 'Castro Contreras'], ['Yessly Josselyn', 'Poma de la Cruz'], ['Alan Nicolas', 'García Avalos'], ['Luis David', 'Morales Brenis'], ['Diego Steven Martin', 'Espinoza Picon'], ['Christian Piero', 'Guevara Laiza']];
  const col = ['#2563b8', '#0f8f6b', '#c98a00', '#d9423f', '#7a5cc7', '#138a99'];
  const tb = [['Pedidos', 99441, 1], ['Clientes', 99441], ['Ítems', 112650], ['Pagos', 103886], ['Reseñas', 99224], ['Productos', 32951], ['Vendedores', 3095], ['Geolocalización', 1000163], ['Categorías', 71]];
  const tec = [['Asociación', 'clientes', C.azul], ['Clustering', 'clientes', C.lago], ['Grafos', 'clientes', C.viol], ['Series temporales', 'pronostico', C.sol], ['Regresión', 'modelo', C.brasa], ['Clasificación', 'modelo', C.azul], ['Explicabilidad', 'explicacion', C.lago], ['Minería de textos', 'resenas', C.viol], ['Monitoreo', 'monitoreo', C.sol]];
  const pts = [[620, 70], [760, 150], [905, 95], [840, 300], [690, 250], [960, 230]], arc = (a, b, h) => `M${a[0]},${a[1]} Q${(a[0] + b[0]) / 2},${Math.min(a[1], b[1]) - h} ${b[0]},${b[1]}`;
  return `<header class="portada">
    <svg class="rutas" viewBox="0 0 1000 380" preserveAspectRatio="xMaxYMid slice" aria-hidden="true">
      <path d="${arc(pts[0], pts[1], 40)}"/><path d="${arc(pts[1], pts[2], 50)}"/><path d="${arc(pts[2], pts[5], 30)}"/><path d="${arc(pts[4], pts[3], 35)}"/><path d="${arc(pts[1], pts[4], 20)}"/>
      <path class="dibuja" style="stroke-dasharray:900;stroke-width:2.2" d="${arc(pts[0], pts[3], 55)}"/>${pts.map(q => `<circle cx="${q[0]}" cy="${q[1]}" r="4"/>`).join('')}</svg>
    <div class="inst"><img src="${window.LOGO_UNMSM || ''}" alt="Escudo de la Universidad Nacional Mayor de San Marcos"><div><b>Universidad Nacional Mayor de San Marcos</b><span>Facultad de Ingeniería de Sistemas e Informática · Escuela Profesional de Ingeniería de Software</span></div></div>
    <div class="portada-grid"><div>
      <p class="curso">Minería de Datos · Grupo 4 · Proyecto final</p>
      <h1>Data<em>Smart</em></h1>
      <p class="bajada">Plataforma inteligente para analizar, segmentar y predecir el comportamiento de clientes y pedidos, construida con los datos reales de Olist, un marketplace de Brasil.</p>
      <div class="acciones"><a class="btn sol" href="#probar" onclick="event.preventDefault();document.getElementById('probar').scrollIntoView({behavior:'smooth'})">Probar el modelo</a><a class="btn fant" href="#/panorama">Explorar los datos</a></div></div>
      <div class="guia-p" aria-label="Ficha del proyecto"><div class="cab"><b>Ficha del proyecto</b><span>Entregable 4 · 2026</span></div><dl>
        <dt>Curso</dt><dd>Minería de Datos</dd><dt>Equipo</dt><dd>Grupo 4 · 6 integrantes</dd>
        <dt>Dataset</dt><dd>Brazilian E-Commerce Public Dataset by Olist (Kaggle)</dd><dt>Periodo</dt><dd>sep. 2016 – ago. 2018</dd>
        <dt>Analizado</dt><dd>${fN(k.pedidos)} pedidos entregados</dd><dt>Método</dt><dd>CRISP-DM en 4 entregables</dd></dl><div class="barcode" aria-hidden="true"></div></div></div>
  </header>
  <section class="bloque"><h2>El equipo <small class="mut">Grupo 4</small></h2><div class="equipo">${eq.map((m, i) => `<div class="miembro"><div class="av" style="background:${col[i]};color:${col[i]}"><span style="color:#fff">${m[0][0]}${m[1][0]}</span></div><b>${m[0]}</b><span>${m[1]}</span></div>`).join('')}</div></section>
  <section class="bloque"><h2>Los datos</h2><div class="datos-grid"><div>
    <p>Olist conecta a pequeños vendedores con compradores de todo Brasil. Su conjunto público reúne cerca de <b>100 mil pedidos</b> hechos entre 2016 y 2018, con todo lo que pasa alrededor de cada uno: qué se compró, cuánto se pagó, desde dónde salió, cuándo llegó y qué opinó el cliente.</p>
    <p>Trabajamos con los <b>${fN(k.pedidos)} pedidos entregados</b>, de ${fN(k.clientes)} clientes y ${fN(k.vendedores)} vendedores, que suman ${fR(k.ingreso)} en ventas. La pregunta que guía todo el proyecto: <b>¿se puede saber, al momento de comprar, si un pedido llegará tarde?</b></p>
    <div class="tecnicas" style="margin-top:12px">${tec.map(t => `<a href="#/${t[1]}"><i style="background:${t[2]}"></i>${t[0]}</a>`).join('')}</div></div>
    <div><div class="tablas">${tb.map(t => `<div class="tabla-ch ${t[2] ? 'central' : ''}"><b>${t[0]}</b><span>${fN(t[1])} filas</span></div>`).join('')}</div><p class="mut" style="font-size:.82rem;margin-top:8px">Las 9 tablas del conjunto, unidas por el identificador del pedido, del cliente, del producto y del vendedor.</p></div></div></section>
  <section class="bloque"><h2>Cómo llegamos aquí</h2><ol class="ruta-ent">
    <li data-n="1"><b>Negocio y datos</b><span>Semana 7 · problema, KPIs, EDA y calidad</span></li>
    <li data-n="2"><b>Preparación</b><span>Semana 10 · dataset integrado y reglas de asociación</span></li>
    <li data-n="3"><b>Modelamiento</b><span>Semana 13 · segmentos, pronóstico, grafos y regresión</span></li>
    <li data-n="4" class="hoy"><b>Producto final</b><span>Semana 16 · clasificación, textos, explicabilidad, monitoreo y esta web</span></li></ol></section>
  <div class="separa" id="probar"><span>Pruébalo tú mismo</span></div>`;
}

/* ---------- 1. Inicio ---------- */
SEC.push({
  id: 'inicio', t: 'Inicio', i: '⌂', render(el) {
    const k = D.resumen.kpi, R = D.resumen, cl = D.clasificacion, ml = D.monitoreo.temporal;
    el.innerHTML = portadaProyecto() + `<div class="hero"><div><h2 class="grande">¿Llegará a tiempo este pedido?</h2>
      <p class="lead">Con 96 mil pedidos reales de Olist (Brasil, 2016–2018) construimos un modelo que estima el riesgo de entrega tardía <b>antes de que ocurra</b>. Cambia la ruta y el plazo prometido y míralo funcionar, aquí mismo, sin servidor.</p>
      <div class="grid g2" style="margin:8px 0"><label class="f">Sale desde${selEstados('h-o', 'SP', D.modelo.rutas.map(r => r.seller_state).filter((v, i, a) => a.indexOf(v) === i).sort())}</label><label class="f">Llega a${selEstados('h-d', 'RJ')}</label>
      <label class="f"><span>Plazo prometido al cliente: <b id="h-pv"></b> días</span><input type="range" id="h-p" min="4" max="60" step="1"></label>
      <label class="f"><span>Carga de la plataforma: <b id="h-cv"></b></span><input type="range" id="h-c" min="0.6" max="3" step="0.05" value="1.1"></label></div>
      <div id="h-et"></div><p class="mut" style="font-size:.84rem;margin-top:8px" id="h-nota"></p></div>
      <div class="card" style="padding:8px"><div id="h-mapa"></div><div class="legend" style="padding:0 8px 6px"><span><i style="background:#1c4f95"></i>más pedidos tardíos en el destino</span><span><i style="background:#e6eef7"></i>menos</span></div></div></div>
      ${G('El modelo no “adivina”: combina la ruta, el plazo prometido, el historial del vendedor y qué tan cargada está la plataforma esa semana. Mueve los controles y mira cómo cambia el riesgo.')}
      <div class="grid g4" style="margin:18px 0">${kpi(fN(k.pedidos), 'pedidos entregados analizados')}${kpi(fR(k.ingreso), 'ingreso total pagado')}${kpi(fP(k.pct_tardias), 'llegan después de la fecha prometida', '<span class="tag warn">el problema a resolver</span>')}${kpi(fD(k.puntaje, 2) + ' / 5', 'puntaje medio de reseñas')}</div>
      <h2>Lo que descubrimos</h2><div class="grid g3">
      <div class="card"><h3>El retraso cuesta reputación</h3><p>Los pedidos tardíos reciben reseña baja (1–2 estrellas) en el <b>${fP(R.tardia_puntaje.find(d => d.entrega_tardia === 1).pct_baja, 0)}</b> de los casos; los puntuales, solo en el <b>${fP(R.tardia_puntaje.find(d => d.entrega_tardia === 0).pct_baja, 0)}</b>.</p></div>
      <div class="card"><h3>Se puede anticipar, con límites</h3><p>En la prueba aleatoria el modelo logra AUC ${fD(cl.final.final.AUC_ROC, 2)}. Con validación temporal (abril–agosto 2018) baja a ${fD(ml.AUC_ROC, 2)}: los picos de demanda y las huelgas no se predicen solos.</p></div>
      <div class="card"><h3>Lo que más pesa</h3><p>El plazo prometido, la carga reciente de la plataforma y el estado del comprador. La distancia importa, pero menos de lo que parece.</p></div>
      <div class="card"><h3>Las reseñas lo confirman</h3><p>Leyendo ${fN(D.texto.resumen.n_resenas)} comentarios en portugués, “no recibí” y “aguardando” son las señales más fuertes de un mal servicio.</p></div>
      <div class="card"><h3>Un modelo se vigila</h3><p>La plataforma cambió tanto que el modelo necesita monitoreo: medimos la deriva (PSI), definimos alertas y comparamos 4 políticas de reentrenamiento.</p></div>
      <div class="card"><h3>Todo es reproducible</h3><p>Datos, código, pruebas automáticas y despliegue gratuito están en el repositorio. Cada cifra de este tablero sale de un script.</p></div></div>
      <h2 style="margin-top:26px">Cómo recorrer el tablero</h2><ol class="pasos"><li><div><b>Panorama y Mapa</b>: qué vende la plataforma y dónde se retrasan los envíos.</div></li><li><div><b>Clientes y Pronóstico</b>: segmentos, qué se compra junto y cuánto se venderá.</div></li><li><div><b>Simulador</b>: calcula el riesgo de un pedido y mira por qué.</div></li><li><div><b>Modelo y Explicación</b>: cómo de bueno es y qué factores usa.</div></li><li><div><b>Reseñas y Monitoreo</b>: qué dicen los clientes y cómo cuidar el modelo en el tiempo.</div></li></ol>
      <footer><b>Proyecto DataSmart · Minería de Datos · UNMSM – FISI, Ingeniería de Software · Grupo 4.</b> Equipo: Luis Alejandro Castro Contreras, Yessly Josselyn Poma de la Cruz, Alan Nicolas García Avalos, Luis David Morales Brenis, Diego Steven Martin Espinoza Picon y Christian Piero Guevara Laiza. Datos: Brazilian E-Commerce Public Dataset by Olist (Kaggle, CC BY-NC-SA 4.0). Mapa: @svg-maps/brazil (CC BY 4.0).</footer>`;
    const mapa = mapaBrasil('#h-mapa', Object.fromEntries(R.estados.map(s => [s.customer_state, s.pct_tardias])), { rampa: ['#eaf1f8', '#9bc0e8', '#1c4f95'], fmt: v => fP(v), alt: 'Mapa de riesgo por estado y ruta del pedido simulado' });
    const arco = mapa.svg.append('path').attr('class', 'ruta-linea');
    let manual = false; const upd = (cambioRuta) => {
      const o = $('#h-o').value, d = $('#h-d').value, ri = rutaInfo(o, d); if (cambioRuta) { $('#h-p').value = Math.round(ri.plazo); }
      const inp = entrada({ seller_state: o, customer_state: d, distancia_km: ri.dist, dias_estimados: +$('#h-p').value, carga_rel: +$('#h-c').value });
      $('#h-pv').textContent = inp.dias_estimados; $('#h-cv').textContent = fD(inp.carga_rel, 2) + (inp.carga_rel > 1.4 ? ' (pico)' : inp.carga_rel < .9 ? ' (calma)' : ' (normal)');
      $('#h-et').innerHTML = etiqueta(inp, simular(inp, 0)); $('#h-nota').textContent = `Distancia y plazo típicos de esta ruta: ${ri.fuente}${ri.n ? ' (' + fN(ri.n) + ' pedidos)' : ''}. El resto de datos del pedido se toma como típico.`;
      const a = mapa.centros[o], b = mapa.centros[d]; if (a && b) { const mx = (a[0] + b[0]) / 2, my = (a[1] + b[1]) / 2 - Math.hypot(a[0] - b[0], a[1] - b[1]) * .25; arco.attr('d', `M${a[0]},${a[1]} Q${mx},${my} ${b[0]},${b[1]}`); }
    };
    $('#h-p').value = Math.round(rutaInfo('SP', 'RJ').plazo); upd(false);
    $('#h-o').onchange = () => upd(true); $('#h-d').onchange = () => upd(true); $('#h-p').oninput = () => upd(false); $('#h-c').oninput = () => upd(false);
  }
});

/* ---------- 2. Panorama ---------- */
SEC.push({
  id: 'panorama', t: 'Panorama', i: '▤', render(el) {
    const R = D.resumen, k = R.kpi, ms = R.mensual.map(d => ({ x: MESES(d.mes), ...d }));
    el.innerHTML = `<h2>Panorama del negocio</h2><p class="lead">Qué se vende, cuánto crece y cómo califican los clientes. Periodo: ${k.periodo[0]} a ${k.periodo[1]}.</p>
    <div class="grid g4">${kpi(fN(k.clientes), 'clientes únicos')}${kpi(fR(k.ticket).replace(' mil', ' '), 'ticket medio por pedido')}${kpi(fD(k.dias_entrega, 1) + ' días', 'tiempo medio de entrega')}${kpi(fN(k.vendedores), 'vendedores registrados')}</div>
    <div class="grid g2" style="margin-top:16px"><div class="card"><h3>Ingreso y pedidos por mes</h3><p class="sub">Crecimiento sostenido, con el pico de noviembre de 2017 (Black Friday).</p><div class="chips" id="p-met"><button class="chip" aria-pressed="true" data-m="ingreso">Ingreso</button><button class="chip" aria-pressed="false" data-m="pedidos">Pedidos</button><button class="chip" aria-pressed="false" data-m="pct_tardias">% tardíos</button></div><div id="p-mes"></div>${G('Cada punto es un mes. Cambia entre ingreso, número de pedidos y porcentaje de entregas tardías: noviembre de 2017 y marzo de 2018 sobresalen.')}</div>
    <div class="card"><h3>Categorías que más ingresan</h3><p class="sub">Las 15 mayores, en reales brasileños.</p><div id="p-cat"></div></div></div>
    <div class="grid g3" style="margin-top:16px"><div class="card"><h3>Puntaje de las reseñas</h3><p class="sub">La mayoría satisface; el 1 es el segundo grupo más grande.</p><div id="p-pun"></div></div>
    <div class="card"><h3>Entregar más lento, calificar peor</h3><p class="sub">% de reseñas de 1–2 estrellas según días de entrega.</p><div id="p-ent"></div></div>
    <div class="card"><h3>Distancia y retraso</h3><p class="sub">% de pedidos tardíos por décil de distancia vendedor–comprador (km).</p><div id="p-dist"></div></div></div>
    ${X('Unidad de análisis: pedido entregado (96 469). Ingreso = suma de pagos. “Tardío” = entregado después de la fecha estimada. Distancia: Haversine entre la mediana de coordenadas del prefijo postal del vendedor y del comprador.')}`;
    const draw = m => { const f = { ingreso: fR, pedidos: fN, pct_tardias: v => fP(v) }[m]; lineas('#p-mes', [{ name: { ingreso: 'Ingreso', pedidos: 'Pedidos', pct_tardias: '% tardíos' }[m], color: C.azul, puntos: true, pts: ms.map(d => ({ x: d.x, y: d[m] })) }], { fy: f, fx: d3.timeFormat('%b %y'), h: 250, l: 58 }); };
    draw('ingreso'); $$('#p-met .chip').forEach(b => b.onclick = () => { $$('#p-met .chip').forEach(x => x.setAttribute('aria-pressed', x === b)); draw(b.dataset.m); });
    barrasH('#p-cat', R.categorias.map(d => ({ ...d, n: cat(d.categoria_principal) })), { x: 'ingreso', y: 'n', l: 135, fmt: fR, paso: 22, tip: d => `<b>${d.n}</b><br>${fN(d.pedidos)} pedidos · ${fP(d.pct_tardias)} tardíos · puntaje ${fD(d.puntaje, 2)}` });
    barrasV('#p-pun', R.puntajes.map(d => ({ e: d.review_score + '★', n: d.resenas })), { x: 'e', y: 'n', h: 230, fmt: fN, color: d => d.e < '3' ? C.brasa : d.e > '3' ? C.lago : C.sol });
    barrasV('#p-ent', R.entrega_puntaje, { x: 'rango', y: 'pct_baja', h: 230, fmt: v => fP(v, 0), valores: true, color: d => d3.interpolateRgb('#6aa4e6', '#d9423f')(Math.min(1, d.pct_baja * 1.6)) });
    barrasV('#p-dist', R.distancia_deciles.map(d => ({ ...d, k: fN(d.dist) })), { x: 'k', y: 'pct_tardias', h: 230, fmt: v => fP(v, 0), tip: d => `A ${d.k} km: ${fP(d.pct_tardias)} tardíos · ${fD(d.dias, 1)} días` });
  }
});

/* ---------- 3. Mapa ---------- */
SEC.push({
  id: 'mapa', t: 'Mapa', i: '◍', render(el) {
    const R = D.resumen, E = Object.fromEntries(R.estados.map(s => [s.customer_state, s]));
    const MET = [['pct_tardias', '% entregas tardías', v => fP(v), ['#eaf6f0', '#f0c060', '#c0302d']], ['dias', 'Días de entrega', v => fD(v, 1), ['#eaf1f8', '#7fb0e6', '#1c4f95']], ['pedidos', 'Pedidos', fN, ['#eaf1f8', '#7fb0e6', '#1c4f95']], ['ingreso', 'Ingreso', fR, ['#eaf1f8', '#7fb0e6', '#1c4f95']], ['puntaje', 'Puntaje medio', v => fD(v, 2), ['#c0302d', '#f0c060', '#eaf6f0']], ['distancia', 'Distancia mediana (km)', fN, ['#eaf1f8', '#7fb0e6', '#1c4f95']]];
    el.innerHTML = `<h2>Dónde se retrasan los envíos</h2><p class="lead">El mapa colorea cada estado de destino. Toca un estado para ver sus números.</p>
    <div class="chips" id="m-met">${MET.map((m, i) => `<button class="chip" aria-pressed="${i === 0}" data-k="${m[0]}">${m[1]}</button>`).join('')}</div>
    <div class="grid g21" style="margin-top:12px"><div class="card"><div id="m-map"></div><div class="legend" id="m-leg"></div>${G('Los estados del norte y nordeste están lejos del polo vendedor (São Paulo) y tardan más. Cambia de métrica para ver distintos ángulos.')}</div>
    <div class="grid" style="align-content:start"><div class="card" id="m-det"></div><div class="card"><h3>Ranking</h3><div id="m-tab"></div></div></div></div>
    <div class="card" style="margin-top:16px"><h3>Malla geográfica de pedidos</h3><p class="sub">Cada círculo agrupa pedidos en cuadrículas de ~0,9°: tamaño = volumen, color = % tardíos. Las zonas rojas se concentran en el nordeste y el norte.</p><div id="m-grid"></div>${X('Coordenadas por mediana de lat/lng del prefijo postal (tabla de geolocalización limpiada: 261 831 duplicados y 42 puntos fuera de Brasil eliminados).')}</div>`;
    let met = 'pct_tardias', sel = 'SP';
    const det = () => { const s = E[sel]; $('#m-det').innerHTML = `<h3>${ESTADOS[sel]} (${sel})</h3><p class="mut">Destino de ${fN(s.pedidos)} pedidos</p><div class="grid g2"><div><div class="mut">% tardíos</div><b class="num" style="font-size:1.3rem">${fP(s.pct_tardias)}</b></div><div><div class="mut">Días de entrega</div><b class="num" style="font-size:1.3rem">${fD(s.dias, 1)}</b></div><div><div class="mut">Plazo prometido</div><b class="num" style="font-size:1.3rem">${fD(s.plazo, 0)} d</b></div><div><div class="mut">Puntaje</div><b class="num" style="font-size:1.3rem">${fD(s.puntaje, 2)}</b></div><div><div class="mut">Distancia</div><b class="num" style="font-size:1.3rem">${fN(s.distancia)} km</b></div><div><div class="mut">Ingreso</div><b class="num" style="font-size:1.3rem">${fR(s.ingreso)}</b></div></div>`; };
    const draw = () => { const m = MET.find(x => x[0] === met), v = Object.fromEntries(R.estados.map(s => [s.customer_state, s[met]]));
      const mp = mapaBrasil('#m-map', v, { rampa: m[3], fmt: m[2], tip: d => `<b>${d.nombre}</b><br>${m[1]}: ${m[2](v[d.id])}<br>${fN(E[d.id].pedidos)} pedidos`, click: d => { sel = d.id; det(); mp.gs.selectAll('path.e').classed('sel', x => x.id === sel); }, alt: m[1] + ' por estado' });
      mp.gs.selectAll('path.e').classed('sel', x => x.id === sel); const dm = d3.extent(Object.values(v)); $('#m-leg').innerHTML = `<span><i style="background:${m[3][0]}"></i>${m[2](dm[0])}</span><span><i style="background:${m[3][2]}"></i>${m[2](dm[1])}</span>`;
      $('#m-tab').innerHTML = tabla([{ h: 'Estado', f: s => s.customer_state + ' · ' + ESTADOS[s.customer_state] }, { h: m[1], n: 1, f: s => m[2](s[met]) }], [...R.estados].sort((a, b) => b[met] - a[met]), 300); det(); };
    draw(); $$('#m-met .chip').forEach(b => b.onclick = () => { $$('#m-met .chip').forEach(x => x.setAttribute('aria-pressed', x === b)); met = b.dataset.k; draw(); });
    const L = lienzo('#m-grid', 700, 520, { l: 10, r: 10, t: 10, b: 10 }), gx = d3.extent(R.grilla, d => d.gx), gy = d3.extent(R.grilla, d => d.gy), s = Math.min(L.W / (gx[1] - gx[0] + 2), L.H / (gy[1] - gy[0] + 2)), r = d3.scaleSqrt([8, d3.max(R.grilla, d => d.n)], [2.5, 16]), col = d3.scaleSequential(d3.interpolateRgbBasis(['#7fb0e6', '#f0c060', '#c0302d'])).domain([.03, .2]).clamp(true);
    L.g.selectAll('circle').data(R.grilla).join('circle').attr('cx', d => (d.gx - gx[0] + 1) * s).attr('cy', d => (gy[1] - d.gy + 1) * s).attr('r', d => r(d.n)).attr('fill', d => col(d.tard)).attr('fill-opacity', .75).attr('stroke', '#fff').attr('stroke-width', .5)
      .on('mousemove', (e, d) => tt.show(`${fN(d.n)} pedidos<br><b>${fP(d.tard)}</b> tardíos · ${fD(d.dias, 1)} días`, e)).on('mouseleave', tt.hide);
  }
});

/* ---------- 4. Clientes ---------- */
SEC.push({
  id: 'clientes', t: 'Clientes', i: '◉', render(el) {
    const E = D.entregable23;
    el.innerHTML = `<h2>Clientes: segmentos, compras conjuntas y red de categorías</h2><p class="lead">Tres miradas sobre a quién le vende la plataforma y qué compra.</p>
    <div class="chips" id="c-tab"><button class="chip" aria-pressed="true" data-t="seg">Segmentos (K-Means)</button><button class="chip" aria-pressed="false" data-t="reg">Qué se compra junto</button><button class="chip" aria-pressed="false" data-t="red">Red de categorías</button></div><div id="c-cont" style="margin-top:12px"></div>`;
    const NOM = ['Compradores únicos de ticket medio', 'Clientes recientes', 'Clientes de alto valor', 'Clientes recurrentes'];
    const vistas = {
      seg() {
        const P = E.perfil; $('#c-cont').innerHTML = `<div class="grid g21"><div class="card"><h3>Mapa de clientes (PCA)</h3><p class="sub">Cada punto es un cliente; el color es su segmento. Los ejes resumen 5 medidas (recencia, frecuencia, monto, reseña, entrega).</p><div id="c-pca"></div><div class="legend" id="c-leg"></div>${G('Los segmentos se separan porque los clientes se parecen en cuándo compraron, cuánto gastaron y cuántas veces. Pasa el cursor por la tabla para entender cada grupo.')}</div>
        <div class="card"><h3>Perfil de cada segmento</h3>${tabla([{ h: 'Seg.', f: p => `<span style="color:${PAL[p.cluster_kmeans]}">●</span> ${p.cluster_kmeans + 1}` }, { h: 'Clientes', n: 1, f: p => fN(p.clientes) }, { h: 'Recencia (d)', n: 1, f: p => fN(p.recencia) }, { h: 'Frec.', n: 1, f: p => fD(p.frecuencia, 2) }, { h: 'Monto', n: 1, f: p => 'R$ ' + fN(p.monetario) }, { h: '% ingreso', n: 1, f: p => fD(p.pct_ingreso, 1) }], P)}<p class="sub" style="margin-top:8px">k = 4 elegido por silueta (${fD(E.k.find(k => k.k === 4).silhouette, 3)}); comparado con jerárquico Ward y DBSCAN.</p></div></div>
        <div class="grid g2" style="margin-top:16px"><div class="card"><h3>¿Cuántos segmentos?</h3><div id="c-k"></div>${X('La silueta es máxima en k=5 (0,254); se eligió k=4 (0,238, Davies-Bouldin 1,26) porque los segmentos se interpretan mejor para el negocio. DBSCAN deja entre 6 % y 64 % de ruido según eps.')}</div><div class="card"><h3>Comparación de algoritmos</h3>${tabla([{ h: 'Modelo', f: c => c.modelo }, { h: 'Silueta', n: 1, f: c => fD(c.silhouette, 3) }, { h: 'Davies-B.', n: 1, f: c => fD(c.davies_bouldin, 2) }, { h: '% ruido', n: 1, f: c => fD(c.ruido * 100, 0) }], E.clus_comp)}</div></div>`;
        dispersion('#c-pca', E.pca, { x: 'pc1', y: 'pc2', color: d => PAL[d.cluster], lx: 'Componente 1', ly: 'Componente 2', h: 330, fx: d => '', fy: d => '' }); leyenda('#c-leg', P.map(p => [`Seg. ${p.cluster_kmeans + 1} (${fP(p.pct_clientes / 100, 0)} de clientes)`, PAL[p.cluster_kmeans]]));
        lineas('#c-k', [{ name: 'Silueta', color: C.lago, puntos: true, pts: E.k.map(d => ({ x: d.k, y: d.silhouette })) }], { fy: v => fD(v, 2), h: 220, lx: 'número de segmentos k' });
      },
      reg() {
        const r = E.reglas.slice().sort((a, b) => b.lift - a.lift); $('#c-cont').innerHTML = `<div class="grid g21"><div class="card"><h3>Combinaciones de categorías que se compran juntas</h3><p class="sub">Solo ${fN(E.param[0].canastas_multicategoria)} de ${fN(E.param[0].clientes_totales)} clientes compraron en 2 o más categorías (2,4 %): el negocio es mayormente de una sola compra.</p>${tabla([{ h: 'Si compra…', f: x => cat(x.antecedente) }, { h: '…también compra', f: x => cat(x.consecuente) }, { h: 'Soporte', n: 1, f: x => fP(x.support, 2) }, { h: 'Confianza', n: 1, f: x => fP(x.confidence, 0) }, { h: 'Lift', n: 1, f: x => fD(x.lift, 1) }, { h: 'Clientes', n: 1, f: x => x.n_clientes }], r, 420)}${G('<b>Lift</b> mayor que 1 significa que la combinación ocurre más de lo que esperaríamos por azar. Por ejemplo, un lift de 3 = tres veces más frecuente.')}</div>
        <div class="card"><h3>Tres algoritmos, mismas reglas</h3>${tabla([{ h: 'Algoritmo', f: a => a.algoritmo }, { h: 'Conjuntos', n: 1, f: a => a.itemsets_frecuentes }, { h: 'Reglas', n: 1, f: a => a.reglas }, { h: 'Tiempo (s)', n: 1, f: a => fD(a.tiempo_s, 3) }], E.alg)}<p class="sub" style="margin-top:8px">Apriori, FP-Growth y ECLAT producen exactamente los mismos conjuntos (soporte mín. ${fP(E.param[0].min_support, 1)}, confianza mín. ${fP(E.param[0].min_confidence, 0)}).</p></div></div>`;
      },
      red() {
        const g = E.grafo[0]; $('#c-cont').innerHTML = `<div class="grid g21"><div class="card"><h3>Red de categorías</h3><p class="sub">Cada nodo es una categoría; el grosor de la línea es la cantidad de clientes que compraron en ambas. El color es su comunidad.</p><div id="c-red"></div></div>
        <div class="card"><h3>Qué mide la red</h3><div class="grid g2"><div><div class="mut">Nodos</div><b class="num" style="font-size:1.3rem">${g.nodos}</b></div><div><div class="mut">Aristas</div><b class="num" style="font-size:1.3rem">${g.aristas}</b></div><div><div class="mut">Densidad</div><b class="num" style="font-size:1.3rem">${fD(g.densidad, 2)}</b></div><div><div class="mut">Modularidad</div><b class="num" style="font-size:1.3rem">${fD(g.modularidad, 2)}</b></div></div>${G('Modularidad baja (0,17) = las categorías no forman bloques muy aislados: un cliente que compra en una puede comprar en cualquiera.')}<h3 style="margin-top:12px">Categorías más influyentes</h3>${tabla([{ h: 'Categoría', f: n => cat(n.categoria) }, { h: 'PageRank', n: 1, f: n => fD(n.pagerank, 3) }, { h: 'Clientes', n: 1, f: n => fN(n.clientes) }], E.nodos.slice().sort((a, b) => b.pagerank - a.pagerank).slice(0, 8))}</div></div>`;
        red('#c-red', E.nodos, E.aristas);
      }
    };
    const go = t => { $$('#c-tab .chip').forEach(x => x.setAttribute('aria-pressed', x.dataset.t === t)); vistas[t](); }; $$('#c-tab .chip').forEach(b => b.onclick = () => go(b.dataset.t)); go('seg');
  }
});

/* ---------- 5. Pronóstico ---------- */
SEC.push({
  id: 'pronostico', t: 'Pronóstico', i: '↗', render(el) {
    const E = D.entregable23, f = d3.timeParse('%Y-%m-%d'), h = E.pron_h;
    el.innerHTML = `<h2>Pronóstico de ventas</h2><p class="lead">Ventas diarias hasta agosto de 2018 y pronóstico de los 90 días siguientes con el mejor modelo (Ridge con rezagos, MAPE ${fD(E.s_comp[0].MAPE, 1)} %).</p>
    <div class="card"><h3>Ventas diarias y pronóstico a 90 días</h3><div id="s-main"></div><div class="legend" id="s-leg"></div>${G('La línea azul es lo que ocurrió; la verde punteada es lo que el modelo espera para los próximos 90 días. La franja amarilla marca noviembre, cuando las ventas suelen dispararse.')}</div>
    <div class="grid g2" style="margin-top:16px"><div class="card"><h3>Prueba con los últimos 30 días</h3><p class="sub">Se ocultaron al modelo y se compararon con la realidad.</p><div id="s-hold"></div><div class="legend" id="s-hl"></div></div>
    <div class="card"><h3>Comparación de modelos</h3>${tabla([{ h: 'Modelo', f: m => m.modelo }, { h: 'MAE (R$)', n: 1, f: m => fN(m.MAE) }, { h: 'MAPE', n: 1, f: m => fD(m.MAPE, 1) + ' %' }, { h: 'sMAPE', n: 1, f: m => fD(m.sMAPE, 1) + ' %' }], E.s_comp)}<h3 style="margin-top:12px">Ventas esperadas</h3>${tabla([{ h: 'Horizonte', f: x => x.horizonte_dias + ' días' }, { h: 'Ventas', n: 1, f: x => fR(x['ventas_pronosticadas_BRL']) }, { h: 'Promedio diario', n: 1, f: x => fR(x.promedio_diario) }], h)}${X('Rezagos 1–28 días, media móvil, calendario. Validación con ventana final de 30 días. Holt-Winters (m=7) y GB con rezagos como comparación. SARIMA/Prophet se ejecutan en Colab (script 05b).')}</div></div>`;
    const real = E.serie.map(d => ({ x: f(d.fecha), y: d.ventas })), pr = E.pron.map(d => ({ x: f(d.fecha), y: d.pronostico }));
    lineas('#s-main', [{ name: 'Ventas reales', color: C.azul, pts: real, w: 1.4 }, { name: 'Pronóstico 90 días', color: C.lago, dash: '6 4', pts: pr, w: 2.4 }], { fy: fR, fx: d3.timeFormat('%b %y'), h: 290, l: 62, bandas: [{ x0: new Date('2017-11-01'), x1: new Date('2017-11-30') }] }); leyenda('#s-leg', [['Real', C.azul], ['Pronóstico', C.lago], ['Noviembre', C.sol]]);
    const mods = ['real', 'Ridge con rezagos', 'Holt-Winters (m=7)', 'Naive estacional (sem.)'], cols = [C.ink, C.lago, C.sol, C.brasa];
    lineas('#s-hold', mods.map((m, i) => ({ name: m === 'real' ? 'Real' : m, color: cols[i], w: i ? 1.8 : 2.8, dash: i > 1 ? '4 3' : null, pts: E.holdout.map(d => ({ x: f(d.fecha), y: d[m] })) })), { fy: fR, fx: d3.timeFormat('%d %b'), h: 250, l: 62 }); leyenda('#s-hl', mods.map((m, i) => [m === 'real' ? 'Real' : m, cols[i]]));
  }
});
