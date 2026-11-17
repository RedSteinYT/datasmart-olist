"""Construye (1) dist/ para hosting estático y (2) dist/datasmart.html: el tablero completo en UN solo archivo que funciona sin internet."""
import json, shutil
from pathlib import Path
R = Path(__file__).resolve().parents[1]; W = R / "web"; D = R / "dist"
shutil.rmtree(D, ignore_errors=True); D.mkdir()
for d in ("css", "js", "vendor", "data"): shutil.copytree(W / d, D / d)
shutil.copy(W / "index.html", D / "index.html"); (D / ".nojekyll").write_text("")
datos = {p.stem: json.load(open(p)) for p in (W / "data").glob("*.json")}
h = (W / "index.html").read_text()
css = (W / "css/app.css").read_text()
h = h.replace('<link rel="stylesheet" href="css/app.css">', f"<style>{css}</style>")
orden = ["vendor/d3.min.js", "js/logo.js", "js/brasil.js", "js/model.js", "js/texto.js", "js/charts.js", "js/app_core.js", "js/app_modelo.js", "js/main.js"]
for s in orden: h = h.replace(f'<script src="{s}"></script>', "")
embed = "window.DATA_EMBED=" + json.dumps(datos, ensure_ascii=False, separators=(",", ":")) + ";"
js = embed + "\n" + "\n".join((W / s).read_text().replace("</script>", "<\\/script>") for s in orden)
h = h.replace("</body>", f"<script>{js}</script></body>")
(D / "datasmart.html").write_text(h)
print("dist/ listo;", "datasmart.html =", round((D / "datasmart.html").stat().st_size / 1e6, 2), "MB")
