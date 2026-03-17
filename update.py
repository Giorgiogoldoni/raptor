import yfinance as yf
import pandas as pd
import numpy as np
import json
from datetime import datetime
import time

# Lista ridotta per test, poi aggiungi gli altri
ASSETS = [
    {"ticker": "LQQ.PA", "nome": "Nasdaq 2x Lev", "cat": "ETF LEVA"},
    {"ticker": "3LNV.MI", "nome": "3x Long NVIDIA", "cat": "LEVA 3X"},
    {"ticker": "BTC-USD", "nome": "Bitcoin", "cat": "CRYPTO"},
    {"ticker": "^GSPC", "nome": "S&P 500", "cat": "INDICI"}
]

def calcola_kama(series, period=10, fast=2, slow=30):
    series = series.ffill().bfill()
    change = abs(series - series.shift(period))
    volatility = abs(series - series.shift(1)).rolling(window=period).sum()
    er = (change / volatility).replace([np.inf, -np.inf], 0).fillna(0)
    sc = (er * (2/(fast+1) - 2/(slow+1)) + 2/(slow+1))**2
    kama = series.copy()
    for i in range(period, len(series)):
        kama.iloc[i] = kama.iloc[i-1] + sc.iloc[i] * (series.iloc[i] - kama.iloc[i-1])
    return kama

output_data = []
for asset in ASSETS:
    try:
        df = yf.download(asset['ticker'], period="150d", interval="1d", progress=False)
        if df.empty: continue
        # FIX: Squeeze rimuove il problema delle colonne doppie di Yahoo
        close_s = df['Close'].squeeze()
        df['kama_v'] = calcola_kama(close_s, 10, 5, 20)
        df['kama_l'] = calcola_kama(close_s, 10, 2, 30)
        
        status = "BUY" if df['Close'].iloc[-1] > df['kama_v'].iloc[-1] else "SELL"
        
        output_data.append({
            "ticker": asset['ticker'], "nome": asset['nome'], "categoria": asset['cat'],
            "price": float(df['Close'].iloc[-1]), "status": status,
            "signal_date": datetime.now().strftime("%d/%m/%Y"),
            "history": {"dates": [], "prices": [], "kv": [], "kl": []} # Semplificato per test
        })
    except Exception as e: print(f"Errore {asset['ticker']}: {e}")

with open('data.json', 'w') as f:
    json.dump({"last_update": datetime.now().strftime("%d/%m/%Y %H:%M"), "data": output_data}, f, indent=4)
