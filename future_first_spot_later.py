# spot truoc future sau:
precision_ft = 0
precision_spot =1
um_futures_client.change_leverage(symbol=pair, leverage=4, recvWindow=6000)


bid_spot = float(spot_client.book_ticker(pair_spot)['bidPrice'])
ask_spot = float(spot_client.book_ticker(pair_spot)['askPrice'])
mark_spot = float(spot_client.ticker_price(pair_spot)['price'])
price_spot = mark_spot
print("order spot at", price_spot)

usdt = 11
quantity_spot = round(usdt/price_spot,precision_spot)
# if quantity_ft < quantity_spot:
#     quantity_ft += 0.1

open_spot = spot_client.new_order(symbol=pair_spot, side="BUY", type="LIMIT", quantity=quantity_spot, price=price_spot, timeInForce="GTC")

order_id_spot = open_spot["orderId"]
while True:
    res_query_spot = spot_client.get_order(symbol=pair_spot, orderId=order_id_spot, recvWindow=6000)
    if res_query_spot['status'] == "FILLED":
        executedQty_spot = float(res_query_spot['executedQty'])
        usdt_value_spot = float(res_query_spot['cummulativeQuoteQty'])
        price_spot = float(res_query_spot['price'])
        # print("spot:", price_spot, usdt_value_spot, "quantity:", executedQty_spot, res_query_spot['type'])
        print("price_spot =", price_spot)
        print("usdt_value_spot =",usdt_value_spot)
        print("quantity_spot =", executedQty_spot)
        print("type_spot =",res_query_spot['type'])
        print("---------------------")
        now_ft_price = float(um_futures_client.mark_price(pair)['markPrice']) 
        now_ft_price = round(now_ft_price, 4)
        # round(usdt_value_spot/now_ft_price, 1)
        quantity_ft = round((usdt)/now_ft_price, precision_ft)
        open_future = um_futures_client.new_order(symbol=pair, side="SELL", type="LIMIT", quantity=quantity_ft, price = now_ft_price, timeInForce="GTC")

        # open_future = um_futures_client.new_order(symbol=pair, side="SELL", type="MARKET", quantity=quantity_ft)
        ft_order_id = open_future["orderId"]
        print("ft_order_id =", ft_order_id)
        while True:
            res_query_ft = um_futures_client.query_order(symbol=pair, orderId=ft_order_id, recvWindow=6000)
            if res_query_ft['status'] == "FILLED":
                # avg_spot = float(spot_order['price'])
                price_ft = float(res_query_ft['avgPrice'])
                executedQty_future = float(res_query_ft['executedQty'])
                usdt_value_ft = float(res_query_ft['cumQuote'])
                print("price_ft =", price_ft)
                print("usdt_value_ft =",usdt_value_ft)
                print("quantity_ft =", executedQty_future)
                print("type_ft =",res_query_ft['type'])
                break
            time.sleep(0.1)
        break
    time.sleep(0.1)