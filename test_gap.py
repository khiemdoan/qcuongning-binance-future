from binance_ft.um_futures import UMFutures
um_futures_client = UMFutures()
from binance.spot import Spot
spot_client = Spot()

import time, sys
pair = sys.argv[1]
print(0.075+0.075+0.045*2)
pair_spot = pair
# pair_spot = pair.replace("USDT", "FDUSD")
init_ft = float(um_futures_client.mark_price(pair)['markPrice'])
init_spot = float(spot_client.ticker_price(pair_spot)['price'])
print("init", init_ft, init_spot)
while True:
    # curret_ft = float(um_futures_client.mark_price(pair)['markPrice'])
    curret_ft = float(um_futures_client.book_ticker(pair)['askPrice'])  # > mark price
    # curret_spot = float(spot_client.ticker_price(pair)['price'])
    curret_spot = float(spot_client.book_ticker(pair_spot)['bidPrice'])  # < mark price

    # print(curret_spot-curret_ft)

    gap_ft = -(curret_ft - init_ft)/init_ft * 100
    gap_spot = (curret_spot - init_spot)/init_spot * 100

    if gap_spot + gap_ft > 0.25:
        print(gap_spot + gap_ft)
        if gap_spot > 0:
            print("tang")
        else:
            print("giam")

    # print(gap_ft, gap_spot)
    time.sleep(0.1)