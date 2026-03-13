"""
handlers/info/__init__.py
──────────────────────────
Registra todos los handlers informativos.

Uso desde main.py:
    from handlers.info import register
    register(application)
"""

from handlers.info.commands import register as register_commands


def register(application):
    register_commands(application)