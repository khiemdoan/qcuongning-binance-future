import os
import time
from datetime import datetime
import pandas as pd
import requests
from binance_ft.um_futures import UMFutures
from helper import get_commision, get_precision, key, secret, is_pin_bar, is_decrease, update_tele, over_time
from datetime import datetime, timedelta
import numpy as np
import xgboost as xgb
from auto_order_manual import post_tele, update_dict, parse_df_markdown
import threading
from binance_ft.error import ClientError
from colorama import Fore, Style
from binance.spot import Spot
import time

symbol = 'ORDIUSDT'

date = time.strftime("%Y-%m")
excel_file_path = f'{symbol}_{date}.csv'
dict_price = {}
lock = threading.Lock()

if os.path.exists(excel_file_path):
    df = pd.read_csv(excel_file_path, header=0, index_col=0)
    dict_price = df.to_dict('index')
    if  len(dict_price):
        len_filled = len(df[df['filled']=="T"])         
        print(f"load previous {excel_file_path} contain {len(dict_price)} with {len(df[df['break']==True])} break and {len_filled} filled")
    index = len(dict_price)
else:
    index = 0
    dict_price = {}

def get_latest_kline_start_time(symbol, interval, limit=3):
    klines = client_spot.klines(symbol=symbol, interval=interval, limit=limit)
    kline_start_time = int(klines[-1][0])
    return datetime.fromtimestamp(kline_start_time / 1000), klines


def add_to_dict():
    print(Fore.WHITE + "start [add_to_dict] ...")

    global dict_price, index
    while True:
        kline_start_time, klines = get_latest_kline_start_time(symbol, interval, 31)
        next_kline_start_time = kline_start_time + timedelta(minutes=int(interval[:-1]))
        now = datetime.now()
        sleep_duration = (next_kline_start_time - now).total_seconds()    
        if sleep_duration > 0:
            print(Fore.WHITE + f"[add_to_dict] {kline_start_time} Sleeping for {sleep_duration} seconds until the next kline starts...")
            time.sleep(sleep_duration)
            current_kline_time, klines = get_latest_kline_start_time(symbol, interval, 31)
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
            if current_kline_time>kline_start_time:
                x_array = ohlc[-31:-1]
                order_price = ohlc[-2][3] # close price of last klines

                print(Fore.WHITE + f"[add_to_dict][{current_kline_time}]A new kline has started!")
            else:
                print(Fore.WHITE + f"[add_to_dict][{current_kline_time}]In current kline")
                x_array = ohlc[-30:]
                order_price = ohlc[-1][3] # close price of last klines
            x_array_cp = x_array.copy()

            start = time.time()
            min_vol = np.min(x_array[:,-1])
            x_array[:,-1] = x_array[:,-1]/min_vol
            min_price = np.min(x_array[:,:4])
            max_price = np.max(x_array[:,:4])
            x_array[:,:4] = (x_array[:,:4] - min_price) / (max_price - min_price)


            x_array = np.array([x_array]).reshape(1, -1)
            # print(x_array.shape)
            dtest = xgb.DMatrix(x_array)
            y_pred_prob = bst.predict(dtest)[0]
            duration = time.time()-start
            if y_pred_prob !=0:
                print(Fore.CYAN+"[add_to_dict] y_pred_prob=", y_pred_prob)
                post_tele(f"add_to_dict: y pred prob = {y_pred_prob}, in {duration:.3f}s")
            with lock:
                if int(y_pred_prob) == 1:
                    if  is_decrease(x_array_cp[-1]) or is_decrease(x_array_cp[-2]) or is_pin_bar(x_array_cp[-1]):   # it nhat 1 nen do trong 2 nen truoc do
                        quantity_ft = round((usdt)/order_price, precision_ft)
                        try:
                            open_future = client.new_order(symbol=symbol, side="SELL", type="MARKET", quantity=quantity_ft)
                            dict_price = update_dict(dict_price, open_future, order_price, index, cut_loss, take_profit)
                            index+=1
                        except ClientError as error:
                            print(Fore.RED + error.error_message)
                            post_tele(error.error_message)
                        
        else:
            time.sleep(2)

