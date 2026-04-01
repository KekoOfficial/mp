import asyncio
import json
import os
import datetime
import sqlite3
from threading import Thread
from flask import Flask, request, jsonify, render_template, session, redirect, url_for
from telegram import Update
from telegram.ext import Application, MessageHandler, ContextTypes, filters
from pyngrok import ngrok # Requiere: pip install pyngrok

from config import TOKEN, LOG_FILE, QUEUE_FILE, WEB_HOST, WEB_PORT, DB_PATH, NGROK_AUTH_TOKEN

# =========================
# 🔥 INICIALIZACIÓN
# =========================
app = Flask(__name__)
app.secret_key = "IMP_V10_TITAN_GLOBAL"
tg_app = Application.builder().token(TOKEN).build()

# =========================
# 🗄️ SEGURIDAD & LOGS
# =========================
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
    # Formato compatible con tus HTML/CSS v10
    line = f"TG|{uid}:{name}|{msg}|{hora}|{side}"
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(line + "\n")
        f.flush()

# =========================
# 🤖 BOT DE TELEGRAM (TU LÓGICA)
# =========================
async def recibir_tg(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text: return
    user = update.effective_user
    save_log_v10(user.id, user.first_name, update.message.text, "IN")
    print(f"📩 INCOMING: {user.first_name}")

tg_app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, recibir_tg))

# =========================
# 📡 RUTAS WEB (PANEL V10)
# =========================
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        u, p = request.form.get('u'), request.form.get('p')
        conn = sqlite3.connect(DB_PATH)
        res = conn.execute('SELECT * FROM users WHERE user=? AND pass=?', (u, p)).fetchone()
        conn.close()
        if res:
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
        with open(LOG_FILE, "r", encoding="utf-8") as f: return f.read()
    return ""

@app.route("/api/send", methods=["POST"])
def send_api():
    if 'admin' not in session: return jsonify({"s": "err"}), 401
    data = request.json
    queue = json.load(open(QUEUE_FILE)) if os.path.exists(QUEUE_FILE) else []
    queue.append({"id": data["id"], "msg": data["msg"], "op": session['admin']})
    with open(QUEUE_FILE, "w") as f: json.dump(queue, f)
    return jsonify({"status": "ok"})

# =========================
# 🚀 CORE DE EJECUCIÓN
# =========================
async def run_bot_v10():
    await tg_app.initialize()
    await tg_app.start()
    await tg_app.bot.delete_webhook(drop_pending_updates=True) # Tu Fix
    await tg_app.updater.start_polling()
    print("💎 TITAN BOT V10: ONLINE")

    while True:
        if os.path.exists(QUEUE_FILE):
            try:
                with open(QUEUE_FILE, "r") as f: queue = json.load(f)
                if queue:
                    for item in queue:
                        try:
                            await tg_app.bot.send_message(chat_id=int(item["id"]), text=item["msg"])
                            save_log_v10(item["id"], f"OP({item['op']})", item["msg"], "OUT")
                        except Exception as e: print(f"❌ Error: {e}")
                    with open(QUEUE_FILE, "w") as f: json.dump([], f)
            except: pass
        await asyncio.sleep(0.8)

def run_global_tunnel():
    """Inicia Ngrok para el enlace MpServer personalizado"""
    if NGROK_AUTH_TOKEN:
        ngrok.set_auth_token(NGROK_AUTH_TOKEN)
    
    # Esto genera el enlace público
    public_url = ngrok.connect(WEB_PORT).public_url
    print(f"\n🌍 ENLACE GLOBAL ACTIVO (MpServer): {public_url}")
    print(f"🔑 ACCESO PARA LOS 10 OPERADORES\n")

if __name__ == "__main__":
    init_db()
    # 1. Túnel Global
    Thread(target=run_global_tunnel).start()
    # 2. Servidor Web
    Thread(target=lambda: app.run(host=WEB_HOST, port=WEB_PORT, use_reloader=False)).start()
    # 3. Bot Titan
    asyncio.run(run_bot_v10())
