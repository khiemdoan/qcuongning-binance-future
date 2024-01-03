pair = "TRTBUSD"
pair_spot = pair.replace("USDT", "BUSD")
init_ft = float(um_futures_client.mark_price(pair)['markPrice'])
init_ft = round(init_ft, 4)
um_futures_client.change_leverage(symbol=pair, leverage=4, recvWindow=6000)
um_futures_client.cancel_open_orders(symbol=pair, recvWindow=2000)
res_ft_order = um_futures_client.new_order(symbol=pair,side="SELL",type="LIMIT",quantity=250,timeInForce="GTC",price=init_ft, reduceOnly=False)
order_id = res_ft_order["orderId"]
while True:
    res = um_futures_client.query_order(symbol=pair, orderId=order_id, recvWindow=6000)
    if res['status'] == "FILLED":
        avg_price = float(res['avgPrice'])
        oriQty = float(res['origQty'])
        usdt_value = float(res['cumQuote'])
        print("future:", avg_price, usdt_value)
        res_spot_order=spot_client.new_order(symbol=pair_spot, side="BUY", type="MARKET", quoteOrderQty=usdt_value)
        spot_order_id = res_spot_order["orderId"]
        while True:
            spot_order = spot_client.get_order(symbol=pair_spot, orderId=spot_order_id, recvWindow=6000)
            if spot_order['status'] == "FILLED":
                # avg_spot = float(spot_order['price'])
                executedQty_spot = float(spot_order['executedQty'])
                usdt_value_spot = float(spot_order['cummulativeQuoteQty'])
                avg_price_spot = round(usdt_value_spot/executedQty_spot, 4)
                print("spot: ", avg_price_spot, usdt_value_spot)
            time.sleep(0.1)
            break
        break
    time.sleep(0.1)