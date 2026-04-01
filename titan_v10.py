import asyncio
import json
import os
import datetime
import sqlite3
import subprocess
from threading import Thread, Lock
from flask import Flask, request, jsonify, render_template, session, redirect, url_for
from telegram import Update
from telegram.ext import Application, MessageHandler, ContextTypes, filters
from config import TOKEN, LOG_FILE, QUEUE_FILE, DB_PATH, WEB_HOST, WEB_PORT

# =========================
# 🔥 CONFIGURACIÓN & SEGURIDAD
# =========================
app = Flask(__name__)
app.secret_key = "IMP_V10_TITAN_ULTRA_HIDRA"
tg_app = Application.builder().token(TOKEN).build()
file_lock = Lock() # Evita errores de escritura simultánea

def init_db():
    if not os.path.exists(os.path.dirname(DB_PATH)):
        os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.execute('CREATE TABLE IF NOT EXISTS users (user TEXT UNIQUE, pass TEXT)')
    if conn.execute('SELECT COUNT(*) FROM users').fetchone()[0] == 0:
        for i in range(1, 11):
            conn.execute('INSERT INTO users VALUES (?, ?)', (f'admin{i}', '1234'))
    conn.commit()
    conn.close()

def save_log_v10(uid, name, msg, side="IN"):
    hora = datetime.datetime.now().strftime("%H:%M:%S")
    # Formato: PLAT|ID:NAME|MSG|HORA|LADO (Importante para tus HTML)
    line = f"TG|{uid}:{name}|{msg.replace('|', '-')}|{hora}|{side}"
    with file_lock:
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(line + "\n")
            f.flush()

# =========================
# 🤖 BOT DE TELEGRAM (TU LÓGICA GANADORA)
# =========================
async def recibir_tg(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message and update.message.text:
        u = update.effective_user
        save_log_v10(u.id, u.first_name, update.message.text, "IN")
        print(f"📩 [{u.first_name}]: {update.message.text}")

tg_app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, recibir_tg))

# =========================
# 📡 RUTAS WEB (PANEL MPSERVER)
# =========================
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        u, p = request.form.get('u'), request.form.get('p')
        conn = sqlite3.connect(DB_PATH)
        res = conn.execute('SELECT * FROM users WHERE user=? AND pass=?', (u, p)).fetchone()
        conn.close()
        if res:
            session.permanent = True
            session['admin'] = u
            return redirect(url_for('home'))
        return "❌ ACCESO DENEGADO"
    return render_template('login.html')

@app.route('/')
def home():
    if 'admin' not in session: return redirect(url_for('login'))
    return render_template('set.html', user=session['admin'])

@app.route('/chat/<cid>')
def chat_view(cid):
    if 'admin' not in session: return redirect(url_for('login'))
    return render_template('chat.html', cid=cid)

@app.route("/api/logs")
def get_logs():
    if os.path.exists(LOG_FILE):
        with open(LOG_FILE, "r", encoding="utf-8") as f:
            return f.read()
    return ""

@app.route("/api/send", methods=["POST"])
def send_api():
    if 'admin' not in session: return jsonify({"s": "err"}), 401
    data = request.json
    queue = []
    with file_lock:
        if os.path.exists(QUEUE_FILE):
            try: queue = json.load(open(QUEUE_FILE))
            except: queue = []
        
        queue.append({"id": data["id"], "msg": data["msg"], "op": session['admin']})
        with open(QUEUE_FILE, "w") as f:
            json.dump(queue, f, indent=4)
    return jsonify({"status": "ok"})

# =========================
# 🚀 TÚNEL NGROK (BYPASS ANDROID)
# =========================
def run_tunnel():
    print("\n🚀 INICIANDO TÚNEL GLOBAL (MPSERVER)...")
    try:
        # Usamos el binario local ./ngrok para evitar errores de pyngrok
        subprocess.Popen(["./ngrok", "http", "5000"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        print("🌍 TÚNEL LANZADO CON ÉXITO.")
        print("🔗 Link en: https://dashboard.ngrok.com/tunnels/agents\n")
    except Exception as e:
        print(f"❌ Error al lanzar túnel: {e}")

# =========================
# ⚙️ CORE DE EJECUCIÓN
# =========================
async def run_bot():
    await tg_app.initialize()
    await tg_app.start()
    
    # 🔥 TU FIX DE LIMPIEZA
    await tg_app.bot.delete_webhook(drop_pending_updates=True)
    await tg_app.updater.start_polling()
    
    print("💎 V10 TITAN ONLINE - ESCUCHANDO...")

    while True:
        if os.path.exists(QUEUE_FILE):
            with file_lock:
                try:
                    with open(QUEUE_FILE, "r") as f: queue = json.load(f)
                    if queue:
                        for item in queue:
                            try:
                                await tg_app.bot.send_message(chat_id=int(item["id"]), text=item["msg"])
                                save_log_v10(item["id"], f"OP({item['op']})", item["msg"], "OUT")
                                print(f"✔ Respuesta enviada a {item['id']}")
                            except Exception as e:
                                print(f"❌ Error Telegram: {e}")
                        with open(QUEUE_FILE, "w") as f: json.dump([], f)
                except: pass
        await asyncio.sleep(0.8)

if __name__ == "__main__":
    init_db()
    # 1. Lanzamos el túnel global
    run_tunnel()
    # 2. Servidor Flask en segundo plano (Tu lógica de Thread)
    Thread(target=lambda: app.run(host="0.0.0.0", port=5000, use_reloader=False), daemon=True).start()
    # 3. Bot en hilo principal
    try:
        asyncio.run(run_bot())
    except KeyboardInterrupt:
        print("\n🛑 Sistema cerrado por el operador.")
