"""Máquina de estados para el flujo conversacional del bot de control electoral.

Estados:
    INICIO                      → Saludo + solicitar cédula
    ESPERANDO_CEDULA            → Validar formato, consultar API, verificar duplicados
    CONFIRMACION_DATOS          → Mostrar datos del votante, pedir confirmación (Sí/No)
    PREGUNTA_CONSULTA           → Preguntar si solicitó tarjetón de consulta
    ESPERANDO_CANDIDATO_CONSULTA→ Solicitar candidato de consulta presidencial
    CONFIRMANDO_CONSULTA        → Confirmar candidato de consulta
    ESPERANDO_CANDIDATO_SENADO  → Solicitar candidato de Senado
    CONFIRMANDO_SENADO          → Confirmar candidato de Senado
    ESPERANDO_CANDIDATO_CAMARA  → Solicitar candidato de Cámara
    CONFIRMANDO_CAMARA          → Confirmar candidato de Cámara
    ESPERANDO_FOTO              → Solicitar foto del carnet electoral
    COMPLETADO                  → Mensaje de agradecimiento
"""

import logging

from whatsapp.sender import send_text, send_buttons, mark_as_read
from whatsapp.media import download_media
from services.votantes_api import buscar_votante, formatear_datos_votante
from services.firebase_db import (
    verificar_duplicado,
    guardar_registro,
    obtener_conversacion,
    actualizar_conversacion,
    crear_conversacion,
    eliminar_conversacion,
)
from services.firebase_storage import subir_foto_carnet
from services.ocr_service import verificar_carnet
from services.candidatos_service import buscar_candidato, formatear_lista_candidatos

logger = logging.getLogger(__name__)

# Estados
ESTADO_INICIO = "INICIO"
ESTADO_ESPERANDO_CEDULA = "ESPERANDO_CEDULA"
ESTADO_CONFIRMACION_DATOS = "CONFIRMACION_DATOS"
ESTADO_PREGUNTA_CONSULTA = "PREGUNTA_CONSULTA"
ESTADO_ESPERANDO_CANDIDATO_CONSULTA = "ESPERANDO_CANDIDATO_CONSULTA"
ESTADO_CONFIRMANDO_CONSULTA = "CONFIRMANDO_CONSULTA"
ESTADO_ESPERANDO_CANDIDATO_SENADO = "ESPERANDO_CANDIDATO_SENADO"
ESTADO_CONFIRMANDO_SENADO = "CONFIRMANDO_SENADO"
ESTADO_ESPERANDO_CANDIDATO_CAMARA = "ESPERANDO_CANDIDATO_CAMARA"
ESTADO_CONFIRMANDO_CAMARA = "CONFIRMANDO_CAMARA"
ESTADO_ESPERANDO_FOTO = "ESPERANDO_FOTO"
ESTADO_COMPLETADO = "COMPLETADO"


PALABRAS_REINICIO = {"hola", "hello", "hi", "inicio", "reiniciar", "menu", "menú", "empezar", "comenzar"}


