import asyncio
import json
import os
import datetime
import sys
import psutil
import time
import sqlite3
import logging
import shutil
import platform
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, MessageHandler, CommandHandler, ContextTypes, filters
from config import TOKEN, LOG_FILE, QUEUE_FILE

# --- CONFIGURACIÓN DE NÚCLEO ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "database/omega_core.db")
LOG_PATH = os.path.join(BASE_DIR, LOG_FILE)
QUEUE_PATH = os.path.join(BASE_DIR, QUEUE_FILE)
MEDIA_DIR = os.path.join(BASE_DIR, "static/media")
BACKUP_DIR = os.path.join(BASE_DIR, "backups")

# Inicialización de Entorno
for path in [os.path.dirname(DB_PATH), MEDIA_DIR, BACKUP_DIR]:
    os.makedirs(path, exist_ok=True)

# Logging Industrial
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
    handlers=[logging.FileHandler("database/system.log"), logging.StreamHandler()]
)
logger = logging.getLogger("OMEGA_CORE")

# ==========================================
# 🧠 GESTIÓN DE DATOS MASIVA (SQLITE PRO)
# ==========================================

class DataCenter:
    @staticmethod
    def init():
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        # Tabla de Mensajes (Log Infinito)
        cursor.execute('''CREATE TABLE IF NOT EXISTS logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            plat TEXT, uid TEXT, name TEXT, content TEXT, 
            type TEXT, timestamp DATETIME DEFAULT CURRENT_TIMESTAMP)''')
        # Tabla de Usuarios (CRM)
        cursor.execute('''CREATE TABLE IF NOT EXISTS users (
            uid TEXT PRIMARY KEY, name TEXT, username TEXT, 
            last_seen DATETIME, msg_count INTEGER DEFAULT 0)''')
        # Tabla de Configuración Dinámica
        cursor.execute('''CREATE TABLE IF NOT EXISTS settings (
            key TEXT PRIMARY KEY, value TEXT)''')
        conn.commit()
        conn.close()

    @staticmethod
    def save(plat, uid, name, msg, mtype="text", uname="N/A"):
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        # 1. Guardar Mensaje
        cursor.execute("INSERT INTO logs (plat, uid, name, content, type) VALUES (?,?,?,?,?)",
                     (plat, str(uid), name, str(msg), mtype))
        # 2. Actualizar/Crear Usuario
        cursor.execute('''INSERT INTO users (uid, name, username, last_seen, msg_count) 
                          VALUES (?,?,?,?,1) ON CONFLICT(uid) DO UPDATE SET 
                          last_seen=excluded.last_seen, msg_count=msg_count+1''', 
                       (str(uid), name, uname, datetime.datetime.now()))
        conn.commit()
        conn.close()
        
        # Sincronización con el TXT de la Web (Compatibilidad)
        with open(LOG_PATH, "a", encoding="utf-8") as f:
            hora = datetime.datetime.now().strftime("%H:%M")
            f.write(f"{plat}|{uid}:{name}|{msg}|{hora}|{mtype}\n")

# ==========================================
# 🛠️ SISTEMA DE COMANDOS "OMEGA"
# ==========================================

async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    kb = [
        [KeyboardButton("📊 Monitor Full"), KeyboardButton("🔋 Energía")],
        [KeyboardButton("📁 Backups"), KeyboardButton("🌐 Network")],
        [KeyboardButton("⚙️ Ajustes"), KeyboardButton("🧹 Purga")]
    ]
    await update.message.reply_text(
        "🚀 **SISTEMA OMEGA v7.0 ONLINE**\nBienvenido, Noa. Infraestructura lista.",
        reply_markup=ReplyKeyboardMarkup(kb, resize_keyboard=True), parse_mode="Markdown"
    )

