"""
handlers/fixture/callbacks.py
───────────────────────────────
Maneja todos los callbacks de los botones inline del fixture.

Flujo:
    fix|dia|{dia_key}
        → fix|rama|{dia_key}|{rama_key}
            → fix|cat|{dia_key}|{rama_key}|{cat_key}
                → mensaje con partidos filtrados + botón "Buscar otro"
    fix|volver
        → vuelve al primer paso

Registro:
    Llamar a register(application) desde main.py
"""

import logging
from datetime import datetime, timedelta

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import CallbackQueryHandler, ContextTypes

from services.larrysport import LarrySportService
from handlers.fixture.keyboards import (
    DIAS,
    RAMAS,
    teclado_categoria,
    teclado_dia,
    teclado_rama,
)
from handlers.fixture.formatters import armar_mensaje_fixture

logger = logging.getLogger(__name__)
larrysport = LarrySportService()

# ─── Labels para el título del mensaje ────────────────────────────

_LABEL_DIA = {
    "sab":      "Sábado",
    "dom":      "Domingo",
    "todos_dia": "",
}

_LABEL_RAMA = {
    "damas":      "Damas",
    "caballeros": "Caballeros",
    "todos_rama": "",
}


# ─── Filtrado de próximos ─────────────────────────────────────────

def _filtrar_proximos(
    partidos,
    dia_key: str,
    rama_key: str,
    cat_key: str,
    dias_adelante: int = 14,
):
    """
    Filtra partidos próximos según día, rama y categoría.
    Solo incluye partidos no jugados dentro de los próximos días_adelante días.
    """
    from services.larrysport.models import Partido
    from handlers.fixture.keyboards import DIAS, RAMAS

    ahora  = datetime.now()
    limite = ahora + timedelta(days=dias_adelante)

    dia_val  = DIAS.get(dia_key)
    rama_val = RAMAS.get(rama_key)
    cat_val  = None if cat_key == "todas" else cat_key.capitalize()

    resultado = []
    for p in partidos:
        if p.jugado:
            continue

        # Verificar que la fecha esté dentro del rango
        fecha = _parsear_fecha(p.fecha_raw)
        if fecha is None or not (ahora <= fecha <= limite):
            continue

        if dia_val and not p.fecha_raw.lower().startswith(dia_val):
            continue
        if rama_val and p.rama != rama_val:
            continue
        if cat_val and p.categoria != cat_val:
            continue

        resultado.append(p)

    return resultado


# Meses en español → número (necesario para parsear fecha_raw)
_MESES = {
    "enero": 1, "febrero": 2, "marzo": 3, "abril": 4,
    "mayo": 5, "junio": 6, "julio": 7, "agosto": 8,
    "septiembre": 9, "octubre": 10, "noviembre": 11, "diciembre": 12,
}

def _parsear_fecha(fecha_raw: str) -> datetime | None:
    """Convierte fecha_raw a datetime. Retorna None si no puede parsear."""
    try:
        partes = fecha_raw.split()
        # formato: "sáb 21 marzo 19:45"
        dia  = int(partes[1])
        mes  = _MESES.get(partes[2].lower(), 0)
        hora = partes[3] if len(partes) > 3 else "00:00"
        h, m = map(int, hora.split(":"))
        return datetime(datetime.now().year, mes, dia, h, m)
    except Exception:
        return None


# ─── Callback principal ───────────────────────────────────────────

async def callback_fixture(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data  = query.data

    partidos, fecha_cache = larrysport.get_fixture()

    # ── Paso 1: eligió día → mostrar ramas ────────────────────────
    if data.startswith("fix|dia|"):
        dia_key   = data.removeprefix("fix|dia|")
        dia_label = _LABEL_DIA.get(dia_key, "Todos los días") or "Todos los días"

        await query.edit_message_text(
            f"🤾 *FIXTURE MARIANO ACOSTA*\n"
            f"📅 _{dia_label}_ → ¿Qué rama?",
            parse_mode="Markdown",
            reply_markup=teclado_rama(dia_key, partidos),
        )

    # ── Paso 2: eligió rama → mostrar categorías ──────────────────
    elif data.startswith("fix|rama|"):
        _, _, dia_key, rama_key = data.split("|")
        dia_label  = _LABEL_DIA.get(dia_key, "")  or "Todos"
        rama_label = _LABEL_RAMA.get(rama_key, "") or "Todos"

        await query.edit_message_text(
            f"🤾 *FIXTURE MARIANO ACOSTA*\n"
            f"📅 _{dia_label}_ • 👥 _{rama_label}_ → ¿Qué categoría?",
            parse_mode="Markdown",
            reply_markup=teclado_categoria(dia_key, rama_key, partidos),
        )

    # ── Paso 3: eligió categoría → mostrar partidos ───────────────
    elif data.startswith("fix|cat|"):
        _, _, dia_key, rama_key, cat_key = data.split("|")

        filtrados = _filtrar_proximos(partidos, dia_key, rama_key, cat_key)

        # Título descriptivo
        partes_titulo = filter(None, [
            _LABEL_DIA.get(dia_key, ""),
            _LABEL_RAMA.get(rama_key, ""),
            "" if cat_key == "todas" else cat_key.capitalize(),
        ])
        subtitulo = " • ".join(partes_titulo)
        titulo = f"MARIANO ACOSTA — {subtitulo}" if subtitulo else "MARIANO ACOSTA"

        filtrados = _filtrar_proximos(partidos, dia_key, rama_key, cat_key)

        mensaje = armar_mensaje_fixture(filtrados, titulo, fecha_cache)

        teclado_volver = InlineKeyboardMarkup([[
            InlineKeyboardButton("🔄 Buscar otro", callback_data="fix|volver")
        ]])

        await query.edit_message_text(
            mensaje,
            parse_mode="Markdown",
            reply_markup=teclado_volver,
        )

    # ── Volver al inicio ──────────────────────────────────────────
    elif data == "fix|volver":
        await query.edit_message_text(
            "🤾 *FIXTURE MARIANO ACOSTA*\n_¿Qué día querés ver?_",
            parse_mode="Markdown",
            reply_markup=teclado_dia(partidos),
        )


# ─── Registro ─────────────────────────────────────────────────────

def register(application):
    """Registra el handler de callbacks en la aplicación de Telegram."""
    application.add_handler(CallbackQueryHandler(callback_fixture, pattern=r"^fix\|"))