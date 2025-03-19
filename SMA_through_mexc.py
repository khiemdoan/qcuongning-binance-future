import requests
import numpy as np
from datetime import datetime,timedelta
import time
from helper import post_tele
import random
from SMA_mexc import get_latest_kline_start_time, calculate_sma, get_klines_spot, binance_sym

    
if __name__ == "__main__":
    print("SMA through")

    symbol = "ENAUSDT"
    interval = "15m"
    thresh = 0.01
    start = True
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
        time_kline = datetime.fromtimestamp(klines[-1][-2] / 1000)
        syms = binance_sym()
        choice_syms = random.choices(syms, k=30)
        print(time_kline, choice_syms)
        pick = []
        for sym in choice_syms:
            sym = sym.replace("_", "")
            klines = get_klines_spot(sym, interval, 31)
            klines = klines[:-1]
            try:
                sma = calculate_sma(klines)
                close = float(klines[-1][4])
                open = float(klines[-1][1])
                rate = close/sma*100
                if close < sma * (1-thresh) and open > sma:
                    pick.append(sym)
                    post_tele(f"{time_kline} [THROUGH] {sym} close={close:.4f} sma={sma:.4f} (={sma * (1-thresh):.4f}), rate={rate:.1f}")
            except IndexError:
                print(klines, sym)
        print("pincking", pick)
        if not len(pick):
            post_tele(f"{time_kline} Not found Sym")
