key="7NvUEUX4tnzOja5KQ99gmUG37DQOV9oelvz1akWAr2Zts9X57djRMwbvfgjQoykp"
secret="X9CWCXNsdypjEU8Q0AQaoaqPrcnaX4wpDe5KVxsAfThkVJJAvufiGJ3tb95QqnQC"

key_test = "c21f1bb909318f36de0f915077deadac8322ad7df00c93606970441674c1b39b"
secret_test = "be2d7e74239b2e959b3446b880451cbb4dee2e6be9d391c4c55ae7ca0976f403"
# key api test2
import sys
import time, math
import binance_ft
from binance_ft.um_futures import UMFutures
import openpyxl

def xlsx_to_nested_dict(file_path):
    workbook = openpyxl.load_workbook(file_path)
    sheet = workbook.active

    data = {}

    for row in sheet.iter_rows(min_row=2, values_only=True):
        key = row[0]
        values = row[1:]
        data[key] = {}
        for col_idx, col_value in enumerate(values, start=1):
            data[key][sheet.cell(row=1, column=col_idx).value] = col_value

    return data

def get_commision(ft_order_id, um_futures_client, pair):
    bnb_price = float(um_futures_client.ticker_price("BNBUSDT")['price'])

    
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
            commision_open_future += float(res['commission'])*bnb_price
    all_spend = sum([float(res['quoteQty']) for res in res_ft_open])
    all_coin = sum([float(res['qty']) for res in res_ft_open])
    all_pnl = sum([float(res['realizedPnl']) for res in res_ft_open])

    mean_price = all_spend/all_coin
    # if res_ft_open[0]['maker']:
    #     print("--> this order is maker")
    # else:
    #     print("--> this order is taker")
    return commision_open_future, all_spend, all_coin, mean_price, all_pnl

def get_precision(pair, um_futures_client):
    future_info = um_futures_client.exchange_info()['symbols']
    kk = [i['filters'] for i in future_info if i['symbol'] == pair][0]
    precision_qlt = int(-math.log10(float(kk[1]['minQty'])))
    precision_price = int(-math.log10(float(kk[0]['minPrice'])))

    return precision_qlt, precision_price

def get_status_pos(pair, um_futures_client):
    list_risks = um_futures_client.get_position_risk(recvWindow=6000)
    for pos in list_risks:
        if pos['symbol'] == pair:
            mean_price = float(pos['entryPrice'])
            pnl = float(pos["unRealizedProfit"])
            coin_num = abs(float(pos["positionAmt"]))
            return mean_price, pnl, coin_num
    else:
        return 0, 0, 0




