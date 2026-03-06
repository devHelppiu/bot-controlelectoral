import logging

import requests

from config import WHATSAPP_TOKEN, WHATSAPP_API_VERSION

logger = logging.getLogger(__name__)


def download_media(media_id: str) -> bytes | None:
    """Descargar archivo multimedia de WhatsApp.

    1. Obtener la URL del media usando el media_id
    2. Descargar el archivo binario desde esa URL
    """
    headers = {"Authorization": f"Bearer {WHATSAPP_TOKEN}"}

    # Paso 1: Obtener URL del media
    media_url = f"https://graph.facebook.com/{WHATSAPP_API_VERSION}/{media_id}"
    resp = requests.get(media_url, headers=headers, timeout=30)
    resp.raise_for_status()
    media_data = resp.json()

    download_url = media_data.get("url")
    if not download_url:
        logger.error("No se encontró URL de descarga para media_id: %s", media_id)
        return None

    # Paso 2: Descargar el archivo
    resp = requests.get(download_url, headers=headers, timeout=60)
    resp.raise_for_status()
    return resp.content
