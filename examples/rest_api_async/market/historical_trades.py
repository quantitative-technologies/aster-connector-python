import logging
import asyncio
from aster.rest_api import AsyncClient
from aster.lib.utils import config_logging


async def main():
    config_logging(logging, logging.DEBUG)
    key = ""
    client = AsyncClient(key=key)
    try:
        logging.info(await client.historical_trades("BTCUSDT", **{"limit": 10}))
    finally:
        await client.close()


if __name__ == "__main__":
    asyncio.run(main())


