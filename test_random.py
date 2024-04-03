import numpy as np
import pandas as pd
from binance_ft.um_futures import UMFutures
import time
import copy
import keyboard

um_futures_client = UMFutures()
from binance.spot import Spot
spot_client = Spot()

import time, sys
pair = sys.argv[1]
cut_loss = 0.99
# print(0.075+0.075+0.045*2)
thresh_gap = 0.25
pair_spot = pair
# pair_spot = pair.replace("USDT", "FDUSD")
init_ft = float(um_futures_client.mark_price(pair)['markPrice'])
init_spot = float(spot_client.ticker_price(pair_spot)['price'])
print("init", init_ft, init_spot)
max_gap = 0
dict_price = {}
print_dict = {}

index = 0


while True:
    mark_ft = float(um_futures_client.mark_price(pair)['markPrice'])

    ask_ft = float(um_futures_client.book_ticker(pair)['askPrice'])  # > mark price
    # print(ask_ft)
    mark_spot = float(spot_client.ticker_price(pair)['price'])
    bid_spot = float(spot_client.book_ticker(pair_spot)['bidPrice'])  # < mark price

    for key in dict_price.keys():
        if dict_price[key]['break']:
            continue
        if mark_ft < dict_price[key]['low_boundary']:
            dict_price[key]['break'] = True
        if mark_ft > dict_price[key]['highest_price']:
            dict_price[key]['highest_price'] = mark_ft
            dict_price[key]["highest_rate"]  = mark_ft/dict_price[key]["mark_price"] *100
        
    gap_ft = -(ask_ft - init_ft)/init_ft * 100
    gap_spot = (bid_spot - init_spot)/init_spot * 100
    gap = gap_ft + gap_spot
    if np.random.random() > 0.98:
        time_get_gap = time.strftime("%Y-%m-%d %H:%M:%S")
        mark_ft_at_this_gap = mark_ft
        dict_price[index] = {}
        dict_price[index]["time"] = time_get_gap
        dict_price[index]["side"] = "tang" if gap_spot > 0 else "giam"
        dict_price[index]["gap"] = 0
        dict_price[index]["mark_price"] = mark_ft_at_this_gap
        dict_price[index]["highest_price"] = mark_ft_at_this_gap
        dict_price[index]["highest_rate"] = 100
        dict_price[index]['break'] = False
        dict_price[index]['low_boundary'] = mark_ft_at_this_gap * cut_loss
        index+=1

    
    
    if len(print_dict) != len(dict_price):
        print_dict = copy.deepcopy(dict_price)
        print("-----",time.strftime("%Y-%m-%d %H:%M:%S"), "-----")
        for dictt in print_dict:
            print(print_dict[dictt])

        df = pd.DataFrame.from_dict(dict_price, orient='index')
        excel_file_path = f'data_test_gap_{pair}_{cut_loss}_random.xlsx'
        df.to_excel(excel_file_path)
    time.sleep(0.1)
        



