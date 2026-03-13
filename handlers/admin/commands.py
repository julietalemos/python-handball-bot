"""
handlers/admin/commands.py
───────────────────────────
Comandos exclusivos para admins:
  /actualizar → Fuerza el scraping y actualiza el caché
  /cache_info → Muestra el estado actual del caché

Registro:
    Llamar a register(application) desde main.py
"""

import asyncio
import logging
import sys
import os

from telegram import Update
from telegram.ext import CommandHandler, ContextTypes

from config.settings import Settings
from services.larrysport import LarrySportService

logger = logging.getLogger(__name__)
settings = Settings()
larrysport = LarrySportService()


# ─── Helpers ──────────────────────────────────────────────────────

def _es_admin(user_id: int) -> bool:
    return user_id in settings.ADMIN_IDS


# ─── /actualizar ──────────────────────────────────────────────────

async def cmd_actualizar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Fuerza el scraping de FEMEBAL y actualiza el caché.
    Solo admins. Lanza el proceso en segundo plano para no bloquear el bot.
    """
    if not _es_admin(update.effective_user.id):
        await update.message.reply_text("⛔ No tenés permisos para este comando.")
        return

    msg = await update.message.reply_text(
        "🔄 *Actualizando fixture desde FEMEBAL...*\n"
        "_Esto puede tardar 10-15 minutos, esperá._",
        parse_mode="Markdown",
    )

    #async def _ejecutar():
    try:
        proc = await asyncio.create_subprocess_exec(
            sys.executable,                          # el mismo python del venv
            "-m", "services.larrysport.run_scraper", # corre el script
            cwd=os.getcwd(),                         # desde la raíz del proyecto
            # stdout=asyncio.subprocess.PIPE,
            # stderr=asyncio.subprocess.PIPE,
            stdout=None,  # deja que el scraper imprima directo a la consola del bot
            stderr=None,  # deja que el scraper imprima directo a la consola del bot
        )
        stdout, stderr = await proc.communicate()   # espera que termine

        if proc.returncode == 0:
            await msg.edit_text("✅ Fixture actualizado!")
        else:
            logger.error(f"Scraper falló:\n{stderr.decode()}")
            await msg.edit_text("❌ Hubo un error.")
    except Exception as e:
        logger.error(f"Error en /actualizar: {e}")
        await msg.edit_text("❌ Hubo un error.")

    #asyncio.create_task(_ejecutar())


# ─── /cache_info ──────────────────────────────────────────────────

async def cmd_cache_info(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Muestra el estado actual del caché. Solo admins."""
    if not _es_admin(update.effective_user.id):
        await update.message.reply_text("⛔ No tenés permisos para este comando.")
        return

    await update.message.reply_text(larrysport.cache_info())


# ─── Registro ─────────────────────────────────────────────────────

def register(application):
    """Registra los comandos de admin en la aplicación de Telegram."""
    application.add_handler(CommandHandler("actualizar", cmd_actualizar))
    application.add_handler(CommandHandler("cache_info", cmd_cache_info))