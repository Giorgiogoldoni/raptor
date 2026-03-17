import yfinance as yf
import json
from datetime import datetime

# Aggiungi qui i tuoi ticker (Ticker Yahoo : Nome Dashboard)
asset_list = {"LQQ.PA": "LQQ", "BTC-USD": "BTC", "GDX": "GDX"}
results = []

for symbol, label in asset_list.items():
    d = yf.Ticker(symbol).history(period="1mo")
    results.append({
        "ticker": label,
        "price": d['Close'].iloc[-1],
        "kama_v": d['Close'].rolling(10).mean().iloc[-1]
    })

with open('data.json', 'w') as f:
    json.dump({"last_update": datetime.now().strftime("%d/%m %H:%M"), "data": results}, f)
