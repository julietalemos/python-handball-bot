"""
services/larrysport/models.py
──────────────────────────────
Modelo de dominio para un partido de Mariano Acosta.

Todos los campos son los mismos que usaba el dict original,
tipados explícitamente para facilitar autocompletado y detección de errores.
"""

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class Partido:
    # ── Torneo ──────────────────────────────────────────────────
    torneo:    str          # Nombre corto del torneo  (ej. "Torneo Apertura")
    division:  str          # Sección del torneo       (ej. "Liga de Honor Plata")
    rama:      str          # "Femenino" | "Masculino"
    categoria: str          # "Mayores" | "Junior" | "Juveniles" | …

    # ── Fecha ───────────────────────────────────────────────────
    fecha_raw: str          # Texto original           (ej. "sáb 21 marzo 19:45")
    hora:      str          # Solo la hora             (ej. "19:45")

    # ── Equipos ─────────────────────────────────────────────────
    local:      str
    visitante:  str
    es_local:   bool        # True si Mariano Acosta es el local
    rival:      str         # Nombre del rival (o "Por confirmar")

    # ── Resultado (None = partido no jugado aún) ─────────────────
    marcador_local:     Optional[int] = None
    marcador_visitante: Optional[int] = None
    jugado:             bool          = False