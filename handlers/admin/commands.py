"""
handlers/admin/commands.py
───────────────────────────
Comandos exclusivos para admins:
  /cache_info → Muestra el estado actual del caché

Registro:
    Llamar a register(application) desde main.py
"""

import logging

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
    """Informa que el fixture se actualiza manualmente. Solo admins."""
    if not _es_admin(update.effective_user.id):
        await update.message.reply_text("⛔ No tenés permisos para este comando.")
        return
    await update.message.reply_text(
        "ℹ️ El fixture se actualiza manualmente.\n"
        "Subí el archivo `fixture_cache.json` a la carpeta `data/` del repo.",
        parse_mode="Markdown",
    )


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