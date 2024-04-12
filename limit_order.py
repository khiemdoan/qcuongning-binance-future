
# key api test2
import sys
import time, math
from binance_ft.um_futures import UMFutures
from random_order import get_commision, get_precision, get_status_pos, key, secret


if __name__ == "__main__":
    # um_futures_client = UMFutures(key=key, secret=secret)

    um_futures_client = UMFutures(key="c21f1bb909318f36de0f915077deadac8322ad7df00c93606970441674c1b39b", secret="be2d7e74239b2e959b3446b880451cbb4dee2e6be9d391c4c55ae7ca0976f403", base_url="https://testnet.binancefuture.com")

    usdt = 300
    pair = sys.argv[1]
    print("******", pair, "*******")

    precision_ft = get_precision(pair, um_futures_client)


    # now_ft_price = float(um_futures_client.mark_price(pair)['markPrice']) 
    # bid_price = float(um_futures_client.book_ticker(pair)['bidPrice'])
    bid_price = float(um_futures_client.book_ticker(pair)['askPrice'])

    



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

        print(f"already set a open at {a}, with {coin_open} {pair}, pnl {b}")
    else:
        open_future = um_futures_client.new_order(symbol=pair, side="SELL", type="LIMIT", quantity=quantity_ft, price = bid_price, timeInForce="GTC")
        # open_future = um_futures_client.new_order(symbol=pair, side="SELL", type="MARKET", quantity=quantity_ft)        
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



