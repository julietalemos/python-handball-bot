"""
handlers/admin/__init__.py
───────────────────────────
Registra todos los handlers de administración.

Uso desde main.py:
    from handlers.admin import register
    register(application)
"""

from handlers.admin.commands import register as register_commands


def register(application):
    register_commands(application)