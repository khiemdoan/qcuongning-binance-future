import ccxt
import pandas as pd
import streamlit as st
from datetime import datetime, timedelta
from SMA_mexc import get_klines_spot, binance_sym, get_symbol, get_klines, get_contract_funding_rate, get_syms_future
from helper import calculate_rsi_with_ema, compute_rsi_pd
from tqdm import tqdm
from binance_ft.um_futures import UMFutures
import numpy as np
# --- INIT ---
um_futures_client = UMFutures()

# st.set_page_config(page_title="Coin Short Screener", layout="wide")
# st.title("🔻 Coin Short Screener Dashboard")

# --- INPUT ---
top_n = st.slider("Top coin by volume", 10, 100, 30)
rsi_threshold = st.slider("RSI threshold (overbought)", 70, 90, 75)
price_pump_min = st.slider("Min % pump in 24h", 10, 300, 50)
funding_threshold = st.slider("Funding Rate ≤ (âm)", -1.0, 0.0, -0.1)


# --- GET SYMBOLS ---
symbols = get_syms_future()
# symbols = um_futures_client.exchange_info()['symbols']
# symbols = sorted(symbols, key=lambda x: markets[x].get("quoteVolume", 0), reverse=True)[:top_n]
print(f"Found {len(symbols)} symbols to analyze")
# --- FILTER COINS ---
results = []

for symbol_info in tqdm(symbols):
    try:
        symbol = symbol_info
        ohlcv = get_klines(symbol, interval="Min60", limit=100)
        # symbol = symbol_info['symbol']
        # ohlcv = um_futures_client.klines(symbol, "1h")
        # ohclv_data = np.array(ohlcv, dtype=float)
        # print(symbol,  ohlcv)
        
        df = pd.DataFrame(ohlcv['data'], columns=["time", "open", "high", "low", "close", "volume"])
        # df = pd.DataFrame(ohclv_data[:,:6], columns=["time", "open", "high", "low", "close", "volume"])

        # import ipdb; ipdb.set_trace()
        df['time'] = pd.to_datetime(df['time'], unit='ms')
        df.set_index("time", inplace=True)

        # RSI
        df['rsi'] = compute_rsi_pd(df['close'])

        # Price pump %
        change_24h = (df['close'].iloc[-1] - df['close'].iloc[-24]) / df['close'].iloc[-24] * 100
        current_rsi = df['rsi'].iloc[-1]

        # Funding Rate (simulated, placeholder)
        funding_rate_json = get_contract_funding_rate(symbol)['data']
        # funding_rate_json = um_futures_client.funding_rate(symbol=symbol, limit=1)[-1]
        # print(f"Funding Rate JSON: {funding_rate_json}")
        # print(f"Funding Rate JSON: {funding_rate_json}")
        fr_value = funding_rate_json.get("fundingRate", 0)
        # print(f"Funding Rate for {symbol}: {fr_value}")

        if change_24h > price_pump_min and current_rsi > rsi_threshold and fr_value < funding_threshold:
            results.append({
                'Symbol': symbol,
                'Pump 24h (%)': round(change_24h, 2),
                'RSI': round(current_rsi, 2),
                'Funding Rate': round(fr_value * 100, 4)
            })

    except Exception as e:
        print(f"Error processing {symbol}: {e}")
        continue

# --- SHOW RESULTS ---
df_result = pd.DataFrame(results)
if not df_result.empty:
    st.success(f"🔍 {len(df_result)} coin phù hợp để xem xét short")
    st.dataframe(df_result.sort_values(by="Pump 24h (%)", ascending=False))
else:
    st.warning("😐 Không tìm thấy coin nào phù hợp với tiêu chí hiện tại.")
