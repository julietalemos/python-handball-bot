"""
services/larrysport/parser.py
──────────────────────────────
Parsea el texto plano extraído de la página de FEMEBAL y retorna
una lista de objetos Partido para Mariano Acosta.

Función pública:
    extraer_partidos(texto, torneo_nombre, rama, categoria, division)
        → list[Partido]
"""

import logging
import re

from services.larrysport.models import Partido
from config.settings import Settings
NOMBRE_CLUB = Settings.NOMBRE_CLUB

logger = logging.getLogger(__name__)

# Días de la semana válidos al inicio de una línea de fecha
_PATRON_FECHA = re.compile(
    r'^(lun|mar|mié|jue|vie|sáb|dom)\s+\d{1,2}\s+\w+\s+\d{1,2}:\d{2}$',
    re.IGNORECASE,
)

# Separadores de fecha que hay que ignorar (ej: "Fecha 1", "Fecha 12")
_PATRON_SEPARADOR = re.compile(r'^Fecha\s+\d+$', re.IGNORECASE)

# Caracteres del área de uso privado de Unicode (íconos de la página)
_PATRON_ICONOS = re.compile(r'[\ue000-\uf8ff]')


def _limpiar_lineas(texto: str) -> list[str]:
    """
    Toma el texto crudo de la página y retorna líneas limpias:
      - Elimina íconos Unicode privados
      - Elimina líneas vacías
      - Elimina separadores tipo "Fecha 1"
    """
    lineas = []
    for linea in texto.split("\n"):
        limpia = _PATRON_ICONOS.sub("", linea).strip()
        if limpia and not _PATRON_SEPARADOR.match(limpia):
            lineas.append(limpia)
    return lineas


def _buscar_visitante_y_marcador(
    lineas: list[str], desde: int
) -> tuple[str, int | None, int | None]:
    """
    A partir de la línea del equipo local (índice `desde`), busca hacia adelante:
      - El nombre del equipo visitante
      - El marcador (si el partido ya se jugó)

    Retorna (visitante, marcador_local, marcador_visitante).
    """
    visitante = ""
    marcador_local = None
    marcador_visitante = None

    for j in range(desde, min(desde + 6, len(lineas))):
        linea = lineas[j]

        # Marcador: "21 18" → dos números separados por espacio
        marc = re.match(r'^(\d+)\s+(\d+)$', linea)
        if marc:
            marcador_local = int(marc.group(1))
            marcador_visitante = int(marc.group(2))
            continue

        # Ignorar "vs" / "vs."
        if linea.lower() in ("vs", "vs."):
            continue

        # Visitante: línea con letras que no parece una nueva fecha
        if (re.search(r'[a-zA-ZáéíóúÁÉÍÓÚñÑ]', linea) and
                not _PATRON_FECHA.match(linea)):
            visitante = linea
            break

    return visitante, marcador_local, marcador_visitante


def extraer_partidos(
    texto: str,
    torneo_nombre: str,
    rama: str,
    categoria: str,
    division: str = "",
) -> list[Partido]:
    """
    Parsea el texto completo de un torneo y retorna los partidos
    en los que participa Mariano Acosta.

    Args:
        texto:          Texto plano extraído con page.evaluate("() => document.body.innerText")
        torneo_nombre:  Nombre del torneo (ej. "Torneo Apertura")
        rama:           "Femenino" | "Masculino"
        categoria:      "Mayores" | "Junior" | etc.
        division:       Sección del torneo (ej. "Liga de Honor Plata"), puede ser vacío

    Returns:
        Lista de Partido. Puede ser vacía si el club no tiene partidos en este torneo.
    """
    lineas = _limpiar_lineas(texto)
    partidos: list[Partido] = []

    i = 0
    while i < len(lineas):
        linea = lineas[i]

        if not _PATRON_FECHA.match(linea):
            i += 1
            continue

        # Encontramos una línea de fecha — la siguiente es el equipo local
        fecha_raw = linea
        if i + 1 >= len(lineas):
            i += 1
            continue

        local = lineas[i + 1]
        visitante, marcador_local, marcador_visitante = _buscar_visitante_y_marcador(
            lineas, i + 2
        )

        # Solo nos interesan partidos de Mariano Acosta
        club_en_local     = NOMBRE_CLUB.lower() in local.lower()
        club_en_visitante = NOMBRE_CLUB.lower() in visitante.lower()

        if not club_en_local and not club_en_visitante:
            i += 1
            continue

        es_local = club_en_local
        rival    = visitante if es_local else local

        partido = Partido(
            torneo=torneo_nombre,
            division=division,
            rama=rama,
            categoria=categoria,
            fecha_raw=fecha_raw,
            hora=fecha_raw.split()[-1] if fecha_raw else "",
            local=local,
            visitante=visitante,
            es_local=es_local,
            rival=rival if rival else "Por confirmar",
            marcador_local=marcador_local,
            marcador_visitante=marcador_visitante,
            jugado=marcador_local is not None,
        )
        partidos.append(partido)
        logger.info(f"  ✅ {local} vs {visitante} ({fecha_raw})")

        i += 1

    return partidos