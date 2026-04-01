import asyncio
import json
import os
from telegram import Update
from telegram.ext import Application, MessageHandler, ContextTypes, filters

from config import TOKEN, LOG_FILE, QUEUE_FILE

# Crear carpeta de fotos si no existe
os.makedirs("static/avatars", exist_ok=True)

# =========================
# 📂 UTIL
# =========================

def save_log(text):
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(text + "\n")

def load_queue():
    if os.path.exists(QUEUE_FILE):
        try:
            with open(QUEUE_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            return []
    return []

def save_queue(q):
    with open(QUEUE_FILE, "w", encoding="utf-8") as f:
        json.dump(q, f, indent=4)

# =========================
# 📸 NUEVO: DESCARGAR AVATAR
# =========================

async def descargar_avatar(user_id, context: ContextTypes.DEFAULT_TYPE):
    path = f"static/avatars/{user_id}.jpg"
    if os.path.exists(path):
        return
    try:
        photos = await context.bot.get_user_profile_photos(user_id, limit=1)
        if photos.total_count > 0:
            file = await context.bot.get_file(photos.photos[0][0].file_id)
            await file.download_to_drive(path)
            print(f"📸 Avatar guardado para {user_id}")
    except Exception as e:
        print(f"⚠️ Error foto {user_id}: {e}")

# =========================
# 📩 RECIBIR MENSAJES
# =========================

async def recibir(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text:
        return

    user = update.effective_user
    msg = update.message.text

    # Formato MpServer: ID|Nombre: Mensaje
    line = f"{user.id}|{user.first_name}: {msg}"
    print("📩", line)
    save_log(line)
    
    # Descargar avatar en segundo plano
    asyncio.create_task(descargar_avatar(user.id, context))

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

    print("🤖 MPSERVER BOT ONLINE")

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
