import io
import logging
import re

logger = logging.getLogger(__name__)

_ocr_engine = None


def _get_ocr():
    global _ocr_engine
    if _ocr_engine is None:
        from rapidocr_onnxruntime import RapidOCR
        _ocr_engine = RapidOCR()
    return _ocr_engine


def verificar_carnet(image_bytes: bytes, datos_votante: dict) -> dict:
    """Verificar la foto del carnet electoral usando OCR local (RapidOCR).

    Compara el texto extraído con los datos del votante.
    """
    from PIL import Image

    try:
        img = Image.open(io.BytesIO(image_bytes)).convert("RGB")
    except Exception:
        logger.warning("No se pudo abrir la imagen")
        return {
            "verificado": False,
            "texto_extraido": "",
            "coincidencias": [],
            "confianza": 0.0,
        }

    ocr = _get_ocr()
    result, _ = ocr(img)

    if not result:
        logger.warning("No se detectó texto en la imagen")
        return {
            "verificado": False,
            "texto_extraido": "",
            "coincidencias": [],
            "confianza": 0.0,
        }

    # result es lista de (bbox, texto, score)
    texto_completo = " ".join(line[1] for line in result).upper()
    logger.info("Texto OCR extraído: %s", texto_completo[:200])

    # Datos a buscar en el carnet
    cedula = str(datos_votante.get("cedula", ""))
    nombre_completo = datos_votante.get("nombre_completo", "").upper()

    coincidencias = []
    total_checks = 0

    # Verificar cédula
    if cedula:
        total_checks += 1
        cedula_limpia = re.sub(r"[.\s]", "", cedula)
        texto_limpio = re.sub(r"[.\s]", "", texto_completo)
        if cedula_limpia in texto_limpio:
            coincidencias.append(f"Cédula: {cedula}")

    # Verificar nombre
    if nombre_completo:
        total_checks += 1
        if nombre_completo in texto_completo:
            coincidencias.append(f"Nombre completo: {nombre_completo}")
        else:
            partes_encontradas = 0
            partes_totales = 0
            for parte in nombre_completo.split():
                if len(parte) > 2:
                    partes_totales += 1
                    if parte in texto_completo:
                        partes_encontradas += 1
            if partes_totales > 0 and partes_encontradas >= partes_totales * 0.6:
                coincidencias.append(
                    f"Nombre parcial: {partes_encontradas}/{partes_totales} partes"
                )

    confianza = len(coincidencias) / max(total_checks, 1)
    verificado = confianza >= 0.5

    return {
        "verificado": verificado,
        "texto_extraido": texto_completo[:500],
        "coincidencias": coincidencias,
        "confianza": confianza,
    }
