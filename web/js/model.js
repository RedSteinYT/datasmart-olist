/* Modelo de riesgo de entrega tardía en el navegador: evalúa los 300 árboles XGBoost exportados y explica con valores de Shapley muestreados.
   Módulo sin DOM (se prueba con Node y se compara con Python). */
(function (root) {
  const sig = z => 1 / (1 + Math.exp(-z));
  function mulberry(a) { return function () { a |= 0; a = a + 0x6D2B79F5 | 0; let t = Math.imul(a ^ a >>> 15, 1 | a); t = t + Math.imul(t ^ t >>> 7, 61 | t) ^ t; return ((t ^ t >>> 14) >>> 0) / 4294967296; }; }
  function margin(M, x) {
    let s = M.base_margin;
    for (let k = 0; k < M.trees.length; k++) {
      const t = M.trees[k]; let i = 0;
      while (t.l[i] !== -1) { const v = Math.fround(x[t.f[i]]); i = (v === null || v !== v) ? (t.d[i] ? t.l[i] : t.r[i]) : (v < Math.fround(t.c[i]) ? t.l[i] : t.r[i]); }
      s += t.c[i];
    }
    return s;
  }
  const prob = (M, x) => sig(margin(M, x));
  function index(M) {
    if (M._idx) return M._idx;
    const col = {}; M.columns.forEach((c, i) => col[c] = i);
    const grupos = M.num.concat(['customer_state', 'cat']);
    const cols = {}; grupos.forEach(g => cols[g] = []);
    M.columns.forEach((c, i) => { if (c.startsWith('customer_state_')) cols.customer_state.push(i); else if (c.startsWith('cat_')) cols.cat.push(i); else cols[c].push(i); });
    return M._idx = { col, grupos, cols };
  }
  /* entrada (valores originales) -> vector de 61 columnas, igual que build_X de Python */
  function vector(M, inp) {
    const { col } = index(M), x = new Array(M.columns.length).fill(0), L = new Set(M.log_cols);
    M.num.forEach(n => { let v = inp[n]; if (v === undefined || v === null || v !== v) v = M.medianas_fill[n] ?? 0; x[col[n]] = L.has(n) ? Math.log1p(Math.max(v, 0)) : v; });
    const s = 'customer_state_' + inp.customer_state, c = 'cat_' + (M.cats.includes(inp.cat) ? inp.cat : 'otras');
    if (col[s] !== undefined) x[col[s]] = 1; if (col[c] !== undefined) x[col[c]] = 1;
    return x;
  }
  function banda(M, p) { return p >= M.q90 ? 'Alto' : p >= M.q60 ? 'Medio' : 'Bajo'; }
  /* Shapley por permutaciones sobre 20 jugadores (18 numéricas + estado + categoría), base = promedio sobre 100 pedidos de referencia.
     Cada permutación usa un pedido de referencia distinto (en ciclo); los aportes suman exactamente prob(x) - prob media de los pedidos usados. */
  function shapley(M, inp, nperm = 200, seed = 1) {
    const { grupos, cols } = index(M), x = vector(M, inp), rnd = mulberry(seed), G = grupos.length, B = M.fondo, phi = new Array(G).fill(0);
    let base = 0;
    for (let p = 0; p < nperm; p++) {
      const order = grupos.map((_, i) => i); for (let i = G - 1; i > 0; i--) { const j = Math.floor(rnd() * (i + 1)); [order[i], order[j]] = [order[j], order[i]]; }
      const z = B[p % B.length].slice(); let prev = prob(M, z); base += prev;
      for (const g of order) { for (const c of cols[grupos[g]]) z[c] = x[c]; const cur = prob(M, z); phi[g] += cur - prev; prev = cur; }
    }
    base /= nperm; return { base, p: prob(M, x), phi: phi.map(v => v / nperm), grupos };
  }
  const api = { sig, margin, prob, vector, banda, shapley, index, mulberry };
  if (typeof module !== 'undefined') module.exports = api; else root.Modelo = api;
})(typeof window !== 'undefined' ? window : globalThis);