def count_dict_items():
    print(Fore.GREEN + "start [count_dict_items] ... ")
    global dict_price, indexz, askPrice, index, last_command_time, enable_new_order, enable_pnl

    while True:
        with lock:
            last_command_time, enable_new_order, enable_pnl, indexz, dict_price = update_tele(last_command_time, enable_new_order, enable_pnl, indexz, dict_price, askPrice)  
            indexz += 1
            # bidPrice = float(client.book_ticker(symbol)['bidPrice'])

            askPrice = float(client.book_ticker(symbol)['askPrice'])  # > mark price

            if indexz % 10 == 0:
                reses = client.get_all_orders(symbol)
                order_ids = [value['orderId'] for value in dict_price.values()]
                for res in reses[-3:]:
                    if res['side'] == "SELL" and res['orderId'] not in order_ids and res['time']/1000 > last_command_time:
                        print("!!!update order id", res['orderId'], "in", datetime.fromtimestamp(res['time']/1000))
                        dict_price = update_dict(dict_price, res, round(float(res['price']), precision_price), index, 1.05, 0.99, manual=True)
                        index+=1
                        

            msg = ""
            for key in dict_price.keys():
                if dict_price[key]['filled'] == "F":
                    try:
                        res_query = client.query_order(symbol=symbol, orderId=dict_price[key]['orderId'], recvWindow=6000)
                    
                        if res_query['status'] == "FILLED":
                            commis, usdt_open, coin_open, mean_price, all_pnl = get_commision(dict_price[key]['orderId'], client, symbol)
                            print(Fore.GREEN + "[count_dict_items]", time.strftime("%Y-%m-%d %H:%M:%S"), f"Open order {key} usdt_open: {usdt_open:.3f} coin_open: {coin_open:.3f}, mean_price: {mean_price:.3f}, commis: {commis:.3f}")
                            dict_price[key]['filled'] = "T"
                            dict_price[key]['coin'] = round(coin_open, precision_ft)
                            dict_price[key]['commis'] = round(commis,2)
                            dict_price[key]["askPrice"] = mean_price
                            dict_price[key]["highest_rate"] = 100
                            dict_price[key]['break'] = False
                            if not dict_price[key]['manual']: 
                                dict_price[key]['low_boundary'] = mean_price * take_profit
                                dict_price[key]['high_boundary'] = mean_price * cut_loss
                            msg += f"*open* id: {key} at:{mean_price:.3f}, low:{dict_price[key]['low_boundary']:.2f}, high:{dict_price[key]['high_boundary']:.2f}\n"
                        elif res_query['status'] == "CANCELED":
                            dict_price[key]['filled'] = "CANCELED"
                    except ClientError as err:
                        print(key, dict_price[key])
                        post_tele(err.error_message)


                else:
                    # not filled yet
                    if dict_price[key]['break'] == True:
                        continue
                    dict_price[key]['pnl'] = round(dict_price[key]['coin'] * (dict_price[key]['askPrice'] - askPrice),4)
                    if askPrice > dict_price[key]['highest_price']:
                        dict_price[key]['highest_price'] = askPrice
                        dict_price[key]["highest_rate"]  = round(askPrice/dict_price[key]["askPrice"] *100, 1)
                    if askPrice < dict_price[key]['low_boundary'] or askPrice >= dict_price[key]['high_boundary'] or (over_time(dict_price[key]['time']) and not dict_price[key]['manual']):
                        print(over_time(dict_price[key]['time']), "overtime")
                        close_future = client.new_order(symbol=symbol, side="BUY", type="MARKET", quantity=dict_price[key]['coin'])
                        commis, usdt_open, coin_open, mean_price, all_pnl = get_commision(close_future['orderId'], client, symbol)
                        print(Fore.GREEN + "[count_dict_items]", time.strftime("%Y-%m-%d %H:%M:%S"), f"Close order {key} usdt_open: {usdt_open:.3f} coin_open: {coin_open:.3f}, mean_price: {mean_price:.3f}, commis: {commis:.3f}")    
                        dict_price[key]['commis'] += round(commis,2)
                        dict_price[key]['close_price'] = mean_price
                        dict_price[key]['pnl'] = coin_open * (dict_price[key]["askPrice"] - mean_price) - dict_price[key]['commis']
                        dict_price[key]['break'] = True
                        msg += f"*close* id: {key}, pnl: {dict_price[key]['pnl']:.2f}, price:{mean_price:.2f}\n"

                    
                        
            if len(msg) > 0:
                post_tele(msg)
            df = pd.DataFrame.from_dict(dict_price, orient='index')
            # df.to_excel(excel_file_path)
            df.to_csv(excel_file_path)

            if indexz % 500 == 0 and len(dict_price):
                print(Fore.GREEN + "[count_dict_items] Update:", time.strftime("%Y-%m-%d %H:%M:%S"),"price:", askPrice) 
                try:
                    df = pd.DataFrame.from_dict(dict_price, orient='index')
                    md = parse_df_markdown(df)
                    md = "xgboost\n " + md
                    post_tele(md)
                except (requests.exceptions.SSLError, KeyError) as e:
                    print("post markdown error")
        time.sleep(1)

    
if __name__ == "__main__":
    # Initialize the Binance client
    api_key=key
    api_secret=secret
    # client = UMFutures(key="c21f1bb909318f36de0f915077deadac8322ad7df00c93606970441674c1b39b", secret="be2d7e74239b2e959b3446b880451cbb4dee2e6be9d391c4c55ae7ca0976f403", base_url="https://testnet.binancefuture.com")
    client_spot = Spot()
    client = UMFutures(key=api_key, secret=api_secret)

    bst = xgb.Booster()
    bst.load_model('xgboost_model_ORDI_15m_15k_first_maxdepth20_3class.json')
    cut_loss, take_profit = 1.03, 0.97

    last_command_time = int(time.time())
    enable_new_order = False
    enable_pnl = True
    indexz = 0
    askPrice = 0



    interval = '15m'
    usdt = 1000
    precision_ft, precision_price = get_precision(symbol, client)


    add_thread = threading.Thread(target=add_to_dict)
    count_thread = threading.Thread(target=count_dict_items)

    # Start threads
    add_thread.start()
    count_thread.start()

    # Optionally, wait for threads to finish (infinite loop in this case, so we don't actually join)
    add_thread.join()
    count_thread.join()

        