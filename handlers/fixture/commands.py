"""
handlers/fixture/commands.py
──────────────────────────────
Comandos públicos del fixture:
  /fixture      → Flujo interactivo con botones para filtrar partidos
  /resultados   → Resultados recientes
  /fixture_full → Fixture completo como archivo .txt

Registro:
    Llamar a register(application) desde main.py
"""

import io
import logging
from collections import defaultdict

from telegram import Update
from telegram.ext import CommandHandler, ContextTypes

from services.larrysport import LarrySportService
from handlers.fixture.formatters import armar_mensaje_resultados
from handlers.fixture.keyboards import teclado_dia

logger = logging.getLogger(__name__)
larrysport = LarrySportService()


# ─── /partidos ─────────────────────────────────────────────────────

async def cmd_partidos(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Primer paso del flujo: elegir día."""
    partidos, _ = larrysport.get_fixture()

    if not partidos:
        await update.message.reply_text(
            "📭 El caché está vacío. Un admin debe correr /actualizar primero."
        )
        return

    await update.message.reply_text(
        "🤾 *FIXTURE MARIANO ACOSTA*\n_¿Qué día querés ver?_",
        parse_mode="Markdown",
        reply_markup=teclado_dia(partidos),
    )


# ─── /resultados ──────────────────────────────────────────────────

async def cmd_resultados(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Muestra los resultados recientes ordenados del más nuevo al más viejo."""
    partidos, fecha_cache = larrysport.get_fixture()

    if not partidos:
        await update.message.reply_text(
            "📭 El caché está vacío. Un admin debe correr /actualizar primero."
        )
        return

    jugados = [p for p in partidos if p.jugado]
    mensaje = armar_mensaje_resultados(jugados, fecha_cache)
    await update.message.reply_text(mensaje, parse_mode="Markdown")


# ─── /fixture_full ────────────────────────────────────────────────

async def cmd_fixture_full(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Manda el fixture completo como archivo .txt."""
    partidos, _ = larrysport.get_fixture()

    if not partidos:
        await update.message.reply_text(
            "📭 El caché está vacío. Un admin debe correr /actualizar primero."
        )
        return

    proximos = [p for p in partidos if not p.jugado]
    if not proximos:
        await update.message.reply_text("📭 No hay partidos próximos.")
        return

    # Agrupamos por rama + categoría
    grupos: dict[str, list] = defaultdict(list)
    for p in proximos:
        grupos[f"{p.rama} - {p.categoria}"].append(p)

    lineas = ["FIXTURE COMPLETO - MARIANO ACOSTA HANDBALL", "=" * 45, ""]
    for grupo, ps in sorted(grupos.items()):
        lineas.append(f"[ {grupo.upper()} ]")
        for p in ps:
            division  = p.division or p.torneo
            condicion = "Local" if p.es_local else "Visitante"
            lineas.append(f"  {division}")
            lineas.append(f"  {p.fecha_raw} — {condicion}")
            lineas.append(f"  {p.local} vs {p.visitante}")
            lineas.append("")
        lineas.append("")

    archivo = io.BytesIO("\n".join(lineas).encode("utf-8"))
    archivo.name = "fixture_mariano_acosta.txt"

    await update.message.reply_document(
        document=archivo,
        filename="fixture_mariano_acosta.txt",
        caption=f"📋 Fixture completo — {len(proximos)} partidos próximos",
    )


# ─── Registro ─────────────────────────────────────────────────────

def register(application):
    """Registra los comandos de fixture en la aplicación de Telegram."""
    application.add_handler(CommandHandler("partidos",  cmd_partidos))
    application.add_handler(CommandHandler("resultados",   cmd_resultados))
    application.add_handler(CommandHandler("fixture", cmd_fixture_full))