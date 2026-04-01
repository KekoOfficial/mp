import asyncio
import json
import os
from telegram import Update
from telegram.ext import Application, MessageHandler, ContextTypes, filters

from config import TOKEN, LOG_FILE, QUEUE_FILE

# =========================
# 📂 UTIL
# =========================

def save_log(text):
    with open(LOG_FILE, "a") as f:
        f.write(text + "\n")

def load_queue():
    if os.path.exists(QUEUE_FILE):
        try:
            return json.load(open(QUEUE_FILE))
        except:
            return []
    return []

def save_queue(q):
    with open(QUEUE_FILE, "w") as f:
        json.dump(q, f)

# =========================
# 📩 RECIBIR MENSAJES
# =========================

async def recibir(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message:
        return

    user = update.effective_user
    msg = update.message.text

    line = f"{user.id}|{user.first_name}: {msg}"
    print("📩", line)

    save_log(line)

# =========================
# 🚀 BOT
# =========================

async def main():
    app = Application.builder().token(TOKEN).build()

    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, recibir))

    await app.initialize()
    await app.start()

    # 🔥 FIX IMPORTANTE
    await app.bot.delete_webhook(drop_pending_updates=True)

    await app.updater.start_polling()

    print("🤖 BOT ONLINE")

    while True:
        queue = load_queue()

        if queue:
            for item in queue:
                try:
                    await app.bot.send_message(
                        chat_id=int(item["id"]),
                        text=item["msg"]
                    )
                    print("✔ enviado a", item["id"])
                except Exception as e:
                    print("❌ error:", e)

            save_queue([])

        await asyncio.sleep(1)

if __name__ == "__main__":
    asyncio.run(main())