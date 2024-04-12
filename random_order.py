key="7NvUEUX4tnzOja5KQ99gmUG37DQOV9oelvz1akWAr2Zts9X57djRMwbvfgjQoykp"
secret="X9CWCXNsdypjEU8Q0AQaoaqPrcnaX4wpDe5KVxsAfThkVJJAvufiGJ3tb95QqnQC"
# key api test2
import sys
import time, math
from binance_ft.um_futures import UMFutures

def get_commision(order_dict, um_futures_client, pair):
    bnb_price = float(um_futures_client.ticker_price("BNBUSDT")['price'])

    ft_order_id = order_dict["orderId"]
    
    while True:
        res_query = um_futures_client.query_order(symbol=pair, orderId=ft_order_id, recvWindow=6000)
        if res_query['status'] == "FILLED":
            break
        time.sleep(0.1)

    res_ft_open = um_futures_client.get_account_trades(symbol=pair, orderId=ft_order_id)
    commision_open_future = 0
    for res in res_ft_open:
        if res['commissionAsset']=="USDT":
            commision_open_future += float(res['commission'])
        elif res['commissionAsset']=="BNB":
            commision_open_future += float(res['commission']) *bnb_price
    all_spend = sum([float(res['quoteQty']) for res in res_ft_open])
    all_coin = sum([float(res['qty']) for res in res_ft_open])
    all_pnl = sum([float(res['realizedPnl']) for res in res_ft_open])

    mean_price = all_spend/all_coin
    if res_ft_open[0]['maker']:
        print("--> this order is maker")
    else:
        print("--> this order is taker")
    return commision_open_future, all_spend, all_coin, mean_price, all_pnl

def get_precision(pair, um_futures_client):
    future_info = um_futures_client.exchange_info()['symbols']
    kk = [i['filters'] for i in future_info if i['symbol'] == pair][0][1]
    precision_ft = int(-math.log10(float(kk['minQty'])))
    return precision_ft

def get_status_pos(pair, um_futures_client):
    list_risks = um_futures_client.get_position_risk()
    for pos in list_risks:
        if pos['symbol'] == pair:
            mean_price = float(pos['entryPrice'])
            pnl = float(pos["unRealizedProfit"])
            coin_num = abs(float(pos["positionAmt"]))
            return mean_price, pnl, coin_num
    else:
        return 0, 0, 0


if __name__ == "__main__":
    um_futures_client = UMFutures(key=key, secret=secret)

    # um_futures_client = UMFutures(key=key, secret=secret, base_url="https://testnet.binancefuture.com")

    usdt = 300
    pair = sys.argv[1]
    print("******", pair, "*******")

    precision_ft = get_precision(pair, um_futures_client)


    # now_ft_price = float(um_futures_client.mark_price(pair)['markPrice']) 
    bid_price = float(um_futures_client.book_ticker(pair)['bidPrice'])

    quantity_ft = round((usdt)/bid_price, precision_ft)
    print("bid price:", round(bid_price,4), "quantity: ", quantity_ft)

    a,b,c  = get_status_pos(pair, um_futures_client)
    if c != 0:

        usdt_open = usdt
        commis = usdt * 0.0005
        coin_open = c
        mean_price = a
        all_pnl = b
        coin_open = round(coin_open, precision_ft)

        print(f"already set a open at {a}, with {coin_open} {pair}, pnnl {b}")
    else:
        open_future = um_futures_client.new_order(symbol=pair, side="SELL", type="MARKET", quantity=quantity_ft)
        commis, usdt_open, coin_open, mean_price, all_pnl = get_commision(open_future, um_futures_client, pair)
        coin_open = round(coin_open, precision_ft)

    low_ratio = 0.99
    high_ratio = 1.05

    


    print("commis, usdt_open, coin_open", commis, usdt_open, coin_open, "mean_price", mean_price)
    print("[SELL] close if price lower: ", mean_price * low_ratio, "or higher than", mean_price * high_ratio)
    while True:
        ask_price = float(um_futures_client.book_ticker(pair)['askPrice'])
        if ask_price < mean_price *low_ratio or ask_price > mean_price * high_ratio:
            print("ask_price", ask_price)
            close_future = um_futures_client.new_order(symbol=pair, side="BUY", type="MARKET", quantity=coin_open)
            time.sleep(1)
            break
        time.sleep(0.1)

    commision_close, all_spend_close, all_coin_close, mean_price_close, all_pnl_close = get_commision(close_future, um_futures_client, pair)

    print("commision_close, all_spend_close, all_coin_close, mean_price_close, all_pnl_close")
    print(commision_close, all_spend_close, all_coin_close, mean_price_close, all_pnl_close)

    print("final pnl: ", all_pnl_close - commis - commision_close)



