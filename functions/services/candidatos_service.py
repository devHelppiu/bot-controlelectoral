"""Servicio de búsqueda de candidatos desde candidatos.json."""

import json
import logging
import os
import unicodedata

logger = logging.getLogger(__name__)

_candidatos = None


def _cargar_candidatos():
    global _candidatos
    if _candidatos is not None:
        return _candidatos
    ruta = os.path.join(os.path.dirname(__file__), "..", "candidatos.json")
    with open(ruta, encoding="utf-8") as f:
        _candidatos = json.load(f)
    return _candidatos


def _normalizar(texto: str) -> str:
    """Quita tildes y pasa a mayúsculas."""
    nfkd = unicodedata.normalize("NFKD", texto)
    return "".join(c for c in nfkd if not unicodedata.combining(c)).upper().strip()


def buscar_candidato(texto: str, corporacion: str, departamento: str | None = None) -> list[dict]:
    """Busca candidatos cuyo nombre coincida con el texto.

    Args:
        texto: Texto libre escrito por el usuario.
        corporacion: 'senado', 'camara' o 'consulta'.
        departamento: Departamento para filtrar (solo aplica a cámara).

    Returns:
        Lista de candidatos que coinciden (máx 10).
    """
    datos = _cargar_candidatos()
    lista = datos.get(corporacion, [])

    # Filtrar por departamento en cámara
    if corporacion == "camara" and departamento:
        dep_norm = _normalizar(departamento)
        lista = [c for c in lista if _normalizar(c.get("departamento", "")) == dep_norm]

    termino = _normalizar(texto)

    if len(termino) < 2:
        return []

    palabras = [p for p in termino.split() if len(p) >= 2]
    if not palabras:
        return []

    resultados = []

    for c in lista:
        nombre_words = _normalizar(c["nombre"]).split()
        coincidencias = sum(1 for p in palabras if p in nombre_words)
        if coincidencias > 0:
            resultados.append((coincidencias, c))

    # Ordenar por mayor número de coincidencias
    resultados.sort(key=lambda x: x[0], reverse=True)

    # Si hay resultados con más coincidencias, descartar los de menor puntaje
    if resultados:
        max_score = resultados[0][0]
        if max_score > 1:
            resultados = [r for r in resultados if r[0] == max_score]

    return [r[1] for r in resultados[:10]]


def formatear_lista_candidatos(candidatos: list[dict]) -> str:
    """Formatea la lista de candidatos encontrados para mostrar al usuario."""
    lineas = []
    for i, c in enumerate(candidatos, 1):
        lineas.append(
            f"*{i}.* {c['nombre']}\n"
            f"    Partido: {c['partido']}\n"
            f"    Depto: {c['departamento']}"
        )
    return "\n\n".join(lineas)
