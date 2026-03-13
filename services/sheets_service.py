"""
services/sheets_service.py
───────────────────────────
Toda la lógica de interacción con Google Sheets.

Estructura de la planilla:
  • Hoja "Partidos":    fecha | rival | hora | lugar | categoria | estado
  • Hoja "Asistencia":  partido_id | jugador_id | nombre | telegram_id | estado | timestamp
  • Hoja "Jugadores":   telegram_id | nombre | username | categoria | activo
"""

import logging
from datetime import datetime
from typing import Optional

import gspread
from google.oauth2.service_account import Credentials

from config.settings import Settings

logger = logging.getLogger(__name__)

# Permisos que necesita la Service Account de Google
SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]


class SheetsService:
    """
    Servicio principal para leer y escribir en Google Sheets.

    Uso:
        sheets = SheetsService()
        partido = sheets.get_proximo_partido()
        sheets.registrar_confirmacion(telegram_id=123, nombre="Juan")
    """

    def __init__(self):
        self.settings = Settings()
        self._cliente = None
        self._planilla = None

    def _conectar(self) -> gspread.Spreadsheet:
        """
        Establece conexión con Google Sheets.
        Usa lazy loading: solo conecta cuando se necesita.
        """
        if self._planilla is None:
            try:
                # Autenticamos con el archivo JSON de la Service Account
                credenciales = Credentials.from_service_account_file(
                    self.settings.GOOGLE_CREDENTIALS_PATH,
                    scopes=SCOPES,
                )
                self._cliente = gspread.authorize(credenciales)
                self._planilla = self._cliente.open_by_key(
                    self.settings.GOOGLE_SHEET_ID
                )
                logger.info("✅ Conectado a Google Sheets correctamente")
            except Exception as e:
                logger.error(f"❌ Error conectando a Google Sheets: {e}")
                raise

        return self._planilla

    # ─── PARTIDOS ────────────────────────────────────────────────

    def get_proximo_partido(self) -> Optional[dict]:
        """
        Obtiene el próximo partido con estado 'programado'.
        Retorna un dict con los datos o None si no hay partidos.

        Formato esperado en la hoja "Partidos":
        | ID | Fecha      | Rival          | Hora  | Lugar          | Categoría | Estado     |
        | 1  | 15/06/2025 | Club Atletico  | 18:00 | Gimnasio Norte | Primera   | programado |
        """
        try:
            planilla = self._conectar()
            hoja = planilla.worksheet(self.settings.SHEET_PARTIDOS)
            registros = hoja.get_all_records()  # Lista de dicts con headers como keys

            ahora = datetime.now()

            for registro in registros:
                if registro.get("Estado", "").lower() == "programado":
                    # Parseamos la fecha para verificar que sea futura
                    try:
                        fecha = datetime.strptime(registro["Fecha"], "%d/%m/%Y")
                        if fecha >= ahora.replace(hour=0, minute=0, second=0):
                            return {
                                "id": registro.get("ID"),
                                "fecha": registro.get("Fecha"),
                                "rival": registro.get("Rival"),
                                "hora": registro.get("Hora"),
                                "lugar": registro.get("Lugar"),
                                "categoria": registro.get("Categoría"),
                                "estado": registro.get("Estado"),
                            }
                    except ValueError:
                        logger.warning(
                            f"Fecha con formato incorrecto en partido ID {registro.get('ID')}"
                        )
                        continue

            return None  # No hay partidos programados

        except Exception as e:
            logger.error(f"Error obteniendo próximo partido: {e}")
            raise

    def crear_partido(self, fecha: str, rival: str, hora: str, lugar: str, categoria: str) -> int:
        """
        Agrega un nuevo partido a la planilla.
        Retorna el ID del partido creado.

        Args:
            fecha:     "15/06/2025"
            rival:     "Club Atlético XYZ"
            hora:      "18:00"
            lugar:     "Gimnasio Municipal Norte"
            categoria: "Primera División"
        """
        try:
            planilla = self._conectar()
            hoja = planilla.worksheet(self.settings.SHEET_PARTIDOS)

            # Obtenemos todos los registros para calcular el próximo ID
            registros = hoja.get_all_records()
            nuevo_id = len(registros) + 1  # ID autoincremental simple

            # Agregamos la fila al final de la hoja
            hoja.append_row([
                nuevo_id,
                fecha,
                rival,
                hora,
                lugar,
                categoria,
                "programado",  # Estado inicial
                datetime.now().strftime("%d/%m/%Y %H:%M"),  # Timestamp de creación
            ])

            logger.info(f"✅ Partido #{nuevo_id} creado: {rival} - {fecha}")
            return nuevo_id

        except Exception as e:
            logger.error(f"Error creando partido: {e}")
            raise

    # ─── ASISTENCIA ──────────────────────────────────────────────

    def registrar_confirmacion(
        self,
        partido_id: int,
        telegram_id: int,
        nombre: str,
        username: str = "",
        estado: str = "confirmado",
    ) -> bool:
        """
        Registra o actualiza la confirmación de un jugador.

        Si el jugador ya confirmó para este partido, actualiza su estado.
        Si es nuevo, agrega una fila.

        Returns:
            True si fue una confirmación nueva, False si fue actualización.
        """
        try:
            planilla = self._conectar()
            hoja = planilla.worksheet(self.settings.SHEET_ASISTENCIA)
            registros = hoja.get_all_records()

            timestamp = datetime.now().strftime("%d/%m/%Y %H:%M:%S")

            # Buscamos si el jugador ya tiene registro para este partido
            for idx, registro in enumerate(registros, start=2):  # start=2 porque fila 1 es header
                if (
                    str(registro.get("Partido ID")) == str(partido_id)
                    and str(registro.get("Telegram ID")) == str(telegram_id)
                ):
                    # Actualizamos el estado existente
                    # La columna "Estado" es la 5ta (E), "Timestamp" la 6ta (F)
                    hoja.update_cell(idx, 5, estado)
                    hoja.update_cell(idx, 6, timestamp)
                    logger.info(f"Actualizado: {nombre} → {estado} (Partido #{partido_id})")
                    return False  # No es nuevo, fue actualización

            # Si llegamos acá, es un registro nuevo
            hoja.append_row([
                partido_id,
                telegram_id,
                nombre,
                username,
                estado,
                timestamp,
            ])
            logger.info(f"Nuevo registro: {nombre} → {estado} (Partido #{partido_id})")
            return True

        except Exception as e:
            logger.error(f"Error registrando confirmación: {e}")
            raise

    def get_lista_confirmados(self, partido_id: int) -> dict:
        """
        Obtiene la lista de jugadores y su estado para un partido.

        Returns:
            {
                "confirmados": [{"nombre": "Juan", "username": "@juan"}, ...],
                "cancelados":  [{"nombre": "Pedro", ...}],
                "total": 5
            }
        """
        try:
            planilla = self._conectar()
            hoja = planilla.worksheet(self.settings.SHEET_ASISTENCIA)
            registros = hoja.get_all_records()

            confirmados = []
            cancelados = []

            for registro in registros:
                if str(registro.get("Partido ID")) == str(partido_id):
                    info = {
                        "nombre": registro.get("Nombre", "Sin nombre"),
                        "username": registro.get("Username", ""),
                    }
                    if registro.get("Estado") == "confirmado":
                        confirmados.append(info)
                    elif registro.get("Estado") == "cancelado":
                        cancelados.append(info)

            return {
                "confirmados": confirmados,
                "cancelados": cancelados,
                "total": len(confirmados),
            }

        except Exception as e:
            logger.error(f"Error obteniendo lista de confirmados: {e}")
            raise

    def get_stats_partido(self, partido_id: int) -> dict:
        """
        Estadísticas de asistencia para un partido.
        Útil para el comando /stats del admin.
        """
        lista = self.get_lista_confirmados(partido_id)
        return {
            "confirmados": lista["total"],
            "cancelados": len(lista["cancelados"]),
            "pendientes": "N/A",  # Requeriría lista completa de jugadores
            "lista_confirmados": lista["confirmados"],
        }
