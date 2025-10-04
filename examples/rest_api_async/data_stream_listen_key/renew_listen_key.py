#!/usr/bin/env python
import logging
import asyncio
from aster.rest_api import AsyncClient
from aster.lib.utils import config_logging
from dotenv import load_dotenv
import os


async def main():
    load_dotenv()
    config_logging(logging, logging.DEBUG)
    key = os.getenv("ASTER_KEY")
    client = AsyncClient(key, base_url="https://fapi.asterdex.com")
    try:
        response = await client.new_listen_key()
        listen_key = response["listenKey"]
        await client.renew_listen_key(listen_key)
        logging.info(f"Listen key {listen_key} renewed successfully")
    finally:
        await client.close()


if __name__ == "__main__":
    asyncio.run(main())


