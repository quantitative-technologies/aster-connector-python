#!/usr/bin/env python
import logging
import asyncio
from aster.rest_api import AsyncClient
from aster.lib.utils import config_logging


async def main():
    config_logging(logging, logging.DEBUG)
    key = ""
    client = AsyncClient(key, base_url="https://fapi.asterdex.com")
    try:
        logging.info(await client.close_listen_key(""))
    finally:
        await client.close()


if __name__ == "__main__":
    asyncio.run(main())


