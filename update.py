import yfinance as yf
import pandas as pd
import numpy as np
import json
from datetime import datetime
import time

# --- CONFIGURAZIONE ASSET (ESTRATTI DAL TUO FILE E INTEGRATI) ---
ASSETS = [
    # --- INDICI E ETF LEVA (Dal tuo CSV) ---
    {"ticker": "LQQ.PA", "nome": "Nasdaq-100 2x Leveraged", "cat": "ETF LEVA"},
    {"ticker": "CL2.PA", "nome": "MSCI USA 2x Leveraged", "cat": "ETF LEVA"},
    {"ticker": "DAXLEV.PA", "nome": "LevDax 2x Daily", "cat": "ETF LEVA"},
    {"ticker": "XS2L.MI", "nome": "S&P 500 2x Leveraged", "cat": "ETF LEVA"},
    {"ticker": "5MIB.MI", "nome": "FTSE MIB 5x Long", "cat": "ETF LEVA"},
    {"ticker": "XSD2.MI", "nome": "ShortDAX x2 Daily", "cat": "ETF INVERSE"},
    {"ticker": "XSPS.MI", "nome": "S&P 500 Inverse", "cat": "ETF INVERSE"},
    
    # --- GRANITESHARES 3x (Dal tuo CSV) ---
    {"ticker": "3LNV.MI", "nome": "3x Long NVIDIA", "cat": "LEVA 3X"},
    {"ticker": "3LTS.MI", "nome": "3x Long Tesla", "cat": "LEVA 3X"},
    {"ticker": "3LCR.MI", "nome": "3x Long UniCredit", "cat": "LEVA 3X"},
    {"ticker": "3LMI.MI", "nome": "3x Long MicroStrategy", "cat": "LEVA 3X"},
    {"ticker": "3LCO.MI", "nome": "3x Long Coinbase", "cat": "LEVA 3X"},
    {"ticker": "3SNV.MI", "nome": "3x Short NVIDIA", "cat": "LEVA 3X"},
    {"ticker": "3STS.MI", "nome": "3x Short Tesla", "cat": "LEVA 3X"},

    # --- INDICI PRINCIPALI ---
    {"ticker": "^GSPC", "nome": "S&P 500 Index", "cat": "INDICI"},
    {"ticker": "^IXIC", "nome": "Nasdaq 100", "cat": "INDICI"},
    {"ticker": "^FTSEMIB.MI", "nome": "FTSE MIB", "cat": "INDICI"},
    {"ticker": "^GDAXI", "nome": "DAX 40", "cat": "INDICI"},

    # --- FOREX ---
    {"ticker": "EURUSD=X", "nome": "EUR/USD", "cat": "FOREX"},
    {"ticker": "GBPUSD=X", "nome": "GBP/USD", "cat": "FOREX"},
    {"ticker": "USDJPY=X", "nome": "USD/JPY", "cat": "FOREX"},

    # --- CRYPTO ---
    {"ticker": "BTC-USD", "nome": "Bitcoin", "cat": "CRYPTO"},
    {"ticker": "ETH-USD", "nome": "Ethereum", "cat": "CRYPTO"},
    {"ticker": "SOL-USD", "nome": "Solana", "cat": "CRYPTO"},
    
    # --- COMMODITIES ---
    {"ticker": "GC=F", "nome": "Oro (Gold)", "cat": "COMMODITIES"},
    {"ticker": "CL=F", "nome": "Crude Oil", "cat": "COMMODITIES"},
    {"ticker": "LOIL.MI", "nome": "WTI Oil 2x Leveraged", "cat": "COMMODITIES"}
]

# Nota: Puoi aggiungere gli altri ticker dal CSV seguendo lo schema sopra.

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
    # Regola Raptor: Prezzo > KV > KL = BUY | Prezzo < KV < KL = SELL
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

print(f"Inizio aggiornamento Raptor per {len(ASSETS)} asset...")

for asset in ASSETS:
    try:
        df = yf.download(asset['ticker'], period="150d", interval="1d", progress=False)
        
        if df.empty or len(df) < 50:
            print(f"Saltato {asset['ticker']}: Dati insufficienti.")
            continue

        # Pulizia MultiIndex e conversione in serie piana
        close_series = df['Close'].squeeze()
        
        df['kama_v'] = calcola_kama(close_series, 10, 5, 20)
        df['kama_l'] = calcola_kama(close_series, 10, 2, 30)
        
        df = df.dropna(subset=['kama_v', 'kama_l'])
        status, s_date = get_signal_info(df)
        history_df = df.tail(45)
        
        output_data.append({
            "ticker": asset['ticker'],
            "nome": asset['nome'],
            "categoria": asset['cat'],
            "price": float(df['Close'].iloc[-1]),
            "kama_v": float(df['kama_v'].iloc[-1]),
            "kama_l": float(df['kama_l'].iloc[-1]),
            "status": status,
            "signal_date": s_date,
            "history": {
                "dates": history_df.index.strftime('%d/%m').tolist(),
                "prices": [float(x) for x in history_df['Close'].values.flatten()],
                "kv": [float(x) for x in history_df['kama_v'].values.flatten()],
                "kl": [float(x) for x in history_df['kama_l'].values.flatten()]
            }
        })
        print(f"OK: {asset['ticker']} -> {status}")
        time.sleep(0.2) # Protezione anti-ban
    except Exception as e:
        print(f"ERRORE su {asset['ticker']}: {e}")

# Creazione JSON finale
final_json = {
    "last_update": datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
    "data": output_data
}

with open('data.json', 'w') as f:
    json.dump(final_json, f, indent=4)

print(f"Aggiornamento completato! {len(output_data)} asset salvati.")