def procesar_mensaje(mensaje: dict) -> None:
    """Procesar un mensaje entrante y ejecutar la acción correspondiente según el estado."""
    from_number = mensaje["from_number"]
    message_id = mensaje["message_id"]

    # Marcar como leído
    try:
        mark_as_read(message_id)
    except Exception as e:
        logger.warning("No se pudo marcar como leído: %s", e)

    # Detectar si el usuario quiere reiniciar el flujo
    texto = (mensaje.get("text") or "").strip().lower()
    if texto in PALABRAS_REINICIO:
        eliminar_conversacion(from_number)
        _estado_inicio(from_number)
        return

    # Obtener estado actual de la conversación
    conv = obtener_conversacion(from_number)

    if conv is None:
        _estado_inicio(from_number)
        return

    estado = conv.get("estado", ESTADO_INICIO)

    if estado == ESTADO_ESPERANDO_CEDULA:
        _estado_esperando_cedula(from_number, mensaje, conv)
    elif estado == ESTADO_CONFIRMACION_DATOS:
        _estado_confirmacion_datos(from_number, mensaje, conv)
    elif estado == ESTADO_PREGUNTA_CONSULTA:
        _estado_pregunta_consulta(from_number, mensaje, conv)
    elif estado == ESTADO_ESPERANDO_CANDIDATO_CONSULTA:
        _estado_esperando_candidato(from_number, mensaje, conv, "consulta")
    elif estado == ESTADO_CONFIRMANDO_CONSULTA:
        _estado_confirmando_candidato(from_number, mensaje, conv, "consulta")
    elif estado == ESTADO_ESPERANDO_CANDIDATO_SENADO:
        _estado_esperando_candidato(from_number, mensaje, conv, "senado")
    elif estado == ESTADO_CONFIRMANDO_SENADO:
        _estado_confirmando_candidato(from_number, mensaje, conv, "senado")
    elif estado == ESTADO_ESPERANDO_CANDIDATO_CAMARA:
        _estado_esperando_candidato(from_number, mensaje, conv, "camara")
    elif estado == ESTADO_CONFIRMANDO_CAMARA:
        _estado_confirmando_candidato(from_number, mensaje, conv, "camara")
    elif estado == ESTADO_ESPERANDO_FOTO:
        _estado_esperando_foto(from_number, mensaje, conv)
    else:
        # Estado desconocido o COMPLETADO: reiniciar
        _estado_inicio(from_number)


def _estado_inicio(from_number: str) -> None:
    """Enviar saludo y solicitar cédula."""
    send_text(
        from_number,
        "👋 ¡Hola! Bienvenido al *Sistema de Participación Electoral*.\n\n"
        "Este bot te permite registrar tu apoyo electoral.\n\n"
        "Por favor, escribe tu *número de cédula* para comenzar:",
    )
    crear_conversacion(from_number, ESTADO_ESPERANDO_CEDULA)


def _estado_esperando_cedula(from_number: str, mensaje: dict, conv: dict) -> None:
    """Validar cédula, consultar API de votantes y verificar duplicados."""
    if mensaje["type"] != "text" or not mensaje.get("text"):
        send_text(from_number, "⚠️ Por favor, envía tu *número de cédula* (solo números):")
        return

    cedula = mensaje["text"].strip().replace(".", "").replace(" ", "")

    # Validar formato numérico
    if not cedula.isdigit() or len(cedula) < 5:
        send_text(
            from_number,
            "❌ El número de cédula no es válido. Debe contener solo números.\n\n"
            "Por favor, intenta de nuevo:",
        )
        return

    # Verificar duplicado
    if verificar_duplicado(cedula):
        send_text(
            from_number,
            "⚠️ Esta cédula ya fue registrada anteriormente.\n\n"
            "Cada cédula solo puede registrar un apoyo. "
            "Si crees que es un error, contacta al administrador.",
        )
        eliminar_conversacion(from_number)
        return

    send_text(from_number, "🔍 Buscando tus datos, por favor espera un momento...")

    # Consultar API de votantes
    datos = buscar_votante(cedula)
    if datos is None:
        send_text(
            from_number,
            "❌ No se encontraron datos para esa cédula en el sistema.\n\n"
            "Verifica el número e intenta de nuevo:",
        )
        return

    # Mostrar datos y pedir confirmación
    texto_datos = formatear_datos_votante(datos)
    send_text(from_number, texto_datos)

    send_buttons(
        from_number,
        "¿Estos datos son correctos?",
        [
            {"id": "btn_si", "title": "✅ Sí, confirmo"},
            {"id": "btn_no", "title": "❌ No, corregir"},
        ],
    )

    # Guardar datos temporales en la conversación
    actualizar_conversacion(from_number, {
        "estado": ESTADO_CONFIRMACION_DATOS,
        "cedula": cedula,
        "datos_votante": datos,
    })


