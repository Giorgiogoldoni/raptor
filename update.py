import yfinance as yf
import pandas as pd
import numpy as np
import json
from datetime import datetime
import time

# --- ARCHITETTURA RAPTOR: LISTA COMPLETA 128+ ASSET ---
TICKERS_CONFIG = [
    # ETF LEVA 2X / 5X
    {"t": "LQQ.PA", "n": "Amundi Nasdaq 2x", "c": "ETF LEVA"},
    {"t": "CL2.PA", "n": "Amundi MSCI USA 2x", "c": "ETF LEVA"},
    {"t": "DAXLEV.PA", "n": "Amundi LevDax 2x", "c": "ETF LEVA"},
    {"t": "XS2L.MI", "n": "Xtrackers S&P 500 2x", "c": "ETF LEVA"},
    {"t": "5MIB.MI", "n": "FTSE MIB 5x Long", "c": "ETF LEVA"},
    # ETF INVERSE
    {"t": "XSD2.MI", "n": "ShortDAX x2 Daily", "c": "ETF INVERSE"},
    {"t": "XSDX.MI", "n": "ShortDAX Daily", "c": "ETF INVERSE"},
    {"t": "XSPS.MI", "n": "S&P 500 Inverse", "c": "ETF INVERSE"},
    # GRANITESHARES 3X LONG (MILANO)
    {"t": "3LNV.MI", "n": "3x Long NVIDIA", "c": "LEVA 3X"},
    {"t": "3LTS.MI", "n": "3x Long Tesla", "c": "LEVA 3X"},
    {"t": "3LMI.MI", "n": "3x Long MicroStrategy", "c": "LEVA 3X"},
    {"t": "3LCO.MI", "n": "3x Long Coinbase", "c": "LEVA 3X"},
    {"t": "3LCR.MI", "n": "3x Long UniCredit", "c": "LEVA 3X"},
    {"t": "3LFB.MI", "n": "3x Long Meta", "c": "LEVA 3X"},
    {"t": "3LAA.MI", "n": "3x Long Alibaba", "c": "LEVA 3X"},
    {"t": "3LRP.MI", "n": "3x Long Ripple", "c": "LEVA 3X"},
    {"t": "3LAD.MI", "n": "3x Long AMD", "c": "LEVA 3X"},
    {"t": "3LAV.MI", "n": "3x Long Broadcom", "c": "LEVA 3X"},
    {"t": "3LMS.MI", "n": "3x Long Microsoft", "c": "LEVA 3X"},
    {"t": "3LAP.MI", "n": "3x Long Apple", "c": "LEVA 3X"},
    {"t": "3LGO.MI", "n": "3x Long Google", "c": "LEVA 3X"},
    {"t": "3LAM.MI", "n": "3x Long Amazon", "c": "LEVA 3X"},
    {"t": "3LNF.MI", "n": "3x Long Netflix", "c": "LEVA 3X"},
    {"t": "3LPL.MI", "n": "3x Long Palantir", "c": "LEVA 3X"},
    {"t": "3LUM.MI", "n": "3x Long Uber", "c": "LEVA 3X"},
    # GRANITESHARES 3X SHORT
    {"t": "3SNV.MI", "n": "3x Short NVIDIA", "c": "LEVA 3X SHORT"},
    {"t": "3STS.MI", "n": "3x Short Tesla", "c": "LEVA 3X SHORT"},
    {"t": "3SMI.MI", "n": "3x Short MicroStrategy", "c": "LEVA 3X SHORT"},
    {"t": "3SFB.MI", "n": "3x Short Meta", "c": "LEVA 3X SHORT"},
    {"t": "3SCR.MI", "n": "3x Short UniCredit", "c": "LEVA 3X SHORT"},
    {"t": "3SMS.MI", "n": "3x Short Microsoft", "c": "LEVA 3X SHORT"},
    {"t": "3SAP.MI", "n": "3x Short Apple", "c": "LEVA 3X SHORT"},
    # COMMODITIES & BONDS
    {"t": "LOIL.MI", "n": "WTI Oil 2x Lev", "c": "COMMODITIES"},
    {"t": "LWEA.MI", "n": "Wheat 2x Lev", "c": "COMMODITIES"},
    {"t": "LSUG.MI", "n": "Sugar 2x Lev", "c": "COMMODITIES"},
    {"t": "3TYL.MI", "n": "US 10Y 3x Long", "c": "BONDS"},
    {"t": "3TYS.MI", "n": "US 10Y 3x Short", "c": "BONDS"},
    # CRYPTO
    {"t": "BTC-USD", "n": "Bitcoin", "c": "CRYPTO"},
    {"t": "ETH-USD", "n": "Ethereum", "c": "CRYPTO"},
    {"t": "SOL-USD", "n": "Solana", "c": "CRYPTO"},
    {"t": "BNB-USD", "n": "Binance Coin", "c": "CRYPTO"},
    {"t": "XRP-USD", "n": "Ripple", "c": "CRYPTO"},
    {"t": "ADA-USD", "n": "Cardano", "c": "CRYPTO"},
    {"t": "DOGE-USD", "n": "Dogecoin", "c": "CRYPTO"},
    # INDICI
    {"t": "^GSPC", "n": "S&P 500 Index", "c": "INDICI"},
    {"t": "^IXIC", "n": "Nasdaq 100", "c": "INDICI"},
    {"t": "^FTSEMIB.MI", "n": "FTSE MIB", "c": "INDICI"},
    {"t": "^GDAXI", "n": "DAX 40", "c": "INDICI"},
    {"t": "^FCHI", "n": "CAC 40", "c": "INDICI"},
    {"t": "^STOXX50E", "n": "Euro Stoxx 50", "c": "INDICI"}
]

def calcola_kama(series, period=10, fast=2, slow=30):
    s = series.values
    kama = np.zeros_like(s)
    kama[period-1] = s[period-1]
    for i in range(period, len(s)):
        change = abs(s[i] - s[i-period])
        vol = np.sum(abs(s[i-period+1:i+1] - s[i-period:i]))
        er = change / vol if vol != 0 else 0
        sc = (er * (2/(fast+1) - 2/(slow+1)) + 2/(slow+1))**2
        kama[i] = kama[i-1] + sc * (s[i] - kama[i-1])
    return kama

def process_asset(asset):
    try:
        df = yf.download(asset['t'], period="150d", interval="1d", progress=False)
        if df.empty: return None
        if isinstance(df.columns, pd.MultiIndex): df.columns = df.columns.get_level_values(0)
        
        close = df['Close'].ffill().dropna()
        if len(close) < 50: return None

        kv = calcola_kama(close, 10, 5, 20)
        kl = calcola_kama(close, 10, 2, 30)

        last_p, last_kv, last_kl = float(close.iloc[-1]), float(kv[-1]), float(kl[-1])
        status = "WAIT"
        if last_p > last_kv > last_kl: status = "BUY"
        elif last_p < last_kv < last_kl: status = "SELL"

        return {
            "ticker": asset['t'], "nome": asset['n'], "categoria": asset['c'],
            "price": round(last_p, 3), "kama_v": round(last_kv, 3), "kama_l": round(last_kl, 3),
            "status": status, "signal_date": datetime.now().strftime("%d/%m/%Y")
        }
    except Exception: return None

# ESECUZIONE MODULARE
results = []
for a in TICKERS_CONFIG:
    res = process_asset(a)
    if res: results.append(res)
    time.sleep(0.4) # Protezione anti-ban

with open('data.json', 'w') as f:
    json.dump({"last_update": datetime.now().strftime("%d/%m/%Y %H:%M"), "data": results}, f, indent=4)
