"""
config/settings.py
──────────────────
Centraliza TODA la configuración del proyecto.
Lee las variables desde el archivo .env (nunca hardcodeadas en el código).

¿Por qué esto es importante?
  → Si subís el código a GitHub, tus contraseñas NO quedan expuestas.
  → Podés cambiar valores sin tocar el código fuente.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Carga el archivo .env desde la raíz del proyecto
BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")


class Settings:
    """
    Clase singleton de configuración.
    Uso: settings = Settings()  →  settings.TELEGRAM_TOKEN
    """

    # ─── Telegram ────────────────────────────────────────────────
    TELEGRAM_TOKEN: str = os.getenv("TELEGRAM_TOKEN", "")

    # Username del DT/admin sin el @  (ej: "profe_martinez")
    ADMIN_USERNAME: str = os.getenv("ADMIN_USERNAME", "")

    # IDs de Telegram de los admins (separados por coma en .env)
    # Ej en .env:  ADMIN_IDS=123456789,987654321
    _admin_ids_raw: str = os.getenv("ADMIN_IDS", "")
    ADMIN_IDS: list[int] = (
        [int(x.strip()) for x in _admin_ids_raw.split(",") if x.strip()]
        if _admin_ids_raw
        else []
    )

    # ─── Google Sheets ───────────────────────────────────────────
    # Ruta al archivo JSON de credenciales de la Service Account
    GOOGLE_CREDENTIALS_PATH: str = os.getenv(
        "GOOGLE_CREDENTIALS_PATH",
        str(BASE_DIR / "credentials" / "google_credentials.json"),
    )

    # ID de la planilla de Google Sheets
    # Lo encontrás en la URL: docs.google.com/spreadsheets/d/ESTE_ES_EL_ID/edit
    GOOGLE_SHEET_ID: str = os.getenv("GOOGLE_SHEET_ID", "")

    # Nombre de las hojas dentro de la planilla
    SHEET_PARTIDOS: str = os.getenv("SHEET_PARTIDOS", "Partidos")
    SHEET_ASISTENCIA: str = os.getenv("SHEET_ASISTENCIA", "Asistencia")
    SHEET_JUGADORES: str = os.getenv("SHEET_JUGADORES", "Jugadores")

    # ─── Base de datos local (SQLite para backup/cache) ──────────
    DATABASE_PATH: str = os.getenv(
        "DATABASE_PATH", str(BASE_DIR / "data" / "handball.db")
    )

    # ─── Configuración del club ───────────────────────────────────
    NOMBRE_CLUB: str = os.getenv("NOMBRE_CLUB", "")
    COBRANZA_MAIL: str = os.getenv("COBRANZA_MAIL", "")
    ALIAS_CLUB: str = os.getenv("ALIAS_CLUB", "")
    TITULAR_CUENTA: str = os.getenv("TITULAR_CUENTA", "")

    SECRETARIA_TELEFONO: str = os.getenv("SECRETARIA_TELEFONO", "")
    SECRETARIA_HORARIOS: str = os.getenv("SECRETARIA_HORARIOS", "")
    SECRETARIA_DIRECCION: str = os.getenv("SECRETARIA_DIRECCION", "")

    # ─── Logging ─────────────────────────────────────────────────
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    LOG_PATH: str = os.getenv("LOG_PATH", str(BASE_DIR / "logs" / "bot.log"))

    def validate(self) -> None:
        """
        Valida que las variables críticas estén configuradas.
        Llamar al inicio del programa para detectar errores de config temprano.
        """
        errores = []

        if not self.TELEGRAM_TOKEN:
            errores.append("❌ TELEGRAM_TOKEN no está configurado en .env")

        if not self.GOOGLE_SHEET_ID:
            errores.append("❌ GOOGLE_SHEET_ID no está configurado en .env")

        if not Path(self.GOOGLE_CREDENTIALS_PATH).exists():
            errores.append(
                f"❌ No se encontró el archivo de credenciales: {self.GOOGLE_CREDENTIALS_PATH}"
            )

        if errores:
            raise EnvironmentError(
                "\n".join(["Errores de configuración:"] + errores)
            )

        return True
