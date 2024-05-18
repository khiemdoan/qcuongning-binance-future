import os
import numpy as np
import pandas as pd
from binance_ft.um_futures import UMFutures
import time
import time, sys
from helper import get_commision, get_precision, get_status_pos, key, secret, xlsx_to_nested_dict
from binance_ft.error import ClientError
import requests

def parse_df_markdown(df):
    df_show = df[df['break'] == False].drop(columns=['highest_price', 'highest_rate', 'orderId', 'filled', 'coin', "commis", "time", "close_price", "break"]).fillna(0)
    df_show = df_show.rename(columns={"low_boundary": "lb", "askPrice":"ap", "high_boundary":"hp"})
    df_show = df_show.apply(lambda x: x.round(2))
    markdown_text = df_show.to_markdown()
    return markdown_text

um_futures_client = UMFutures(key=key, secret=secret)
print("import um_futures_client")
# um_futures_client = UMFutures(key="c21f1bb909318f36de0f915077deadac8322ad7df00c93606970441674c1b39b", secret="be2d7e74239b2e959b3446b880451cbb4dee2e6be9d391c4c55ae7ca0976f403", base_url="https://testnet.binancefuture.com")
pair = sys.argv[1]
cut_loss = 0.99
take_profit = 1.05
pair_spot = pair
usdt = 150
prob_open = 0.9
enable_new_order = False
precision_ft = get_precision(pair, um_futures_client)

# um_futures_client.cancel_open_orders(symbol=pair, recvWindow=2000)
sleep_time_new_order = 0.4 #h
sleep_time_new_order_sec = sleep_time_new_order * 60 * 60
print("sleep_time_new_order:", sleep_time_new_order_sec)
date = time.strftime("%Y-%m-%d")
excel_file_path = f'{pair}_{cut_loss}_{sleep_time_new_order}_{date}.xlsx'
if os.path.exists(excel_file_path):
    df = pd.read_excel(excel_file_path, header=0, index_col=0)
    dict_price = df.to_dict('index')
    print(f"load previous {excel_file_path} contain {len(dict_price)} with {len(df[df['break']==True])} break and {len(df[df['filled']==True])} filled")
    index = len(dict_price)

else:
    try:
        requests.post(f"https://api.telegram.org/bot5910304360:AAGW_t3F1x9cATh7d6VUDCquJFX0dPC2W-M/sendMessage?chat_id=-895385211&text=-----new-----")
    except requests.exceptions.ConnectionError as e:
        print(e)
    index = 0
    dict_price = {}



random_sleep = sleep_time_new_order_sec//2
time_order = time.time()
indexz = 0
reply = True
while True:
    indexz += 1
    bidPrice = float(um_futures_client.book_ticker(pair)['bidPrice'])

    askPrice = float(um_futures_client.book_ticker(pair)['askPrice'])  # > mark price

    response = um_futures_client.account(recvWindow=6000)
    for assett in response['assets']:
        if assett['asset'] == "USDT":
            if float(assett['walletBalance']) > 0 and not reply:
                reply = True
                requests.post(f"https://api.telegram.org/bot5910304360:AAGW_t3F1x9cATh7d6VUDCquJFX0dPC2W-M/sendMessage?chat_id=-895385211&text=alive")
            elif float(assett['walletBalance']) ==  0:
                reply = False

    if askPrice > 40.5:
        enable_new_order = True
    elif  askPrice < 40:
        enable_new_order = False
    msg = ""
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
                dict_price[key]['commis'] = round(commis,2)
                msg += f"*open* id: {key} at:{mean_price:.3f}, low:{dict_price[key]['low_boundary']:.2f}, high:{dict_price[key]['high_boundary']:.2f}\n"
            elif res_query['status'] == "CANCELED":
                dict_price[key]['filled'] = "CANCELED"



        if dict_price[key]['filled'] is True:
            if dict_price[key]['break']:
                continue
            dict_price[key]['pnl'] = dict_price[key]['coin'] * (dict_price[key]['askPrice'] - askPrice)
            if askPrice > dict_price[key]['highest_price']:
                dict_price[key]['highest_price'] = askPrice
                dict_price[key]["highest_rate"]  = round(askPrice/dict_price[key]["askPrice"] *100, 1)
            if askPrice < dict_price[key]['low_boundary'] or askPrice >= dict_price[key]['high_boundary']:
                close_future = um_futures_client.new_order(symbol=pair, side="BUY", type="MARKET", quantity=dict_price[key]['coin'])
                time.sleep(0.5)
                commis, usdt_open, coin_open, mean_price, all_pnl = get_commision(close_future['orderId'], um_futures_client, pair)
                print(time.strftime("%Y-%m-%d %H:%M:%S"), f"Close order {key} usdt_open: {usdt_open:.3f} coin_open: {coin_open:.3f}, mean_price: {mean_price:.3f}, commis: {commis:.3f}")
                
                dict_price[key]['commis'] += round(commis,2)
                dict_price[key]['close_price'] = mean_price

                dict_price[key]['pnl'] = coin_open * (dict_price[key]["askPrice"] - mean_price) - dict_price[key]['commis']
                dict_price[key]['break'] = True
                msg += f"*close* id: {key}, pnl: {dict_price[key]['pnl']:.2f}, price:{mean_price:.2f}\n"
                
    if len(msg) > 0:
        requests.post(f"https://api.telegram.org/bot5910304360:AAGW_t3F1x9cATh7d6VUDCquJFX0dPC2W-M/sendMessage?chat_id=-895385211&text={msg}&parse_mode=Markdown")
        df = pd.DataFrame.from_dict(dict_price, orient='index')
        df.to_excel(excel_file_path)
        
    if time.time() - time_order > random_sleep:
        if np.random.random() > prob_open:
            time_order = time.time()
            print("\n-----",time.strftime("%Y-%m-%d %H:%M:%S"), "-----")
            random_sleep = np.random.randint(int(sleep_time_new_order_sec*0.8), int(sleep_time_new_order_sec*1.2))
            if enable_new_order:
                time_get_gap = time.strftime("%Y-%m-%d %H:%M:%S")
                quantity_ft = round((usdt)/askPrice, precision_ft)
                msg = f"{time_get_gap} create new order {index} price: {askPrice}"
                requests.post(f"https://api.telegram.org/bot5910304360:AAGW_t3F1x9cATh7d6VUDCquJFX0dPC2W-M/sendMessage?chat_id=-895385211&text={msg}")
                try:
                    open_future = um_futures_client.new_order(symbol=pair, side="SELL", type="LIMIT", quantity=quantity_ft, price = askPrice, timeInForce="GTC")
                except ClientError as error:
                    enable_new_order = False
                    print(error.error_message)
                    requests.post(f"https://api.telegram.org/bot5910304360:AAGW_t3F1x9cATh7d6VUDCquJFX0dPC2W-M/sendMessage?chat_id=-895385211&text={error.error_message}")
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
    if indexz % 500 == 0:
        md = parse_df_markdown(df)
        try:
            requests.post(f"https://api.telegram.org/bot5910304360:AAGW_t3F1x9cATh7d6VUDCquJFX0dPC2W-M/sendMessage?chat_id=-895385211&text={md}&parse_mode=Markdown")
        except requests.exceptions.SSLError as e:
            print("post markdown error", e.error_message)
    time.sleep(1)
        



