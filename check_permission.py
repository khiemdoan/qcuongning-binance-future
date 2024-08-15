from helper import key, secret
from binance_ft.um_futures import UMFutures
from binance_ft.error import ClientError

client = UMFutures(key=key, secret=secret)

try: 
    res_query = client.query_order(symbol="ORDIUSDT", orderId=10471802294, recvWindow=6000)
    print(res_query)
except ClientError as err:
    print(err.error_message)