"""
handlers/fixture/keyboards.py
───────────────────────────────
Teclados inline para el flujo de filtros de fixture.

Cada teclado muestra solo las opciones que tienen partidos disponibles,
evitando botones que llevarían a resultados vacíos.

Funciones públicas:
    teclado_dia(partidos)               → InlineKeyboardMarkup
    teclado_rama(dia_key, partidos)     → InlineKeyboardMarkup
    teclado_categoria(dia_key, rama_key, partidos) → InlineKeyboardMarkup
"""

from telegram import InlineKeyboardButton, InlineKeyboardMarkup

from services.larrysport.models import Partido

# ─── Mapeos de keys a valores reales ──────────────────────────────
# Usados también en callbacks.py para traducir de vuelta

DIAS: dict[str, str | None] = {
    "sab":      "sáb",
    "dom":      "dom",
    "todos_dia": None,
}

RAMAS: dict[str, str | None] = {
    "damas":      "Femenino",
    "caballeros": "Masculino",
    "todos_rama": None,
}

# Orden canónico de categorías
CATEGORIAS = ["Mayores", "Junior", "Juveniles", "Cadetes", "Menores", "Infantiles"]


# ─── Filtrado básico para detectar opciones disponibles ───────────

def _partidos_para_dia(partidos: list[Partido], dia_key: str) -> list[Partido]:
    dia_val = DIAS.get(dia_key)
    if dia_val is None:
        return partidos
    return [p for p in partidos if p.fecha_raw.lower().startswith(dia_val)]


def _partidos_para_rama(partidos: list[Partido], rama_key: str) -> list[Partido]:
    rama_val = RAMAS.get(rama_key)
    if rama_val is None:
        return partidos
    return [p for p in partidos if p.rama == rama_val]


# ─── Teclados ─────────────────────────────────────────────────────

def teclado_dia(partidos: list[Partido]) -> InlineKeyboardMarkup:
    """Muestra solo los días que tienen partidos próximos."""
    dias_disponibles: set[str] = set()
    for p in partidos:
        fecha = p.fecha_raw.lower()
        if fecha.startswith("sáb"):
            dias_disponibles.add("sab")
        elif fecha.startswith("dom"):
            dias_disponibles.add("dom")

    botones = []
    if "sab" in dias_disponibles:
        botones.append(InlineKeyboardButton("📅 Sábado", callback_data="fix|dia|sab"))
    if "dom" in dias_disponibles:
        botones.append(InlineKeyboardButton("📅 Domingo", callback_data="fix|dia|dom"))
    botones.append(InlineKeyboardButton("📅 Todos", callback_data="fix|dia|todos_dia"))

    return InlineKeyboardMarkup([botones])


def teclado_rama(dia_key: str, partidos: list[Partido]) -> InlineKeyboardMarkup:
    """Muestra solo las ramas que tienen partidos en el día elegido."""
    filtrados = _partidos_para_dia(partidos, dia_key)
    ramas_disponibles = {p.rama for p in filtrados}

    botones = []
    if "Femenino" in ramas_disponibles:
        botones.append(InlineKeyboardButton("👩 Damas", callback_data=f"fix|rama|{dia_key}|damas"))
    if "Masculino" in ramas_disponibles:
        botones.append(InlineKeyboardButton("👨 Caballeros", callback_data=f"fix|rama|{dia_key}|caballeros"))
    botones.append(InlineKeyboardButton("🏆 Todos", callback_data=f"fix|rama|{dia_key}|todos_rama"))

    return InlineKeyboardMarkup([botones])


def teclado_categoria(
    dia_key: str, rama_key: str, partidos: list[Partido]
) -> InlineKeyboardMarkup:
    """Muestra solo las categorías que tienen partidos en el día y rama elegidos."""
    filtrados = _partidos_para_rama(_partidos_para_dia(partidos, dia_key), rama_key)
    cats_disponibles = {p.categoria for p in filtrados}

    botones = [
        InlineKeyboardButton(cat, callback_data=f"fix|cat|{dia_key}|{rama_key}|{cat.lower()}")
        for cat in CATEGORIAS
        if cat in cats_disponibles
    ]
    botones.append(InlineKeyboardButton("🏆 Todas", callback_data=f"fix|cat|{dia_key}|{rama_key}|todas"))

    filas = [botones[i:i+3] for i in range(0, len(botones), 3)]
    return InlineKeyboardMarkup(filas)