"""
services/larrysport/cache.py
─────────────────────────────
Lectura y escritura de los archivos de caché en data/.

Cada tipo de caché tiene su propio par leer/escribir.
leer_fixture() deserializa los dicts del JSON a objetos Partido.

Archivos:
  data/fixture_cache.json
  data/posiciones_cache.json
  data/goleadores_cache.json
"""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Optional

from services.larrysport.models import Partido

logger = logging.getLogger(__name__)

# ─── Rutas ────────────────────────────────────────────────────────

_DATA_DIR = Path(__file__).resolve().parent.parent.parent / "data"

FIXTURE_CACHE_PATH     = _DATA_DIR / "fixture_cache.json"
POSICIONES_CACHE_PATH  = _DATA_DIR / "posiciones_cache.json"
GOLEADORES_CACHE_PATH  = _DATA_DIR / "goleadores_cache.json"


# ─── Helpers internos ─────────────────────────────────────────────

def _leer_json(path: Path) -> dict:
    """Lee un archivo JSON. Retorna dict vacío si no existe o hay error."""
    try:
        if path.exists():
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
    except Exception as e:
        logger.warning(f"No se pudo leer {path.name}: {e}")
    return {}


def _escribir_json(path: Path, datos: dict) -> None:
    """Escribe un dict como JSON, creando el directorio si no existe."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(datos, f, ensure_ascii=False, indent=2)


def _partido_desde_dict(d: dict) -> Partido:
    """Convierte un dict del JSON a un objeto Partido."""
    return Partido(
        torneo=d.get("torneo", ""),
        division=d.get("division", ""),
        rama=d.get("rama", ""),
        categoria=d.get("categoria", ""),
        fecha_raw=d.get("fecha_raw", ""),
        hora=d.get("hora", ""),
        local=d.get("local", ""),
        visitante=d.get("visitante", ""),
        es_local=d.get("es_local", False),
        rival=d.get("rival", "Por confirmar"),
        marcador_local=d.get("marcador_local"),
        marcador_visitante=d.get("marcador_visitante"),
        jugado=d.get("jugado", False),
    )


def _partido_a_dict(p: Partido) -> dict:
    """Convierte un objeto Partido a dict serializable para JSON."""
    return {
        "torneo":             p.torneo,
        "division":           p.division,
        "rama":               p.rama,
        "categoria":          p.categoria,
        "fecha_raw":          p.fecha_raw,
        "hora":               p.hora,
        "local":              p.local,
        "visitante":          p.visitante,
        "es_local":           p.es_local,
        "rival":              p.rival,
        "marcador_local":     p.marcador_local,
        "marcador_visitante": p.marcador_visitante,
        "jugado":             p.jugado,
    }


# ─── Fixture ──────────────────────────────────────────────────────

def leer_fixture() -> tuple[list[Partido], Optional[datetime]]:
    """
    Lee el caché de fixture.

    Retorna:
        (partidos, fecha_actualizacion)
        Si el caché está vacío retorna ([], None).
    """
    datos = _leer_json(FIXTURE_CACHE_PATH)
    if not datos or not datos.get("partidos"):
        logger.warning("Caché de fixture vacío.")
        return [], None

    partidos = [_partido_desde_dict(d) for d in datos["partidos"]]

    fecha = None
    try:
        fecha = datetime.fromisoformat(datos["actualizado"])
    except Exception:
        pass

    return partidos, fecha


def escribir_fixture(partidos: list[Partido]) -> None:
    """Guarda la lista de Partido en el caché con timestamp."""
    datos = {
        "actualizado": datetime.now().isoformat(),
        "partidos": [_partido_a_dict(p) for p in partidos],
    }
    _escribir_json(FIXTURE_CACHE_PATH, datos)
    logger.info(f"✅ Fixture guardado ({len(partidos)} partidos)")


def info_fixture() -> str:
    """Resumen del estado del caché para mostrar al admin."""
    datos = _leer_json(FIXTURE_CACHE_PATH)
    if not datos:
        return "⚠️ Caché vacío. Usá /actualizar para cargar los fixtures."
    cant = len(datos.get("partidos", []))
    try:
        dt = datetime.fromisoformat(datos["actualizado"])
        fecha_str = dt.strftime("%d/%m/%Y a las %H:%M")
    except Exception:
        fecha_str = datos.get("actualizado", "desconocida")
    return f"📦 Caché: {cant} partidos\n🕐 Última actualización: {fecha_str}"


# ─── Posiciones ───────────────────────────────────────────────────

def leer_posiciones() -> tuple[dict, Optional[datetime]]:
    """
    Lee el caché de posiciones.

    Retorna:
        (posiciones_dict, fecha_actualizacion)
        Si el caché está vacío retorna ({}, None).
    """
    datos = _leer_json(POSICIONES_CACHE_PATH)
    if not datos or not datos.get("posiciones"):
        return {}, None

    fecha = None
    try:
        fecha = datetime.fromisoformat(datos["actualizado"])
    except Exception:
        pass

    return datos["posiciones"], fecha


def escribir_posiciones(posiciones: dict) -> None:
    """Guarda las posiciones en el caché con timestamp."""
    datos = {
        "actualizado": datetime.now().isoformat(),
        "posiciones": posiciones,
    }
    _escribir_json(POSICIONES_CACHE_PATH, datos)
    logger.info("✅ Posiciones guardadas")


# ─── Goleadores ───────────────────────────────────────────────────

def leer_goleadores() -> tuple[dict, Optional[datetime]]:
    """
    Lee el caché de goleadores.

    Retorna:
        (goleadores_dict, fecha_actualizacion)
        Si el caché está vacío retorna ({}, None).
    """
    datos = _leer_json(GOLEADORES_CACHE_PATH)
    if not datos or not datos.get("goleadores"):
        return {}, None

    fecha = None
    try:
        fecha = datetime.fromisoformat(datos["actualizado"])
    except Exception:
        pass

    return datos["goleadores"], fecha


def escribir_goleadores(goleadores: dict) -> None:
    """Guarda los goleadores en el caché con timestamp."""
    datos = {
        "actualizado": datetime.now().isoformat(),
        "goleadores": goleadores,
    }
    _escribir_json(GOLEADORES_CACHE_PATH, datos)
    logger.info("✅ Goleadores guardados")