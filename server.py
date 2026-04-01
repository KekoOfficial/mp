from flask import Flask, render_template, request, jsonify, session, redirect
import os, json
from config import WEB_HOST, WEB_PORT, LOG_FILE, QUEUE_FILE, WEB_USER, WEB_PASS

app = Flask(__name__)
app.secret_key = "mpserver_2026_ultra_secure"

# ==========================================
# 🔐 ACCESO AL PANEL (LOGIN INTEGRADO)
# ==========================================

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        user = request.form.get("user")
        password = request.form.get("pass")
        if user == WEB_USER and password == WEB_PASS:
            session["log"] = True
            return redirect("/settings") # Redirige al Set principal
        return "Acceso Denegado", 401
    
    return '''
    <!DOCTYPE html>
    <html>
    <head>
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <style>
            body { background:#000; color:#00d2ff; font-family:sans-serif; display:flex; justify-content:center; align-items:center; height:100vh; margin:0; }
            form { background:#111; padding:30px; border-radius:15px; border:1px solid #222; width:85%; max-width:320px; text-align:center; }
            input { width:100%; margin:10px 0; padding:12px; background:#000; color:white; border:1px solid #333; border-radius:8px; box-sizing:border-box; }
            button { width:100%; padding:12px; background:#00d2ff; border:none; border-radius:8px; font-weight:bold; cursor:pointer; color:#000; }
        </style>
        <title>MpServer Login</title>
    </head>
    <body>
        <form method="post">
            <h2 style="margin-top:0;">MPSERVER</h2>
            <input name="user" placeholder="Usuario" required>
            <input name="pass" type="password" placeholder="Password" required>
            <button type="submit">ENTRAR</button>
        </form>
    </body>
    </html>
    '''

# ==========================================
# 📡 RUTAS DE NAVEGACIÓN (TUS HTMLS)
# ==========================================

@app.route("/")
def index():
    # Por defecto, si entras a la raíz, te manda al chat de Telegram
    if not session.get("log"): return redirect("/login")
    return render_template("chatelegram.html")

@app.route("/settings") # Tu SET de Telegram
def settings():
    if not session.get("log"): return redirect("/login")
    return render_template("set.html")

@app.route("/setig") # Tu SET de Instagram
def setig():
    if not session.get("log"): return redirect("/login")
    return render_template("setig.html")

@app.route("/chatelegram")
def chatelegram():
    if not session.get("log"): return redirect("/login")
    return render_template("chatelegram.html")

@app.route("/chatig")
def chatig():
    if not session.get("log"): return redirect("/login")
    return render_template("chatig.html")

# ==========================================
# 📂 API DE DATOS (LOGS Y ENVÍO)
# ==========================================

@app.route("/logs")
def get_logs():
    if not session.get("log"): return jsonify({"error": "unauthorized"}), 401
    if not os.path.exists(LOG_FILE): return jsonify({"logs": []})
    try:
        with open(LOG_FILE, "r", encoding="utf-8") as f:
            return jsonify({"logs": [l.strip() for l in f.readlines()]})
    except:
        return jsonify({"logs": []})

@app.route("/send", methods=["POST"])
def send():
    if not session.get("log"): return jsonify({"error": "unauthorized"}), 401
    data = request.json
    
    # Mantenemos tu lógica de queue.json intacta
    try:
        q = []
        if os.path.exists(QUEUE_FILE):
            with open(QUEUE_FILE, "r") as f:
                q = json.load(f)
        
        # Agregamos el mensaje a la cola
        q.append({
            "id": data["id"], 
            "msg": data["msg"],
            "plat": data.get("plat", "TG") # Guardamos plataforma si viene
        })
        
        with open(QUEUE_FILE, "w") as f:
            json.dump(q, f, indent=4)
            
        return jsonify({"status": "ok"})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

# Otras páginas de tu estructura
EXTRAS = ["perfil", "grupos", "llamadas", "novedades", "archivados", "privacidad", "seguridad", "notificaciones", "ayuda", "info"]
@app.route('/<page>')
def custom_pages(page):
    if not session.get("log"): return redirect("/login")
    if page in EXTRAS:
        return render_template(f"{page}.html")
    return "404", 404

if __name__ == "__main__":
    app.run(host=WEB_HOST, port=WEB_PORT)
