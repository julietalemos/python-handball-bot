"""
services/larrysport/__init__.py
────────────────────────────────
Interfaz pública del paquete larrysport.

Uso desde cualquier parte del proyecto:
    from services.larrysport import LarrySportService

    service = LarrySportService()
    partidos = service.get_partidos()       # Lee del caché (instantáneo)
    partidos = service.actualizar_cache()   # Scrapea y guarda (~10-15 min)
"""

import logging

from services.larrysport.cache import (
    info_fixture,
    leer_fixture,
)
from datetime import datetime
from services.larrysport.models import Partido
from typing import Optional, List

logger = logging.getLogger(__name__)


class LarrySportService:
    """
    Interfaz principal del servicio LarrySport.

    get_partidos()     → lee del caché (instantáneo, retorna list[Partido])
    actualizar_cache() → scrapea FEMEBAL y guarda (tarda ~10-15 min)
    cache_info()       → resumen del estado del caché para admins
    """

    def get_partidos(self) -> list[Partido]:
        """
        Lee los partidos desde el caché local.
        Si el caché está vacío retorna lista vacía — no scrapea en caliente.
        """
        partidos, _ = leer_fixture()
        if not partidos:
            logger.warning("Caché vacío. Usá /actualizar para cargar los fixtures.")
        return partidos

    def cache_info(self) -> str:
        """Resumen del estado del caché para mostrar al admin."""
        return info_fixture()
    
    def get_fixture(self) -> tuple[list[Partido], Optional[datetime]]:
        """
        Lee los partidos y la fecha de actualización desde el caché.
        Retorna ([], None) si el caché está vacío.
        """
        partidos, fecha = leer_fixture()
        if not partidos:
            logger.warning("Caché vacío. Usá /actualizar para cargar los fixtures.")
        return partidos, fecha