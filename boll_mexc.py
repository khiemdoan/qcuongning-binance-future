import requests
import numpy as np
from datetime import datetime,timedelta
import time
from helper import post_tele
import random
from SMA_mexc import get_latest_kline_start_time, get_klines_spot, binance_sym
import pandas as pd

def calculate_bollinger_bands(klines, window=20, num_std=2):
    close_prices = np.array([float(kline[4]) for kline in klines]) 
    prices = pd.Series(close_prices)

    ma = prices.rolling(window=window).mean()
    std = prices.rolling(window=window).std()
    upper_band = ma + (num_std * std)
    lower_band = ma - (num_std * std)
    return ma.tolist(), upper_band.tolist(), lower_band.tolist()

    
if __name__ == "__main__":

    symbol = "ENAUSDT"
    interval = "15m"
    start = True
    avg = 0
    while True:
        kline_start_time, klines = get_latest_kline_start_time(symbol, interval, 20)
        next_kline_start_time = kline_start_time + timedelta(minutes=int(interval[:-1]))
        now = datetime.now()
        sleep_duration = (next_kline_start_time - now).total_seconds()
        if start:
            sleep_duration = 0
            start = False
        print("sleep", sleep_duration/60, "minute")
        time.sleep(sleep_duration+3)
        time_kline = datetime.fromtimestamp(klines[-1][0] / 1000)
        syms = binance_sym()
        choice_syms = random.choices(syms, k=30)
        choice_syms.append("ORDIUSDT")
        choice_syms.append("AVAXUSDT")

        print(time_kline, choice_syms)
        pick = []
        start_time = time.time()
        for sym in choice_syms:
            sym = sym.replace("_", "")
            klines = get_klines_spot(sym, interval, 31)
            klines = klines[:-1]
            klines = np.array(klines, dtype=float)
            try:
                sma, upper_band, lower_band = calculate_bollinger_bands(klines)
                avg = (klines[:, 2] + klines[:,3])/2
                previous_open = float(klines[-1][1])
                if klines[-1][4] < klines[-1][1] and avg[-2] > upper_band[-2] and avg[-3] > upper_band[-3]:
                    post_tele(f"{time_kline} {sym} meet require {avg[-1]:.4f} <{upper_band[-1]:.4f}-{lower_band[-1]:.4f}>, wait price at {previous_open:.4f}")
                    pick.append(sym)
            except (IndexError, ValueError):
                print(klines, sym)
        print("picking", pick, f"in {time.time()-start_time:.3f}s")
        if not len(pick):
            post_tele(f"{time_kline} Not found Sym")