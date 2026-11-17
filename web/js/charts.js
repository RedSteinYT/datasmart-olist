/* Gráficos con D3 (sin dependencias de compilación). Todos responsivos mediante viewBox. */
const C = { lago: '#0f8f6b', sol: '#e8a900', brasa: '#d9423f', azul: '#2563b8', viol: '#7a5cc7', gris: '#8796a8', ink: '#0b1f3a' };
const PAL = [C.azul, C.lago, C.sol, C.brasa, C.viol, '#16a6b6', '#c25b9b', '#7a8b3c'];
const fN = n => n == null ? '–' : Math.round(n).toLocaleString('es-PE');
const fD = (n, d = 1) => n == null ? '–' : n.toLocaleString('es-PE', { minimumFractionDigits: d, maximumFractionDigits: d });
const fP = (n, d = 1) => n == null ? '–' : (n * 100).toLocaleString('es-PE', { minimumFractionDigits: d, maximumFractionDigits: d }) + ' %';
const fR = n => n == null ? '–' : 'R$ ' + (Math.abs(n) >= 1e6 ? fD(n / 1e6, 2) + ' M' : Math.abs(n) >= 1e3 ? fD(n / 1e3, 1) + ' mil' : fD(n, 0));
const fPP = n => (n >= 0 ? '+' : '−') + fD(Math.abs(n) * 100, 1) + ' pp';
const tt = (() => { let el; return { show(html, ev) { if (!el) { el = document.createElement('div'); el.className = 'tt'; document.body.appendChild(el); } el.innerHTML = html; el.style.display = 'block'; const x = Math.min(ev.clientX + 14, innerWidth - 270); el.style.left = x + 'px'; el.style.top = (ev.clientY + 14) + 'px'; }, hide() { if (el) el.style.display = 'none'; } }; })();
function lienzo(sel, w, h, m = {}) {
  const el = typeof sel === 'string' ? document.querySelector(sel) : sel; el.innerHTML = '';
  const M = { t: 10, r: 14, b: 30, l: 46, ...m }, svg = d3.select(el).append('svg').attr('viewBox', `0 0 ${w} ${h}`).attr('width', '100%').attr('role', 'img');
  return { svg, g: svg.append('g').attr('transform', `translate(${M.l},${M.t})`), W: w - M.l - M.r, H: h - M.t - M.b, M, el };
}
function ejes(L, x, y, o = {}) {
  if (o.gridY !== false) L.g.append('g').attr('class', 'grid').call(d3.axisLeft(y).ticks(5).tickSize(-L.W).tickFormat(''));
  L.g.append('g').attr('class', 'axis').attr('transform', `translate(0,${L.H})`).call(d3.axisBottom(x).ticks(o.nx || 6).tickFormat(o.fx || null).tickSizeOuter(0));
  L.g.append('g').attr('class', 'axis').call(d3.axisLeft(y).ticks(5).tickFormat(o.fy || null).tickSizeOuter(0));
  if (o.ly) L.svg.append('text').attr('x', 4).attr('y', 10).text(o.ly);
  if (o.lx) L.svg.append('text').attr('x', L.M.l + L.W / 2).attr('y', L.H + L.M.t + L.M.b - 2).attr('text-anchor', 'middle').text(o.lx);
}
function barrasH(sel, data, o) {
  const k = o.x, n = data.length, h = Math.max(120, n * (o.paso || 26) + 30), L = lienzo(sel, 640, h, { l: o.l || 150, r: 50, b: 22, t: 4 });
  const x = d3.scaleLinear([0, o.max || d3.max(data, d => d[k]) * 1.05], [0, L.W]), y = d3.scaleBand(data.map(d => d[o.y]), [0, L.H]).padding(.28);
  L.g.append('g').attr('class', 'axis').call(d3.axisLeft(y).tickSize(0)).select('.domain').remove();
  L.g.append('g').attr('class', 'axis').attr('transform', `translate(0,${L.H})`).call(d3.axisBottom(x).ticks(4).tickFormat(o.fmt || null));
  L.g.selectAll('rect').data(data).join('rect').attr('x', 0).attr('y', d => y(d[o.y])).attr('height', y.bandwidth()).attr('rx', 3).attr('width', d => Math.max(0, x(d[k]))).attr('fill', d => o.color ? o.color(d) : C.azul)
    .on('mousemove', (e, d) => o.tip && tt.show(o.tip(d), e)).on('mouseleave', tt.hide);
  L.g.selectAll('.v').data(data).join('text').attr('class', 'v t').attr('x', d => x(d[k]) + 4).attr('y', d => y(d[o.y]) + y.bandwidth() / 2 + 4).text(d => (o.fmt || fN)(d[k]));
}
function barrasV(sel, data, o) {
  const L = lienzo(sel, 640, o.h || 250, { b: 36, l: o.l || 46 }), x = d3.scaleBand(data.map(d => d[o.x]), [0, L.W]).padding(.25), mx = o.max || Math.max(d3.max(data, d => d[o.y]) * 1.1, 0), mn = Math.min(0, d3.min(data, d => d[o.y]) * 1.1), y = d3.scaleLinear([mn, mx], [L.H, 0]);
  ejes(L, x, y, { fy: o.fmt, nx: 20 });
  L.g.selectAll('rect').data(data).join('rect').attr('x', d => x(d[o.x])).attr('width', x.bandwidth()).attr('y', d => Math.min(y(d[o.y]), y(0))).attr('height', d => Math.abs(y(0) - y(d[o.y]))).attr('rx', 3).attr('fill', d => o.color ? o.color(d) : C.azul)
    .on('mousemove', (e, d) => tt.show(o.tip ? o.tip(d) : `${d[o.x]}: <b>${(o.fmt || fN)(d[o.y])}</b>`, e)).on('mouseleave', tt.hide);
  if (o.valores) L.g.selectAll('.v').data(data).join('text').attr('class', 'v t').attr('text-anchor', 'middle').attr('x', d => x(d[o.x]) + x.bandwidth() / 2).attr('y', d => y(d[o.y]) - 4).text(d => (o.fmt || fN)(d[o.y]));
  return { L, x, y };
}
/* series: [{name,color,dash,pts:[{x,y}]}], x puede ser Date o número */
function lineas(sel, series, o = {}) {
  const all = series.flatMap(s => s.pts), L = lienzo(sel, 700, o.h || 270, { l: o.l || 52 }), tiempo = all[0].x instanceof Date;
  const x = (tiempo ? d3.scaleTime : d3.scaleLinear)(d3.extent(all, d => d.x), [0, L.W]), y = d3.scaleLinear(o.ylim || [Math.min(0, d3.min(all, d => d.y)), d3.max(all, d => d.y) * 1.08], [L.H, 0]);
  ejes(L, x, y, { fy: o.fy, fx: o.fx, ly: o.ly, lx: o.lx });
  (o.bandas || []).forEach(b => L.g.append('rect').attr('x', x(b.x0)).attr('width', Math.max(0, x(b.x1) - x(b.x0))).attr('y', 0).attr('height', L.H).attr('fill', b.c || C.sol).attr('opacity', .13));
  (o.refY || []).forEach(r => { L.g.append('line').attr('x1', 0).attr('x2', L.W).attr('y1', y(r.y)).attr('y2', y(r.y)).attr('stroke', r.c || C.brasa).attr('stroke-dasharray', '5 4'); L.g.append('text').attr('x', L.W).attr('y', y(r.y) - 4).attr('text-anchor', 'end').text(r.t); });
  series.forEach(s => { const ln = d3.line().x(d => x(d.x)).y(d => y(d.y)).defined(d => d.y != null);
    L.g.append('path').datum(s.pts).attr('fill', 'none').attr('stroke', s.color).attr('stroke-width', s.w || 2.2).attr('stroke-dasharray', s.dash || null).attr('d', ln);
    if (s.puntos) L.g.append('g').selectAll('circle').data(s.pts.filter(d => d.y != null)).join('circle').attr('cx', d => x(d.x)).attr('cy', d => y(d.y)).attr('r', 3.4).attr('fill', s.color).on('mousemove', (e, d) => tt.show(`${s.name}<br><b>${(o.fy || fD)(d.y)}</b> · ${tiempo ? d3.timeFormat('%d %b %Y')(d.x) : d.x}`, e)).on('mouseleave', tt.hide); });
  const f = L.svg.append('rect').attr('x', L.M.l).attr('y', L.M.t).attr('width', L.W).attr('height', L.H).attr('fill', 'transparent');
  if (o.hover !== false && all.length < 3000) { const bis = d3.bisector(d => d.x).center;
    f.on('mousemove', e => { const [mx] = d3.pointer(e, L.g.node()), xv = x.invert(mx); tt.show(`<b>${tiempo ? d3.timeFormat('%d %b %Y')(xv) : fD(xv, 2)}</b><br>` + series.map(s => { const d = s.pts[bis(s.pts, xv)]; return `<span style="color:${s.color}">●</span> ${s.name}: ${d && d.y != null ? (o.fy || fD)(d.y) : '–'}`; }).join('<br>'), e); }).on('mouseleave', tt.hide); }
  return { x, y, L };
}
function leyenda(sel, items) { document.querySelector(sel).innerHTML = items.map(i => `<span><i style="background:${i[1]}"></i>${i[0]}</span>`).join(''); }
function dispersion(sel, pts, o) {
  const L = lienzo(sel, 600, o.h || 320, { l: 46 }), x = d3.scaleLinear(d3.extent(pts, d => d[o.x]), [0, L.W]).nice(), y = d3.scaleLinear(d3.extent(pts, d => d[o.y]), [L.H, 0]).nice();
  ejes(L, x, y, { lx: o.lx, ly: o.ly, fx: o.fx, fy: o.fy });
  if (o.diag) L.g.append('line').attr('x1', x(x.domain()[0])).attr('y1', y(x.domain()[0])).attr('x2', x(x.domain()[1])).attr('y2', y(x.domain()[1])).attr('stroke', C.brasa).attr('stroke-dasharray', '5 4');
  L.g.selectAll('circle').data(pts).join('circle').attr('cx', d => x(d[o.x])).attr('cy', d => y(d[o.y])).attr('r', o.r || 2.2).attr('fill', d => o.color(d)).attr('fill-opacity', o.op || .55);
}
function calor(sel, filas, cols, val, o = {}) {
  const cw = o.cw || 46, ch = 22, L = lienzo(sel, o.l + cols.length * cw + 10, filas.length * ch + 34, { l: o.l || 150, t: 24, r: 4, b: 4 });
  const col = d3.scaleThreshold(o.cortes || [.1, .25], ['#bfe4d4', '#f6d27a', '#ee8a85']);
  cols.forEach((c, j) => L.g.append('text').attr('x', j * cw + cw / 2).attr('y', -8).attr('text-anchor', 'middle').text(c));
  filas.forEach((f, i) => { L.g.append('text').attr('x', -6).attr('y', i * ch + 15).attr('text-anchor', 'end').attr('class', 't').text(f);
    cols.forEach((c, j) => { const v = val(f, c); L.g.append('rect').attr('x', j * cw + 1).attr('y', i * ch + 1).attr('width', cw - 2).attr('height', ch - 2).attr('rx', 3).attr('fill', v == null ? '#0000' : col(v))
      .on('mousemove', e => tt.show(`${f} · ${c}<br><b>${o.fv ? o.fv(v) : fD(v, 2)}</b>`, e)).on('mouseleave', tt.hide);
      if (o.txt && v != null) L.g.append('text').attr('x', j * cw + cw / 2).attr('y', i * ch + 15).attr('text-anchor', 'middle').attr('style', 'fill:#14233a;font-size:10px').text(o.txt(v)); }); });
}
function red(sel, nodos, aristas) {
  const L = lienzo(sel, 700, 460, { l: 6, r: 6, t: 6, b: 6 }), com = d3.scaleOrdinal(PAL), r = d3.scaleSqrt(d3.extent(nodos, d => d.clientes), [5, 26]), w = d3.scaleLinear(d3.extent(aristas, d => d.clientes_en_comun), [.6, 5]);
  const ns = nodos.map(d => ({ ...d, id: d.categoria })), ls = aristas.map(d => ({ source: d.origen, target: d.destino, v: d.clientes_en_comun }));
  const sim = d3.forceSimulation(ns).force('l', d3.forceLink(ls).id(d => d.id).distance(70).strength(.25)).force('c', d3.forceManyBody().strength(-170)).force('m', d3.forceCenter(L.W / 2, L.H / 2)).force('k', d3.forceCollide(d => r(d.clientes) + 3)).stop();
  for (let i = 0; i < 260; i++) sim.tick();
  L.g.selectAll('line').data(ls).join('line').attr('x1', d => d.source.x).attr('y1', d => d.source.y).attr('x2', d => d.target.x).attr('y2', d => d.target.y).attr('stroke', C.gris).attr('stroke-opacity', .35).attr('stroke-width', d => w(d.v));
  L.g.selectAll('circle').data(ns).join('circle').attr('cx', d => d.x).attr('cy', d => d.y).attr('r', d => r(d.clientes)).attr('fill', d => com(d.comunidad)).attr('stroke', '#fff').attr('stroke-width', 1.5)
    .on('mousemove', (e, d) => tt.show(`<b>${d.categoria}</b><br>${fN(d.clientes)} clientes · grado ${d.grado}<br>PageRank ${fD(d.pagerank, 3)} · intermediación ${fD(d.intermediacion, 3)}<br>comunidad ${d.comunidad + 1}`, e)).on('mouseleave', tt.hide);
  L.g.selectAll('text').data(ns.filter(d => d.clientes > 1500 || d.grado > 24)).join('text').attr('x', d => d.x).attr('y', d => d.y - r(d.clientes) - 4).attr('text-anchor', 'middle').attr('class', 't').text(d => d.categoria.replace(/_/g, ' '));
}
/* Mapa de Brasil por estado (rutas SVG de @svg-maps/brazil, licencia CC BY 4.0) */
function mapaBrasil(sel, valores, o = {}) {
  const el = document.querySelector(sel); el.innerHTML = '';
  const svg = d3.select(el).append('svg').attr('viewBox', BRASIL.viewBox).attr('class', 'mapa').attr('width', '100%').attr('role', 'img').attr('aria-label', o.alt || 'Mapa de Brasil por estado');
  const vs = Object.values(valores).filter(v => v != null), esc = d3.scaleSequential(o.inv ? d3.interpolateRgbBasis(['#d9423f', '#f6d27a', '#bfe4d4']) : d3.interpolateRgbBasis(o.rampa || ['#e6eef7', '#7fb0e6', '#1c4f95']))
    .domain(o.dom || [d3.min(vs), d3.max(vs)]);
  const gs = svg.append('g'), gp = gs.append('g'), go = gs.append('g').attr('pointer-events', 'none'), gl = gs.append('g'); const centros = {};
  let act = null; const fill = d => valores[d.id] == null ? '#0000' : esc(valores[d.id]);
  const marca = (d, ev) => {
    if (act === (d && d.id)) { if (d && ev) tt.show(o.tip ? o.tip(d) : `<b>${d.nombre}</b><br>${(o.fmt || fD)(valores[d.id])}`, ev); return; }
    go.selectAll('*').remove(); gl.selectAll('text').classed('hov', false); act = d ? d.id : null;
    if (!d) { tt.hide(); return; }
    go.append('path').attr('class', 'lift').attr('d', d.path).attr('fill', fill(d));
    gl.selectAll('text').filter(t => t.id === d.id).classed('hov', true);
    if (ev) tt.show(o.tip ? o.tip(d) : `<b>${d.nombre}</b><br>${(o.fmt || fD)(valores[d.id])}`, ev);
  };
  const deEvento = e => { const t = e.target.closest && e.target.closest('path.e'); return t ? d3.select(t).datum() : null; };
  gp.selectAll('path').data(BRASIL.estados).join('path').attr('class', 'e').attr('d', d => d.path).attr('fill', fill).attr('data-uf', d => d.id)
    .on('click', (e, d) => o.click && o.click(d));
  svg.on('pointermove', e => { if (e.pointerType !== 'touch') marca(deEvento(e), e); })
    .on('pointerleave', e => { if (e.pointerType !== 'touch') marca(null); })
    .on('pointerdown', e => { if (e.pointerType !== 'touch') return; const d = deEvento(e); marca(d && d.id === act ? null : d, e); });
  document.addEventListener('pointerdown', e => { if (act && !svg.node().contains(e.target)) marca(null); });
  addEventListener('scroll', () => { if (act) marca(null); }, { passive: true });
  gp.selectAll('path').each(function (d) { const b = this.getBBox(); centros[d.id] = [b.x + b.width / 2, b.y + b.height / 2]; });
  gl.selectAll('text').data(BRASIL.estados).join('text').attr('class', 'uf').attr('x', d => centros[d.id][0]).attr('y', d => centros[d.id][1] + 3).attr('text-anchor', 'middle').attr('style', 'font-size:10px;font-weight:600;fill:#0b1f3a;pointer-events:none;paint-order:stroke;stroke:#fff9;stroke-width:2px').text(d => d.id);
  return { svg, centros, esc, gs };
}
