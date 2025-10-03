import logging
import asyncio
from aster.rest_api import AsyncClient
from aster.lib.utils import config_logging
from aster.error import ClientError

from dotenv import load_dotenv
import os

async def main():
    load_dotenv()

    config_logging(logging, logging.DEBUG)
    key = os.getenv("ASTER_KEY")
    secret = os.getenv("ASTER_SECRET")
    client = AsyncClient(key, secret, base_url="https://fapi.asterdex.com")

    client_order_id = "c27443d13d7572994e1ebde79b33296c"
    symbol = "SOLUSDT"

    try:
        response = await client.cancel_order(symbol=symbol, origClientOrderId=client_order_id, recvWindow=6000)
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



