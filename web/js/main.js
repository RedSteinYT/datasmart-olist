/* Arranque: carga de datos, navegación (riel, barra inferior y hoja móvil), modo Guiado/Experto y tema con transición. */
async function cargar() {
  const nombres = { resumen: 'resumen', entregable23: 'entregable23', clasificacion: 'clasificacion', texto: 'texto', monitoreo: 'monitoreo', modelo: 'modelo', tmodelo: 'texto_modelo' };
  if (window.DATA_EMBED) { for (const k in nombres) D[k] = window.DATA_EMBED[nombres[k]]; return; }
  await Promise.all(Object.entries(nombres).map(async ([k, f]) => { const r = await fetch(`data/${f}.json`); if (!r.ok) throw new Error('No se pudo cargar ' + f); D[k] = await r.json(); }));
}
const CORTO = t => typeof t === 'string' ? t.replace(' (7 días vs. 8 semanas previas)', '') : t;
const ICO = {
  inicio: '<path d="M3 11l9-7 9 7v8.5a1.5 1.5 0 0 1-1.5 1.5H15v-6H9v6H4.5A1.5 1.5 0 0 1 3 19.5z"/>',
  panorama: '<path d="M4 20V11M10 20V4M16 20v-7M21 20H3"/>',
  mapa: '<path d="M12 21s-7-6.2-7-11.5a7 7 0 0 1 14 0C19 14.8 12 21 12 21z"/><circle cx="12" cy="9.5" r="2.5"/>',
  clientes: '<circle cx="9" cy="8" r="3.5"/><path d="M2.5 20a6.5 6.5 0 0 1 13 0M16 4.6a3.5 3.5 0 0 1 0 6.8M21.5 20a6.5 6.5 0 0 0-4-6"/>',
  pronostico: '<path d="M3 17l6-6 4 4 8-8M15 7h6v6"/>',
  simulador: '<path d="M21 7.5L12 3 3 7.5 12 12zM3 7.5v9L12 21l9-4.5v-9M12 12v9"/>',
  modelo: '<path d="M4 16a8 8 0 1 1 16 0"/><path d="M12 16l4.5-5"/><circle cx="12" cy="16" r="1.4"/>',
  explicacion: '<path d="M9 18h6M10 21.5h4M12 2.5a6.5 6.5 0 0 0-3.8 11.8c.5.4.8 1 .8 1.6V16h6v-.1c0-.6.3-1.2.8-1.6A6.5 6.5 0 0 0 12 2.5z"/>',
  resenas: '<path d="M20.5 12a8.5 8.5 0 0 1-12.3 7.6L3 21l1.4-5A8.5 8.5 0 1 1 20.5 12z"/><path d="M8.5 11h7M8.5 14h4"/>',
  monitoreo: '<path d="M3 12h4l3-8 4 16 3-8h4"/>',
  mas: '<rect x="4" y="4" width="6.5" height="6.5" rx="1.5"/><rect x="13.5" y="4" width="6.5" height="6.5" rx="1.5"/><rect x="4" y="13.5" width="6.5" height="6.5" rx="1.5"/><rect x="13.5" y="13.5" width="6.5" height="6.5" rx="1.5"/>',
  guiado: '<path d="M3 5.5h6a3 3 0 0 1 3 3V20a2.2 2.2 0 0 0-2.2-2.2H3zM21 5.5h-6a3 3 0 0 0-3 3V20a2.2 2.2 0 0 1 2.2-2.2H21z"/>',
  experto: '<path d="M4 6h9M17 6h3M4 12h3M11 12h9M4 18h11M19 18h1"/><circle cx="15" cy="6" r="2"/><circle cx="9" cy="12" r="2"/><circle cx="17" cy="18" r="2"/>'
};
const ico = k => `<svg viewBox="0 0 24 24" aria-hidden="true">${ICO[k] || ''}</svg>`;
const TABS = ['inicio', 'mapa', 'simulador', 'explicacion'];
function iniciar() {
  for (const k in D.modelo.nombres) D.modelo.nombres[k] = CORTO(D.modelo.nombres[k]); for (const k in D.monitoreo.nombres) D.monitoreo.nombres[k] = CORTO(D.monitoreo.nombres[k]);
  ['perm', 'shap'].forEach(k => D.clasificacion[k].forEach(d => d.variable = CORTO(d.variable))); D.clasificacion.casos.forEach(c => c.factores.forEach(f => f.variable = CORTO(f.variable)));
  const nav = $('#nav'), main = $('#paginas'), hechas = {};
  nav.innerHTML = '<span class="ind" aria-hidden="true"></span>' + SEC.map(s => `<a class="nav" href="#/${s.id}" data-id="${s.id}">${ico(s.id)}<span>${s.t}</span></a>`).join('');
  $('#tabbar').innerHTML = '<span class="pil" aria-hidden="true"></span>' + TABS.map(id => `<a href="#/${id}" data-id="${id}">${ico(id)}<span>${SEC.find(s => s.id === id).t}</span></a>`).join('') + `<button type="button" id="b-mas" aria-haspopup="dialog">${ico('mas')}<span>Más</span></button>`;
  $('#hoja-secs').innerHTML = SEC.map(s => `<a href="#/${s.id}" data-id="${s.id}">${ico(s.id)}<span>${s.t}</span></a>`).join('');
  main.innerHTML = SEC.map(s => `<section class="pg" id="pg-${s.id}" aria-label="${s.t}"></section>`).join('');
  const hoja = $('#hoja'), velo = $('#velo'), abrir = v => { hoja.classList.toggle('abierta', v); velo.classList.toggle('abierta', v); };
  $('#b-mas').onclick = () => abrir(true); velo.onclick = () => abrir(false); $$('#hoja-secs a').forEach(a => a.addEventListener('click', () => abrir(false)));
  addEventListener('keydown', e => { if (e.key === 'Escape') abrir(false); });
  const moverInd = () => { const a = $('#nav a[aria-current=page]'), ind = $('#nav .ind'); if (a && ind) { ind.style.transform = `translateY(${a.offsetTop}px)`; ind.style.height = a.offsetHeight + 'px'; } };
  const ir = () => { const id = (location.hash.match(/#\/(\w+)/) || [])[1] || 'inicio', s = SEC.find(x => x.id === id) || SEC[0];
    $$('.pg').forEach(p => p.classList.toggle('on', p.id === 'pg-' + s.id));
    $$('#nav a, #hoja-secs a').forEach(a => a.setAttribute('aria-current', a.dataset.id === s.id ? 'page' : 'false'));
    const ti = TABS.indexOf(s.id), pos = ti < 0 ? 4 : ti; $$('#tabbar > a, #tabbar > button').forEach((b, i) => b.classList.toggle('act', i === pos)); $('#tabbar .pil').style.transform = `translateX(${pos * 100}%)`;
    $('#ab-sec').textContent = s.t; document.title = s.t + ' · DataSmart Olist'; moverInd();
    if (!hechas[s.id]) { hechas[s.id] = 1; try { s.render($('#pg-' + s.id)); } catch (e) { console.error(e); $('#pg-' + s.id).innerHTML = `<div class="callout alerta"><b>Error</b>No se pudo dibujar esta sección: ${e.message}</div>`; } }
    scrollTo({ top: 0, behavior: 'instant' }); };
  addEventListener('hashchange', ir); addEventListener('resize', moverInd); ir();
  const DESC = { guiado: 'Explicaciones en lenguaje sencillo', experto: 'Métricas, parámetros y detalle técnico' };
  $$('[data-modo]').forEach(g => g.innerHTML = ['guiado', 'experto'].map(m => `<button type="button" data-m="${m}" aria-pressed="false">${ico(m)}${m === 'guiado' ? 'Guiado' : 'Experto'}</button>`).join(''));
  const modo = m => { document.body.classList.toggle('m-guiado', m === 'guiado'); document.body.classList.toggle('m-experto', m === 'experto');
    $$('[data-modo]').forEach(g => g.dataset.v = m); $$('[data-modo] button').forEach(b => b.setAttribute('aria-pressed', b.dataset.m === m)); $$('[data-modo-desc]').forEach(p => p.textContent = DESC[m]); guarda('modo', m); };
  $$('[data-modo] button').forEach(b => b.onclick = () => modo(b.dataset.m)); modo(lee('modo') || 'guiado');
  const pinta = t => { document.documentElement.dataset.tema = t; $$('[data-tema-sw]').forEach(b => b.setAttribute('aria-checked', t === 'oscuro')); $$('[data-tema-txt]').forEach(s => s.textContent = t === 'oscuro' ? 'Tema oscuro' : 'Tema claro'); guarda('tema', t); };
  const tema = (t, ev) => {
    if (!document.startViewTransition || matchMedia('(prefers-reduced-motion: reduce)').matches) return pinta(t);
    const r = ev && ev.currentTarget ? ev.currentTarget.getBoundingClientRect() : { left: innerWidth / 2, top: 0, width: 0, height: 0 }, x = r.left + r.width / 2, y = r.top + r.height / 2, rad = Math.hypot(Math.max(x, innerWidth - x), Math.max(y, innerHeight - y));
    document.startViewTransition(() => pinta(t)).ready.then(() => document.documentElement.animate({ clipPath: [`circle(0px at ${x}px ${y}px)`, `circle(${rad}px at ${x}px ${y}px)`] }, { duration: 650, easing: 'cubic-bezier(.2,.8,.2,1)', pseudoElement: '::view-transition-new(root)' }));
  };
  $$('[data-tema-sw]').forEach(b => b.onclick = ev => tema(document.documentElement.dataset.tema === 'oscuro' ? 'claro' : 'oscuro', ev));
  pinta(lee('tema') || (matchMedia('(prefers-color-scheme: dark)').matches ? 'oscuro' : 'claro'));
}
cargar().then(iniciar).catch(e => { document.body.insertAdjacentHTML('beforeend', `<main><div class="callout alerta"><b>No se pudieron cargar los datos</b>${e.message}. Si abriste index.html con doble clic, usa la versión de un solo archivo (datasmart.html) o un servidor local (python -m http.server).</div></main>`); });
