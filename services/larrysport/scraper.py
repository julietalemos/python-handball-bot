"""
services/larrysport/scraper.py
───────────────────────────────
Scraping de FEMEBAL Tournament Tracker con Playwright.
Itera sobre todas las combinaciones de rama/categoría,
extrae los partidos de Mariano Acosta y retorna la lista completa.

Función pública:
    scrape_todos() → list[Partido]
"""

import asyncio
import logging
import re

from playwright.async_api import async_playwright, Browser, Page

from config.settings import Settings
from services.larrysport.models import Partido
from services.larrysport.parser import extraer_partidos

logger = logging.getLogger(__name__)

# ─── Constantes ───────────────────────────────────────────────────

URL_FEMEBAL = "https://www.femebal.com/tournament-tracker/?noAdv=0"

COMBINACIONES: list[tuple[str, str]] = [
    ("Femenino",  "Mayores"),
    ("Masculino", "Mayores"),
    ("Femenino",  "Junior"),
    ("Masculino", "Junior"),
    ("Femenino",  "Juveniles"),
    ("Masculino", "Juveniles"),
    ("Femenino",  "Cadetes"),
    ("Masculino", "Cadetes"),
    ("Femenino",  "Menores"),
    ("Masculino", "Menores"),
    ("Femenino",  "Infantiles"),
    ("Masculino", "Infantiles"),
]

SECCIONES_CONOCIDAS = [
    "LHD Hipotecario Seguros", "Liga de Honor Plata", "Liga de Honor",
    "1º División", "2º División", "3º División", "4º División",
    "1° División", "2° División", "3° División", "4° División",
    "Torneos multidivision", "Torneos Multidivisión",
]

_PATRON_ICONOS = re.compile(r"[\ue000-\uf8ff]")


# ─── Navegación ───────────────────────────────────────────────────

async def _cargar_pagina(page: Page) -> None:
    await page.goto(URL_FEMEBAL, timeout=30000)
    await page.wait_for_load_state("networkidle", timeout=30000)
    await asyncio.sleep(2)


async def _seleccionar_rama_categoria(page: Page, rama: str, categoria: str) -> None:
    await page.click('[class*="ms-Dropdown"]')
    await asyncio.sleep(1)
    await page.click(f'button:has-text("{rama}")')
    await asyncio.sleep(3)

    dropdowns = await page.query_selector_all('[class*="ms-Dropdown"]')
    await dropdowns[5].click()
    await asyncio.sleep(1)
    await page.click(f'button:has-text("{categoria}")')
    await asyncio.sleep(3)


# ─── Detección de torneos ─────────────────────────────────────────

async def _get_cajas_torneos(page: Page) -> list[dict]:
    """
    Retorna las cajas de torneos visibles con su nombre y división.
    La división es el encabezado de sección que aparece antes del grupo de cajas
    (ej: "Liga de Honor Plata").
    """
    texto_pagina = await page.evaluate("() => document.body.innerText")
    lineas_raw = [l.strip() for l in texto_pagina.split("\n") if l.strip()]
    lineas = [_PATRON_ICONOS.sub("", l).strip() for l in lineas_raw]
    lineas = [l for l in lineas if l]

    # Mapeamos cada torneo a su sección según el orden en que aparecen
    seccion_actual = ""
    mapa_torneo_seccion: dict[str, str] = {}
    torneo_count: dict[str, int] = {}

    for linea in lineas:
        if any(linea.startswith(s) or s in linea for s in SECCIONES_CONOCIDAS):
            seccion_actual = linea
        elif (linea.startswith("Torneo") or
              linea.startswith("Super 8") or
              linea.startswith("Copa")):
            count = torneo_count.get(linea, 0)
            torneo_count[linea] = count + 1
            mapa_torneo_seccion[f"{linea}_{count}"] = seccion_actual

    # Leemos las cajas del DOM
    cajas_dom = await page.query_selector_all(".tournament-box.clickable")
    resultado = []
    contadores: dict[str, int] = {}

    for caja in cajas_dom:
        txt = await caja.inner_text()
        txt_limpio = _PATRON_ICONOS.sub("", txt).replace("\n", " ").strip()
        txt_limpio = re.sub(r"\s+", " ", txt_limpio)

        count = contadores.get(txt_limpio, 0)
        contadores[txt_limpio] = count + 1
        division = mapa_torneo_seccion.get(f"{txt_limpio}_{count}", "")

        resultado.append({"texto": txt_limpio, "division": division})

    return resultado


# ─── Scraping por torneo ──────────────────────────────────────────

