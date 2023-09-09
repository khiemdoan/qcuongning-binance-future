#!/usr/bin/env python
from binance_ft.um_futures import UMFutures
import logging
from binance_ft.lib.utils import config_logging

config_logging(logging, logging.DEBUG)

um_futures_client = UMFutures()
logging.info(um_futures_client.funding_rate("BTCUSDT", **{"limit": 100}))
