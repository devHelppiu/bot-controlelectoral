import logging
import time
import io

from firebase_admin import storage

logger = logging.getLogger(__name__)


def subir_foto_carnet(cedula: str, image_bytes: bytes, content_type: str = "image/jpeg") -> str:
    """Subir foto del carnet electoral a Firebase Storage.

    Retorna la URL pública de la imagen.
    """
    bucket = storage.bucket()
    timestamp = int(time.time())
    blob_name = f"fotos_carnet/{cedula}_{timestamp}.jpg"
    blob = bucket.blob(blob_name)

    blob.upload_from_string(image_bytes, content_type=content_type)
    blob.make_public()

    logger.info("Foto subida: %s", blob.public_url)
    return blob.public_url
