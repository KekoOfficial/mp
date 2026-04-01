from flask import Flask, render_template, request, jsonify, session, redirect
import os
import json
from config import WEB_HOST, WEB_PORT, LOG_FILE, QUEUE_FILE, WEB_USER, WEB_PASS

app = Flask(__name__)
app.secret_key = "mpserver_secure_key_2026"

# ==========================================
# 🔐 SEGURIDAD (MPSERVER LOGIN)
# ==========================================

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        user = request.form.get("user")
        password = request.form.get("pass")
        # Validamos contra los datos de config.py
        if user == WEB_USER and password == WEB_PASS:
            session["logged_in"] = True
            return redirect("/")
        return "Acceso Denegado: Credenciales Incorrectas", 401
    
    return '''
    <body style="background:#000; color:#00d2ff; font-family:sans-serif; display:flex; justify-content:center; align-items:center; height:100vh;">
        <form method="post" style="background:#111; padding:30px; border-radius:15px; border:1px solid #222; width:300px;">
            <h2 style="text-align:center;">MPSERVER</h2>
            <input name="user" placeholder="Usuario" style="width:100%; margin:10px 0; padding:12px; background:#000; color:white; border:1px solid #333; border-radius:8px;">
            <input name="pass" type="password" placeholder="Password" style="width:100%; margin:10px 0; padding:12px; background:#000; color:white; border:1px solid #333; border-radius:8px;">
            <button type="submit" style="width:100%; padding:12px; background:#00d2ff; border:none; border-radius:8px; font-weight:bold; cursor:pointer; color:#000;">ENTRAR AL PANEL</button>
        </form>
    </body>
    '''

def is_logged():
    return session.get("logged_in")

# ==========================================
# 📡 RUTAS MPSERVER
# ==========================================

@app.route("/")
def index():
    if not is_logged(): return redirect("/login")
    return render_template("index.html")

@app.route("/settings")
def settings():
    if not is_logged(): return redirect("/login")
    return render_template("set.html")

@app.route("/logs")
def api_logs():
    if not is_logged(): return jsonify({"error": "unauthorized"}), 401
    if not os.path.exists(LOG_FILE): return jsonify({"logs": []})
    with open(LOG_FILE, "r", encoding="utf-8") as f:
        return jsonify({"logs": f.readlines()[-150:]})

@app.route("/send", methods=["POST"])
def api_send():
    if not is_logged(): return jsonify({"error": "unauthorized"}), 401
    data = request.json
    try:
        q = json.load(open(QUEUE_FILE)) if os.path.exists(QUEUE_FILE) else []
    except: q = []
    
    q.append({"id": data["id"], "msg": data["msg"]})
    with open(QUEUE_FILE, "w") as f: json.dump(q, f, indent=4)
    return jsonify({"status": "ok"})

# Manejo de las 10 páginas extra
EXTRAS = ["perfil", "grupos", "llamadas", "novedades", "archivados", "privacidad", "seguridad", "notificaciones", "ayuda", "info"]
@app.route('/<page>')
def custom_pages(page):
    if not is_logged(): return redirect("/login")
    if page in EXTRAS: return render_template(f"{page}.html")
    return "404", 404

if __name__ == "__main__":
    app.run(host=WEB_HOST, port=WEB_PORT)