def _estado_confirmacion_datos(from_number: str, mensaje: dict, conv: dict) -> None:
    """Procesar confirmación de datos (Sí/No)."""
    respuesta = None

    if mensaje["type"] == "button_reply":
        respuesta = mensaje.get("button_id", "")
    elif mensaje["type"] == "text":
        texto = mensaje.get("text", "").lower().strip()
        if texto in ("si", "sí", "yes", "1", "confirmo"):
            respuesta = "btn_si"
        elif texto in ("no", "2", "corregir"):
            respuesta = "btn_no"

    if respuesta == "btn_si":
        send_text(
            from_number,
            "✅ ¡Datos confirmados!\n\n"
            "Ahora vamos a registrar tu apoyo.\n\n"
            "📌 *SENADO:* Escribe el *nombre o apellido* de tu candidato para *Senado*:",
        )
        actualizar_conversacion(from_number, {"estado": ESTADO_ESPERANDO_CANDIDATO_SENADO})

    elif respuesta == "btn_no":
        send_text(
            from_number,
            "🔄 Entendido. Por favor, escribe nuevamente tu *número de cédula* correcto:",
        )
        actualizar_conversacion(from_number, {
            "estado": ESTADO_ESPERANDO_CEDULA,
            "cedula": None,
            "datos_votante": None,
        })

    else:
        send_buttons(
            from_number,
            "Por favor responde usando los botones: ¿Los datos son correctos?",
            [
                {"id": "btn_si", "title": "✅ Sí, confirmo"},
                {"id": "btn_no", "title": "❌ No, corregir"},
            ],
        )


def _estado_esperando_candidato(from_number: str, mensaje: dict, conv: dict, corporacion: str) -> None:
    """Buscar coincidencias de candidato en la BD."""
    labels = {"senado": "Senado", "camara": "Cámara", "consulta": "Consulta Presidencial"}
    label = labels.get(corporacion, corporacion)

    if mensaje["type"] != "text" or not mensaje.get("text"):
        send_text(
            from_number,
            f"⚠️ Por favor, escribe el *nombre o apellido* de tu candidato de *{label}*:",
        )
        return

    texto = mensaje["text"].strip()
    if len(texto) < 2:
        send_text(
            from_number,
            f"❌ Texto muy corto. Escribe al menos un apellido de tu candidato de *{label}*:",
        )
        return

    resultados = buscar_candidato(
        texto, corporacion,
        departamento=conv.get("datos_votante", {}).get("departamento_votacion") if corporacion == "camara" else None,
    )

    if len(resultados) == 0:
        send_text(
            from_number,
            f"❌ No se encontró ningún candidato de *{label}* con ese nombre.\n\n"
            "Verifica e intenta de nuevo. Puedes escribir solo el *apellido*:",
        )
        return

    if len(resultados) == 1:
        # Coincidencia única: confirmar directamente
        candidato = resultados[0]
        _confirmar_candidato(from_number, conv, corporacion, candidato)
        return

    # Múltiples coincidencias: pedir que elija
    lista = formatear_lista_candidatos(resultados)
    send_text(
        from_number,
        f"🔎 Se encontraron *{len(resultados)} candidatos* de *{label}* con ese nombre:\n\n"
        f"{lista}\n\n"
        "Escribe el *número* del candidato correcto:",
    )

    estado_confirm_map = {
        "consulta": ESTADO_CONFIRMANDO_CONSULTA,
        "senado": ESTADO_CONFIRMANDO_SENADO,
        "camara": ESTADO_CONFIRMANDO_CAMARA,
    }
    estado_confirm = estado_confirm_map[corporacion]
    actualizar_conversacion(from_number, {
        "estado": estado_confirm,
        "opciones_candidato": resultados,
    })


