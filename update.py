import yfinance as yf
import pandas as pd
import numpy as np
import json
from datetime import datetime
import time

# --- LISTA INTEGRALE ASSET ---
ASSETS = [
    # LEVA 3X LONG
    {"ticker": "3LNV.MI", "nome": "3x Long NVIDIA", "cat": "LEVA 3X"},
    {"ticker": "3LTS.MI", "nome": "3x Long Tesla", "cat": "LEVA 3X"},
    {"ticker": "3LMI.MI", "nome": "3x Long MicroStrategy", "cat": "LEVA 3X"},
    {"ticker": "3LCO.MI", "nome": "3x Long Coinbase", "cat": "LEVA 3X"},
    {"ticker": "3LCR.MI", "nome": "3x Long UniCredit", "cat": "LEVA 3X"},
    {"ticker": "3LFB.MI", "nome": "3x Long Meta", "cat": "LEVA 3X"},
    {"ticker": "3LAA.MI", "nome": "3x Long Alibaba", "cat": "LEVA 3X"},
    {"ticker": "3LRP.MI", "nome": "3x Long Ripple", "cat": "LEVA 3X"},
    {"ticker": "3LAD.MI", "nome": "3x Long AMD", "cat": "LEVA 3X"},
    # LEVA 3X SHORT
    {"ticker": "3SNV.MI", "nome": "3x Short NVIDIA", "cat": "LEVA 3X SHORT"},
    {"ticker": "3STS.MI", "nome": "3x Short Tesla", "cat": "LEVA 3X SHORT"},
    {"ticker": "3SMI.MI", "nome": "3x Short MicroStrategy", "cat": "LEVA 3X SHORT"},
    {"ticker": "3SFB.MI", "nome": "3x Short Meta", "cat": "LEVA 3X SHORT"},
    {"ticker": "3SCR.MI", "nome": "3x Short UniCredit", "cat": "LEVA 3X SHORT"},
    # ETF LEVA & INVERSE
    {"ticker": "LQQ.PA", "nome": "Nasdaq 2x Long", "cat": "ETF LEVA"},
    {"ticker": "CL2.PA", "nome": "MSCI USA 2x Long", "cat": "ETF LEVA"},
    {"ticker": "DAXLEV.PA", "nome": "DAX 2x Long", "cat": "ETF LEVA"},
    {"ticker": "XS2L.MI", "nome": "S&P 500 2x Long", "cat": "ETF LEVA"},
    {"ticker": "XSD2.MI", "nome": "ShortDAX x2", "cat": "ETF INVERSE"},
    {"ticker": "XSPS.MI", "nome": "S&P 500 Inverse", "cat": "ETF INVERSE"},
    {"ticker": "5MIB.MI", "nome": "FTSE MIB 5x Long", "cat": "ETF LEVA"},
    # COMMODITIES & BONDS
    {"ticker": "LOIL.MI", "nome": "WTI Oil 2x Lev", "cat": "COMMODITIES"},
    {"ticker": "LWEA.MI", "nome": "Wheat 2x Lev", "cat": "COMMODITIES"},
    {"ticker": "3TYL.MI", "nome": "US 10Y 3x Long", "cat": "BONDS"},
    {"ticker": "3TYS.MI", "nome": "US 10Y 3x Short", "cat": "BONDS"},
    # INDICI & CRYPTO
    {"ticker": "^GSPC", "nome": "S&P 500 Index", "cat": "INDICI"},
    {"ticker": "^IXIC", "nome": "Nasdaq 100", "cat": "INDICI"},
    {"ticker": "^FTSEMIB.MI", "nome": "FTSE MIB Index", "cat": "INDICI"},
    {"ticker": "BTC-USD", "nome": "Bitcoin", "cat": "CRYPTO"},
    {"ticker": "ETH-USD", "nome": "Ethereum", "cat": "CRYPTO"}
]

def calcola_kama(series, period=10, fast=2, slow=30):
    s = series.ffill().bfill().values
    n = len(s)
    kama = np.zeros(n)
    kama[period-1] = s[period-1]
    
    for i in range(period, n):
        # Efficiency Ratio
        change = abs(s[i] - s[i-period])
        vol = np.sum(abs(s[i-period+1:i+1] - s[i-period:i]))
        er = change / vol if vol != 0 else 0
        # Smoothing Constant
        sc = (er * (2/(fast+1) - 2/(slow+1)) + 2/(slow+1))**2
        kama[i] = kama[i-1] + sc * (s[i] - kama[i-1])
    return kama

output_data = []

for asset in ASSETS:
    try:
        df = yf.download(asset['ticker'], period="150d", interval="1d", progress=False)
        if df.empty or len(df) < 50: continue

        # Pulizia dati per nuovo formato Yahoo
        prices = df['Close'].squeeze().ffill()
        
        kv_arr = calcola_kama(prices, 10, 5, 20)
        kl_arr = calcola_kama(prices, 10, 2, 30)
        
        last_p = float(prices.iloc[-1])
        last_kv = float(kv_arr[-1])
        last_kl = float(kl_arr[-1])
        
        status = "WAIT"
        if last_p > last_kv > last_kl: status = "BUY"
        elif last_p < last_kv < last_kl: status = "SELL"
        
        output_data.append({
            "ticker": asset['ticker'], "nome": asset['nome'], "categoria": asset['cat'],
            "price": round(last_p, 3), "kama_v": round(last_kv, 3), "kama_l": round(last_kl, 3),
            "status": status, "signal_date": datetime.now().strftime("%d/%m/%Y"),
            "history": {
                "dates": df.tail(20).index.strftime('%d/%m').tolist(),
                "prices": [round(float(x), 2) for x in prices.tail(20).values]
            }
        })
        time.sleep(0.1)
    except Exception as e:
        print(f"Errore {asset['ticker']}: {e}")

with open('data.json', 'w') as f:
    json.dump({"last_update": datetime.now().strftime("%d/%m/%Y %H:%M"), "data": output_data}, f, indent=4)
