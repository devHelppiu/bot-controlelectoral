"""Entry point — Firebase Cloud Function para webhook de WhatsApp."""

import logging

import firebase_admin
from firebase_admin import credentials
from firebase_functions import https_fn, options

from config import (
    WHATSAPP_VERIFY_TOKEN,
    FIREBASE_DATABASE_URL,
    FIREBASE_STORAGE_BUCKET,
    FIREBASE_CREDENTIALS_PATH,
)
from whatsapp.handler import parse_message
from conversation.flow import procesar_mensaje

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Inicializar Firebase Admin SDK
if not firebase_admin._apps:
    import os

    init_options = {
        "databaseURL": FIREBASE_DATABASE_URL,
        "storageBucket": FIREBASE_STORAGE_BUCKET,
    }
    # En Cloud Functions, las credenciales se detectan automáticamente.
    # En local, usar el archivo de service account.
    cred_path = FIREBASE_CREDENTIALS_PATH
    if os.path.exists(cred_path):
        cred = credentials.Certificate(cred_path)
        firebase_admin.initialize_app(cred, init_options)
    else:
        firebase_admin.initialize_app(options=init_options)


@https_fn.on_request(
    cors=options.CorsOptions(cors_origins="*", cors_methods=["GET", "POST"]),
    region="us-central1",
    memory=options.MemoryOption.MB_256,
    timeout_sec=120,
)
def webhook(req: https_fn.Request) -> https_fn.Response:
    """Webhook para recibir mensajes de WhatsApp (Meta Cloud API).

    GET  → Verificación del webhook (challenge de Meta)
    POST → Procesar mensajes entrantes
    """
    if req.method == "GET":
        return _verify_webhook(req)

    if req.method == "POST":
        return _handle_message(req)

    return https_fn.Response("Method not allowed", status=405)


def _verify_webhook(req: https_fn.Request) -> https_fn.Response:
    """Verificar webhook con Meta (subscription verification)."""
    mode = req.args.get("hub.mode")
    token = req.args.get("hub.verify_token")
    challenge = req.args.get("hub.challenge")

    if mode == "subscribe" and token == WHATSAPP_VERIFY_TOKEN:
        logger.info("Webhook verificado exitosamente")
        return https_fn.Response(challenge, status=200)

    logger.warning("Verificación de webhook fallida: token inválido")
    return https_fn.Response("Forbidden", status=403)


def _handle_message(req: https_fn.Request) -> https_fn.Response:
    """Procesar mensaje entrante de WhatsApp."""
    try:
        body = req.get_json(silent=True)
        if not body:
            return https_fn.Response("OK", status=200)

        mensaje = parse_message(body)
        if mensaje is None:
            # Podría ser una notificación de estado, no un mensaje
            return https_fn.Response("OK", status=200)

        logger.info(
            "Mensaje recibido de %s: tipo=%s",
            mensaje["from_number"],
            mensaje["type"],
        )

        procesar_mensaje(mensaje)

    except Exception as e:
        logger.error("Error procesando webhook: %s", e, exc_info=True)

    # Siempre retornar 200 para que Meta no reintente
    return https_fn.Response("OK", status=200)
