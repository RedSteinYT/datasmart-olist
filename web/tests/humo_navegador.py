"""Prueba de humo: abre cada sección en un Chrome sin cabeza, falla si hay errores de consola o secciones vacías y guarda capturas."""
import sys, json
from pathlib import Path
from playwright.sync_api import sync_playwright
url = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:8765/index.html"; out = Path(sys.argv[2] if len(sys.argv) > 2 else "/tmp/shots"); out.mkdir(exist_ok=True, parents=True)
secs = ["inicio", "panorama", "mapa", "clientes", "pronostico", "simulador", "modelo", "explicacion", "resenas", "monitoreo"]
errs = []
with sync_playwright() as p:
    b = p.chromium.launch(executable_path="/usr/bin/google-chrome", args=["--no-sandbox"])
    for w, h, tag in ((1360, 900, "pc"), (390, 844, "movil")):
        pg = b.new_page(viewport={"width": w, "height": h}); pg.on("console", lambda m: errs.append((tag, m.text)) if m.type == "error" else None); pg.on("pageerror", lambda e: errs.append((tag, str(e))))
        pg.goto(url); pg.wait_for_timeout(1200)
        for s in secs:
            pg.evaluate(f"location.hash='#/{s}'"); pg.wait_for_timeout(700)
            n = pg.evaluate(f"document.querySelectorAll('#pg-{s} svg').length"); txt = pg.evaluate(f"document.querySelector('#pg-{s}').innerText.length")
            print(tag, s, "svg:", n, "texto:", txt)
            if txt < 200: errs.append((tag, f"{s} casi vacía"))
            pg.screenshot(path=str(out / f"{tag}_{s}.png"), full_page=(tag == "pc"))
        pg.close()
    b.close()
print("ERRORES:", errs if errs else "ninguno"); sys.exit(1 if errs else 0)
