import os
import json
from flask import Flask, render_template, request, jsonify
from config import WEB_HOST, WEB_PORT, LOG_FILE, QUEUE_FILE

app = Flask(__name__)

# Asegurar que las carpetas existan para evitar errores al cargar la web
os.makedirs("templates", exist_ok=True)
os.makedirs("static/avatars", exist_ok=True)

# =========================
# 📂 FUNCIONES DE DATOS
# =========================

def load_logs():
    """Lee el archivo de texto donde el Bot guarda los mensajes."""
    if os.path.exists(LOG_FILE):
        with open(LOG_FILE, "r", encoding="utf-8") as f:
            # Retornamos las últimas 100 líneas para no saturar la web
            return f.readlines()[-100:]
    return []

def get_queue():
    """Carga la cola de mensajes pendientes de envío."""
    if os.path.exists(QUEUE_FILE):
        try:
            with open(QUEUE_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            return []
    return []

def save_queue(q):
    """Guarda nuevos mensajes en la cola para que el Bot los procese."""
    with open(QUEUE_FILE, "w", encoding="utf-8") as f:
        json.dump(q, f, indent=4)

# =========================
# 📡 RUTAS DEL PANEL
# =========================

@app.route("/")
def index():
    """Ventana de chat principal."""
    return render_template("index.html")

@app.route("/settings")
def settings():
    """Bandeja de entrada / Lista de chats."""
    return render_template("set.html")

# --- RUTAS PARA LAS 10 PÁGINAS EXTRA ---
# Este bloque maneja perfil.html, grupos.html, etc., de forma automática
EXTRAS = ["perfil", "grupos", "llamadas", "novedades", "archivados", 
          "privacidad", "seguridad", "notificaciones", "ayuda", "info"]

@app.route('/<page>')
def render_custom_pages(page):
    if page in EXTRAS:
        return render_template(f"{page}.html")
    return "Página no encontrada en MpServer", 404

# =========================
# ⚙️ API (COMUNICACIÓN)
# =========================

@app.route("/logs")
def api_logs():
    """El JS de la web llama aquí para actualizar los mensajes en pantalla."""
    return jsonify({"logs": load_logs()})

@app.route("/send", methods=["POST"])
def api_send():
    """Recibe el mensaje desde la web y lo mete a la cola."""
    data = request.json
    if not data or "id" not in data or "msg" not in data:
        return jsonify({"status": "error", "message": "Datos incompletos"}), 400
    
    current_queue = get_queue()
    current_queue.append({
        "id": data["id"],
        "msg": data["msg"]
    })
    save_queue(current_queue)
    
    return jsonify({"status": "ok"})

# =========================
# 🚀 ARRANQUE
# =========================

if __name__ == "__main__":
    print(f"🌐 MpServer Web Interface")
    print(f"🔗 Acceso: http://{WEB_HOST}:{WEB_PORT}")
    # debug=False y use_reloader=False para evitar conflictos con el Bot.py
    app.run(host=WEB_HOST, port=WEB_PORT, debug=False, use_reloader=False)
