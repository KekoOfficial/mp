import asyncio, json, os, datetime
from telegram import Update
from telegram.ext import Application, MessageHandler, ContextTypes, filters
from config import TOKEN, LOG_FILE, QUEUE_FILE

async def registrar(uid, name, msg):
    hora = datetime.datetime.now().strftime("%H:%M")
    linea = f"TG|{uid}:{name}|{msg}|{hora}|text"
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(linea + "\n")
        f.flush()
    print(f"📥 REGISTRO OK: {name} > {msg}")

async def on_msg(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message and update.message.text:
        u = update.effective_user
        await registrar(u.id, u.first_name, update.message.text)

async def worker(app):
    while True:
        if os.path.exists(QUEUE_FILE):
            try:
                with open(QUEUE_FILE, "r") as f: cola = json.load(f)
                if cola:
                    for m in cola:
                        await app.bot.send_message(chat_id=m["id"], text=m["msg"])
                        await registrar("YO", "ADMIN", m["msg"])
                    with open(QUEUE_FILE, "w") as f: json.dump([], f)
            except: pass
        await asyncio.sleep(1)

async def main():
    app = Application.builder().token(TOKEN).build()
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, on_msg))
    await app.initialize()
    await app.start()
    await app.updater.start_polling()
    print("💎 IMPERIO IMP v8 ONLINE - ESCUCHANDO...")
    await worker(app)

if __name__ == "__main__":
    asyncio.run(main())
