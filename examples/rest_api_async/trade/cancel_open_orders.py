import logging
import asyncio
from aster.rest_api import AsyncClient
from aster.lib.utils import config_logging
from aster.error import ClientError


async def main():
    config_logging(logging, logging.DEBUG)
    key = ""
    secret = ""
    client = AsyncClient(key, secret, base_url="https://fapi.asterdex.com")

    try:
        response = await client.cancel_open_orders(symbol = "BTCUSDT", recvWindow=2000)
        logging.info(response)
    except ClientError as error:
        logging.error(
            "Found error. status: {}, error code: {}, error message: {}".format(
                error.status_code, error.error_code, error.error_message
            )
        )
    finally:
        await client.close()


if __name__ == "__main__":
    asyncio.run(main())


