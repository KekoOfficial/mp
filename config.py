import os

# --- TOKEN TELEGRAM ---
TOKEN = "TU_TOKEN_DE_TELEGRAM_AQUI"

# --- CONFIGURACIÓN GLOBAL ---
DOMAIN_NAME = "mpserver.net" # Tu dominio personalizado
AUTH_TOKEN = "IMP_V9_GLOBAL_NOA"
MAX_ADMINS = 10

# --- ESTRUCTURA DE DIRECTORIOS ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
LOG_FILE = os.path.join(BASE_DIR, "logs.txt")
QUEUE_FILE = os.path.join(BASE_DIR, "queue.json")
DB_PATH = os.path.join(BASE_DIR, "database/imperio_v9.db")
MEDIA_DIR = os.path.join(BASE_DIR, "static/media")

# Asegurar carpetas
for folder in [os.path.dirname(DB_PATH), MEDIA_DIR]:
    os.makedirs(folder, exist_ok=True)
