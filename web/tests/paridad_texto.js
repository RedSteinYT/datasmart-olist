// Compara el analizador JS con las probabilidades de Python sobre 300 reseñas.
const T = require('../data/texto_modelo.json'), Tx = require('../js/texto.js'), casos = require('./texto_paridad.json');
let mx = 0; casos.forEach(c => { mx = Math.max(mx, Math.abs(Tx.analizar(T, c.texto).pneg - c.p_neg)); });
console.log('max |JS - Python| =', mx.toExponential(2)); if (mx > 1e-4) { console.error('FALLA paridad de texto'); process.exit(1); } console.log('OK');
