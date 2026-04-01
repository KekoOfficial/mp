import asyncio
import json
import os
import datetime
from telegram import Update
from telegram.ext import Application, MessageHandler, ContextTypes, filters

from config import TOKEN, LOG_FILE, QUEUE_FILE

# =========================
# 📂 MOTOR DE ESCRITURA V10
# =========================

def registrar_v10(uid, name, msg, side="IN"):
    """Escribe en el formato exacto que lee el Setchat.html"""
    hora = datetime.datetime.now().strftime("%H:%M:%S")
    # Formato: TG|ID:Nombre|Mensaje|Hora|Lado(IN/OUT)
    linea = f"TG|{uid}:{name}|{msg}|{hora}|{side}"
    
    try:
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(linea + "\n")
            f.flush() # Forzado de escritura al disco
        print(f"✅ [{side}] {name}: {msg}")
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

    # Guardamos con la nueva lógica V10
    await asyncio.to_thread(registrar_v10, user.id, user.first_name, msg, "IN")

# =========================
# 🚀 NÚCLEO DEL BOT
# =========================

async def main():
    # 1. Configuración de la App
    app = Application.builder().token(TOKEN).build()

    # 2. Manejador de mensajes de texto
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, recibir))

    # 3. Inicialización limpia (Tu lógica ganadora)
    await app.initialize()
    await app.start()

    # 🔥 EL FIX QUE TE FUNCIONABA: Limpia actualizaciones viejas
    await app.bot.delete_webhook(drop_pending_updates=True)

    # 4. Iniciar Polling (Escucha activa)
    await app.updater.start_polling()

    print("💎 IMPERIO IMP V10 ONLINE (ESCUCHANDO...)")

    # 5. Loop de salida (Cola de mensajes desde la Web)
    while True:
        if os.path.exists(QUEUE_FILE):
            try:
                with open(QUEUE_FILE, "r", encoding="utf-8") as f:
                    cola = json.load(f)
                
                if cola:
                    for item in cola:
                        try:
                            # Enviar a Telegram
                            await app.bot.send_message(
                                chat_id=int(item["id"]),
                                text=item["msg"]
                            )
                            # Registrar en el log como mensaje de salida (OUT)
                            # Usamos el nombre del admin que respondió
                            admin_name = item.get("op", "ADMIN")
                            registrar_v10(item["id"], f"OP({admin_name})", item["msg"], "OUT")
                            
                            print(f"✔ Enviado a {item['id']} por {admin_name}")
                        except Exception as e:
                            print(f"❌ Error enviando a {item['id']}: {e}")

                    # Limpiar cola después de procesar
                    with open(QUEUE_FILE, "w", encoding="utf-8") as f:
                        json.dump([], f)
            except Exception as e:
                print(f"⚠ Error en ciclo de cola: {e}")

        await asyncio.sleep(0.8) # Velocidad de respuesta V10

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n🛑 Sistema apagado por el operador.")