def _estado_confirmando_candidato(from_number: str, mensaje: dict, conv: dict, corporacion: str) -> None:
    """Confirmar selección de candidato cuando hay múltiples coincidencias."""
    labels = {"senado": "Senado", "camara": "Cámara", "consulta": "Consulta Presidencial"}
    label = labels.get(corporacion, corporacion)
    opciones = conv.get("opciones_candidato", [])

    if mensaje["type"] != "text" or not mensaje.get("text"):
        send_text(from_number, "⚠️ Por favor, escribe el *número* del candidato:")
        return

    texto = mensaje["text"].strip()

    # Verificar si escribió un número
    if texto.isdigit():
        indice = int(texto)
        if 1 <= indice <= len(opciones):
            candidato = opciones[indice - 1]
            _confirmar_candidato(from_number, conv, corporacion, candidato)
            return
        else:
            send_text(
                from_number,
                f"❌ Número inválido. Escribe un número del *1* al *{len(opciones)}*:",
            )
            return

    # Si escribió texto, buscar de nuevo
    departamento = conv.get("datos_votante", {}).get("departamento_votacion") if corporacion == "camara" else None
    resultados = buscar_candidato(texto, corporacion, departamento=departamento)
    if len(resultados) == 1:
        _confirmar_candidato(from_number, conv, corporacion, resultados[0])
        return
    elif len(resultados) > 1:
        lista = formatear_lista_candidatos(resultados)
        send_text(
            from_number,
            f"🔎 Se encontraron *{len(resultados)} candidatos*:\n\n"
            f"{lista}\n\n"
            "Escribe el *número* del candidato correcto:",
        )
        actualizar_conversacion(from_number, {"opciones_candidato": resultados})
        return
    else:
        send_text(
            from_number,
            f"❌ No se encontró candidato. Escribe el nombre de nuevo o el *número* de la lista anterior:",
        )


def _estado_pregunta_consulta(from_number: str, mensaje: dict, conv: dict) -> None:
    """Preguntar si solicitó el tarjetón de la consulta presidencial."""
    respuesta = None

    if mensaje["type"] == "button_reply":
        respuesta = mensaje.get("button_id", "")
    elif mensaje["type"] == "text":
        texto = mensaje.get("text", "").lower().strip()
        if texto in ("si", "sí", "yes", "1"):
            respuesta = "btn_consulta_si"
        elif texto in ("no", "2"):
            respuesta = "btn_consulta_no"

    if respuesta == "btn_consulta_si":
        send_text(
            from_number,
            "📋 *Consulta Presidencial*\n\n"
            "Escribe el *nombre o apellido* de tu candidato de la consulta:",
        )
        actualizar_conversacion(from_number, {"estado": ESTADO_ESPERANDO_CANDIDATO_CONSULTA})

    elif respuesta == "btn_consulta_no":
        # No solicita consulta → guardar registro y finalizar
        _guardar_y_finalizar(from_number, conv)

    else:
        send_buttons(
            from_number,
            "¿Vas a solicitar el tarjetón de la *Consulta Presidencial*?",
            [
                {"id": "btn_consulta_si", "title": "✅ Sí"},
                {"id": "btn_consulta_no", "title": "❌ No"},
            ],
        )


def _confirmar_candidato(from_number: str, conv: dict, corporacion: str, candidato: dict) -> None:
    """Registra el candidato seleccionado y avanza al siguiente paso."""
    nombre = candidato["nombre"]
    partido = candidato["partido"]
    labels = {"senado": "Senado", "camara": "Cámara", "consulta": "Consulta Presidencial"}
    label = labels.get(corporacion, corporacion)

    if corporacion == "senado":
        send_text(
            from_number,
            f"✅ *{label}* registrado:\n"
            f"👤 *{nombre}*\n"
            f"🏛️ Partido: {partido}\n\n"
            "Ahora, escribe el *nombre o apellido* de tu candidato para *Cámara*:",
        )
        actualizar_conversacion(from_number, {
            "estado": ESTADO_ESPERANDO_CANDIDATO_CAMARA,
            "candidato_senado": nombre,
            "partido_senado": partido,
            "opciones_candidato": None,
        })
    elif corporacion == "camara":
        send_text(
            from_number,
            f"✅ *{label}* registrado:\n"
            f"👤 *{nombre}*\n"
            f"🏛️ Partido: {partido}\n\n",
        )
        send_buttons(
            from_number,
            "¿Vas a solicitar el tarjetón de la *Consulta Presidencial*?",
            [
                {"id": "btn_consulta_si", "title": "✅ Sí"},
                {"id": "btn_consulta_no", "title": "❌ No"},
            ],
        )
        actualizar_conversacion(from_number, {
            "estado": ESTADO_PREGUNTA_CONSULTA,
            "candidato_camara": nombre,
            "partido_camara": partido,
            "opciones_candidato": None,
        })
    else:
        # consulta → guardar registro y finalizar
        actualizar_conversacion(from_number, {
            "candidato_consulta": nombre,
            "partido_consulta": partido,
            "opciones_candidato": None,
        })
        conv["candidato_consulta"] = nombre
        conv["partido_consulta"] = partido
        _guardar_y_finalizar(from_number, conv)


