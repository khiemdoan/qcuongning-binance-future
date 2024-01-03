#!/usr/bin/env python
import logging
from binance_ft.cm_futures import CMFutures as Client
from binance_ft.lib.utils import config_logging
from binance_ft.error import ClientError

config_logging(logging, logging.DEBUG)

key = ""
secret = ""

client = Client(key, secret, base_url="https://dapi.binance.com")

try:
    response = client.new_order(
        symbol="BTCUSD_PERP",
        side="SELL",
        type="LIMIT",
        quantity=0.001,
        timeInForce="GTC",
        price=59808.02,
    )
    logging.info(response)
except ClientError as error:
    logging.error(
        "Found error. status: {}, error code: {}, error message: {}".format(
            error.status_code, error.error_code, error.error_message
        )
    )
