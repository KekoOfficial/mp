import os

# ==========================================
# 🔑 CREDENCIALES DE ACCESO (MODIFICAR AQUÍ)
# ==========================================
TOKEN = "TU_TOKEN_DE_TELEGRAM_AQUI"
IG_USER = "usuario_instagram"
IG_PASS = "password_instagram"

# Token Maestro para entrar a la Web desde cualquier país
# URL: http://tu-url.loca.lt/?auth=NOA_MASTER_2026
AUTH_TOKEN = "NOA_MASTER_2026"

# ==========================================
# 📂 RUTAS E INFRAESTRUCTURA
# ==========================================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Archivos Críticos
LOG_FILE = os.path.join(BASE_DIR, "logs.txt")
QUEUE_FILE = os.path.join(BASE_DIR, "queue.json")
DB_PATH = os.path.join(BASE_DIR, "database/imperio_omega.db")

# Directorios de Almacenamiento
MEDIA_DIR = os.path.join(BASE_DIR, "static/media")
STATIC_DIR = os.path.join(BASE_DIR, "static")
TEMPLATE_DIR = os.path.join(BASE_DIR, "templates")

# ==========================================
# ⚡ AJUSTES DE RED Y TUNEL
# ==========================================
WEB_HOST = "0.0.0.0"
WEB_PORT = 5000
SUBDOMAIN_LT = "imperio-imp-noa"  # Subdominio personalizado para LocalTunnel

# ==========================================
# 🛡️ SEGURIDAD Y RENDIMIENTO
# ==========================================
DEBUG_MODE = False        # Cambiar a True solo para desarrollo
MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # Límite de subida: 16MB
