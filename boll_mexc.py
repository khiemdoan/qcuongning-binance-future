import requests
import numpy as np
from datetime import datetime,timedelta
import time
from helper import post_tele
import random

BASE_URL = "https://api.mexc.com" 

def get_latest_kline_start_time(symbol, interval, limit=3):
    klines = get_klines(symbol, interval, limit)
    kline_start_time = int(klines[-1][0])
    return datetime.fromtimestamp(kline_start_time / 1000), klines

def calculate_bollinger_bands(klines):    
    # Extract closing prices
    close_prices = np.array([float(kline[4]) for kline in klines]) 

    # Calculate SMA (Simple Moving Average)
    sma = np.mean(close_prices)

    # Calculate standard deviation
    std_dev = np.std(close_prices)

    # Compute Bollinger Bands
    upper_band = sma + (2 * std_dev)
    lower_band = sma - (2 * std_dev)

    return sma, upper_band, lower_band

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
    
def get_klines(symbol, interval, limit):
    """Fetch MEXC account balance"""
    # endpoint = "/api/v3/avgPrice"
    endpoint = "/api/v3/klines"
    url = BASE_URL + endpoint
    params = {"symbol": symbol, "interval":interval, "limit":limit}
    response = requests.get(url, params=params)
    if response.status_code == 200:
        return response.json()
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
        time_kline = datetime.fromtimestamp(klines[-1][0] / 1000)
        syms = get_syms_future()
        choice_syms = random.choices(syms, k=20)
        print(time_kline, choice_syms)
        for sym in choice_syms:
            sym = sym.replace("_", "")
            klines = get_klines(sym, interval, 21)
            klines = klines[:-1]
            try:
                sma, upper_band, lower_band = calculate_bollinger_bands(klines)
                # print("bollind band at", time_kline)
                avg = (float(klines[-1][2]) + float(klines[-1][3]))/2
                # print("avg price: ", avg)
                # print("upper_band", upper_band, "lower_band", lower_band)
                if avg > upper_band or avg < lower_band:
                    print("**************", sym)
                    post_tele(f"{time_kline} {sym} over band avg={avg:.4f} <{upper_band:.4f}-{lower_band:.4f}>")
            except IndexError:
                print(klines)