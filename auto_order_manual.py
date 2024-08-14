import datetime
import os
import numpy as np
import pandas as pd
from binance_ft.um_futures import UMFutures
import time
import time, sys
from helper import get_commision, get_precision, get_status_pos, key, secret, xlsx_to_nested_dict, key_test, secret_test
from binance_ft.error import ClientError
import requests
import argparse


def parse_df_markdown(df):
    df_show = df[df['break'] == False].drop(columns=['highest_price', 'highest_rate', 'orderId', 'filled', 'coin', "commis", "time", "close_price", "break"]).fillna(0)
    df_show = df_show.rename(columns={"low_boundary": "lb", "askPrice":"ap", "high_boundary":"hp"})
    df_show = df_show.apply(lambda x: x.round(2))
    markdown_text = df_show.to_markdown()
    return markdown_text

def update_dict(dict_price, order, price, index, cut_loss, take_profit):
    if "time" in order:
        
        time_get_gap = datetime.datetime.fromtimestamp(order['time'] / 1000).strftime("%Y-%m-%d %H:%M:%S")
    else:
        time_get_gap = datetime.datetime.fromtimestamp(order['updateTime'] / 1000).strftime("%Y-%m-%d %H:%M:%S")

    msg = f"{time_get_gap} create new order {index} price: {price}"
    post_tele(msg)
    dict_price[index] = {}
    dict_price[index]["time"] = time_get_gap
    dict_price[index]["askPrice"] = price
    dict_price[index]["highest_price"] = price
    dict_price[index]["highest_rate"] = 100
    dict_price[index]['break'] = False
    dict_price[index]['low_boundary'] = price * take_profit
    dict_price[index]['high_boundary'] = price * cut_loss
    dict_price[index]['orderId'] = order["orderId"]
    dict_price[index]['filled'] = False
    dict_price[index]['close_price'] = 0
    dict_price[index]['pnl'] = 0
    return dict_price

def post_tele(msg):
    try:
        link_api = "https://api.telegram.org/bot5910304360:AAGW_t3F1x9cATh7d6VUDCquJFX0dPC2W-M/sendMessage?"
        chat_id = "-895385211"
        requests.post(f"{link_api}chat_id={chat_id}&text={msg}&parse_mode=Markdown")
    except requests.exceptions.SSLError as e:
        print("post_tele", e)



