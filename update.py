import yfinance as yf
import pandas as pd
import numpy as np
import json
from datetime import datetime
import time

# --- LISTA COMPLETA ASSET (TUTTI I TICKER DEL TUO PROGETTO) ---
ASSETS = [
    # --- ETF LEVA & INVERSE ---
    {"ticker": "LQQ.PA", "nome": "Amundi Nasdaq-100 2x", "cat": "ETF LEVA"},
    {"ticker": "CL2.PA", "nome": "Amundi MSCI USA 2x", "cat": "ETF LEVA"},
    {"ticker": "DAXLEV.PA", "nome": "Amundi LevDax 2x", "cat": "ETF LEVA"},
    {"ticker": "XS2L.MI", "nome": "Xtrackers S&P 500 2x", "cat": "ETF LEVA"},
    {"ticker": "XSD2.MI", "nome": "Xtrackers ShortDAX x2", "cat": "ETF INVERSE"},
    {"ticker": "XSPS.MI", "nome": "Xtrackers S&P 500 Short", "cat": "ETF INVERSE"},
    {"ticker": "XSDX.MI", "nome": "Xtrackers ShortDAX Daily", "cat": "ETF INVERSE"},
    {"ticker": "5MIB.MI", "nome": "FTSE MIB 5x Long", "cat": "ETF LEVA"},

    # --- GRANITESHARES 3x LONG ---
    {"ticker": "3LNV.MI", "nome": "3x Long NVIDIA", "cat": "LEVA 3X"},
    {"ticker": "3LTS.MI", "nome": "3x Long Tesla", "cat": "LEVA 3X"},
    {"ticker": "3LMI.MI", "nome": "3x Long MicroStrategy", "cat": "LEVA 3X"},
    {"ticker": "3LCO.MI", "nome": "3x Long Coinbase", "cat": "LEVA 3X"},
    {"ticker": "3LCR.MI", "nome": "3x Long UniCredit", "cat": "LEVA 3X"},
    {"ticker": "3LFB.MI", "nome": "3x Long Meta", "cat": "LEVA 3X"},
    {"ticker": "3LAA.MI", "nome": "3x Long Alibaba", "cat": "LEVA 3X"},
    {"ticker": "3LRP.MI", "nome": "3x Long Ripple", "cat": "LEVA 3X"},
    {"ticker": "3LAD.MI", "nome": "3x Long AMD", "cat": "LEVA 3X"},

    # --- GRANITESHARES 3x SHORT ---
    {"ticker": "3SNV.MI", "nome": "3x Short NVIDIA", "cat": "LEVA 3X SHORT"},
    {"ticker": "3STS.MI", "nome": "3x Short Tesla", "cat": "LEVA 3X SHORT"},
    {"ticker": "3SMI.MI", "nome": "3x Short MicroStrategy", "cat": "LEVA 3X SHORT"},
    {"ticker": "3SFB.MI", "nome": "3x Short Meta", "cat": "LEVA 3X SHORT"},
    {"ticker": "3SCR.MI", "nome": "3x Short UniCredit", "cat": "LEVA 3X SHORT"},

    # --- COMMODITIES & BONDS LEVA ---
    {"ticker": "LOIL.MI", "nome": "WTI Oil 2x Lev", "cat": "COMMODITIES"},
    {"ticker": "LWEA.MI", "nome": "Wheat 2x Lev", "cat": "COMMODITIES"},
    {"ticker": "LSUG.MI", "nome": "Sugar 2x Lev", "cat": "COMMODITIES"},
    {"ticker": "3TYL.MI", "nome": "US 10Y Treas. 3x Long", "cat": "BONDS"},
    {"ticker": "3TYS.MI", "nome": "US 10Y Treas. 3x Short", "cat": "BONDS"},

    # --- INDICI & CRYPTO (SOTTOSTANTI) ---
    {"ticker": "^GSPC", "nome": "S&P 500 Index", "cat": "INDICI"},
    {"ticker": "^IXIC", "nome": "Nasdaq 100", "cat": "INDICI"},
    {"ticker": "^FTSEMIB.MI", "nome": "FTSE MIB Index", "cat": "INDICI"},
    {"ticker": "BTC-USD", "nome": "Bitcoin", "cat": "CRYPTO"},
    {"ticker": "ETH-USD", "nome": "Ethereum", "cat": "CRYPTO"},
    {"ticker": "SOL-USD", "nome": "Solana", "cat": "CRYPTO"}
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
        print(f"Aggiornamento: {asset['ticker']}...")
        df = yf.download(asset['ticker'], period="150d", interval="1d", progress=False)
        if df.empty or len(df) < 50: continue

        # Fix per MultiIndex Yahoo Finance
        close_series = df['Close'].squeeze()
        
        df['kama_v'] = calcola_kama(close_series, 10, 5, 20)
        df['kama_l'] = calcola_kama(close_series, 10, 2, 30)
        df = df.dropna(subset=['kama_v', 'kama_l'])

        # Logica Segnale
        last_close = close_series.iloc[-1]
        last_kv = df['kama_v'].iloc[-1]
        last_kl = df['kama_l'].iloc[-1]
        
        status = "WAIT"
        if last_close > last_kv > last_kl: status = "BUY"
        elif last_close < last_kv < last_kl: status = "SELL"

        # Trova data inizio segnale
        df['status_tmp'] = "WAIT"
        df.loc[(df['Close'].squeeze() > df['kama_v']) & (df['kama_v'] > df['kama_l']), 'status_tmp'] = "BUY"
        df.loc[(df['Close'].squeeze() < df['kama_v']) & (df['kama_v'] < df['kama_l']), 'status_tmp'] = "SELL"
        
        s_date = df.index[-1]
        for i in range(len(df)-2, -1, -1):
            if df['status_tmp'].iloc[i] != status:
                s_date = df.index[i+1]
                break

        output_data.append({
            "ticker": asset['ticker'],
            "nome": asset['nome'],
            "categoria": asset['cat'],
            "price": float(last_close),
            "kama_v": float(last_kv),
            "kama_l": float(last_kl),
            "status": status,
            "signal_date": s_date.strftime('%d/%m/%Y'),
            "history": {
                "dates": df.tail(30).index.strftime('%d/%m').tolist(),
                "prices": [float(x) for x in df['Close'].tail(30).values.flatten()]
            }
        })
        time.sleep(0.2)
    except Exception as e:
        print(f"Errore su {asset['ticker']}: {e}")

final_json = {
    "last_update": datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
    "data": output_data
}

with open('data.json', 'w') as f:
    json.dump(final_json, f, indent=4)
