import os

# Configurações Base
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
APP_VERSION = "1.0.0"

# Pastas de Uploads
UPLOADS_DIR = os.path.join(BASE_DIR, "uploads")
PENDING_DIR = os.path.join(UPLOADS_DIR, "pending")
PROCESSED_DIR = os.path.join(UPLOADS_DIR, "processed")

# Base de Dados
DB_PATH = os.path.join(BASE_DIR, "smartinvoice.db")
SQLALCHEMY_DATABASE_URI = f"sqlite:///{DB_PATH}"

# Servidor Web (Mobile)
WEB_HOST = "0.0.0.0"
WEB_PORT = 5000

# Segurança
MOBILE_APP_TOKEN = "12345" # Placeholder para token temporário

# Integração Email IMAP (Para importação automática de faturas)
IMAP_SERVER = os.environ.get("IMAP_SERVER", "") # ex: imap.gmail.com
IMAP_PORT = int(os.environ.get("IMAP_PORT", 993))
IMAP_USER = os.environ.get("IMAP_USER", "")
IMAP_PASS = os.environ.get("IMAP_PASS", "")