def _guardar_y_finalizar(from_number: str, conv: dict) -> None:
    """Guardar registro en Firebase y enviar mensaje de despedida."""
    cedula = conv.get("cedula", "")
    datos_votante = conv.get("datos_votante", {})
    candidato_consulta = conv.get("candidato_consulta", "")
    partido_consulta = conv.get("partido_consulta", "")
    candidato_senado = conv.get("candidato_senado", "")
    candidato_camara = conv.get("candidato_camara", "")
    partido_senado = conv.get("partido_senado", "")
    partido_camara = conv.get("partido_camara", "")

    registro = {
        "cedula": cedula,
        "nombre_completo": datos_votante.get("nombre_completo", ""),
        "nombres": datos_votante.get("nombres", ""),
        "apellidos": datos_votante.get("apellidos", ""),
        "departamento_votacion": datos_votante.get("departamento_votacion", ""),
        "municipio_votacion": datos_votante.get("municipio_votacion", ""),
        "zona": datos_votante.get("zona", ""),
        "puesto": datos_votante.get("puesto", ""),
        "mesa": datos_votante.get("mesa", ""),
        "direccion": datos_votante.get("direccion", ""),
        "departamento_residencia": datos_votante.get("departamento_residencia", ""),
        "municipio_residencia": datos_votante.get("municipio_residencia", ""),
        "candidato_consulta": candidato_consulta,
        "partido_consulta": partido_consulta,
        "candidato_senado": candidato_senado,
        "partido_senado": partido_senado,
        "candidato_camara": candidato_camara,
        "partido_camara": partido_camara,
        "foto_url": "",
        "ocr_verificado": False,
        "ocr_texto_extraido": "",
        "ocr_coincidencias": [],
        "ocr_confianza": 0,
        "telefono_whatsapp": from_number,
    }

    guardar_registro(cedula, registro)

    # Construir resumen
    resumen_consulta = ""
    if candidato_consulta:
        resumen_consulta = f"\n🗳️ Consulta: {candidato_consulta}"

    send_text(
        from_number,
        f"🎉 *¡Apoyo registrado exitosamente!*\n\n"
        f"📋 *Resumen:*\n"
        f"👤 {datos_votante.get('nombre_completo', '')}\n"
        f"🆔 Cédula: {cedula}{resumen_consulta}\n"
        f"🏛️ Senado: {candidato_senado}\n"
        f"🏛️ Cámara: {candidato_camara}\n\n"
        f"📸 El día de las elecciones te solicitaremos la foto del tarjetón "
        f"para confirmar tu apoyo.\n\n"
        f"¡Gracias por participar! 🇨🇴",
    )

    eliminar_conversacion(from_number)