async def _scrape_torneo(
    page: Page,
    idx: int,
    torneo_nombre: str,
    division: str,
    rama: str,
    categoria: str,
    nombre_club: str,
) -> list[Partido]:
    """
    Abre un torneo por índice, extrae el texto y parsea los partidos.
    Retorna lista vacía si el club no tiene partidos en ese torneo.
    """
    cajas_fresh = await page.query_selector_all(".tournament-box.clickable")
    if idx >= len(cajas_fresh):
        return []

    await cajas_fresh[idx].click()
    await asyncio.sleep(3)

    # Algunos torneos tienen selector de fechas
    try:
        todas = await page.query_selector('button:has-text("Todas las fechas")')
        if todas:
            await todas.click()
            await asyncio.sleep(2)
    except Exception:
        pass

    texto = await page.evaluate("() => document.body.innerText")

    if nombre_club.lower() not in texto.lower():
        logger.info(f"    ↷ Sin partidos de {nombre_club}, saltando")
        return []

    return extraer_partidos(texto, torneo_nombre, rama, categoria, division)


async def _volver_al_menu(page: Page, rama: str, categoria: str) -> list[dict]:
    """
    Intenta volver al menú de torneos. Si no encuentra el botón,
    recarga la página y reaplica los filtros.
    Retorna las cajas actualizadas.
    """
    volver = await page.query_selector('button:has-text("Volver al menú")')
    if volver:
        await volver.click()
        await asyncio.sleep(2)
    else:
        await _cargar_pagina(page)
        await _seleccionar_rama_categoria(page, rama, categoria)

    return await _get_cajas_torneos(page)


# ─── Scraping por rama/categoría ─────────────────────────────────

async def _scrape_rama_categoria(
    browser: Browser, rama: str, categoria: str, nombre_club: str
) -> list[Partido]:
    partidos_totales: list[Partido] = []
    page = await browser.new_page()

    try:
        await _cargar_pagina(page)
        await _seleccionar_rama_categoria(page, rama, categoria)

        cajas = await _get_cajas_torneos(page)
        logger.info(f"  {len(cajas)} torneos en {rama}/{categoria}")

        idx = 0
        while idx < len(cajas):
            torneo_nombre = cajas[idx]["texto"]
            division      = cajas[idx]["division"]
            logger.info(f"    → {torneo_nombre} [{division}]")

            try:
                partidos = await _scrape_torneo(
                    page, idx, torneo_nombre, division, rama, categoria, nombre_club
                )
                partidos_totales.extend(partidos)
                cajas = await _volver_al_menu(page, rama, categoria)

            except Exception as e:
                logger.warning(f"    Error en '{torneo_nombre}': {e}")
                try:
                    await _cargar_pagina(page)
                    await _seleccionar_rama_categoria(page, rama, categoria)
                    cajas = await _get_cajas_torneos(page)
                except Exception:
                    break

            idx += 1

    except Exception as e:
        logger.error(f"Error en {rama}/{categoria}: {e}")
    finally:
        await page.close()

    return partidos_totales


# ─── Deduplicación ────────────────────────────────────────────────

def _deduplicar(partidos: list[Partido]) -> list[Partido]:
    """
    Elimina partidos duplicados usando como clave única:
    rama + categoría + local + visitante + fecha.
    La combinación rama/categoría evita descartar partidos válidos
    que se juegan en distintas categorías con los mismos equipos.
    """
    vistos: set[str] = set()
    resultado: list[Partido] = []

    for p in partidos:
        clave = f"{p.rama}|{p.categoria}|{p.local}|{p.visitante}|{p.fecha_raw}"
        if clave not in vistos:
            vistos.add(clave)
            resultado.append(p)

    return resultado


# ─── Función pública ──────────────────────────────────────────────

async def scrape_todos() -> list[Partido]:
    """
    Scrapea todas las combinaciones rama/categoría de FEMEBAL
    y retorna los partidos de Mariano Acosta deduplicados.

    Es una corutina — debe llamarse con await o desde un event loop.
    El manejo del event loop (para llamadas síncronas) está en __init__.py.
    """
    nombre_club = Settings.NOMBRE_CLUB
    todos: list[Partido] = []

    async with async_playwright() as p:
        browser = await p.chromium.launch(
                        executable_path="/usr/bin/chromium",    
                        headless=True
                        )
        try:
            for rama, categoria in COMBINACIONES:
                logger.info(f"━━ {rama} / {categoria} ━━")
                try:
                    partidos = await _scrape_rama_categoria(
                        browser, rama, categoria, nombre_club
                    )
                    todos.extend(partidos)
                except Exception as e:
                    logger.error(f"Fallo {rama}/{categoria}: {e}")
                    continue
        finally:
            await browser.close()

    return _deduplicar(todos)