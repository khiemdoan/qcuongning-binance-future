from datetime import datetime, timedelta
import random 
from fastapi import FastAPI, File, UploadFile, Request
from fastapi. responses import HTMLResponse, FileResponse, JSONResponse
from fastapi. staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from PIL import Image 
import os
from fastapi.templating import Jinja2Templates 
import numpy as np
import pandas as pd
from binance_ft.um_futures import UMFutures
import xgboost as xgb
from helper import calculate_rsi_with_ema
from xgboost_order import inference

app = FastAPI()
# Allow CORS for frontend
app.add_middleware (
    CORSMiddleware,
    allow_origins=["http://localhost:8000"],
    allow_credentials=True,
    allow_methods= ["*"],
    allow_headers=["*"],
)

templates = Jinja2Templates (directory="templates")
@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    return templates.TemplateResponse("index.html",{"request":request})

@app.get("/price")
async def get_price():
    res = client.ticker_price(symbol)['price']
    return {"price": float(res)}

@app.get("/select")
async def check_select(option):
    klines = client.klines(symbol="ORDIUSDT", interval="15m", limit = 10)
    if option == "current":
        end_ts = klines[-1][0]
    elif option == "previous":
        end_ts = klines[-2][0]
    elif option == "pre-previous":
        end_ts = klines[-3][0]
    else:
        dt = datetime.strptime(option, '%Y-%m-%d %H:%M:%S')
        dt = dt - timedelta(hours=7)
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
        pred_str = "decrease 3"
    kline_start_time = int(klines[-1][0])
    timestring =  datetime.fromtimestamp(kline_start_time / 1000)
    o,h,l,c,v = ohlc[-1]
    price_data = f"{info}\n{timestring} - {symbol} - open: {o}, high: {h}, low: {l}, close: {c}, volumn: {v}, pred: {pred_str}\nrsi_6 = {str_rsi}"
    return {"message":price_data}

@app.get("/show")
async def show():
    df = pd.read_csv("./ORDIUSDT_2024-10.csv")
    df = df[df["manual"]==False][["time", "askPrice", "close_price", "pnl"]].iloc[-10:]
    html_table = df.to_html(classes="dataframe", index=False)
    return {"html": html_table}

@app.get("/plot")
async def plot():
    klines = client.klines(symbol="ORDIUSDT", interval="15m", limit=30)
    close_list = [i[4] for i in klines]
    time = list(range(len(close_list)))
    response_data ={"time": time,"data": close_list}
    return JSONResponse (content=response_data)

if __name__=="__main__":
    bst = xgb.Booster()
    bst.load_model('./ORDIUSDT_15m_tp3_sl3_60pcent_mancond_fapiv1.json')

    client = UMFutures()
    interval = "15m"
    limit = 31
    symbol = "ORDIUSDT"

    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=80)