"""
handlers/fixture/formatters.py
────────────────────────────────
Funciones de formateo de partidos para mensajes de Telegram (Markdown).

Funciones públicas:
    formatear_partido(p)                    → str con un partido
    armar_mensaje_fixture(partidos, titulo) → str con próximos partidos
    armar_mensaje_resultados(partidos)      → str con resultados recientes
"""

from datetime import datetime
from typing import Optional

from services.larrysport.models import Partido

# ─── Helpers internos ─────────────────────────────────────────────

def _fecha_cache_str(fecha: Optional[datetime]) -> str:
    """Convierte datetime del caché a string legible. Retorna vacío si None."""
    if not fecha:
        return ""
    return fecha.strftime("%d/%m %H:%M")


def _nombres_partido(p: Partido) -> tuple[str, str]:
    """
    Retorna (local_str, visitante_str) con el equipo de Mariano Acosta en negrita.
    """
    if p.es_local:
        return f"*{p.local}*", p.visitante
    return p.local, f"*{p.visitante}*"


def _linea_torneo(p: Partido) -> str:
    """Línea del torneo con división si está disponible."""
    division = p.division or p.torneo
    return f"🏆 _{division}_ • {p.categoria}\n"


# ─── Formateo de partido individual ──────────────────────────────

def formatear_partido(p: Partido) -> str:
    """
    Formatea un partido individual para Telegram.
    Muestra resultado si ya se jugó, o fecha y condición si es próximo.
    """
    local_str, visitante_str = _nombres_partido(p)
    linea_torneo = _linea_torneo(p)

    if p.jugado:
        resultado = f"{p.marcador_local}-{p.marcador_visitante}"
        gano = (
            (p.marcador_local or 0) > (p.marcador_visitante or 0)
            if p.es_local else
            (p.marcador_visitante or 0) > (p.marcador_local or 0)
        )
        emoji = "🏆" if gano else "💔"
        return (
            f"{linea_torneo}"
            f"📆 {p.fecha_raw}\n"
            f"{emoji} {local_str} *{resultado}* {visitante_str}\n"
        )
    else:
        condicion = "🏠 Local" if p.es_local else "✈️ Visitante"
        return (
            f"{linea_torneo}"
            f"📆 {p.fecha_raw} — {condicion}\n"
            f"⚔️ {local_str} vs {visitante_str}\n"
        )


# ─── Mensajes completos ───────────────────────────────────────────

def armar_mensaje_fixture(
    partidos: list[Partido],
    titulo: str,
    fecha_cache: Optional[datetime] = None,
) -> str:
    """
    Arma el mensaje de fixture con próximos partidos.
    Los partidos deben venir ya filtrados (solo próximos).
    """
    if not partidos:
        return "📭 No hay partidos con ese filtro."

    fecha_str = _fecha_cache_str(fecha_cache)

    msg = f"🤾 *{titulo}*\n"
    if fecha_str:
        msg += f"_Actualizado: {fecha_str}_\n"
    msg += "─" * 28 + "\n\n"
    msg += "📅 *PRÓXIMOS*\n\n"

    for p in partidos:
        msg += formatear_partido(p) + "\n"

    return msg.strip()


def armar_mensaje_resultados(
    partidos: list[Partido],
    fecha_cache: Optional[datetime] = None,
) -> str:
    """
    Arma el mensaje de resultados recientes.
    Los partidos deben venir ya filtrados (solo jugados).
    """
    if not partidos:
        return "📭 No hay resultados recientes."

    fecha_str = _fecha_cache_str(fecha_cache)

    msg = "✅ *RESULTADOS MARIANO ACOSTA*\n"
    if fecha_str:
        msg += f"_Actualizado: {fecha_str}_\n"
    msg += "─" * 28 + "\n\n"

    for p in partidos:
        msg += formatear_partido(p) + "\n"

    return msg.strip()