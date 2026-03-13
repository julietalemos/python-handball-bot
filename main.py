"""
╔══════════════════════════════════════════════════════════════════╗
║               BOT HANDBALL - CLUB MARIANO ACOSTA                 ║
║                   Gestión de Días de Partido                     ║
╚══════════════════════════════════════════════════════════════════╝

Punto de entrada principal del bot.
Para correr: python main.py
"""

import asyncio
import datetime
import logging
import os
import sys

from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

from config.settings import Settings
from handlers.fixture import register as register_fixture
from handlers.admin import register as register_admin
from handlers.info import register as register_info
from services.larrysport import LarrySportService
from utils.logger import setup_logger

logger = setup_logger("main")


# ─── /start ───────────────────────────────────────────────────────

async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    nombre = update.effective_user.first_name
    mensaje = (
        f"👋 ¡Hola {nombre}! Soy el bot del <b>Club Mariano Acosta</b> 🤾\n\n"
        "Estoy acá para ayudarte!\n\n"
        "🤾 <b>Fixture</b>\n"
        "Comandos disponibles:\n"
        "/partidos - Ver próximos partidos\n"
        "/resultados - Ver resultados recientes\n"
        "/fixture - Archivo fixture de todas las categorías\n\n"
        "📋 <b>Info del club</b>\n"
        "/contacto - Datos de secretaría\n"
        "/alias - Datos para el pago de la cuota\n\n"
        "💡 <b>Sugerencias</b>\n"
        "/sugerencia - Mandanos tu idea, recomendación o mensaje\n\n"
        "🛠 <i>Desarrollado por Julile</i>"
    )
    await update.message.reply_text(mensaje, parse_mode="HTML")


# ─── Error handler ────────────────────────────────────────────────

async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE):
    logger.error(f"Error en update {update}: {context.error}", exc_info=True)
    if isinstance(update, Update) and update.effective_message:
        await update.effective_message.reply_text(
            "⚠️ Ocurrió un error inesperado. El equipo técnico fue notificado."
        )


# ─── Job semanal ──────────────────────────────────────────────────

async def job_actualizar_fixture(context):
    logger.info("⏰ Job semanal: actualizando fixture...")
    proc = await asyncio.create_subprocess_exec(
        sys.executable,
        "-m", "services.larrysport.run_scraper",
        cwd=os.getcwd(),
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    stdout, stderr = await proc.communicate()
    if proc.returncode == 0:
        logger.info("✅ Job completado.")
    else:
        logger.error(f"❌ Job falló:\n{stderr.decode()}")


# ─── Main ─────────────────────────────────────────────────────────

def main():
    settings = Settings()
    logger.info("🚀 Iniciando Bot Mariano Acosta...")
    logger.info(f"   Modo admin: {settings.ADMIN_USERNAME}")

    app = ApplicationBuilder().token(settings.TELEGRAM_TOKEN).build()

    # /start
    app.add_handler(CommandHandler("start", cmd_start))

    # Fixture y admin (incluyen todos sus comandos y callbacks)
    register_fixture(app)
    register_admin(app)
    register_info(app)
    
    # Error handler global
    app.add_error_handler(error_handler)

    # Job semanal — próximo miércoles a las 03:00
    now = datetime.datetime.now()
    days_until_wednesday = (2 - now.weekday()) % 7
    if days_until_wednesday == 0 and now.hour >= 3:
        days_until_wednesday = 7
    next_wednesday = (
        now.replace(hour=3, minute=0, second=0, microsecond=0)
        + datetime.timedelta(days=days_until_wednesday)
    )
    app.job_queue.run_repeating(
        job_actualizar_fixture,
        interval=datetime.timedelta(weeks=1),
        first=next_wednesday,
        name="actualizar_fixture_semanal",
    )
    logger.info(f"📅 Próxima actualización automática: {next_wednesday.strftime('%d/%m/%Y %H:%M')}")

    logger.info("✅ Bot corriendo. Presioná Ctrl+C para detener.")
    app.run_polling(
        allowed_updates=Update.ALL_TYPES,
        drop_pending_updates=True,
    )


if __name__ == "__main__":
    main()