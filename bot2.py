import asyncio
import json
import os
import datetime
import requests
from telegram import Update
from telegram.ext import Application, MessageHandler, ContextTypes, filters

from config import TOKEN_BOT_2, LOG_GLOBAL, CONSOLA_URL

# =========================
# 🎨 LÓGICA DE RANGOS MP
# =========================

def obtener_rango(uid):
    """Asigna rangos y colores neón basados en el ID o jerarquía"""
    # Ejemplo de IDs de confianza (puedes añadir los de Martín Mp y sus generales)
    admins_id = [123456789, 987654321] 
    vips_id = [555666777]

    if uid in admins_id:
        return {"nom": "FUNDADOR", "col": "#ff003c"} # Rojo Alerta
    elif uid in vips_id:
        return {"nom": "GENERAL", "col": "#00e5ff"}  # Cian Eléctrico
    else:
        return {"nom": "GUERRERO", "col": "#00ff41"} # Verde Matrix

# =========================
# 📂 ESCRITURA V10 GLOBAL
# =========================

def registrar_global(uid, name, msg, pfp_url):
    """Formato avanzado para el Global Chat de 5,975 miembros"""
    hora = datetime.datetime.now().strftime("%H:%M:%S")
    rango = obtener_rango(uid)
    
    # Estructura de datos completa para la web
    datos_mensaje = {
        "id": uid,
        "user": name,
        "msg": msg,
        "hora": hora,
        "rango": rango["nom"],
        "color": rango["col"],
        "foto": pfp_url or "https://via.placeholder.com/50" # Foto por defecto
    }

    # 1. Guardar en Log Físico (Igual que el Bot 1)
    linea = f"GLOBAL|{uid}|{name}|{rango['nom']}|{msg}|{hora}"
    with open(LOG_GLOBAL, "a", encoding="utf-8") as f:
        f.write(linea + "\n")

    # 2. Puente hacia consola.js para actualización en tiempo real
    try:
        requests.post(f"{CONSOLA_URL}/api/global_stream", json=datos_mensaje, timeout=1)
    except:
        pass

# =========================
# 📩 RECEPTOR MASIVO
# =========================

async def recibir_global(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text:
        return

    user = update.effective_user
    msg = update.message.text
    
    # Intentar obtener foto de perfil del miembro
    pfp_url = ""
    try:
        fotos = await user.get_profile_photos(limit=1)
        if fotos.total_count > 0:
            file = await context.bot.get_file(fotos.photos[0][-1].file_id)
            pfp_url = file.file_path
    except:
        pfp_url = "https://i.imgur.com/8K9mK9m.png" # Icono Imperio MP

    # Ejecutar registro V10 sin bloquear el bot
    await asyncio.to_thread(registrar_global, user.id, user.first_name, msg, pfp_url)

# =========================
# 🚀 NÚCLEO GLOBAL V10
# =========================

async def main():
    app = Application.builder().token(TOKEN_BOT_2).build()
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, recibir_global))

    await app.initialize()
    await app.start()
    
    # Limpieza total para que el Imperio arranque sin mensajes viejos
    await app.bot.delete_webhook(drop_pending_updates=True)
    await app.updater.start_polling()

    print(f"🌐 MOTOR GLOBAL V10 ONLINE - PROTEGIENDO A 5,975 MIEMBROS")

    # Mantener el motor despierto
    while True:
        await asyncio.sleep(10)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n🛑 Motor Global apagado.")
