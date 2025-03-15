import os
import sys
import time
from datetime import datetime
import pandas as pd
import requests
from binance_ft.um_futures import UMFutures
from helper import get_commision, get_precision, get_status_pos, key, secret, xlsx_to_nested_dict
from datetime import datetime, timedelta
import numpy as np
import xgboost as xgb
from auto_order_manual import post_tele, update_dict, parse_df_markdown
import threading
from binance_ft.error import ClientError
from colorama import Fore, Style
from binance.spot import Spot
from xgboost_order import is_pin_bar, is_decrease


if __name__ == "__main__":
    client = UMFutures()
    bst = xgb.Booster()
    bst.load_model('ORDIUSDT_15m_tp3_sl3_60pcent_mancond_fapiv1.json')

    end_str = sys.argv[1]+" "+sys.argv[2]
    
    end_ts = int(datetime.strptime(end_str, '%Y-%m-%d %H:%M:%S').timestamp() * 1000)
    
    params = {
        # 'startTime': start_ts,
        'endTime': end_ts,
        'limit': 31
    }

    klines = client.klines(symbol="ORDIUSDT", interval="15m", **params)
    print(len(klines))
    print(datetime.fromtimestamp(klines[0][0] / 1000), "to", datetime.fromtimestamp(klines[-1][0] / 1000))

    ohlc = []
    for item in klines:
        ohlc.append([
            float(item[1]), #o
            float(item[2]), #H
            float(item[3]), #L
            float(item[4]), #C
            float(item[5]) #V
        ])
    
    ohlc = np.array(ohlc)
    x_array = ohlc[-31:-1]
    x_array_cp = x_array.copy()

    

    min_vol = np.min(x_array[:,-1])
    x_array[:,-1] = x_array[:,-1]/min_vol
    min_price = np.min(x_array[:,:4])
    max_price = np.max(x_array[:,:4])
    x_array[:,:4] = (x_array[:,:4] - min_price) / (max_price - min_price)
    manual_condition = is_decrease(x_array_cp[-1]) or is_decrease(x_array_cp[-2]) or is_pin_bar(x_array_cp[-1])   # it nhat 1 nen do trong 2 nen truoc do
    print(is_decrease(x_array_cp[-1]))
    print(is_decrease(x_array_cp[-2]))


    x_array = np.array([x_array]).reshape(1, -1)
    dtest = xgb.DMatrix(x_array)
    y_pred_prob = bst.predict(dtest)
    print(y_pred_prob, manual_condition)