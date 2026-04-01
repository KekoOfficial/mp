import asyncio
import json
import os
import datetime
import sqlite3
import logging
import psutil
from telegram import Update
from telegram.ext import Application, MessageHandler, ContextTypes, filters
from instagrapi import Client
from config import TOKEN, LOG_FILE, QUEUE_FILE, IG_USER, IG_PASS

# --- CONFIGURACIÓN DE RUTAS Y CONSTANTES DE SISTEMA ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MEDIA_DIR = os.path.join(BASE_DIR, "static/media")
DB_PATH = os.path.join(BASE_DIR, "database/mpserver.db")
os.makedirs(MEDIA_DIR, exist_ok=True)
os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)

# Configuración de Logs del Sistema (Terminal)
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger("MPServer_Titan")

# ==========================================
# 🗄️ GESTIÓN DE BASE DE DATOS (SQLITE3)
# ==========================================

def inicializar_db():
    """Crea la estructura de datos si no existe."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS mensajes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            plataforma TEXT,
            remitente_id TEXT,
            remitente_nombre TEXT,
            contenido TEXT,
            tipo TEXT,
            fecha_hora DATETIME,
            visto INTEGER DEFAULT 0
        )
    ''')
    conn.commit()
    conn.close()

def guardar_mensaje(plat, rid, rname, texto, tipo="text"):
    """Guarda el mensaje tanto en el TXT (compatibilidad) como en SQL (velocidad)."""
    ahora = datetime.datetime.now()
    hora_txt = ahora.strftime("%H:%M")
    
    # 1. Guardar en TXT para tu lógica actual
    linea = f"{plat}|{rid}:{rname}|{texto}|{hora_txt}|{tipo}"
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(linea + "\n")
    
    # 2. Guardar en SQL para futuras expansiones
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO mensajes (plataforma, remitente_id, remitente_nombre, contenido, tipo, fecha_hora)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (plat, rid, rname, texto, tipo, ahora))
        conn.commit()
        conn.close()
    except Exception as e:
        logger.error(f"Error SQL: {e}")

# ==========================================
# 📸 MOTOR INSTAGRAM (CORE V5 - ELITE)
# ==========================================

class InstagramManager:
    def __init__(self):
        self.cl = Client()
        self.session_path = os.path.join(BASE_DIR, "database/ig_session.json")
        self.is_online = False

    async def conectar(self):
        try:
            if os.path.exists(self.session_path):
                self.cl.load_settings(self.session_path)
            
            logger.info(f"Iniciando sesión en Instagram: {IG_USER}...")
            self.cl.login(IG_USER, IG_PASS)
            self.cl.dump_settings(self.session_path)
            self.is_online = True
            logger.info("✅ MOTOR INSTAGRAM CONECTADO")
        except Exception as e:
            logger.error(f"❌ Error crítico IG: {e}")
            self.is_online = False

    async def ciclo_escaneo(self):
        while True:
            if not self.is_online:
                await self.conectar()
                await asyncio.sleep(60)
                continue

            try:
                # amount=10 para capturar más conversaciones simultáneas
                threads = self.cl.get_direct_threads(amount=10)
                for t in threads:
                    if t.read_state > 0:
                        m = t.messages[0]
                        if str(m.user_id) != str(self.cl.user_id):
                            tipo = "text"
                            content = m.text if m.text else "[Multimedia]"
                            
                            if m.item_type == 'media': tipo = "image"
                            elif m.item_type == 'clip': tipo = "video"
                            
                            guardar_mensaje("IG", t.id, t.thread_title, content, tipo)
                            self.cl.direct_thread_mark_as_seen(t.id)
                
                # Reporte de salud al sistema
                await self.reportar_salud()
            except Exception as e:
                logger.warning(f"Ciclo IG interrumpido: {e}")
                if "login_required" in str(e): self.is_online = False
            
            await asyncio.sleep(45)

    async def reportar_salud(self):
        status = {
            "motor": "Instagram",
            "cpu": f"{psutil.cpu_percent()}%",
            "ram": f"{psutil.virtual_memory().percent}%",
            "hora": datetime.datetime.now().strftime("%H:%M:%S")
        }
        with open("database/health.json", "w") as f:
            json.dump(status, f)

# ==========================================
# 🤖 MOTOR TELEGRAM (PRO-HANDLER)
# ==========================================

async def receptor_multimedia_tg(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message: return
    user = update.effective_user
    rid, rname = str(user.id), user.first_name
    
    # Procesamiento por tipo de archivo
    try:
        if update.message.photo:
            file = await context.bot.get_file(update.message.photo[-1].file_id)
            path = os.path.join(MEDIA_DIR, f"tg_img_{file.file_id}.jpg")
            await file.download_to_drive(path)
            guardar_mensaje("TG", rid, rname, f"/static/media/{os.path.basename(path)}", "image")

        elif update.message.video:
            file = await context.bot.get_file(update.message.video.file_id)
            path = os.path.join(MEDIA_DIR, f"tg_vid_{file.file_id}.mp4")
            await file.download_to_drive(path)
            guardar_mensaje("TG", rid, rname, f"/static/media/{os.path.basename(path)}", "video")

        elif update.message.text:
            guardar_mensaje("TG", rid, rname, update.message.text, "text")
            
    except Exception as e:
        logger.error(f"Error Media TG: {e}")

# ==========================================
# ⚡ DESPACHADOR TITAN (ORDEN DE SALIDA)
# ==========================================

async def despachador_central(app, ig_manager):
    while True:
        if os.path.exists(QUEUE_FILE):
            try:
                with open(QUEUE_FILE, "r") as f:
                    cola = json.load(f)
                
                if cola:
                    for msg_task in cola:
                        pid = msg_task["id"]
                        txt = msg_task["msg"]
                        plat = msg_task.get("plat", "TG")

                        try:
                            if plat == "TG":
                                await app.bot.send_message(chat_id=pid, text=txt)
                            elif plat == "IG" and ig_manager.is_online:
                                ig_manager.cl.direct_answer(pid, txt)
                            
                            guardar_mensaje(plat, "YO", "YO", txt, "text")
                        except Exception as e:
                            logger.error(f"Fallo envío {plat} a {pid}: {e}")
                    
                    with open(QUEUE_FILE, "w") as f:
                        json.dump([], f)
            except Exception as e:
                logger.error(f"Error en cola: {e}")
        
        await asyncio.sleep(1.5)

# ==========================================
# 🏁 LANZAMIENTO GLOBAL
# ==========================================

async def main():
    inicializar_db()
    
    # 1. Configurar Telegram
    app_tg = Application.builder().token(TOKEN).build()
    app_tg.add_handler(MessageHandler(filters.ALL & ~filters.COMMAND, receptor_multimedia_tg))
    
    await app_tg.initialize()
    await app_tg.start()
    await app_tg.updater.start_polling(drop_pending_updates=False)

    # 2. Configurar Instagram
    ig_boss = InstagramManager()

    print("\n" + "="*40)
    print("💎 MPSERVER TITAN v5.0 - IMPERIO IMP")
    print(f"🚀 NÚCLEO ACTIVO: {datetime.datetime.now()}")
    print("="*40 + "\n")

    # 3. Ejecución de Tareas en Paralelo (Asincronía Total)
    await asyncio.gather(
        ig_boss.ciclo_escaneo(),
        despachador_central(app_tg, ig_boss)
    )

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n🛑 APAGANDO SISTEMAS... ¡HASTA LA PRÓXIMA, NOA!")
