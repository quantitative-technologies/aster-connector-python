import logging
import asyncio
import time
import websockets
from aster.rest_api import AsyncClient
from aster.lib.utils import config_logging

from dotenv import load_dotenv
import os

stream_url = "wss://fstream.asterdex.com/ws/"

async def handler(msg):
    await asyncio.sleep(0.01)
    print(f"Message received @ {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())}:")
    print(msg)

async def main():
    load_dotenv()
    config_logging(logging, logging.DEBUG)
    key = os.getenv("ASTER_KEY")
    client = AsyncClient(key, base_url="https://fapi.asterdex.com")
    try:
        response = await client.new_listen_key()
        listen_key = response["listenKey"]
        logging.info(f"Listen key {listen_key} created successfully")

        while True:
            async with websockets.connect(stream_url + listen_key) as s:
                while True:
                    msg = await s.recv()
                    await handler(msg)
    finally:
        await client.close()


if __name__ == "__main__":
    asyncio.run(main())
