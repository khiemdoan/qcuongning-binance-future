import os
import time
from datetime import datetime
from turtle import pd
from binance.spot import Spot
from binance_ft.um_futures import UMFutures
from helper import get_commision, get_precision, get_status_pos, key, secret, xlsx_to_nested_dict
from datetime import datetime, timedelta
import numpy as np
import xgboost as xgb
from auto_order_manual import post_tele, update_dict
import threading

# Initialize the Binance client
api_key="7NvUEUX4tnzOja5KQ99gmUG37DQOV9oelvz1akWAr2Zts9X57djRMwbvfgjQoykp"
api_secret="X9CWCXNsdypjEU8Q0AQaoaqPrcnaX4wpDe5KVxsAfThkVJJAvufiGJ3tb95QqnQC"
# client = UMFutures(key="c21f1bb909318f36de0f915077deadac8322ad7df00c93606970441674c1b39b", secret="be2d7e74239b2e959b3446b880451cbb4dee2e6be9d391c4c55ae7ca0976f403", base_url="https://testnet.binancefuture.com")
client = UMFutures(key=api_key, secret=api_secret)

bst = xgb.Booster()
bst.load_model('xgboost_model.json')

def get_latest_kline_start_time(symbol, interval, limit=3):
    klines = client.klines(symbol=symbol, interval=interval, limit=limit)
    kline_start_time = int(klines[-1][0])
    return datetime.fromtimestamp(kline_start_time / 1000), klines

    
if __name__ == "__main__":
    symbol = 'ORDIUSDT'
    interval = '15m'
    usdt = 100
    precision_ft = get_precision(symbol, client)


    while True:
        kline_start_time, klines = get_latest_kline_start_time(symbol, interval, 31)
        print(kline_start_time)

        next_kline_start_time = kline_start_time + timedelta(minutes=15)
        now = datetime.now()
        sleep_duration = (next_kline_start_time - now).total_seconds()    
        if sleep_duration > 0:
            print(f"Sleeping for {sleep_duration} seconds until the next kline starts...")
            time.sleep(sleep_duration)
            current_kline_time, klines = get_latest_kline_start_time(symbol, interval, 31)
            ohlc = []
            for item in klines:
                ohlc.append({
                    float(item[1]), #o
                    float(item[2]), #H
                    float(item[3]), #L
                    float(item[4]), #C
                    float(item[5]) #V
                })
            ohlc = np.array(ohlc)
            if current_kline_time>kline_start_time:
                x_array = ohlc[-31:-1]
                order_price = ohlc[-2][3] # close price of last klines

                print("A new kline has started!")
            else:
                print("In current kline")
                x_array = ohlc[-30:]
                order_price = ohlc[-1][3] # close price of last klines


            x_array[:,-1] = x_array[:,-1]/20000
            min_price = np.min(x_array[:,:4])
            max_price = np.max(x_array[:,:4])
            x_array[:,:4] = (x_array[:,:4] - min_price) / (max_price - min_price)

            x_array = np.array([x_array]).reshape(1, -1)
            dtest = xgb.DMatrix(x_array)
            y_pred_prob = bst.predict(dtest)
            if y_pred_prob >= 0.5:
                high = order_price * 1.03
                low = order_price * 0.97
                print(current_kline_time, order_price, high, low)
                quantity_ft = round((usdt)/order_price, precision_ft)
                close_future = client.new_order(symbol=symbol, side="SELL", type="MARKET", quantity=quantity_ft)
                while True:
                    askPrice = float(client.book_ticker(symbol)['askPrice'])
                    print("waiting_close...")
                    if askPrice > high or askPrice < low:
                        print(time.strftime("%Y-%m-%d %H:%M:%S"), "close", askPrice, high, low)
                        close_future = client.new_order(symbol=symbol, side="BUY", type="MARKET", quantity=quantity_ft)
                        break
                    time.sleep(0.5)

        else:
            time.sleep(2)