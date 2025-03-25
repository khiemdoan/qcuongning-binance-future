import requests
import numpy as np
from datetime import datetime,timedelta
import time
from helper import post_tele
import random

BASE_URL = "https://api.mexc.com" 

def get_latest_kline_start_time(symbol, interval, limit=3):
    klines = get_klines_spot(symbol, interval, limit)
    kline_start_time = int(klines[-1][0])
    return datetime.fromtimestamp(kline_start_time / 1000), klines

def calculate_sma(klines):    
    # Extract closing prices
    close_prices = np.array([float(kline[4]) for kline in klines]) 

    # Calculate SMA (Simple Moving Average)
    sma = np.mean(close_prices)

    return sma

def avgPrice(symbol):
    """Fetch MEXC account balance"""
    # endpoint = "/api/v3/avgPrice"
    endpoint = "/api/v3/ticker/price"
    url = BASE_URL + endpoint
    params = {"symbol": symbol}
    response = requests.get(url, params=params)
    if response.status_code == 200:
        return response.json()
    else:
        return response.text
    
def get_klines_spot(symbol, interval, limit):
    """Fetch MEXC account balance"""
    endpoint = "/api/v3/klines"
    url = BASE_URL + endpoint
    params = {"symbol": symbol, "interval":interval, "limit":limit}
    response = requests.get(url, params=params)
    if response.status_code == 200:
        return response.json()
    else:
        return []
    
def get_klines(symbol, interval, limit):
    """Mexc future klines"""
    symbol = symbol.replace("USDT", "_USDT")
    if interval == "15m":
        interval = "Min15"
    url = f"https://contract.mexc.com/api/v1/contract/kline/{symbol}"
    params = {"symbol": symbol, "interval":interval}
    response = requests.get(url, params=params)
    if response.status_code == 200:
        import ipdb
        ipdb.set_trace()
        return response.json()
    else:
        return response.text
    
def binance_sym():
    BASE_URL= "https://fapi.binance.com"
    endpoint = "/fapi/v1/exchangeInfo"
    url = BASE_URL + endpoint
    response = requests.get(url)
    if response.status_code == 200:
        return [i['symbol'] for i in  response.json()['symbols']]
    else:
        return response.text
    
def get_symbol():
    """Fetch MEXC account balance"""
    # endpoint = "/api/v3/avgPrice"
    endpoint = "/api/v3/defaultSymbols"
    url = BASE_URL + endpoint
    response = requests.get(url)
    if response.status_code == 200:
        return response.json()['data']
    else:
        return response.text
    
def get_syms_future():
    endpoint = "https://contract.mexc.com/api/v1/contract/detail"
    response = requests.get(endpoint)
    if response.status_code == 200:
        return [i['symbol'] for i in response.json()['data']] 
    else:
        return response.text
    
if __name__ == "__main__":

    symbol = "ENAUSDT"
    interval = "15m"
    thresh = 0.03
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
        choice_syms = random.choices(syms, k=20)
        print(time_kline, choice_syms)
        pick = []
        for sym in choice_syms:
            sym = sym.replace("_", "")
            klines = get_klines_spot(sym, interval, 31)
            klines = klines[:-1]
            try:
                sma = calculate_sma(klines)
                close = float(klines[-1][4])
                rate = close/sma*100
                if close < sma * (1-thresh):
                    pick.append(sym)
                    post_tele(f"{time_kline} [DOWN] {sym} close={close:.4f} sma={sma:.4f} (={sma * (1-thresh):.4f}), rate={rate:.1f}")
                elif close > sma * (1+thresh):
                    pick.append(sym)
                    post_tele(f"{time_kline} [UP] {sym} close={close:.4f} sma={sma:.4f} (={sma * (1+thresh):.4f}), rate={rate:.1f}")
            except IndexError:
                print(klines, sym)
        print("pincking", pick)
        if not len(pick):
            post_tele(f"{time_kline} Not found Sym")
