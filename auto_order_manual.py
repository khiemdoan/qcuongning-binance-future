import datetime
import os
import numpy as np
import pandas as pd
from binance_ft.um_futures import UMFutures
import time
import time, sys
from helper import get_commision, get_precision, get_status_pos, key, secret, post_tele, key_test, secret_test
from binance_ft.error import ClientError
import requests
import argparse


def parse_df_markdown(df):
    df_show = df[df['break'] == False].drop(columns=['highest_price', 'highest_rate', 'orderId', 'filled', 'coin', "commis", "time", "close_price", "break"]).fillna(0)
    df_show = df_show.rename(columns={"low_boundary": "lb", "askPrice":"ap", "high_boundary":"hp"})
    df_show = df_show.apply(lambda x: x.round(2))
    markdown_text = df_show.to_markdown()
    return markdown_text

def update_dict(dict_price, order, price, index, cut_loss, take_profit, manual=False):
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
    dict_price[index]['filled'] = "F"
    dict_price[index]['close_price'] = 0
    dict_price[index]['pnl'] = 0
    dict_price[index]['coin'] = 0
    dict_price[index]['commis'] = 0
    dict_price[index]['manual'] = manual


    return dict_price


def update_tele():
    global last_command_time, enable_new_order, enable_pnl, indexz, dict_price
    BOT_TOKEN = '6665726347:AAGJ60eAiJWsurJVf1YrIALjzAWJbrvrZzk'

    url = f"https://api.telegram.org/bot{BOT_TOKEN}/getUpdates"
    response = requests.get(url)
    data = response.json()
    
    if "result" in data and len(data["result"]) > 0:
        cmd = data["result"][-1]["message"]["text"]
        time = data['result'][-1]['message']['date']
        if time > last_command_time:
            last_command_time = time
            print(f"Chat:{datetime.datetime.fromtimestamp(time)}: {cmd}")
            if cmd == "hi":
                post_tele("hello!!!")
            elif cmd == "Price":
                post_tele(str(askPrice))
            elif cmd == "off":
                enable_new_order = False
                post_tele("turn off")
            elif cmd == "on":
                enable_new_order = True
                post_tele("turn on")
            elif cmd == "pnl":
                enable_pnl = not enable_pnl
                indexz = 497
                post_tele("trigger pnl: "+str(enable_pnl))
            elif cmd.startswith("rm"):
                idrm = cmd.split(" ")
                if len(idrm):
                    id_rm = int(idrm[1])
                    post_tele(f"remove {id_rm}")
                    if id_rm in dict_price:
                        dict_price[id_rm]['break'] = True
                    else:
                        post_tele(f"not found {id_rm}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='A simple example script to demonstrate argparse')
    parser.add_argument('pair', type=str, default= "ORDIUSDC",help='The name of the pair to process')
    parser.add_argument("--vol", type=int, default=300)
    parser.add_argument("--en", action='store_true')
    parser.add_argument("--test", action='store_true')
    last_command_time = int(time.time())
    print("start in", datetime.datetime.fromtimestamp(last_command_time))


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
    reply = True
    enable_pnl = True

    # client.cancel_open_orders(symbol=pair, recvWindow=2000)

    date = time.strftime("%Y-%m")
    excel_file_path = f'{pair}_manual_{date}.csv'
    if os.path.exists(excel_file_path):
        df = pd.read_csv(excel_file_path, header=0, index_col=0)
        dict_price = df.to_dict('index')
        if len(dict_price):
            print(f"load previous {excel_file_path} contain {len(dict_price)} with {len(df[df['break']==True])} break and {len(df[df['filled']=='True'])} filled")
            # import ipdb
            # ipdb.set_trace()
            # print(dict_price)

    else:
        post_tele("----new----")
        
        dict_price = {}
    index = len(dict_price)
    order_ids = [value['orderId'] for value in dict_price.values()]
    indexz = 490
    # print("start !!!", index, order_ids)


    while True:
        update_tele()
        indexz += 1
        askPrice = float(client.book_ticker(pair)['askPrice'])  # > mark price        

        # check open order by smartphone to trigger service
        open_orders = [i for i in client.get_orders() if i['symbol'] == pair]
        for open in open_orders:
            if open['side'] == "SELL" and open['orderId'] not in order_ids:
                dict_price = update_dict(dict_price, open, round(float(open['price']), precision_price), index, cut_loss, take_profit)
                index += 1
                order_ids = [value['orderId'] for value in dict_price.values()]

        if indexz % 50 == 0:
            res = client.get_all_orders(pair)[-1]
            if res['side'] == "SELL" and res['orderId'] not in order_ids and res['time']/1000 > last_command_time:
                print("!!!update order id", res['orderId'], "in", datetime.datetime.fromtimestamp(res['time']/1000))
                dict_price = update_dict(dict_price, res, round(float(res['price']), precision_price), index, cut_loss, take_profit)
                index+=1
                order_ids = [value['orderId'] for value in dict_price.values()]




        msg = ""
        for key in dict_price.keys():

            if dict_price[key]['filled'] != "True":
                try:
                    res_query = client.query_order(symbol=pair, orderId=dict_price[key]['orderId'], recvWindow=6000)
                except ClientError:
                    print(key, dict_price[key])
                if res_query['status'] == "FILLED":
                    commis, usdt_open, coin_open, mean_price, all_pnl = get_commision(dict_price[key]['orderId'], client, pair)
                    print(time.strftime("%Y-%m-%d %H:%M:%S"), f"Open order {key} usdt_open: {usdt_open:.3f} coin_open: {coin_open:.3f}, mean_price: {mean_price:.3f}, commis: {commis:.3f}")
                    dict_price[key]['filled'] = "True"
                    dict_price[key]['coin'] = round(coin_open, precision_ft)
                    dict_price[key]['commis'] = round(commis,2)
                    msg += f"*open* id: {key} at:{mean_price:.3f}, low:{dict_price[key]['low_boundary']:.2f}, high:{dict_price[key]['high_boundary']:.2f}\n"
                elif res_query['status'] == "CANCELED":
                    dict_price[key]['filled'] = "CANCELED"



            if dict_price[key]['filled'] == "True":

                if dict_price[key]['break']:
                    continue
                dict_price[key]['pnl'] = round(dict_price[key]['coin'] * (dict_price[key]['askPrice'] - askPrice),3)
                if askPrice > dict_price[key]['highest_price']:
                    dict_price[key]['highest_price'] = askPrice
                    dict_price[key]["highest_rate"]  = round(askPrice/dict_price[key]["askPrice"] *100, 1)
                if askPrice < dict_price[key]['low_boundary'] or askPrice >= dict_price[key]['high_boundary']:
                    close_future = client.new_order(symbol=pair, side="BUY", type="MARKET", quantity=dict_price[key]['coin'])
                    commis, usdt_open, coin_open, mean_price, all_pnl = get_commision(close_future['orderId'], client, pair)
                    print(time.strftime("%Y-%m-%d %H:%M:%S"), f"Close order {key} usdt_open: {usdt_open:.3f} coin_open: {coin_open:.3f}, mean_price: {mean_price:.3f}, commis: {commis:.3f}")    
                    dict_price[key]['commis'] += round(commis,2)
                    dict_price[key]['close_price'] = mean_price

                    dict_price[key]['pnl'] = round(coin_open * (dict_price[key]["askPrice"] - mean_price) - dict_price[key]['commis'], 3)
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
            dict_price = update_dict(dict_price, open_future, askPrice, index, cut_loss, take_profit)
            index+=1
            order_ids = [value['orderId'] for value in dict_price.values()]
        df = pd.DataFrame.from_dict(dict_price, orient='index')
        df.to_csv(excel_file_path)

        if indexz % 500 == 0 and enable_pnl:
            print("Update:", time.strftime("%Y-%m-%d %H:%M:%S"),"price:", askPrice, ", enable:", enable_new_order) 
            try:
                df = pd.DataFrame.from_dict(dict_price, orient='index')
                md = parse_df_markdown(df)
                post_tele(md)
            except (requests.exceptions.SSLError, KeyError) as e:
                print("post markdown error", e)
        time.sleep(1)
        



