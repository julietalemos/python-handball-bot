import asyncio, logging
logging.basicConfig(level=logging.INFO)

from services.larrysport.scraper import scrape_todos
from services.larrysport.cache import escribir_fixture

async def main():
    partidos = await scrape_todos()
    escribir_fixture(partidos)
    print(f"LISTO — {len(partidos)} partidos guardados")

asyncio.run(main())