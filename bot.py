import asyncio
import json
import os
import datetime
from telegram import Update
from telegram.ext import Application, MessageHandler, ContextTypes, filters
from instagrapi import Client
from config import TOKEN, LOG_FILE, QUEUE_FILE, IG_USER, IG_PASS

# Configuración de carpetas
os.makedirs("static/avatars", exist_ok=True)

# Instancia Global de Instagram
ig_client = Client()

# ==========================================
# 📂 UTILIDADES DE DATOS
# ==========================================

def registrar_log(user_id, nombre, mensaje, plataforma):
    """Guarda los mensajes de ambas redes en el mismo archivo."""
    timestamp = datetime.datetime.now().strftime("%H:%M")
    # Formato: ID|PLATAFORMA|NOMBRE: MENSAJE | HORA
    linea = f"{user_id}|{plataforma}|{nombre}: {mensaje} | {timestamp}"
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(linea + "\n")
    print(f"📩 [{plataforma}] {nombre}: {mensaje}")

def leer_cola():
    if os.path.exists(QUEUE_FILE):
        try:
            with open(QUEUE_FILE, "r") as f: return json.load(f)
        except: return []
    return []

def limpiar_cola():
    with open(QUEUE_FILE, "w") as f: json.dump([], f)

# ==========================================
# 🤖 MOTOR TELEGRAM
# ==========================================

async def mensaje_tg(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text: return
    user = update.effective_user
    registrar_log(user.id, user.first_name, update.message.text, "TG")

# ==========================================
# 📸 MOTOR INSTAGRAM
# ==========================================

async def motor_instagram():
    """Bucle que revisa DMs de Instagram cada minuto."""
    if not IG_USER or not IG_PASS:
        print("⚠️ Instagram no configurado. Saltando motor IG.")
        return

    try:
        print(f"🔐 Conectando Motor Instagram (@{IG_USER})...")
        # Intentamos cargar sesión previa para evitar bloqueos
        ig_client.login(IG_USER, IG_PASS)
        print("✅ Motor Instagram: ONLINE")
    except Exception as e:
        print(f"❌ Error Motor Instagram: {e}")
        return

    while True:
        try:
            # Revisar hilos de mensajes directos
            threads = ig_client.get_direct_threads()
            for thread in threads:
                # Si el último mensaje no es nuestro y no está leído
                if thread.read_state == 1:
                    last_msg = thread.messages[0]
                    if last_msg.user_id != ig_client.user_id:
                        user_info = ig_client.user_info(last_msg.user_id)
                        registrar_log(thread.id, user_info.full_name, last_msg.text, "IG")
                        # Opcional: Marcar como visto
                        # ig_client.direct_thread_mark_as_seen(thread.id)
        except Exception as e:
            print(f"⚠️ Error en Motor IG: {e}")
        
        await asyncio.sleep(60) # Espera 1 minuto para seguridad

# ==========================================
# 🚀 ARRANQUE DE CONSOLA
# ==========================================

async def main():
    # 1. Configurar Telegram
    app_tg = Application.builder().token(TOKEN).build()
    app_tg.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, mensaje_tg))

    await app_tg.initialize()
    await app_tg.start()
    
    # drop_pending_updates=False para que lea lo que pasó mientras estaba apagado
    await app_tg.updater.start_polling(drop_pending_updates=False)

    # 2. Iniciar Motor Instagram en segundo plano
    asyncio.create_task(motor_instagram())

    print("---------------------------------")
    print("🚀 MPSERVER: MULTI-MOTOR ACTIVO")
    print("---------------------------------")

    # 3. Bucle de respuestas (Queue)
    while True:
        cola = leer_cola()
        if cola:
            for item in cola:
                try:
                    # Detectar plataforma para responder
                    # Si el ID es puramente numérico y largo, suele ser TG. 
                    # Podrías mejorar esto guardando la plataforma en la cola también.
                    await app_tg.bot.send_message(chat_id=item["id"], text=item["msg"])
                    print(f"✔ Respondido a {item['id']} (TG)")
                except Exception as e:
                    print(f"❌ Error enviando respuesta: {e}")
            limpiar_cola()

        await asyncio.sleep(2)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nTerminando MpServer...")
