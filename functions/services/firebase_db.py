import logging
import time

import firebase_admin
from firebase_admin import db as rtdb

logger = logging.getLogger(__name__)


def _db():
    """Obtener referencia a la Realtime Database."""
    return rtdb.reference()


# ── Registros ──────────────────────────────────────────────

def verificar_duplicado(cedula: str) -> bool:
    """Verificar si ya existe un registro completado para esta cédula."""
    ref = _db().child("registros").child(str(cedula))
    registro = ref.get()
    return registro is not None and registro.get("estado") == "completado"


def guardar_registro(cedula: str, datos: dict) -> None:
    """Guardar registro completo del voto."""
    datos["fecha_registro"] = int(time.time() * 1000)
    datos["estado"] = "completado"
    _db().child("registros").child(str(cedula)).set(datos)
    _incrementar_estadisticas(datos.get("candidato", ""))
    logger.info("Registro guardado para cédula: %s", cedula)


def _incrementar_estadisticas(candidato: str) -> None:
    """Incrementar contadores de estadísticas."""
    stats_ref = _db().child("estadisticas")

    # Incrementar total de registros
    total_ref = stats_ref.child("total_registros")
    current = total_ref.get() or 0
    total_ref.set(current + 1)

    # Incrementar contador por candidato
    if candidato:
        candidato_key = candidato.strip().upper().replace("/", "_").replace(".", "_")
        cand_ref = stats_ref.child("por_candidato").child(candidato_key).child("count")
        current_count = cand_ref.get() or 0
        cand_ref.set(current_count + 1)

        # Guardar nombre original del candidato
        stats_ref.child("por_candidato").child(candidato_key).child("nombre").set(
            candidato.strip()
        )


# ── Conversaciones ─────────────────────────────────────────

def obtener_conversacion(telefono: str) -> dict | None:
    """Obtener estado de la conversación para un número de teléfono."""
    ref = _db().child("conversaciones").child(telefono)
    return ref.get()


def actualizar_conversacion(telefono: str, datos: dict) -> None:
    """Actualizar datos de la conversación."""
    datos["ultima_actividad"] = int(time.time() * 1000)
    _db().child("conversaciones").child(telefono).update(datos)


def crear_conversacion(telefono: str, estado: str) -> None:
    """Crear nueva conversación."""
    _db().child("conversaciones").child(telefono).set({
        "estado": estado,
        "ultima_actividad": int(time.time() * 1000),
    })


def eliminar_conversacion(telefono: str) -> None:
    """Eliminar conversación (después de completar el flujo)."""
    _db().child("conversaciones").child(telefono).delete()