if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='A simple example script to demonstrate argparse')
    parser.add_argument('pair', type=str, default= "ORDIUSDC",help='The name of the pair to process')
    parser.add_argument("--vol", type=int, default=300)
    parser.add_argument("--en", action='store_true')
    parser.add_argument("--test", action='store_true')


    args = parser.parse_args()
    if args.test:
        client = UMFutures(key=key_test, secret=secret_test, base_url="https://testnet.binancefuture.com")
    else:
        client = UMFutures(key=key, secret=secret)
    print("import client")
    pair = args.pair
    cut_loss = 1.05
    take_profit = 0.99
    pair_spot = pair
    usdt = args.vol
    prob_open = 0.5
    enable_new_order = args.en
    precision_ft, precision_price = get_precision(pair, client)
    df = None

    # client.cancel_open_orders(symbol=pair, recvWindow=2000)

    date = time.strftime("%Y-%m")
    excel_file_path = f'{pair}_{cut_loss}_0.4_{date}.xlsx'
    if os.path.exists(excel_file_path):
        df = pd.read_excel(excel_file_path, header=0, index_col=0)
        dict_price = df.to_dict('index')
        print(f"load previous {excel_file_path} contain {len(dict_price)} with {len(df[df['break']==True])} break and {len(df[df['filled']==True])} filled")
        index = len(dict_price)

    else:
        # try:
        #     requests.post(f"https://api.telegram.org/bot5910304360:AAGW_t3F1x9cATh7d6VUDCquJFX0dPC2W-M/sendMessage?chat_id=-895385211&text=-----new-----")
        # except requests.exceptions.ConnectionError as e:
        #     print(e)
        index = 0
        dict_price = {}

        indexz = 0
        reply = True
        price = 0
        temp = False
        open_oder_manual = []
        order_ids = [value['orderId'] for value in dict_price.values()]

    while True:
        indexz += 1
        bidPrice = float(client.book_ticker(pair)['bidPrice'])

        askPrice = float(client.book_ticker(pair)['askPrice'])  # > mark price

        # check balance to trigger service remotely
        try:
            response = client.account(recvWindow=6000)
            for assett in response['assets']:
                if assett['asset'] == "USDT":
                    if float(assett['walletBalance']) > 0 and not reply:
                        reply = True
                        enable_new_order = True
                        post_tele(f"alive-enable_new_order-{enable_new_order}")
                    elif float(assett['walletBalance']) ==  0:
                        reply = False
        except ClientError as err:
            pass
            print("get acount error: ", err.error_message)

        # check open order by smartphone to trigger service
        open_orders = [i for i in client.get_orders() if i['symbol'] == pair]
        for open in open_orders:
            if open['side'] == "SELL" and open['orderId'] not in order_ids:
                dict_price = update_dict(dict_price, open, round(float(open['price']), precision_price), index)
                index += 1
                order_ids = [value['orderId'] for value in dict_price.values()]

        msg = ""
        for key in dict_price.keys():
            if not dict_price[key]['filled']:
                try:
                    res_query = client.query_order(symbol=pair, orderId=dict_price[key]['orderId'], recvWindow=6000)
                except ClientError:
                    print(key, dict_price[key])
                if res_query['status'] == "FILLED":
                    commis, usdt_open, coin_open, mean_price, all_pnl = get_commision(dict_price[key]['orderId'], client, pair)
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
                    close_future = client.new_order(symbol=pair, side="BUY", type="MARKET", quantity=dict_price[key]['coin'])
                    commis, usdt_open, coin_open, mean_price, all_pnl = get_commision(close_future['orderId'], client, pair)
                    print(time.strftime("%Y-%m-%d %H:%M:%S"), f"Close order {key} usdt_open: {usdt_open:.3f} coin_open: {coin_open:.3f}, mean_price: {mean_price:.3f}, commis: {commis:.3f}")    
                    dict_price[key]['commis'] += round(commis,2)
                    dict_price[key]['close_price'] = mean_price

                    dict_price[key]['pnl'] = coin_open * (dict_price[key]["askPrice"] - mean_price) - dict_price[key]['commis']
                    dict_price[key]['break'] = True
                    msg += f"*close* id: {key}, pnl: {dict_price[key]['pnl']:.2f}, price:{mean_price:.2f}\n"
                    
        if len(msg) > 0:
            post_tele(msg)

        
        if enable_new_order:
            enable_new_order = False
            time_get_gap = time.strftime("%Y-%m-%d %H:%M:%S")
            print("\n-----",time_get_gap, "-----")
            quantity_ft = round((usdt)/askPrice, precision_ft)
            try:
                open_future = client.new_order(symbol=pair, side="SELL", type="LIMIT", quantity=quantity_ft, price = askPrice, timeInForce="GTC")
            except ClientError as error:
                print(error.error_message)
                post_tele(error.error_message)
            dict_price = update_dict(dict_price, open_future, askPrice, index)
            index+=1
            order_ids = [value['orderId'] for value in dict_price.values()]

        df = pd.DataFrame.from_dict(dict_price, orient='index')
        df.to_excel(excel_file_path)

        if indexz % 500 == 0:
            print("Update:", time.strftime("%Y-%m-%d %H:%M:%S"),"price:", askPrice, ", enable:", enable_new_order) 
            try:
                df = pd.DataFrame.from_dict(dict_price, orient='index')
                md = parse_df_markdown(df)
                post_tele(md)
            except (requests.exceptions.SSLError, KeyError) as e:
                print("post markdown error")
        time.sleep(1)
        



