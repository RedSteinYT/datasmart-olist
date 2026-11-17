/* Analizador de reseñas (portugués): misma limpieza, TF-IDF (1-2 gramas) y regresión logística que Python. Sin DOM. */
(function (root) {
  function limpiar(t, SW) {
    t = t.toLowerCase().replace(/https?:\/\/\S+/g, ' ').replace(/\d+/g, ' ').replace(/(.)\1{2,}/gsu, '$1$1').replace(/[^a-záàâãéêíóôõúüç\s]/g, ' ');
    return t.split(/\s+/).filter(w => w && w.length > 1 && !SW.has(w));
  }
  function analizar(T, raw) {
    if (!T._v) { T._v = new Map(T.vocab.map((w, i) => [w, i])); T._sw = new Set(T.stopwords); }
    const toks = limpiar(raw, T._sw), grams = toks.slice();
    for (let i = 0; i < toks.length - 1; i++) grams.push(toks[i] + ' ' + toks[i + 1]);
    const tf = new Map(); grams.forEach(g => { const j = T._v.get(g); if (j !== undefined) tf.set(j, (tf.get(j) || 0) + 1); });
    let norm = 0; const w = []; tf.forEach((c, j) => { const v = (1 + Math.log(c)) * T.idf[j]; w.push([j, v]); norm += v * v; }); norm = Math.sqrt(norm) || 1;
    let z = T.intercept; const aport = [];
    w.forEach(([j, v]) => { const a = T.coef[j] * v / norm; z += a; aport.push({ termino: T.vocab[j], aporte: a }); });
    aport.sort((a, b) => Math.abs(b.aporte) - Math.abs(a.aporte));
    const pneg = 1 / (1 + Math.exp(-z));
    const aspectos = Object.entries(T.aspectos).filter(([, re]) => new RegExp(re, 'u').test(toks.join(' '))).map(([k]) => k);
    return { tokens: toks, pneg, aporte: aport, aspectos, conocidos: w.length };
  }
  const api = { limpiar, analizar };
  if (typeof module !== 'undefined') module.exports = api; else root.Texto = api;
})(typeof window !== 'undefined' ? window : globalThis);
