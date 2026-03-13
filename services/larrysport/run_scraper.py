import asyncio, logging
logging.basicConfig(level=logging.INFO)

from services.larrysport import LarrySportService

async def main():
    service = LarrySportService()
    await service.actualizar_cache()
    print("LISTO")

asyncio.run(main())