async def manager_sistema(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    
    if text == "📊 Monitor Full":
        mem = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        net = psutil.net_io_counters()
        msg = (f"🖥️ **TELEMETRÍA:**\n"
               f"🔥 CPU: `{psutil.cpu_percent()}%` @ {psutil.cpu_count()} Cores\n"
               f"🧠 RAM: `{mem.percent}%` ({mem.used//1024**2}MB usados)\n"
               f"💾 DISCO: `{disk.percent}%` libres\n"
               f"📡 RED: ↑{net.bytes_sent//1024}KB ↓{net.bytes_recv//1024}KB")
        await update.message.reply_text(msg, parse_mode="Markdown")

    elif text == "📁 Backups":
        zip_name = f"backups/IMP_{int(time.time())}"
        shutil.make_archive(zip_name, 'zip', "database")
        await update.message.reply_document(document=open(f"{zip_name}.zip", 'rb'), caption="📦 Backup de DB y Logs.")

    elif text == "🌐 Network":
        import socket
        hostname = socket.gethostname()
        local_ip = socket.gethostbyname(hostname)
        await update.message.reply_text(f"🌐 **RED:**\nHost: `{hostname}`\nLocal: `{local_ip}:5000`\nOS: `{platform.system()} {platform.release()}`", parse_mode="Markdown")

# ==========================================
# 📥 PROCESADOR DE ENTRADA MASIVA
# ==========================================

async def gateway_mensajes(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message: return
    user = update.effective_user
    uid, name, uname = user.id, user.first_name, user.username or "N/A"

    # Clasificación Automática de 1000 Posibilidades
    try:
        # Texto
        if update.message.text:
            if update.message.text.startswith('/'): return
            DataCenter.save("TG", uid, name, update.message.text, "text", uname)

        # Imágenes (HD)
        elif update.message.photo:
            file = await context.bot.get_file(update.message.photo[-1].file_id)
            path = f"static/media/img_{int(time.time())}.jpg"
            await file.download_to_drive(path)
            DataCenter.save("TG", uid, name, f"/{path}", "image", uname)

        # Notas de Voz / Audio
        elif update.message.voice or update.message.audio:
            media = update.message.voice if update.message.voice else update.message.audio
            file = await context.bot.get_file(media.file_id)
            path = f"static/media/aud_{int(time.time())}.ogg"
            await file.download_to_drive(path)
            DataCenter.save("TG", uid, name, f"/{path}", "audio", uname)

        # Ubicación en Tiempo Real
        elif update.message.location:
            loc = update.message.location
            url = f"https://www.google.com/maps?q={loc.latitude},{loc.longitude}"
            DataCenter.save("TG", uid, name, url, "location", uname)

    except Exception as e:
        logger.error(f"Error en Gateway: {e}")

# ==========================================
# ⚡ MOTOR DE RESPUESTA Y AUTO-MANTENIMIENTO
# ==========================================

async def auto_cleaner():
    """Limpia archivos temporales cada 24 horas para no saturar Termux."""
    while True:
        await asyncio.sleep(86400)
        logger.info("🧹 Iniciando limpieza de mantenimiento...")
        # Aquí puedes agregar lógica para borrar archivos de más de 7 días

async def despacho_web(app):
    while True:
        if os.path.exists(QUEUE_PATH):
            try:
                with open(QUEUE_PATH, "r") as f:
                    cola = json.load(f)
                if cola:
                    for task in cola:
                        await app.bot.send_message(chat_id=task["id"], text=task["msg"])
                        DataCenter.save("TG", "YO", "ADMIN", task["msg"], "text")
                    with open(QUEUE_PATH, "w") as f: json.dump([], f)
            except: pass
        await asyncio.sleep(1)

# ==========================================
# 🏁 ARRANQUE MAESTRO
# ==========================================

async def main():
    DataCenter.init()
    app = Application.builder().token(TOKEN).build()

    # Handlers Pro
    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(MessageHandler(filters.Regex('^(📊 Monitor Full|🔋 Energía|📁 Backups|🌐 Network|⚙️ Ajustes|🧹 Purga)$'), manager_sistema))
    app.add_handler(MessageHandler(filters.ALL & ~filters.COMMAND, gateway_mensajes))

    logger.info("💎 MPSERVER OMEGA v7.0 - DESPLEGADO")
    
    await app.initialize()
    await app.start()
    await app.updater.start_polling(drop_pending_updates=True)

    await asyncio.gather(despacho_web(app), auto_cleaner())

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        sys.exit(0)
