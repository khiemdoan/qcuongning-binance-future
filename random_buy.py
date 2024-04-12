key="7NvUEUX4tnzOja5KQ99gmUG37DQOV9oelvz1akWAr2Zts9X57djRMwbvfgjQoykp"
secret="X9CWCXNsdypjEU8Q0AQaoaqPrcnaX4wpDe5KVxsAfThkVJJAvufiGJ3tb95QqnQC"
# key api test2
import sys
import time, math
from binance_ft.um_futures import UMFutures
from random_order import key, secret, get_commision, get_precision, get_status_pos

if __name__ == "__main__":
    um_futures_client = UMFutures(key=key, secret=secret)

    # um_futures_client = UMFutures(key=key, secret=secret, base_url="https://testnet.binancefuture.com")

    usdt = 300
    pair = sys.argv[1]
    print("******", pair, "*******")

    precision_ft = get_precision(pair, um_futures_client)


    # now_ft_price = float(um_futures_client.mark_price(pair)['markPrice']) 
    bid_price = float(um_futures_client.book_ticker(pair)['bidPrice'])
    ask_price = float(um_futures_client.book_ticker(pair)['askPrice'])

    quantity_ft = round((usdt)/ask_price, precision_ft)
    print("bid price:", round(ask_price,4), "quantity: ", quantity_ft)

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
        open_future = um_futures_client.new_order(symbol=pair, side="BUY", type="MARKET", quantity=quantity_ft)
        time.sleep(1)
        commis, usdt_open, coin_open, mean_price, all_pnl = get_commision(open_future, um_futures_client, pair)
        coin_open = round(coin_open, precision_ft)

    low_ratio = 0.95
    high_ratio = 1.01

    


    print("commis, usdt_open, coin_open", commis, usdt_open, coin_open, "mean_price", mean_price)
    print("[BUY] close if price lower: ", mean_price * low_ratio, "or higher than", mean_price * high_ratio)
    while True:
        bid_price = float(um_futures_client.book_ticker(pair)['bidPrice'])
        if bid_price < mean_price *low_ratio or bid_price > mean_price * high_ratio:
            print("bid_price", bid_price)
            close_future = um_futures_client.new_order(symbol=pair, side="SELL", type="MARKET", quantity=coin_open)
            time.sleep(1)
            break
        time.sleep(0.1)

    commision_close, all_spend_close, all_coin_close, mean_price_close, all_pnl_close = get_commision(close_future, um_futures_client, pair)

    print("commision_close, all_spend_close, all_coin_close, mean_price_close, all_pnl_close")
    print(commision_close, all_spend_close, all_coin_close, mean_price_close, all_pnl_close)

    print("final pnl: ", all_pnl_close - commis - commision_close)



