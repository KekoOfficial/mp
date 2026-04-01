import asyncio
import json
import os
from threading import Thread
from flask import Flask, request, jsonify, render_template
from telegram import Update
from telegram.ext import Application, MessageHandler, ContextTypes, filters

# Configuración (Asegúrate de que config.py tenga TOKEN, LOG_FILE, QUEUE_FILE, WEB_HOST, WEB_PORT)
from config import TOKEN, LOG_FILE, QUEUE_FILE, WEB_HOST, WEB_PORT

app = Flask(__name__)
tg_app = Application.builder().token(TOKEN).build()

# Crear carpetas necesarias para fotos
if not os.path.exists("static/avatars"):
    os.makedirs("static/avatars")

# =========================
# 📂 GESTIÓN DE ARCHIVOS
# =========================

def save_log(text):
    """Guarda los mensajes en el archivo de logs."""
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(text + "\n")

def load_logs():
    """Carga las últimas 100 líneas del log."""
    if os.path.exists(LOG_FILE):
        with open(LOG_FILE, "r", encoding="utf-8") as f:
            return f.readlines()[-100:]
    return []

def get_queue():
    """Carga la cola de mensajes pendientes."""
    if os.path.exists(QUEUE_FILE):
        try:
            with open(QUEUE_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except: return []
    return []

def save_queue(q):
    """Guarda la cola de mensajes en el JSON."""
    with open(QUEUE_FILE, "w", encoding="utf-8") as f:
        json.dump(q, f, indent=4)

# =========================
# 📸 FOTOS DE PERFIL (AVATARS)
# =========================

async def descargar_foto_perfil(user_id, context):
    """Descarga la foto de perfil de Telegram si no existe localmente."""
    foto_path = f"static/avatars/{user_id}.jpg"
    if os.path.exists(foto_path):
        return
    try:
        fotos = await context.bot.get_user_profile_photos(user_id, limit=1)
        if fotos.total_count > 0:
            file = await context.bot.get_file(fotos.photos[0][0].file_id)
            await file.download_to_drive(foto_path)
            print(f"📸 Foto guardada para: {user_id}")
    except Exception as e:
        print(f"❌ Error al descargar foto de {user_id}: {e}")

# =========================
# 🤖 LÓGICA DEL BOT
# =========================

async def manejar_mensaje(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Procesa mensajes entrantes."""
    if not update.message or not update.message.text:
        return

    user = update.effective_user
    msg = update.message.text
    
    # Formato necesario para el panel web
    line = f"{user.id}|{user.first_name}: {msg}"
    save_log(line)
    
    # Tarea en segundo plano para la foto
    asyncio.create_task(descargar_foto_perfil(user.id, context))

tg_app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, manejar_mensaje))

# =========================
# 📡 RUTAS WEB (FLASK)
# =========================

# Rutas principales
@app.route("/")
def home(): return render_template("index.html")

@app.route("/settings")
def settings(): return render_template("set.html")

# Las 10 rutas adicionales solicitadas
@app.route("/perfil")
def perfil(): return render_template("perfil.html")

@app.route("/grupos")
def grupos(): return render_template("grupos.html")

@app.route("/llamadas")
def llamadas(): return render_template("llamadas.html")

@app.route("/novedades")
def novedades(): return render_template("novedades.html")

@app.route("/archivados")
def archivados(): return render_template("archivados.html")

@app.route("/privacidad")
def privacidad(): return render_template("privacidad.html")

@app.route("/seguridad")
def seguridad(): return render_template("seguridad.html")

@app.route("/notificaciones")
def notificaciones(): return render_template("notificaciones.html")

@app.route("/ayuda")
def ayuda(): return render_template("ayuda.html")

@app.route("/info")
def info(): return render_template("info.html")

# API para el panel
@app.route("/logs")
def api_logs():
    return jsonify({"logs": load_logs()})

@app.route("/send", methods=["POST"])
def api_send():
    data = request.json
    if not data: return jsonify({"status": "error"}), 400
    
    q = get_queue()
    q.append({"id": data["id"], "msg": data["msg"]})
    save_queue(q)
    return jsonify({"status": "ok"})

# =========================
# 🚀 EJECUCIÓN SÍNCRONA
# =========================

async def bot_worker():
    """Inicia el bot y procesa la cola de salida."""
    await tg_app.initialize()
    await tg_app.start()
    await tg_app.bot.delete_webhook(drop_pending_updates=True)
    await tg_app.updater.start_polling()

    print(f"✅ Web: http://{WEB_HOST}:{WEB_PORT}")
    print("✅ Bot de Telegram: Activo")

    while True:
        queue = get_queue()
        if queue:
            for item in queue:
                try:
                    await tg_app.bot.send_message(chat_id=int(item["id"]), text=item["msg"])
                except Exception as e:
                    print(f"❌ Error enviando a {item['id']}: {e}")
            save_queue([]) # Limpiar cola tras enviar
        await asyncio.sleep(1)

def run_flask():
    """Ejecuta Flask sin reloader para evitar conflictos de hilos."""
    app.run(host=WEB_HOST, port=WEB_PORT, debug=False, use_reloader=False)

if __name__ == "__main__":
    try:
        # Iniciar Flask en un hilo separado
        Thread(target=run_flask, daemon=True).start()
        # Ejecutar el Bot en el hilo principal
        asyncio.run(bot_worker())
    except (KeyboardInterrupt, SystemExit):
        print("\n🛑 Servidor detenido.")