def _estado_esperando_foto(from_number: str, mensaje: dict, conv: dict) -> None:
    """Procesar foto del carnet electoral: descargar, subir a Storage, verificar con OCR."""
    if mensaje["type"] != "image" or not mensaje.get("image_id"):
        send_text(
            from_number,
            "📸 Por favor, envía una *fotografía* de tu carnet electoral.\n"
            "Asegúrate de que la imagen sea clara y legible.",
        )
        return

    send_text(from_number, "⏳ Procesando tu foto, por favor espera un momento...")

    cedula = conv.get("cedula", "")
    datos_votante = conv.get("datos_votante", {})
    candidato_consulta = conv.get("candidato_consulta", "")
    partido_consulta = conv.get("partido_consulta", "")
    candidato_senado = conv.get("candidato_senado", "")
    candidato_camara = conv.get("candidato_camara", "")
    partido_senado = conv.get("partido_senado", "")
    partido_camara = conv.get("partido_camara", "")

    try:
        # Descargar imagen de WhatsApp
        image_bytes = download_media(mensaje["image_id"])
        if not image_bytes:
            send_text(from_number, "❌ No se pudo descargar la imagen. Por favor, inténtalo de nuevo:")
            return

        # Subir a Firebase Storage
        foto_url = subir_foto_carnet(cedula, image_bytes)

        # Verificar con OCR
        ocr_result = verificar_carnet(image_bytes, datos_votante)

        # Mostrar resultado del análisis OCR al usuario
        texto_ocr = ocr_result.get("texto_extraido", "")
        coincidencias = ocr_result.get("coincidencias", [])

        if texto_ocr:
            ocr_info = f"🔎 *Texto detectado en la foto:*\n_{texto_ocr[:300]}_\n\n"
            if coincidencias:
                ocr_info += "✅ *Coincidencias encontradas:*\n"
                for c in coincidencias:
                    ocr_info += f"  • {c}\n"
            else:
                ocr_info += "⚠️ No se encontraron coincidencias automáticas con tus datos.\n"
            send_text(from_number, ocr_info)
        else:
            send_text(
                from_number,
                "⚠️ No se pudo extraer texto de la foto. "
                "Se guardará como evidencia fotográfica.",
            )

        # Guardar registro completo en Firebase
        registro = {
            "cedula": cedula,
            "nombre_completo": datos_votante.get("nombre_completo", ""),
            "nombres": datos_votante.get("nombres", ""),
            "apellidos": datos_votante.get("apellidos", ""),
            "departamento_votacion": datos_votante.get("departamento_votacion", ""),
            "municipio_votacion": datos_votante.get("municipio_votacion", ""),
            "zona": datos_votante.get("zona", ""),
            "puesto": datos_votante.get("puesto", ""),
            "mesa": datos_votante.get("mesa", ""),
            "direccion": datos_votante.get("direccion", ""),
            "departamento_residencia": datos_votante.get("departamento_residencia", ""),
            "municipio_residencia": datos_votante.get("municipio_residencia", ""),
            "candidato_consulta": candidato_consulta,
            "partido_consulta": partido_consulta,
            "candidato_senado": candidato_senado,
            "partido_senado": partido_senado,
            "candidato_camara": candidato_camara,
            "partido_camara": partido_camara,
            "foto_url": foto_url,
            "ocr_verificado": ocr_result["verificado"],
            "ocr_texto_extraido": ocr_result["texto_extraido"],
            "ocr_coincidencias": ocr_result["coincidencias"],
            "ocr_confianza": ocr_result["confianza"],
            "telefono_whatsapp": from_number,
        }

        guardar_registro(cedula, registro)

        # Mensaje de resultado final
        if ocr_result["verificado"]:
            verificacion_msg = "✅ *Verificación:* Datos del carnet confirmados."
        elif texto_ocr:
            verificacion_msg = (
                "⚠️ *Verificación:* Los datos no coinciden automáticamente. "
                "Registro guardado para revisión."
            )
        else:
            verificacion_msg = "📸 Foto guardada como evidencia."

        # Construir resumen
        resumen_consulta = ""
        if candidato_consulta:
            resumen_consulta = f"\n🗳️ Consulta: {candidato_consulta}"

        send_text(
            from_number,
            f"🎉 *¡Registro completado exitosamente!*\n\n"
            f"📋 *Resumen:*\n"
            f"👤 {datos_votante.get('nombre_completo', '')}\n"
            f"🆔 Cédula: {cedula}{resumen_consulta}\n"
            f"🏛️ Senado: {candidato_senado}\n"
            f"🏛️ Cámara: {candidato_camara}\n"
            f"📸 Foto: Recibida\n\n"
            f"{verificacion_msg}\n\n"
            f"¡Gracias por participar en el proceso electoral! 🇨🇴",
        )

        # Limpiar conversación
        eliminar_conversacion(from_number)

    except Exception as e:
        logger.error("Error procesando foto para %s: %s", from_number, e, exc_info=True)
        send_text(
            from_number,
            "❌ Ocurrió un error al procesar tu foto. Por favor, inténtalo de nuevo:",
        )
