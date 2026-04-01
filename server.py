from flask import Flask, render_template, request, jsonify, session, redirect
import os, json
from config import WEB_HOST, WEB_PORT, LOG_FILE, QUEUE_FILE, WEB_USER, WEB_PASS

app = Flask(__name__)
app.secret_key = "mpserver_2026_secure"

# ==========================================
# 🔐 LOGICA DE ACCESO (INTEGRADA)
# ==========================================

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        user = request.form.get("user")
        password = request.form.get("pass")
        # Validación directa con config.py
        if user == WEB_USER and password == WEB_PASS:
            session["log"] = True
            return redirect("/")
        return "Acceso Denegado", 401
    
    # HTML embebido para evitar el error TemplateNotFound
    return '''
    <!DOCTYPE html>
    <html lang="es">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <style>
            body { background:#000; color:#00d2ff; font-family:sans-serif; display:flex; justify-content:center; align-items:center; height:100vh; margin:0; }
            form { background:#111; padding:30px; border-radius:15px; border:1px solid #222; width:80%; max-width:300px; text-align:center; }
            input { width:100%; margin:10px 0; padding:12px; background:#000; color:white; border:1px solid #333; border-radius:8px; box-sizing:border-box; }
            button { width:100%; padding:12px; background:#00d2ff; border:none; border-radius:8px; font-weight:bold; cursor:pointer; color:#000; margin-top:10px; }
        </style>
        <title>MpServer Login</title>
    </head>
    <body>
        <form method="post">
            <h2 style="margin-top:0;">MPSERVER</h2>
            <input name="user" placeholder="Usuario" required>
            <input name="pass" type="password" placeholder="Contraseña" required>
            <button type="submit">ENTRAR AL PANEL</button>
        </form>
    </body>
    </html>
    '''

# ==========================================
# 📡 RUTAS (TU LÓGICA ORIGINAL)
# ==========================================

@app.route("/")
def index():
    if not session.get("log"): return redirect("/login")
    return render_template("index.html")

@app.route("/settings")
def settings():
    if not session.get("log"): return redirect("/login")
    return render_template("set.html")

@app.route("/logs")
def get_logs():
    if not session.get("log"): return jsonify({"error": "unauthorized"}), 401
    if not os.path.exists(LOG_FILE): return jsonify({"logs": []})
    with open(LOG_FILE, "r", encoding="utf-8") as f:
        # Mantiene tu forma de leer los logs línea por línea
        return jsonify({"logs": [l.strip() for l in f.readlines()]})

@app.route("/send", methods=["POST"])
def send():
    if not session.get("log"): return jsonify({"error": "unauthorized"}), 401
    data = request.json
    # Tu lógica de queue.json intacta
    try:
        if os.path.exists(QUEUE_FILE):
            with open(QUEUE_FILE, "r") as f: q = json.load(f)
        else: q = []
    except: q = []
    
    q.append({"id": data["id"], "msg": data["msg"]})
    
    with open(QUEUE_FILE, "w") as f: 
        json.dump(q, f, indent=4)
        
    return jsonify({"status": "ok"})

# Manejo de páginas extra (Mantiene tu estructura de 10 páginas)
EXTRAS = ["perfil", "grupos", "llamadas", "novedades", "archivados", "privacidad", "seguridad", "notificaciones", "ayuda", "info"]
@app.route('/<page>')
def custom_pages(page):
    if not session.get("log"): return redirect("/login")
    if page in EXTRAS: return render_template(f"{page}.html")
    return "404 Not Found", 404

if __name__ == "__main__":
    # Usa las variables de tu config.py
    app.run(host=WEB_HOST, port=WEB_PORT)
