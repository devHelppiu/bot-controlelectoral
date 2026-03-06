import logging

import requests

from config import WHATSAPP_API_URL, WHATSAPP_TOKEN

logger = logging.getLogger(__name__)


def _headers():
    return {
        "Authorization": f"Bearer {WHATSAPP_TOKEN}",
        "Content-Type": "application/json",
    }


def send_text(to: str, text: str) -> dict:
    """Enviar mensaje de texto simple."""
    payload = {
        "messaging_product": "whatsapp",
        "to": to,
        "type": "text",
        "text": {"body": text},
    }
    resp = requests.post(WHATSAPP_API_URL, json=payload, headers=_headers(), timeout=30)
    resp.raise_for_status()
    return resp.json()


def send_buttons(to: str, body_text: str, buttons: list[dict]) -> dict:
    """Enviar mensaje con botones interactivos.

    buttons: [{"id": "btn_si", "title": "Sí"}, {"id": "btn_no", "title": "No"}]
    """
    payload = {
        "messaging_product": "whatsapp",
        "to": to,
        "type": "interactive",
        "interactive": {
            "type": "button",
            "body": {"text": body_text},
            "action": {
                "buttons": [
                    {"type": "reply", "reply": {"id": b["id"], "title": b["title"]}}
                    for b in buttons[:3]  # WhatsApp permite máximo 3 botones
                ]
            },
        },
    }
    resp = requests.post(WHATSAPP_API_URL, json=payload, headers=_headers(), timeout=30)
    resp.raise_for_status()
    return resp.json()


def mark_as_read(message_id: str) -> dict:
    """Marcar mensaje como leído."""
    payload = {
        "messaging_product": "whatsapp",
        "status": "read",
        "message_id": message_id,
    }
    resp = requests.post(WHATSAPP_API_URL, json=payload, headers=_headers(), timeout=30)
    resp.raise_for_status()
    return resp.json()
