import asyncio, json, os, datetime
from telegram import Update
from telegram.ext import Application, MessageHandler, ContextTypes, filters
from config import TOKEN, LOG_FILE, QUEUE_FILE

# Crear carpetas necesarias
os.makedirs("static/media", exist_ok=True)

def registrar(plataforma, remitente, mensaje):
    """Guarda en el log: PLAT|ID:Nombre|Msg|Hora"""
    hora = datetime.datetime.now().strftime("%H:%M")
    linea = f"{plataforma}|{remitente}|{mensaje}|{hora}"
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(linea + "\n")

async def recibir_tg(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message: return
    uid = update.effective_user.id
    name = update.effective_user.first_name
    
    msg_content = ""
    # Manejo de Fotos
    if update.message.photo:
        file = await context.bot.get_file(update.message.photo[-1].file_id)
        path = f"static/media/tg_{file.file_id}.jpg"
        await file.download_to_drive(path)
        msg_content = f"IMG:/{path}" 
    # Manejo de Videos
    elif update.message.video:
        file = await context.bot.get_file(update.message.video.file_id)
        path = f"static/media/tg_{file.file_id}.mp4"
        await file.download_to_drive(path)
        msg_content = f"VID:/{path}"
    else:
        msg_content = update.message.text

    if msg_content:
        registrar("TG", f"{uid}:{name}", msg_content)

async def main():
    app = Application.builder().token(TOKEN).build()
    app.add_handler(MessageHandler(filters.ALL & ~filters.COMMAND, recibir_tg))
    
    await app.initialize()
    await app.start()
    # Memoria: drop_pending_updates=False lee todo al encender
    await app.updater.start_polling(drop_pending_updates=False)

    print("🚀 MPSERVER CONSOLA: ONLINE")

    while True:
        if os.path.exists(QUEUE_FILE):
            try:
                with open(QUEUE_FILE, "r") as f: q = json.load(f)
                if q:
                    for item in q:
                        # Enviar mensaje
                        await app.bot.send_message(chat_id=item["id"], text=item["msg"])
                        # REGISTRAR MI RESPUESTA PARA VERLA EN EL CHAT
                        registrar("TG", "YO", item["msg"])
                    with open(QUEUE_FILE, "w") as f: json.dump([], f)
            except: pass
        await asyncio.sleep(1)

if __name__ == "__main__":
    asyncio.run(main())
