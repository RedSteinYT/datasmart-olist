"""Capturas del panel web para el informe (usa dist/datasmart.html, funciona por file://)."""
from pathlib import Path
from playwright.sync_api import sync_playwright
R = Path(__file__).resolve().parents[1]; out = R / "docs" / "figuras"; url = (R / "dist" / "datasmart.html").as_uri()
secs = ["inicio", "mapa", "clientes", "simulador", "explicacion", "resenas", "monitoreo"]
with sync_playwright() as p:
    b = p.chromium.launch(executable_path="/usr/bin/google-chrome", args=["--no-sandbox"])
    pg = b.new_page(viewport={"width": 1360, "height": 860}, device_scale_factor=1.4); pg.goto(url); pg.wait_for_timeout(1500)
    for s in secs:
        pg.evaluate(f"location.hash='#/{s}'"); pg.wait_for_timeout(1200); pg.screenshot(path=str(out / f"web_{s}.png"))
    pg.close()
    pm = b.new_page(viewport={"width": 390, "height": 844}, device_scale_factor=2); pm.goto(url); pm.wait_for_timeout(1500)
    pm.evaluate("location.hash='#/simulador'"); pm.wait_for_timeout(1200); pm.screenshot(path=str(out / "web_movil_simulador.png"))
    b.close()
print("ok")
