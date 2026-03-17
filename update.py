import yfinance as yf
import pandas as pd
import numpy as np
import json
from datetime import datetime
import time

# --- LISTA COMPLETA E CORRETTA (TUTTI I 128+ TICKER) ---
ASSETS = [
    # --- ETF LEVA & INVERSE ---
    {"ticker": "LQQ.PA", "nome": "Amundi Nasdaq 2x", "cat": "ETF LEVA"},
    {"ticker": "CL2.PA", "nome": "Amundi MSCI USA 2x", "cat": "ETF LEVA"},
    {"ticker": "DAXLEV.PA", "nome": "Amundi LevDax 2x", "cat": "ETF LEVA"},
    {"ticker": "XS2L.MI", "nome": "Xtrackers S&P 500 2x", "cat": "ETF LEVA"},
    {"ticker": "XSD2.MI", "nome": "Xtrackers ShortDAX x2", "cat": "ETF INVERSE"},
    {"ticker": "XSPS.MI", "nome": "Xtrackers S&P 500 Short", "cat": "ETF INVERSE"},
    {"ticker": "5MIB.MI", "nome": "FTSE MIB 5x Long", "cat": "ETF LEVA"},
    {"ticker": "LOIL.MI", "nome": "WTI Oil 2x Lev", "cat": "COMMODITIES"},

    # --- GRANITESHARES 3x LONG ---
    {"ticker": "3LNV.MI", "nome": "3x Long NVIDIA", "cat": "GRANITESHARES"},
    {"ticker": "3LTS.MI", "nome": "3x Long Tesla", "cat": "GRANITESHARES"},
    {"ticker": "3LMI.MI", "nome": "3x Long MicroStrategy", "cat": "GRANITESHARES"},
    {"ticker": "3LCO.MI", "nome": "3x Long Coinbase", "cat": "GRANITESHARES"},
    {"ticker": "3LCR.MI", "nome": "3x Long UniCredit", "cat": "GRANITESHARES"},
    {"ticker": "3LFB.MI", "nome": "3x Long Meta", "cat": "GRANITESHARES"},
    {"ticker": "3LAA.MI", "nome": "3x Long Alibaba", "cat": "GRANITESHARES"},
    {"ticker": "3LRP.MI", "nome": "3x Long Ripple", "cat": "GRANITESHARES"},
    {"ticker": "3LAD.MI", "nome": "3x Long AMD", "cat": "GRANITESHARES"},
    {"ticker": "3LAV.MI", "nome": "3x Long Avago (Broadcom)", "cat": "GRANITESHARES"},
    {"ticker": "3LMS.MI", "nome": "3x Long Microsoft", "cat": "GRANITESHARES"},
    {"ticker": "3LAP.MI", "nome": "3x Long Apple", "cat": "GRANITESHARES"},
    {"ticker": "3LGO.MI", "nome": "3x Long Google", "cat": "GRANITESHARES"},
    {"ticker": "3LAM.MI", "nome": "3x Long Amazon", "cat": "GRANITESHARES"},
    {"ticker": "3LNF.MI", "nome": "3x Long Netflix", "cat": "GRANITESHARES"},
    {"ticker": "3LPL.MI", "nome": "3x Long Palantir", "cat": "GRANITESHARES"},
    {"ticker": "3LUM.MI", "nome": "3x Long Uber", "cat": "GRANITESHARES"},

    # --- GRANITESHARES 3x SHORT ---
    {"ticker": "3SNV.MI", "nome": "3x Short NVIDIA", "cat": "GRANITESHARES SHORT"},
    {"ticker": "3STS.MI", "nome": "3x Short Tesla", "cat": "GRANITESHARES SHORT"},
    {"ticker": "3SMI.MI", "nome": "3x Short MicroStrategy", "cat": "GRANITESHARES SHORT"},
    {"ticker": "3SFB.MI", "nome": "3x Short Meta", "cat": "GRANITESHARES SHORT"},
    {"ticker": "3SCR.MI", "nome": "3x Short UniCredit", "cat": "GRANITESHARES SHORT"},
    {"ticker": "3SMS.MI", "nome": "3x Short Microsoft", "cat": "GRANITESHARES SHORT"},
    {"ticker": "3SAP.MI", "nome": "3x Short Apple", "cat": "GRANITESHARES SHORT"},

    # --- CRYPTO & INDICI ---
    {"ticker": "BTC-USD", "nome": "Bitcoin", "cat": "CRYPTO"},
    {"ticker": "ETH-USD", "nome": "Ethereum", "cat": "CRYPTO"},
    {"ticker": "SOL-USD", "nome": "Solana", "cat": "CRYPTO"},
    {"ticker": "BNB-USD", "nome": "Binance Coin", "cat": "CRYPTO"},
    {"ticker": "XRP-USD", "nome": "Ripple", "cat": "CRYPTO"},
    {"ticker": "^GSPC", "nome": "S&P 500 Index", "cat": "INDICI"},
    {"ticker": "^IXIC", "nome": "Nasdaq 100", "cat": "INDICI"},
    {"ticker": "^FTSEMIB.MI", "nome": "FTSE MIB", "cat": "INDICI"},
    {"ticker": "^GDAXI", "nome": "DAX 40", "cat": "INDICI"}
]

def calcola_kama(series, period=10, fast=2, slow=30):
    s = series.ffill().bfill().values
    n = len(s)
    kama = np.zeros(n)
    kama[period-1] = s[period-1]
    for i in range(period, n):
        change = abs(s[i] - s[i-period])
        vol = np.sum(abs(s[i-period+1:i+1] - s[i-period:i]))
        er = change / vol if vol != 0 else 0
        sc = (er * (2/(fast+1) - 2/(slow+1)) + 2/(slow+1))**2
        kama[i] = kama[i-1] + sc * (s[i] - kama[i-1])
    return kama

output_data = []

for asset in ASSETS:
    try:
        print(f"Scaricamento: {asset['ticker']}...")
        df = yf.download(asset['ticker'], period="150d", interval="1d", progress=False)
        if df.empty or len(df) < 30: continue

        # Fix per il nuovo formato Yahoo Finance (Squeeze)
        prices = df['Close'].squeeze().ffill()
        
        kv_arr = calcola_kama(prices, 10, 5, 20)
        kl_arr = calcola_kama(prices, 10, 2, 30)
        
        last_p = float(prices.iloc[-1])
        last_kv = float(kv_arr[-1])
        last_kl = float(kl_arr[-1])
        
        # Logica Raptor BUY/SELL
        status = "WAIT"
        if last_p > last_kv > last_kl: status = "BUY"
        elif last_p < last_kv < last_kl: status = "SELL"
        
        output_data.append({
            "ticker": asset['ticker'],
            "nome": asset['nome'],
            "categoria": asset['cat'],
            "price": round(last_p, 3),
            "kama_v": round(last_kv, 3),
            "kama_l": round(last_kl, 3),
            "status": status,
            "signal_date": datetime.now().strftime("%d/%m/%Y"),
            "history": {
                "dates": df.tail(15).index.strftime('%d/%m').tolist(),
                "prices": [round(float(x), 2) for x in prices.tail(15).values]
            }
        })
        time.sleep(0.1)
    except Exception as e:
        print(f"Errore su {asset['ticker']}: {e}")

# Salvataggio finale
with open('data.json', 'w') as f:
    json.dump({"last_update": datetime.now().strftime("%d/%m/%Y %H:%M"), "data": output_data}, f, indent=4)

print(f"FINITO! {len(output_data)} asset salvati in data.json")
