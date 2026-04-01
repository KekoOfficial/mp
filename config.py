from flask import Flask, render_template, request, jsonify, redirect, session, url_for
import os, json, datetime, sqlite3, threading, subprocess
from config import *

app = Flask(__name__)
app.secret_key = "IMP_SECRET_KEY_2026"

# ==========================================
# 🗄️ GESTIÓN DE USUARIOS (SQLITE)
# ==========================================
def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('CREATE TABLE IF NOT EXISTS admins (id INTEGER PRIMARY KEY, user TEXT UNIQUE, pass TEXT)')
    # Crear los 10 slots si está vacío (Usuario: admin1...admin10, Pass: 1234)
    cursor.execute('SELECT COUNT(*) FROM admins')
    if cursor.fetchone()[0] == 0:
        for i in range(1, 11):
            cursor.execute('INSERT INTO admins (user, pass) VALUES (?, ?)', (f'admin{i}', '1234'))
    conn.commit()
    conn.close()

# ==========================================
# 🌐 TUNEL Y RUTAS
# ==========================================
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        u, p = request.form.get('username'), request.form.get('password')
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute('SELECT * FROM admins WHERE user=? AND pass=?', (u, p))
        user = c.fetchone()
        conn.close()
        if user:
            session['admin'] = u
            return redirect(url_for('selector'))
        return "❌ CREDENCIALES INVÁLIDAS"
    return render_template('login.html')

@app.route('/')
def selector():
    if 'admin' not in session: return redirect(url_for('login'))
    return render_template('set.html', admin=session['admin'])

@app.route('/chat/<id>')
def chat(id):
    if 'admin' not in session: return redirect(url_for('login'))
    return render_template('index.html', chat_id=id)

@app.route('/get_logs')
def get_logs():
    if os.path.exists(LOG_FILE):
        with open(LOG_FILE, 'r', encoding='utf-8') as f: return f.read()
    return ""

@app.route('/send_msg', methods=['POST'])
def send_msg():
    data = request.json
    nueva_tarea = {"id": str(data['id']), "msg": data['msg'], "plat": "TG", "admin": session.get('admin')}
    cola = []
    if os.path.exists(QUEUE_FILE):
        with open(QUEUE_FILE, 'r') as f:
            try: cola = json.load(f)
            except: cola = []
    cola.append(nueva_tarea)
    with open(QUEUE_FILE, 'w') as f: json.dump(cola, f)
    return jsonify({"status": "success"})

if __name__ == '__main__':
    init_db()
    # Iniciar túnel en hilo aparte
    def run_lt():
        subprocess.Popen(f"lt --port 5000 --subdomain imperio-imp-v8", shell=True)
    threading.Thread(target=run_lt, daemon=True).start()
    app.run(host='0.0.0.0', port=5000)
