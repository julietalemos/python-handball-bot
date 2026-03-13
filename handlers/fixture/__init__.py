"""
handlers/fixture/__init__.py
──────────────────────────────
Registra todos los handlers del fixture (comandos + callbacks).

Uso desde main.py:
    from handlers.fixture import register
    register(application)
"""

from handlers.fixture.commands import register as register_commands
from handlers.fixture.callbacks import register as register_callbacks


def register(application):
    register_commands(application)
    register_callbacks(application)