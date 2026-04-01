import asyncio
import json
import os
import datetime
from telegram import Update
from telegram.ext import Application, MessageHandler, ContextTypes, filters
from config import TOKEN, LOG_FILE, QUEUE_FILE, IG_USER, IG_PASS

# Directorios de recursos
os.makedirs("static/avatars", exist_ok=True)

# ==========================================
# 📂 GESTIÓN DE MEMORIA Y DATOS
# ==========================================

def save_log(id_user, nombre, mensaje, plataforma="TG"):
    timestamp = datetime.datetime.now().strftime("%H:%M:%S")
    # Formato: ID|Plataforma|Nombre: Mensaje | Hora
    line = f"{id_user}|{plataforma}|{nombre}: {mensaje} | {timestamp}"
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(line + "\n")
    print(f"📩 [{plataforma}] {nombre}: {mensaje}")

def load_queue():
    if os.path.exists(QUEUE_FILE):
        try:
            with open(QUEUE_FILE, "r") as f: return json.load(f)
        except: return []
    return []

def save_queue(q):
    with open(QUEUE_FILE, "w") as f: json.dump(q, f, indent=4)

async def descargar_foto(user_id, context):
    path = f"static/avatars/{user_id}.jpg"
    if not os.path.exists(path):
        try:
            photos = await context.bot.get_user_profile_photos(user_id, limit=1)
            if photos.total_count > 0:
                file = await context.bot.get_file(photos.photos[0][0].file_id)
                await file.download_to_drive(path)
        except: pass

# ==========================================
# 📥 RECEPCIÓN (TELEGRAM)
# ==========================================

async def recibir_tg(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text: return
    user = update.effective_user
    save_log(user.id, user.first_name, update.message.text, "TG")
    asyncio.create_task(descargar_foto(user.id, context))

# ==========================================
# 🚀 CICLO PRINCIPAL (CONSOLA)
# ==========================================

async def main():
    # Configuración de Telegram
    tg_app = Application.builder().token(TOKEN).build()
    tg_app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, recibir_tg))

    await tg_app.initialize()
    await tg_app.start()

    # IMPORTANTE: drop_pending_updates=False permite leer mensajes 
    # que llegaron mientras la consola estaba APAGADA.
    await tg_app.updater.start_polling(drop_pending_updates=False)

    print(f"🚀 MPSERVER CONSOLA ONLINE")
    print(f"📡 Plataformas activas: Telegram" + (f", Instagram (@{IG_USER})" if IG_USER else ""))

    while True:
        queue = load_queue()
        if queue:
            for item in queue:
                try:
                    # Enviar por Telegram
                    await tg_app.bot.send_message(chat_id=int(item["id"]), text=item["msg"])
                    print(f"✔ Respuesta enviada a {item['id']}")
                except Exception as e:
                    print(f"❌ Error al enviar: {e}")
            save_queue([]) # Limpiar cola tras procesar

        await asyncio.sleep(1)

if __name__ == "__main__":
    asyncio.run(main())
