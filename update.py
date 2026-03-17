import yfinance as yf
import pandas as pd
import numpy as np
import json
from datetime import datetime
import time

# --- LISTA COMPLETA DEI TICKER (RAPTOR LEVA 3 & ETF) ---
ASSETS = [
    # ETF LEVA & INVERSE (Mercato Parigi e Milano)
    {"ticker": "LQQ.PA", "nome": "Nasdaq 2x Lev", "cat": "ETF LEVA"},
    {"ticker": "CL2.PA", "nome": "MSCI USA 2x Lev", "cat": "ETF LEVA"},
    {"ticker": "DAXLEV.PA", "nome": "LevDax 2x", "cat": "ETF LEVA"},
    {"ticker": "XS2L.MI", "nome": "S&P 500 2x Lev", "cat": "ETF LEVA"},
    {"ticker": "XSD2.MI", "nome": "ShortDAX x2 Daily", "cat": "ETF INVERSE"},
    {"ticker": "XSPS.MI", "nome": "S&P 500 Inverse", "cat": "ETF INVERSE"},
    {"ticker": "5MIB.MI", "nome": "FTSE MIB 5x Long", "cat": "ETF LEVA"},
    
    # GRANITESHARES 3X (Milano)
    {"ticker": "3LNV.MI", "nome": "3x Long NVIDIA", "cat": "GRANITESHARES"},
    {"ticker": "3LTS.MI", "nome": "3x Long Tesla", "cat": "GRANITESHARES"},
    {"ticker": "3LMI.MI", "nome": "3x Long MicroStrategy", "cat": "GRANITESHARES"},
    {"ticker": "3LCO.MI", "nome": "3x Long Coinbase", "cat": "GRANITESHARES"},
    {"ticker": "3LCR.MI", "nome": "3x Long UniCredit", "cat": "GRANITESHARES"},
    {"ticker": "3SNV.MI", "nome": "3x Short NVIDIA", "cat": "GRANITESHARES SHORT"},
    {"ticker": "3STS.MI", "nome": "3x Short Tesla", "cat": "GRANITESHARES SHORT"},

    # COMMODITIES & BONDS
    {"ticker": "LOIL.MI", "nome": "WTI Oil 2x Lev", "cat": "COMMODITIES"},
    {"ticker": "3TYL.MI", "nome": "US 10Y 3x Long", "cat": "BONDS"},
    {"ticker": "3TYS.MI", "nome": "US 10Y 3x Short", "cat": "BONDS"},

    # INDICI & CRYPTO
    {"ticker": "^GSPC", "nome": "S&P 500 Index", "cat": "INDICI"},
    {"ticker": "^IXIC", "nome": "Nasdaq 100", "cat": "INDICI"},
    {"ticker": "^FTSEMIB.MI", "nome": "FTSE MIB", "cat": "INDICI"},
    {"ticker": "BTC-USD", "nome": "Bitcoin", "cat": "CRYPTO"},
    {"ticker": "ETH-USD", "nome": "Ethereum", "cat": "CRYPTO"}
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

def get_signal_info(df):
    df['status'] = 'WAIT'
    df.loc[(df['Close'] > df['kama_v']) & (df['kama_v'] > df['kama_l']), 'status'] = 'BUY'
    df.loc[(df['Close'] < df['kama_v']) & (df['kama_v'] < df['kama_l']), 'status'] = 'SELL'
    
    current_status = df['status'].iloc[-1]
    signal_date = df.index[-1]
    for i in range(len(df)-2, -1, -1):
        if df['status'].iloc[i] != current_status:
            signal_date = df.index[i+1]
            break
    return current_status, signal_date.strftime('%d/%m/%Y')

output_data = []

for asset in ASSETS:
    try:
        print(f"Elaborazione {asset['ticker']}...")
        df = yf.download(asset['ticker'], period="150d", interval="1d", progress=False)
        
        if df.empty or len(df) < 50:
            continue

        # FIX FONDAMENTALE: squeeze() per gestire il nuovo formato Yahoo Finance
        close_series = df['Close'].squeeze()
        
        df['kama_v'] = calcola_kama(close_series, 10, 5, 20)
        df['kama_l'] = calcola_kama(close_series, 10, 2, 30)
        
        df = df.dropna(subset=['kama_v', 'kama_l'])
        status, s_date = get_signal_info(df)
        
        history_df = df.tail(20)
        
        output_data.append({
            "ticker": asset['ticker'],
            "nome": asset['nome'],
            "categoria": asset['cat'],
            "price": round(float(df['Close'].iloc[-1]), 4),
            "kama_v": round(float(df['kama_v'].iloc[-1]), 4),
            "kama_l": round(float(df['kama_l'].iloc[-1]), 4),
            "status": status,
            "signal_date": s_date,
            "history": {
                "dates": history_df.index.strftime('%d/%m').tolist(),
                "prices": [round(float(x), 2) for x in history_df['Close'].values.flatten()]
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

print(f"Aggiornamento completato! Asset salvati: {len(output_data)}")
