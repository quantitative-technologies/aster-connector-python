import time
import logging
from aster.lib.utils import config_logging
from aster.rest_api import Client
from aster.websocket.client.stream import WebsocketClient

from dotenv import load_dotenv
import os
load_dotenv()

config_logging(logging, logging.DEBUG)

def message_handler(message):
    print(message)

api_key = os.getenv("ASTER_KEY")

client = Client(api_key)
response = client.new_listen_key()

logging.info("Receving listen key : {}".format(response["listenKey"]))

ws_client = WebsocketClient()
ws_client.start()

ws_client.user_data(
    listen_key=response["listenKey"],
    id=1,
    callback=message_handler,
)

time.sleep(30)

logging.debug("closing ws connection")
ws_client.stop()
