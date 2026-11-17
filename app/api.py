"""API de DataSmart (Flask). Sirve además el tablero estático. Ejecutar: python app/api.py  |  gunicorn app.api:app"""
import os, sys
from pathlib import Path
from flask import Flask, jsonify, request, send_from_directory
ROOT = Path(__file__).resolve().parents[1]; sys.path.insert(0, str(ROOT / "src"))
from datasmart.service import Servicio

def crear_app(root=ROOT):
    app = Flask(__name__, static_folder=None); svc = Servicio(root); web = Path(root) / "web"

    @app.after_request
    def cors(r): r.headers["Access-Control-Allow-Origin"] = "*"; r.headers["Access-Control-Allow-Headers"] = "Content-Type"; return r

    @app.get("/api/health")
    def health(): return jsonify(estado="ok", modelo="XGBoost", version="v1-referencia", texto=bool(svc.texto))

    @app.post("/api/predict")
    def predict():
        p = request.get_json(silent=True)
        if not isinstance(p, dict): return jsonify(error="se esperaba un objeto JSON"), 400
        try: return jsonify(svc.predecir(p))
        except (ValueError, TypeError, KeyError) as e: return jsonify(error=str(e)), 422

    @app.post("/api/text")
    def text():
        p = request.get_json(silent=True) or {}; t = str(p.get("texto", "")).strip()
        if not t: return jsonify(error="falta el campo 'texto'"), 422
        if len(t) > 5000: return jsonify(error="texto demasiado largo (máx. 5000)"), 422
        return jsonify(svc.analizar_texto(t))

    @app.get("/api/monitoring")
    def mon(): return jsonify(svc.monitoreo())

    @app.get("/api/model/versions")
    def vers(): return jsonify(svc.versiones())

    @app.get("/api/audit")
    def aud(): return jsonify(svc.auditoria(int(request.args.get("n", 50))))

    @app.get("/")
    def raiz(): return send_from_directory(web, "index.html")
    @app.get("/<path:p>")
    def estatico(p): return send_from_directory(web, p)
    return app

app = crear_app()
if __name__ == "__main__": app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8000)))
