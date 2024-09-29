from PIL import Image
import numpy as np
from torchvision.models import resnet50
from fastapi import FastAPI, File, UploadFile
from fastapi.responses import JSONResponse, PlainTextResponse
from pydantic import BaseModel
import xgboost as xgb
from binance.spot import Spot
from datetime import datetime
from xgboost_order import inference
app = FastAPI()

class TextItem(BaseModel):
    text: str

@app.post("/predict")
async def predict(item: TextItem):
    return {"prediction": item.text}
@app.get("/", response_class=PlainTextResponse)
async def root():
    klines = client_spot.klines(symbol=symbol, interval=interval, limit=limit)
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
    pred = inference(x_array, bst)
    if pred!=1:
        pred_str = "unknown"
    else:
        pred_str = "decrease 3% in next 10 candles"
    kline_start_time = int(klines[-1][0])
    timestring =  datetime.fromtimestamp(kline_start_time / 1000)
    o,h,l,c,v = ohlc[-1]
    price_data = f"{timestring} - {symbol} - open: {o}, high: {h}, low: {l}, close: {c}, volumn: {v}, pred: {pred_str}"
    return price_data
if __name__ == "__main__":
    bst = xgb.Booster()
    client_spot = Spot()
    interval = "15m"
    limit = 31
    symbol = "ORDIUSDT"

    bst.load_model('xgboost_model_ORDI_15m_15k_first_maxdepth20_3class.json')
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=80)