import asyncio
import json
import os
import datetime
import requests # <--- El puente
from telegram import Update
from telegram.ext import Application, MessageHandler, ContextTypes, filters

from config import TOKEN, LOG_FILE, QUEUE_FILE, CONSOLA_URL # Asegúrate de tener CONSOLA_URL en config

# =========================
# 🌉 PUENTE DE ACTUALIZACIÓN
# =========================

def sincronizar_con_nucleo(uid, name, msg, sistema="V10_ADMIN"):
    """Envía una señal a consola.js para actualizar el estado global"""
    try:
        # Este es el puente que conecta con el ecosistema del bot2.py
        requests.post(f"{CONSOLA_URL}/api/bridge", json={
            "sistema": sistema,
            "id": uid,
            "user": name,
            "msg": msg,
            "timestamp": datetime.datetime.now().strftime("%H:%M:%S")
        }, timeout=1)
    except:
        # Silencioso si la consola está offline para no trabar el bot
        pass

# =========================
# 📂 MOTOR DE ESCRITURA V10
# =========================

def registrar_v10(uid, name, msg, side="IN"):
    """Escribe en el formato exacto que lee el Setchat.html"""
    hora = datetime.datetime.now().strftime("%H:%M:%S")
    linea = f"TG|{uid}:{name}|{msg}|{hora}|{side}"

    try:
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(linea + "\n")
            f.flush() 
        print(f"✅ [{side}] {name}: {msg}")
        
        # Activamos el puente solo para mensajes entrantes
        if side == "IN":
            sincronizar_con_nucleo(uid, name, msg)
            
    except Exception as e:
        print(f"❌ ERROR LOG: {e}")

# =========================
# 📩 RECEPTOR DE MENSAJES
# =========================

async def recibir(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text:
        return

    user = update.effective_user
    msg = update.message.text

    await asyncio.to_thread(registrar_v10, user.id, user.first_name, msg, "IN")

# =========================
# 🚀 NÚCLEO DEL BOT
# =========================

async def main():
    app = Application.builder().token(TOKEN).build()
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, recibir))

    await app.initialize()
    await app.start()

    # Limpieza de actualizaciones viejas
    await app.bot.delete_webhook(drop_pending_updates=True)

    await app.updater.start_polling()
    print("💎 IMPERIO IMP V10 ONLINE (ESCUCHANDO...)")

    while True:
        if os.path.exists(QUEUE_FILE):
            try:
                with open(QUEUE_FILE, "r", encoding="utf-8") as f:
                    cola = json.load(f)

                if cola:
                    for item in cola:
                        try:
                            await app.bot.send_message(
                                chat_id=int(item["id"]),
                                text=item["msg"]
                            )
                            admin_name = item.get("op", "ADMIN")
                            registrar_v10(item["id"], f"OP({admin_name})", item["msg"], "OUT")
                            print(f"✔ Enviado a {item['id']} por {admin_name}")
                        except Exception as e:
                            print(f"❌ Error enviando a {item['id']}: {e}")

                    with open(QUEUE_FILE, "w", encoding="utf-8") as f:
                        json.dump([], f)
            except Exception as e:
                print(f"⚠ Error en ciclo de cola: {e}")

        await asyncio.sleep(0.8) 

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n🛑 Sistema apagado por el operador.")
