import os
from pathlib import Path

from dotenv import load_dotenv

# Cargar variables de entorno desde .env
_env_path = Path(__file__).resolve().parent / ".env"
load_dotenv(_env_path)


def _require_env(name: str) -> str:
    """Obtener variable de entorno requerida o lanzar error."""
    value = os.environ.get(name)
    if not value:
        raise RuntimeError(f"Variable de entorno requerida no configurada: {name}")
    return value


# WhatsApp Meta API
WHATSAPP_TOKEN = _require_env("WHATSAPP_TOKEN")
WHATSAPP_PHONE_NUMBER_ID = _require_env("WHATSAPP_PHONE_NUMBER_ID")
WHATSAPP_VERIFY_TOKEN = os.environ.get("WHATSAPP_VERIFY_TOKEN", "controlelectoral2026")
WHATSAPP_API_VERSION = "v21.0"
WHATSAPP_API_URL = f"https://graph.facebook.com/{WHATSAPP_API_VERSION}/{WHATSAPP_PHONE_NUMBER_ID}/messages"

# API Votantes
VOTANTES_API_URL = "https://apivotantes.helppiu.com/completo"
VOTANTES_API_KEY = _require_env("VOTANTES_API_KEY")

# Firebase
FIREBASE_DATABASE_URL = _require_env("FB_DATABASE_URL")
FIREBASE_STORAGE_BUCKET = _require_env("FB_STORAGE_BUCKET")
FIREBASE_CREDENTIALS_PATH = os.environ.get(
    "FB_CREDENTIALS_PATH", ""
)

# Conversación
CONVERSATION_TIMEOUT_HOURS = 24
