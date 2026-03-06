import logging

import requests

from config import VOTANTES_API_URL, VOTANTES_API_KEY

logger = logging.getLogger(__name__)


def buscar_votante(cedula: str) -> dict | None:
    """Buscar votante por número de cédula en la API.

    Retorna el dict con los datos del votante o None si no se encuentra.
    """
    url = f"{VOTANTES_API_URL}/{cedula}"
    headers = {
        "accept": "application/json",
        "X-API-Key": VOTANTES_API_KEY,
    }

    try:
        resp = requests.get(url, headers=headers, timeout=30)
        if resp.status_code == 404:
            return None
        resp.raise_for_status()
        return resp.json()
    except requests.RequestException as e:
        logger.error("Error consultando API de votantes para cédula %s: %s", cedula, e)
        return None


def formatear_datos_votante(datos: dict) -> str:
    """Formatear los datos del votante para enviar por WhatsApp."""
    return (
        f"📋 *Datos encontrados:*\n\n"
        f"👤 *Nombre:* {datos.get('nombre_completo', 'N/A')}\n"
        f"🆔 *Cédula:* {datos.get('cedula', 'N/A')}\n"
        f"📍 *Departamento:* {datos.get('departamento_votacion', 'N/A')}\n"
        f"🏙️ *Municipio:* {datos.get('municipio_votacion', 'N/A')}\n"
        f"🏫 *Puesto:* {datos.get('puesto', 'N/A')}\n"
        f"📝 *Mesa:* {datos.get('mesa', 'N/A')}\n"
        f"📌 *Dirección:* {datos.get('direccion', 'N/A')}\n"
        f"🗺️ *Zona:* {datos.get('zona', 'N/A')}"
    )
