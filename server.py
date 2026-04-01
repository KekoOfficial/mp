import asyncio
import json
import os
from threading import Thread
from flask import Flask, request, jsonify, render_template

from telegram import Update, Bot
from telegram.ext import Application, MessageHandler, ContextTypes, filters

from config import TOKEN, LOG_FILE, QUEUE_FILE, WEB_HOST, WEB_PORT

# =========================
# 🔥 INIT
# =========================

app = Flask(__name__)
bot = Bot(token=TOKEN)

tg_app = Application.builder().token(TOKEN).build()
loop = asyncio.new_event_loop()

# =========================
# 📂 UTIL
# =========================

def save_log(text):
    with open(LOG_FILE, "a") as f:
        f.write(text + "\n")

def load_queue():
    if os.path.exists(QUEUE_FILE):
        try:
            with open(QUEUE_FILE, "r") as f:
                return json.load(f)
        except:
            return []
    return []

def save_queue(q):
    with open(QUEUE_FILE, "w") as f:
        json.dump(q, f)

def load_logs():
    if os.path.exists(LOG_FILE):
        with open(LOG_FILE, "r") as f:
            return f.readlines()[-50:]
    return []

# =========================
# 🤖 RECIBIR MENSAJES
# =========================

async def recibir(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text:
        return

    user = update.effective_user
    msg = update.message.text
    line = f"{user.id}|{user.first_name}: {msg}"

    print("📩", line)
    save_log(line)

tg_app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, recibir))

# =========================
# 📡 API / RUTAS
# =========================

@app.route("/")
def home():
    # Renderiza el archivo desde /templates/index.html
    return render_template("index.html")

@app.route("/send", methods=["POST"])
def send():
    data = request.json
    queue = load_queue()
    queue.append({
        "id": data["id"],
        "msg": data["msg"]
    })
    save_queue(queue)
    return jsonify({"status": "ok"})

@app.route("/logs")
def logs():
    return jsonify({"logs": load_logs()})

# =========================
# 🤖 BOT LOOP
# =========================

async def run_bot():
    await tg_app.initialize()
    await tg_app.start()
    await tg_app.bot.delete_webhook(drop_pending_updates=True)
    await tg_app.updater.start_polling()

    print("🤖 BOT ONLINE")

    while True:
        queue = load_queue()
        if queue:
            for item in queue:
                try:
                    await tg_app.bot.send_message(
                        chat_id=int(item["id"]),
                        text=item["msg"]
                    )
                    print("✔ enviado a", item["id"])
                except Exception as e:
                    print("❌ error:", e)
            save_queue([])
        await asyncio.sleep(1)

# =========================
# 🌐 WEB THREAD
# =========================

def run_web():
    app.run(host=WEB_HOST, port=WEB_PORT, debug=False, use_reloader=False)

# =========================
# 🚀 MAIN
# =========================

async def main():
    Thread(target=run_web).start()
    await run_bot()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nApagando...")
