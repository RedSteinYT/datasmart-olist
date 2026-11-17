// Compara el modelo JS con las probabilidades de Python (300 pedidos de prueba) y verifica la aditividad de Shapley.
const M = require('../data/modelo.json'), Mo = require('../js/model.js');
let maxd = 0; M.prueba_X.forEach((x, i) => { maxd = Math.max(maxd, Math.abs(Mo.prob(M, x) - M.prueba_p[i])); });
console.log('max |JS - Python| =', maxd.toExponential(2)); if (maxd > 1e-5) { console.error('FALLA paridad'); process.exit(1); }
const inp = { customer_state: 'SP', cat: 'health_beauty', n_items: 1, n_vendedores: 1, precio_total: 120, flete_total: 20, peso_total_g: 800, volumen_total_cm3: 6000, ratio_flete: .17, dia_semana: 2, hora: 14, dias_aprobacion: .1, n_cuotas: 2, distancia_km: 450, mismo_estado: 0, dias_estimados: 22, vend_hist_dias: 12, vend_hist_tardio: .05, vend_hist_n: 200, carga_rel: 1.1 };
const s = Mo.shapley(M, inp, 200, 1), suma = s.phi.reduce((a, b) => a + b, 0);
console.log('p =', s.p.toFixed(4), 'base =', s.base.toFixed(4), '| suma Shapley =', (suma + s.base).toFixed(4)); if (Math.abs(suma + s.base - s.p) > 1e-9) { console.error('FALLA aditividad'); process.exit(1); }
console.log('OK');
