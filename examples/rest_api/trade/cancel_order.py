import logging
from aster.rest_api import Client
from aster.lib.utils import config_logging
from aster.error import ClientError

from dotenv import load_dotenv
import os
load_dotenv()

config_logging(logging, logging.DEBUG)

key = os.getenv("ASTER_KEY")
secret = os.getenv("ASTER_SECRET")
client_order_id = "387feb054fd5e2249f00f0fc02fd9f6b"

client = Client(key, secret, base_url="https://fapi.asterdex.com")

try:
    response = client.cancel_order(symbol = "BTCUSDT", origClientOrderId=client_order_id, recvWindow=2000)
    logging.info(response)
except ClientError as error:
    logging.error(
        "Found error. status: {}, error code: {}, error message: {}".format(
            error.status_code, error.error_code, error.error_message
        )
    )
