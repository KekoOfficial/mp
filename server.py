from flask import Flask, render_template, request, jsonify, session, redirect, url_for
import os, json, datetime, sqlite3, threading, subprocess
from config import *

app = Flask(__name__)
app.secret_key = "SISTEMA_V9_CORE_GLOBAL"

# --- BASE DE DATOS DE ADMINISTRADORES ---
def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('CREATE TABLE IF NOT EXISTS admins (user TEXT UNIQUE, pass TEXT)')
    c.execute('SELECT COUNT(*) FROM admins')
    if c.fetchone()[0] == 0:
        # Generar los 10 administradores por defecto
        for i in range(1, 11):
            c.execute('INSERT INTO admins VALUES (?, ?)', (f'admin{i}', '1234'))
    conn.commit()
    conn.close()

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        u, p = request.form.get('u'), request.form.get('p')
        conn = sqlite3.connect(DB_PATH)
        res = conn.execute('SELECT * FROM admins WHERE user=? AND pass=?', (u, p)).fetchone()
        conn.close()
        if res:
            session.permanent = True
            session['admin'] = u
            return redirect(url_for('selector'))
        return "❌ ACCESO DENEGADO"
    return render_template('login.html')

@app.route('/')
def selector():
    if 'admin' not in session: return redirect(url_for('login'))
    return render_template('set.html', admin=session['admin'])

@app.route('/chat/<chat_id>')
def chat(chat_id):
    if 'admin' not in session: return redirect(url_for('login'))
    return render_template('index.html', cid=chat_id)

@app.route('/api/logs')
def get_logs():
    if os.path.exists(LOG_FILE):
        with open(LOG_FILE, 'r', encoding='utf-8') as f:
            return f.read()
    return ""

@app.route('/api/send', methods=['POST'])
def send():
    if 'admin' not in session: return jsonify({"s": "unauthorized"}), 401
    data = request.json
    try:
        task = {
            "id": str(data['id']), 
            "msg": data['msg'], 
            "admin": session['admin'],
            "time": datetime.datetime.now().strftime("%H:%M")
        }
        cola = []
        if os.path.exists(QUEUE_FILE):
            with open(QUEUE_FILE, 'r') as f: cola = json.load(f)
        cola.append(task)
        with open(QUEUE_FILE, 'w') as f: json.dump(cola, f, indent=4)
        return jsonify({"s": "ok"})
    except: return jsonify({"s": "err"}), 500

# ==========================================
# 🌍 TÚNEL PARA ENLACE PERSONALIZADO
# ==========================================
def start_tunnel():
    """
    Usa LocalTunnel con un subdominio fijo. 
    Para usar mpserver.net real, necesitarías Nginx + Certbot.
    """
    subdominio = "mpserver-noa" # Esto creará mpserver-noa.loca.lt
    print(f"\n🚀 GENERANDO ENLACE GLOBAL: https://{subdominio}.loca.lt")
    subprocess.Popen(f"lt --port 5000 --subdomain {subdominio}", shell=True)

if __name__ == '__main__':
    init_db()
    start_tunnel()
    app.run(host='0.0.0.0', port=5000, threaded=True)
