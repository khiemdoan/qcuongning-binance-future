from PIL import Image
import numpy as np
from torchvision.models import resnet50
from fastapi import FastAPI, File, UploadFile
from fastapi.responses import JSONResponse, PlainTextResponse
from pydantic import BaseModel
import xgboost as xgb
from binance.spot import Spot
from xgboost_order import inference
from binance_ft.um_futures import UMFutures
from datetime import datetime, timedelta
from helper import calculate_rsi_with_ema
app = FastAPI()

class TextItem(BaseModel):
    text: str

@app.get("/price")
async def predict():
    askPrice = client.book_ticker(symbol)['askPrice']
    bidPrice = client.book_ticker(symbol)['bidPrice']
    return f"ask: {askPrice}, bid: {bidPrice}"
@app.get("/", response_class=PlainTextResponse)
async def root(time: str, vn: bool):
    time_str = time.replace("_", " ")
    dt = datetime.strptime(time_str, '%Y-%m-%d %H:%M:%S')
    if not vn:
        dt = dt - timedelta(hours=7)
    print(time_str)
    end_ts = int(dt.timestamp() * 1000)
    
    params = {
        # 'startTime': start_ts,
        'endTime': end_ts,
        'limit': 31
    }
    klines = client.klines(symbol="ORDIUSDT", interval="15m", **params)
    
    info = f"{datetime.fromtimestamp(klines[0][0] / 1000)}  to {datetime.fromtimestamp(klines[-2][0] / 1000)}"

    

    ohlc = []
    for item in klines:
        ohlc.append([
            float(item[1]), #o
            float(item[2]), #H
            float(item[3]), #L
            float(item[4]), #C
            float(item[5]) #V
        ])
    ohlc = np.array(ohlc)
    x_array = ohlc[-31:-1]
    rsi_6 = calculate_rsi_with_ema(x_array, 6)
    string_list = [str(int(num)) for num in rsi_6[6:]]

    str_rsi = "-".join(string_list)
    pred = inference(x_array, bst)
    if pred!=1:
        pred_str = "unknown"
    else:
        pred_str = "decrease 3% in next 10 candles"
    kline_start_time = int(klines[-1][0])
    timestring =  datetime.fromtimestamp(kline_start_time / 1000)
    o,h,l,c,v = ohlc[-1]
    price_data = f"{info}\n{timestring} - {symbol} - open: {o}, high: {h}, low: {l}, close: {c}, volumn: {v}, pred: {pred_str}\nrsi_6 = {str_rsi}"
    return price_data
if __name__ == "__main__":
    bst = xgb.Booster()
    client = UMFutures()
    interval = "15m"
    limit = 31
    symbol = "ORDIUSDT"

    bst.load_model('./ORDIUSDT_15m_tp3_sl3_60pcent_mancond_fapiv1.json')
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=80)