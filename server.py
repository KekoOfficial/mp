import os
import json
import sqlite3
import datetime
import threading
import subprocess
from flask import Flask, render_template, request, jsonify, send_from_directory
from config import (
    LOG_FILE, QUEUE_FILE, DB_PATH, AUTH_TOKEN, 
    WEB_HOST, WEB_PORT, SUBDOMAIN_LT, MEDIA_DIR
)

app = Flask(__name__)

# --- MIDDLEWARE DE SEGURIDAD ---
def check_auth(token):
    return token == AUTH_TOKEN

# ==========================================
# 🌐 GESTIÓN DE TÚNEL GLOBAL (LOCAL TUNNEL)
# ==========================================
def start_global_tunnel():
    """Lanza el túnel para acceso desde el extranjero en un hilo aparte."""
    def run():
        print(f"\n🌍 [TUNEL] Intentando abrir acceso global en puerto {WEB_PORT}...")
        try:
            # Requiere: npm install -g localtunnel
            command = f"lt --port {WEB_PORT} --subdomain {SUBDOMAIN_LT}"
            process = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
            for line in iter(process.stdout.readline, b''):
                print(f"🔗 [ENLACE PÚBLICO] {line.decode('utf-8').strip()}")
        except Exception as e:
            print(f"❌ Error al iniciar el túnel: {e}")

    threading.Thread(target=run, daemon=True).start()

# ==========================================
# 🛠️ RUTAS DEL SISTEMA (ENDPOINTS)
# ==========================================

@app.route('/')
def home():
    auth = request.args.get('auth')
    if not check_auth(auth):
        return "🚫 ACCESO NO AUTORIZADO", 403
    return render_template('set.html', auth=auth)

@app.route('/chat/<plat>/<chat_id>')
def chat_room(plat, chat_id):
    auth = request.args.get('auth')
    if not check_auth(auth):
        return "🚫 SESIÓN EXPIRADA", 403
    return render_template('index.html', plat=plat, chat_id=chat_id, auth=auth)

@app.route('/get_logs')
def get_logs():
    auth = request.args.get('auth')
    if not check_auth(auth): return "Error", 401
    
    if os.path.exists(LOG_FILE):
        with open(LOG_FILE, 'r', encoding='utf-8') as f:
            return f.read()
    return ""

@app.route('/send_msg', methods=['POST'])
def send_msg():
    data = request.json
    # Validación de datos de entrada
    if not data or 'msg' not in data or 'id' not in data:
        return jsonify({"status": "error", "message": "Datos incompletos"}), 400

    try:
        nueva_tarea = {
            "id": str(data['id']),
            "msg": data['msg'],
            "plat": data.get('plat', 'TG'),
            "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }

        # Manejo de cola con bloqueo simple para evitar corrupción
        cola = []
        if os.path.exists(QUEUE_FILE):
            with open(QUEUE_FILE, 'r') as f:
                try:
                    cola = json.load(f)
                except: cola = []

        cola.append(nueva_tarea)

        with open(QUEUE_FILE, 'w') as f:
            json.dump(cola, f, indent=4)

        return jsonify({"status": "success", "info": "Enviado a cola de salida"})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

# Servir archivos multimedia (Fotos/Videos)
@app.route('/static/media/<path:filename>')
def serve_media(filename):
    return send_from_directory(MEDIA_DIR, filename)

# ==========================================
# 📊 MONITOR DE SALUD (API)
# ==========================================
@app.route('/api/status')
def system_status():
    import psutil
    return jsonify({
        "cpu": f"{psutil.cpu_percent()}%",
        "ram": f"{psutil.virtual_memory().percent}%",
        "uptime": str(datetime.datetime.now().strftime("%H:%M:%S")),
        "db_size": f"{os.path.getsize(DB_PATH) / 1024:.2f} KB" if os.path.exists(DB_PATH) else "0 KB"
    })

# ==========================================
# 🏁 ARRANQUE MAESTRO
# ==========================================
if __name__ == '__main__':
    # 1. Iniciar acceso internacional
    start_global_tunnel()

    print("\n" + "="*40)
    print("💎 MPSERVER TITANIUM v7.0 - ONLINE")
    print(f"📡 IP LOCAL: http://localhost:{WEB_PORT}?auth={AUTH_TOKEN}")
    print("="*40 + "\n")

    # 2. Correr App Flask (Multihilo para soportar varios usuarios)
    app.run(host=WEB_HOST, port=WEB_PORT, debug=False, threaded=True)
