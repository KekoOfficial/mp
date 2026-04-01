import asyncio
import json
import os
from threading import Thread
from flask import Flask, request, jsonify, render_template
from telegram import Update, Bot
from telegram.ext import Application, MessageHandler, ContextTypes, filters

# Configuración (Asegúrate de tener estos valores en config.py)
from config import TOKEN, LOG_FILE, QUEUE_FILE, WEB_HOST, WEB_PORT

app = Flask(__name__)
tg_app = Application.builder().token(TOKEN).build()

# Crear carpetas necesarias
os.makedirs("static/avatars", exist_ok=True)

# =========================
# 📂 GESTIÓN DE DATOS
# =========================

def save_log(text):
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(text + "\n")

def load_logs():
    if os.path.exists(LOG_FILE):
        with open(LOG_FILE, "r", encoding="utf-8") as f:
            return f.readlines()[-100:]
    return []

def get_queue():
    if os.path.exists(QUEUE_FILE):
        try:
            with open(QUEUE_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except: return []
    return []

def save_queue(q):
    with open(QUEUE_FILE, "w", encoding="utf-8") as f:
        json.dump(q, f)

# =========================
# 📸 GESTIÓN DE AVATARS
# =========================

async def download_avatar(user_id, context):
    path = f"static/avatars/{user_id}.jpg"
    if os.path.exists(path): return
    try:
        photos = await context.bot.get_user_profile_photos(user_id, limit=1)
        if photos.total_count > 0:
            file = await context.bot.get_file(photos.photos[0][0].file_id)
            await file.download_to_drive(path)
    except Exception as e: print(f"Error avatar {user_id}: {e}")

# =========================
# 🤖 LÓGICA TELEGRAM
# =========================

async def on_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text: return
    user = update.effective_user
    line = f"{user.id}|{user.first_name}: {update.message.text}"
    save_log(line)
    asyncio.create_task(download_avatar(user.id, context))

tg_app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, on_message))

# =========================
# 📡 RUTAS WEB (FLASK)
# =========================

@app.route("/")
def index(): return render_template("index.html")

@app.route("/settings")
def settings(): return render_template("set.html")

# Rutas para tus 10 archivos futuros (Plantilla genérica)
@app.route("/page/<name>")
def custom_pages(name):
    try:
        return render_template(f"{name}.html")
    except:
        return "Página no encontrada", 404

@app.route("/logs")
def api_logs(): return jsonify({"logs": load_logs()})

@app.route("/send", methods=["POST"])
def api_send():
    data = request.json
    q = get_queue()
    q.append({"id": data["id"], "msg": data["msg"]})
    save_queue(q)
    return jsonify({"status": "ok"})

# =========================
# 🚀 RUNNERS
# =========================

async def bot_worker():
    await tg_app.initialize()
    await tg_app.start()
    await tg_app.updater.start_polling(drop_pending_updates=True)
    while True:
        q = get_queue()
        if q:
            for m in q:
                try: await tg_app.bot.send_message(chat_id=int(m["id"]), text=m["msg"])
                except: pass
            save_queue([])
        await asyncio.sleep(1)

if __name__ == "__main__":
    Thread(target=lambda: app.run(host=WEB_HOST, port=WEB_PORT, debug=False, use_reloader=False), daemon=True).start()
    asyncio.run(bot_worker())
