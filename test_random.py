import numpy as np
import pandas as pd
from binance_ft.um_futures import UMFutures
import time
import copy

um_futures_client = UMFutures()
from binance.spot import Spot
spot_client = Spot()

import time, sys
pair = sys.argv[1]
cut_loss = 0.99
take_profit = 1.05
# print(0.075+0.075+0.045*2)
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
    mark_ft = float(um_futures_client.book_ticker(pair)['bidPrice'])

    ask_ft = float(um_futures_client.book_ticker(pair)['askPrice'])  # > mark price
    # print(ask_ft)
    mark_spot = float(spot_client.ticker_price(pair)['price'])
    bid_spot = float(spot_client.book_ticker(pair_spot)['bidPrice'])  # < mark price

    for key in dict_price.keys():
        if dict_price[key]['break']:
            continue
        if ask_ft > dict_price[key]['highest_price']:
            dict_price[key]['highest_price'] = ask_ft
            dict_price[key]["highest_rate"]  = ask_ft/dict_price[key]["mark_price"] *100

        if ask_ft < dict_price[key]['low_boundary'] or ask_ft >= dict_price[key]['high_boundary']:
            dict_price[key]['break'] = True
        
        
    if np.random.random() > 0.98:
        time_get_gap = time.strftime("%Y-%m-%d %H:%M:%S")
        mark_ft_at_this_gap = mark_ft
        dict_price[index] = {}
        dict_price[index]["time"] = time_get_gap
        dict_price[index]["gap"] = 0
        dict_price[index]["mark_price"] = mark_ft_at_this_gap
        dict_price[index]["highest_price"] = mark_ft_at_this_gap
        dict_price[index]["highest_rate"] = 100
        dict_price[index]['break'] = False
        dict_price[index]['low_boundary'] = mark_ft_at_this_gap * cut_loss
        dict_price[index]['high_boundary'] = mark_ft_at_this_gap * take_profit

        index+=1

    
    
    if len(print_dict) != len(dict_price):
        print_dict = copy.deepcopy(dict_price)
        print("-----",time.strftime("%Y-%m-%d %H:%M:%S"), "-----")
        # for dictt in print_dict:
        #     print(print_dict[dictt])

        df = pd.DataFrame.from_dict(dict_price, orient='index')
        excel_file_path = f'data_test_gap_{pair}_{cut_loss}_random.xlsx'
        df.to_excel(excel_file_path)
    time.sleep(0.1)
        



