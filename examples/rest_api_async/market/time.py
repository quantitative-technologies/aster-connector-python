import logging
import asyncio
from aster.rest_api import AsyncClient
from aster.lib.utils import config_logging


async def main():
    config_logging(logging, logging.DEBUG)
    client = AsyncClient()
    try:
        logging.info(await client.time())
    finally:
        await client.close()


if __name__ == "__main__":
    asyncio.run(main())


