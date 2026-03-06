import logging

logger = logging.getLogger(__name__)


def parse_message(body: dict) -> dict | None:
    """Parsear payload de webhook de Meta y extraer información relevante.

    Retorna un dict con:
      - from_number: str (número del remitente)
      - message_id: str
      - type: str ("text", "image", "button_reply")
      - text: str | None (contenido del texto)
      - button_id: str | None (id del botón presionado)
      - image_id: str | None (media id de la imagen)
    """
    try:
        entry = body.get("entry", [])
        if not entry:
            return None

        changes = entry[0].get("changes", [])
        if not changes:
            return None

        value = changes[0].get("value", {})
        messages = value.get("messages", [])
        if not messages:
            return None

        msg = messages[0]
        from_number = msg.get("from", "")
        message_id = msg.get("id", "")
        msg_type = msg.get("type", "")

        result = {
            "from_number": from_number,
            "message_id": message_id,
            "type": None,
            "text": None,
            "button_id": None,
            "image_id": None,
        }

        if msg_type == "text":
            result["type"] = "text"
            result["text"] = msg.get("text", {}).get("body", "").strip()

        elif msg_type == "interactive":
            interactive = msg.get("interactive", {})
            if interactive.get("type") == "button_reply":
                result["type"] = "button_reply"
                result["button_id"] = interactive.get("button_reply", {}).get("id", "")
                result["text"] = interactive.get("button_reply", {}).get("title", "")

        elif msg_type == "image":
            result["type"] = "image"
            result["image_id"] = msg.get("image", {}).get("id", "")

        else:
            result["type"] = msg_type

        return result

    except (KeyError, IndexError) as e:
        logger.error("Error parseando mensaje de WhatsApp: %s", e)
        return None
