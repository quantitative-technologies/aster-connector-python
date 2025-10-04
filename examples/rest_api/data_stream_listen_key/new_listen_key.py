#!/usr/bin/env python
import logging
from aster.rest_api import Client
from aster.lib.utils import config_logging

from dotenv import load_dotenv
import os
load_dotenv()

config_logging(logging, logging.DEBUG)

key = os.getenv("ASTER_KEY")

client = Client(key, base_url="https://fapi.asterdex.com")
logging.info(client.new_listen_key())
