import os
import numpy as np
import pandas as pd
from binance_ft.um_futures import UMFutures
import time
import copy
import time, sys
from helper import get_commision, get_precision, get_status_pos, key, secret, xlsx_to_nested_dict
import threading
from binance_ft.error import ClientError

# um_futures_client = UMFutures(key=key, secret=secret)
um_futures_client = UMFutures(key="c21f1bb909318f36de0f915077deadac8322ad7df00c93606970441674c1b39b", secret="be2d7e74239b2e959b3446b880451cbb4dee2e6be9d391c4c55ae7ca0976f403", base_url="https://testnet.binancefuture.com")
pair = sys.argv[1]
cut_loss = 0.99
take_profit = 1.05
pair_spot = pair
usdt = 1000
prob_open = 0.9
precision_ft = get_precision(pair, um_futures_client)
# um_futures_client.cancel_open_orders(symbol=pair, recvWindow=2000)
sleep_time_new_order = 0.01 #h
sleep_time_new_order_sec = sleep_time_new_order * 60 * 60
print("sleep_time_new_order:", sleep_time_new_order_sec)
excel_file_path = f'{pair}_{cut_loss}_{sleep_time_new_order}.xlsx'
if os.path.exists(excel_file_path):
    df = pd.read_excel(excel_file_path, header=0, index_col=0)
    dict_price = df.to_dict('index')
    print(f"load previous {excel_file_path} contain {len(dict_price)} with {len(df[df['break']==True])} break and {len(df[df['filled']==True])} filled")
    index = len(dict_price)

else:
    index = 0
    dict_price = {}



random_sleep = 0
time_order = time.time()
while True:
    bidPrice = float(um_futures_client.book_ticker(pair)['bidPrice'])

    askPrice = float(um_futures_client.book_ticker(pair)['askPrice'])  # > mark price

    for key in dict_price.keys():
        if not dict_price[key]['filled']:
            try:
                res_query = um_futures_client.query_order(symbol=pair, orderId=dict_price[key]['orderId'], recvWindow=6000)
            except ClientError:
                print(key, dict_price[key])
            if res_query['status'] == "FILLED":
                commis, usdt_open, coin_open, mean_price, all_pnl = get_commision(dict_price[key]['orderId'], um_futures_client, pair)
                print(time.strftime("%Y-%m-%d %H:%M:%S"), f"Open order {key} usdt_open: {usdt_open:.3f} coin_open: {coin_open:.3f}, mean_price: {mean_price:.3f}, commis: {commis:.3f}")
                dict_price[key]['filled'] = True
                dict_price[key]['coin'] = round(coin_open, precision_ft)
                dict_price[key]['commis'] = commis
            elif res_query['status'] == "CANCELED":
                dict_price[key]['filled'] = "CANCELED"



        if dict_price[key]['filled']:
            if dict_price[key]['break']:
                continue
            if askPrice > dict_price[key]['highest_price']:
                dict_price[key]['highest_price'] = askPrice
                dict_price[key]["highest_rate"]  = askPrice/dict_price[key]["askPrice"] *100
            if askPrice < dict_price[key]['low_boundary'] or askPrice >= dict_price[key]['high_boundary']:
                close_future = um_futures_client.new_order(symbol=pair, side="BUY", type="MARKET", quantity=dict_price[key]['coin'])
                time.sleep(0.5)
                commis, usdt_open, coin_open, mean_price, all_pnl = get_commision(close_future['orderId'], um_futures_client, pair)
                print(time.strftime("%Y-%m-%d %H:%M:%S"), f"Close order {key} usdt_open: {usdt_open:.3f} coin_open: {coin_open:.3f}, mean_price: {mean_price:.3f}, commis: {commis:.3f}")

                dict_price[key]['commis'] += commis
                dict_price[key]['pnl'] = coin_open * (dict_price[key]["askPrice"] - mean_price) - dict_price[key]['commis']
                dict_price[key]['break'] = True
        
    if time.time() - time_order > random_sleep:
        if np.random.random() > prob_open:
            # print("time to open new order")
            time_order = time.time()
            random_sleep = np.random.randint(int(sleep_time_new_order_sec*0.8), int(sleep_time_new_order_sec*1.2))
            time_get_gap = time.strftime("%Y-%m-%d %H:%M:%S")
            quantity_ft = round((usdt)/askPrice, precision_ft)
            print("\n-----",time.strftime("%Y-%m-%d %H:%M:%S"), "-----")
            print(f"create new order {index} with {quantity_ft} {pair}")
            open_future = um_futures_client.new_order(symbol=pair, side="SELL", type="LIMIT", quantity=quantity_ft, price = askPrice, timeInForce="GTC")
            mark_ft_at_this_gap = askPrice
            dict_price[index] = {}
            dict_price[index]["time"] = time_get_gap
            dict_price[index]["askPrice"] = mark_ft_at_this_gap
            dict_price[index]["highest_price"] = mark_ft_at_this_gap
            dict_price[index]["highest_rate"] = 100
            dict_price[index]['break'] = False
            dict_price[index]['low_boundary'] = mark_ft_at_this_gap * cut_loss
            dict_price[index]['high_boundary'] = mark_ft_at_this_gap * take_profit
            dict_price[index]['orderId'] = open_future["orderId"]
            dict_price[index]['filled'] = False

            index+=1
            df = pd.DataFrame.from_dict(dict_price, orient='index')
            df.to_excel(excel_file_path)
            # x = threading.Thread(target=get_commision, args=(open_future, um_futures_client, pair))
            # x.start()

    time.sleep(1)
        



