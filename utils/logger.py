"""
utils/logger.py
────────────────
Configuración centralizada del sistema de logging.

¿Por qué logging y no print()?
  → Los logs tienen timestamp, nivel (INFO/ERROR/WARNING) y módulo origen.
  → Se pueden guardar en archivo para auditoría y debugging.
  → En producción, podés ver qué pasó cuando el bot falla de madrugada.
"""

import logging
import sys
from pathlib import Path
from config.settings import Settings


def setup_logger(nombre: str) -> logging.Logger:
    """
    Crea y configura un logger con salida a consola Y archivo.

    Args:
        nombre: Nombre del módulo (aparece en cada línea del log)

    Returns:
        Logger configurado listo para usar

    Uso:
        logger = setup_logger("mi_modulo")
        logger.info("Todo bien")
        logger.error("Algo falló", exc_info=True)  # exc_info=True incluye el traceback
    """
    settings = Settings()

    # Creamos el directorio de logs si no existe
    log_path = Path(settings.LOG_PATH)
    log_path.parent.mkdir(parents=True, exist_ok=True)

    # Obtenemos (o creamos) el logger con ese nombre
    logger = logging.getLogger(nombre)

    # Evitamos duplicar handlers si la función se llama múltiples veces
    if logger.handlers:
        return logger

    nivel = getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO)
    logger.setLevel(nivel)

    # Formato: "2025-06-15 18:30:00 | INFO     | main | Mensaje"
    formato = logging.Formatter(
        fmt="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # ─── Handler 1: Consola (stdout) ─────────────────────────────
    # Muestra los logs en tiempo real cuando corrés el bot manualmente
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formato)
    console_handler.setLevel(nivel)
    logger.addHandler(console_handler)

    # ─── Handler 2: Archivo ───────────────────────────────────────
    # Guarda todos los logs en el archivo configurado en .env
    try:
        file_handler = logging.FileHandler(log_path, encoding="utf-8")
        file_handler.setFormatter(formato)
        file_handler.setLevel(nivel)
        logger.addHandler(file_handler)
    except PermissionError:
        logger.warning(f"No se pudo crear el archivo de log en {log_path}")

    return logger
