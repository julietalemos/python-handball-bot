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

import asyncio
import concurrent.futures
import logging

from services.larrysport.cache import (
    escribir_fixture,
    info_fixture,
    leer_fixture,
)
from datetime import datetime
from services.larrysport.models import Partido
from services.larrysport.scraper import scrape_todos
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

    # def actualizar_cache(self) -> list[Partido]:
    #     """
    #     Scrapea FEMEBAL, guarda el caché y retorna los partidos.
    #     Tarda aproximadamente 10-15 minutos.

    #     Funciona tanto desde un script (sin event loop) como desde dentro
    #     del bot (event loop activo): corre el scraping en un thread separado
    #     con su propio event loop para no bloquear el bot.
    #     """
    #     logger.info("🔄 Iniciando scraping de FEMEBAL...")

    #     def _run_en_thread() -> list[Partido]:
    #         loop = asyncio.new_event_loop()
    #         asyncio.set_event_loop(loop)
    #         try:
    #             return loop.run_until_complete(scrape_todos())
    #         finally:
    #             loop.close()

    #     with concurrent.futures.ThreadPoolExecutor() as executor:
    #         partidos = executor.submit(_run_en_thread).result()

    #     escribir_fixture(partidos)
    #     logger.info(f"✅ Cache actualizado — {len(partidos)} partidos")
    #     return partidos
    # def actualizar_cache(self) -> list[Partido]:
    #     """
    #     Scrapea FEMEBAL, guarda el caché y retorna los partidos.
    #     Debe llamarse desde un thread separado (no desde el event loop principal).
    #     """
    #     import asyncio
    #     logger.info("🔄 Iniciando scraping de FEMEBAL...")
    #     loop = asyncio.new_event_loop()
    #     asyncio.set_event_loop(loop)
    #     try:
    #         partidos = loop.run_until_complete(scrape_todos())
    #     finally:
    #         loop.close()
    #     escribir_fixture(partidos)
    #     logger.info(f"✅ Cache actualizado — {len(partidos)} partidos")
    #     return partidos

    async def actualizar_cache(self) -> list[Partido]:
        logger.info("🔄 Iniciando scraping de FEMEBAL...")
        partidos = await scrape_todos()  # ya es async, solo await directo
        escribir_fixture(partidos)
        logger.info(f"✅ Cache actualizado — {len(partidos)} partidos")
        return partidos
    
    def actualizar_cache_sync(self) -> list[Partido]:
        import asyncio
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            return loop.run_until_complete(self.actualizar_cache())
        finally:
            loop.close()

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