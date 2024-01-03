#!/usr/bin/env python
import logging
from binance_ft.cm_futures import CMFutures
from binance_ft.lib.utils import config_logging

config_logging(logging, logging.DEBUG)

cm_futures_client = CMFutures()
logging.info(cm_futures_client.agg_trades("BTCUSD_PERP"))
