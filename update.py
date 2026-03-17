import yfinance as yf
import json
import pandas as pd
from datetime import datetime
import time

def get_kama(series, er_period=10, fast=5, slow=20):
    if len(series) <= er_period: return series
    sc_fast = 2 / (fast + 1)
    sc_slow = 2 / (slow + 1)
    abs_diff = abs(series - series.shift(1))
    rolling_diff = abs_diff.rolling(er_period).sum()
    er = (abs(series - series.shift(er_period)) / rolling_diff).fillna(0)
    sc = (er * (sc_fast - sc_slow) + sc_slow)**2
    kama = [series.iloc[0]]
    for i in range(1, len(series)):
        kama.append(kama[-1] + sc.iloc[i] * (series.iloc[i] - kama[-1]))
    return pd.Series(kama, index=series.index)

# (La tua lista di 128 asset rimane la stessa, qui abbreviata per il codice)
assets_data = [
    {"t": "LQQ", "n": "Amundi Nasdaq-100 2x", "c": "indici azionari"},
    {"t": "CL2", "n": "Amundi MSCI USA 2x", "c": "indici azionari"},
    {"t": "XS2L", "n": "Xtrackers S&P 500 2x", "c": "indici azionari"},
    # ... inserisci qui tutti i 128 ticker come nel file precedente ...
]

results = []

for asset in assets_data:
    for suffix in [".MI", ".PA", ".L", ""]:
        full_t = asset["t"] + suffix
        try:
            data = yf.Ticker(full_t).history(period="1y") # 1 anno per trovare date storiche
            if not data.empty and len(data) > 40:
                kv = get_kama(data['Close'], 10, 5, 20)
                kl = get_kama(data['Close'], 10, 2, 30)
                
                # Trova la data del segnale (backtracking)
                prices = data['Close']
                dates = data.index
                current_state = "BUY" if prices.iloc[-1] >= kv.iloc[-1] else ("SELL" if prices.iloc[-1] < kl.iloc[-1] else "NEUTRAL")
                
                signal_date = dates[-1]
                for i in range(len(prices)-2, -1, -1):
                    state_i = "BUY" if prices.iloc[i] >= kv.iloc[i] else ("SELL" if prices.iloc[i] < kl.iloc[i] else "NEUTRAL")
                    if state_i != current_state:
                        signal_date = dates[i+1]
                        break
                
                h_sub = data.tail(40)
                results.append({
                    "ticker": asset["t"], "nome": asset["n"], "categoria": asset["c"],
                    "price": round(prices.iloc[-1], 3),
                    "kama_v": round(kv.iloc[-1], 3), "kama_l": round(kl.iloc[-1], 3),
                    "status": current_state,
                    "signal_date": signal_date.strftime('%d/%m/%Y'),
                    "history": {
                        "dates": h_sub.index.strftime('%d/%m').tolist(),
                        "prices": h_sub['Close'].round(3).tolist(),
                        "kv": kv.tail(40).round(3).tolist(),
                        "kl": kl.tail(40).round(3).tolist()
                    }
                })
                break
        except: continue
    time.sleep(0.2)

output = {"last_update": datetime.now().strftime("%d/%m/%Y %H:%M:%S"), "data": results}
with open('data.json', 'w') as f:
    json.dump(output, f, indent=2)
