#!/usr/bin/env python
from binance_ft.cm_futures import CMFutures
import logging
from binance_ft.lib.utils import config_logging

config_logging(logging, logging.DEBUG)

cm_futures_client = CMFutures()
logging.info(cm_futures_client.funding_rate("BTCUSD_PERP", **{"limit": 100}))
