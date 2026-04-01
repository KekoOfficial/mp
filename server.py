import asyncio
import json
import os
from threading import Thread
from flask import Flask, request, jsonify, render_template

from telegram import Update, Bot
from telegram.ext import Application, MessageHandler, ContextTypes, filters

# Importamos las variables desde tu config.py
from config import TOKEN, LOG_FILE, QUEUE_FILE, WEB_HOST, WEB_PORT

# =========================
# 🔥 CONFIGURACIÓN INICIAL
# =========================

app = Flask(__name__)
# Usamos el Application de python-telegram-bot v20+
tg_app = Application.builder().token(TOKEN).build()

# =========================
# 📂 UTILIDADES DE ARCHIVOS
# =========================

def save_log(text):
    """Guarda una línea en el archivo de logs."""
    try:
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(text + "\n")
    except Exception as e:
        print(f"❌ Error al guardar log: {e}")

def load_queue():
    """Carga la cola de mensajes pendientes desde el JSON."""
    if os.path.exists(QUEUE_FILE):
        try:
            with open(QUEUE_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            return []
    return []

def save_queue(q):
    """Guarda la lista de mensajes en el archivo JSON."""
    try:
        with open(QUEUE_FILE, "w", encoding="utf-8") as f:
            json.dump(q, f, indent=4)
    except Exception as e:
        print(f"❌ Error al guardar cola: {e}")

def load_logs():
    """Lee las últimas 100 líneas del log para el panel."""
    if os.path.exists(LOG_FILE):
        try:
            with open(LOG_FILE, "r", encoding="utf-8") as f:
                return f.readlines()[-100:]
        except:
            return ["Error al leer el archivo de logs."]
    return ["No hay logs disponibles."]

# =========================
# 🤖 LÓGICA DEL BOT (RECIBIR)
# =========================

async def manejar_mensaje(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Maneja los mensajes entrantes de Telegram."""
    if not update.message or not update.message.text:
        return

    user = update.effective_user
    msg = update.message.text
    
    # Formato: ID|Nombre: Mensaje (Importante para el JS del panel)
    line = f"{user.id}|{user.first_name}: {msg}"
    
    print(f"📩 Nuevo mensaje de {user.first_name}: {msg}")
    save_log(line)

# Añadimos el manejador al bot
tg_app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, manejar_mensaje))

# =========================
# 📡 RUTAS FLASK (PANEL WEB)
# =========================

@app.route("/")
def home():
    """Renderiza el panel de chat principal."""
    return render_template("index.html")

@app.route("/settings")
def settings():
    """Renderiza la página de configuración."""
    return render_template("set.html")

@app.route("/send", methods=["POST"])
def send_api():
    """Recibe mensajes desde el panel web y los encola."""
    data = request.json
    if not data or "id" not in data or "msg" not in data:
        return jsonify({"status": "error", "message": "Datos incompletos"}), 400

    queue = load_queue()
    queue.append({
        "id": data["id"],
        "msg": data["msg"]
    })
    save_queue(queue)
    
    return jsonify({"status": "ok"})

@app.route("/logs")
def get_logs():
    """Devuelve los logs en formato JSON."""
    return jsonify({"logs": load_logs()})

# =========================
# 🔄 BUCLE DE ENVÍO Y BOT
# =========================

async def run_bot_logic():
    """Inicializa el bot y procesa la cola de mensajes de salida."""
    await tg_app.initialize()
    await tg_app.start()
    
    # Limpiamos mensajes acumulados mientras el bot estaba apagado
    await tg_app.bot.delete_webhook(drop_pending_updates=True)
    await tg_app.updater.start_polling()

    print(f"🚀 PANEL WEB EN: http://{WEB_HOST}:{WEB_PORT}")
    print("🤖 BOT DE TELEGRAM ONLINE")

    while True:
        queue = load_queue()
        if queue:
            for item in queue:
                try:
                    await tg_app.bot.send_message(
                        chat_id=int(item["id"]),
                        text=item["msg"]
                    )
                    print(f"✔ Mensaje enviado a ID {item['id']}")
                except Exception as e:
                    print(f"❌ Error al enviar a {item['id']}: {e}")
            
            # Limpiar cola tras procesar
            save_queue([])
            
        await asyncio.sleep(1) # Pausa para no saturar el procesador

# =========================
# 🚀 EJECUCIÓN PRINCIPAL
# =========================

def start_web():
    """Función para correr Flask en un hilo aparte."""
    # Desactivamos el reloader para evitar conflictos con hilos
    app.run(host=WEB_HOST, port=WEB_PORT, debug=False, use_reloader=False)

async def main():
    """Punto de entrada principal."""
    # Ejecutamos el servidor web en un hilo
    Thread(target=start_web, daemon=True).start()
    
    # Ejecutamos la lógica del bot en el hilo principal
    await run_bot_logic()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        print("\n🛑 Servidor apagado correctamente.")
