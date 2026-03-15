"""
handlers/info/commands.py
──────────────────────────
Comandos informativos públicos:
  /contacto   → Datos de secretaría con link a WhatsApp
  /alias      → Datos para el pago de la cuota
  /sugerencia → Envía una sugerencia o recomendación al admin

Registro:
    Llamar a register(application) desde main.py
"""

import logging

from telegram import Update
from telegram.ext import CommandHandler, ContextTypes

from config.settings import Settings

logger = logging.getLogger(__name__)
settings = Settings()


# ─── /contacto ────────────────────────────────────────────────────

async def cmd_contacto(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Muestra los datos de contacto de secretaría."""
    telefono  = settings.SECRETARIA_TELEFONO
    horarios  = settings.SECRETARIA_HORARIOS
    direccion = settings.SECRETARIA_DIRECCION

    # Formateamos el número para el link de WhatsApp (solo dígitos)
    numero_limpio = "".join(filter(str.isdigit, telefono))
    link_wa = f"https://wa.me/{numero_limpio}"

    mensaje = (
        "📋 *SECRETARÍA — MARIANO ACOSTA*\n"
        "─────────────────────────────────\n\n"
        f"📍 {direccion}\n\n"
        f"🕐 *Horarios de atención*\n"
        f"{horarios}\n\n"
        f"📱 *WhatsApp*\n"
        f"[{telefono}]({link_wa})"
    )

    await update.message.reply_text(mensaje, parse_mode="Markdown")


# ─── /alias ───────────────────────────────────────────────────────

async def cmd_alias(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Muestra los datos para el pago de la cuota."""
    alias    = settings.ALIAS_CLUB
    titular  = settings.TITULAR_CUENTA
    mail     = settings.COBRANZA_MAIL

    mensaje = (
        "💳 *PAGO DE CUOTA — MARIANO ACOSTA*\n"
        "───────────────────────────────────\n\n"
        f"👤 *Titular:* {titular}\n"
        f"🏦 *Alias:* `{alias}`\n\n"
        "📧 *Una vez realizado el pago, enviá el comprobante con:*\n"
        "• Nombre y apellido\n"
        "• Categoría\n\n"
        f"Al mail: `{mail}`"
    )

    await update.message.reply_text(mensaje, parse_mode="Markdown")


# ─── /sugerencia ──────────────────────────────────────────────────

async def cmd_sugerencia(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Recibe una sugerencia del usuario y la reenvía al admin por privado.
    Uso: /sugerencia <texto>
    """
    if not context.args:
        await update.message.reply_text(
            "💡 *¿Tenés una sugerencia?*\n\n"
            "Usá el comando así:\n"
            "`/sugerencia Tu mensaje acá`\n\n"
            "_Ejemplo: /sugerencia Estaría bueno ver las posiciones del torneo_",
            parse_mode="Markdown",
        )
        return

    texto = " ".join(context.args)
    usuario = update.effective_user

    nombre   = f"{usuario.first_name} {usuario.last_name or ''}".strip()
    username = f"@{usuario.username}" if usuario.username else "sin username"

    # Notificamos al usuario que llegó
    await update.message.reply_text(
        "✅ *¡Gracias por tu sugerencia!*\n"
        "_Le llegará al equipo del bot._",
        parse_mode="Markdown",
    )

    # Reenviamos a todos los admins
    mensaje_admin = (
        "💡 *NUEVA SUGERENCIA*\n"
        "─" * 28 + "\n\n"
        f"👤 {nombre} ({username})\n"
        f"🆔 `{usuario.id}`\n\n"
        f"_{texto}_"
    )

    for admin_id in settings.ADMIN_IDS:
        try:
            await context.bot.send_message(
                chat_id=admin_id,
                text=mensaje_admin,
                parse_mode="Markdown",
            )
        except Exception as e:
            logger.warning(f"No se pudo notificar al admin {admin_id}: {e}")


# ─── Registro ─────────────────────────────────────────────────────

def register(application):
    """Registra los comandos informativos en la aplicación de Telegram."""
    application.add_handler(CommandHandler("contacto",   cmd_contacto))
    application.add_handler(CommandHandler("alias",      cmd_alias))
    application.add_handler(CommandHandler("sugerencia", cmd_sugerencia))