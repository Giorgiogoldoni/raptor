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
    er = abs(series - series.shift(er_period)) / rolling_diff
    er = er.fillna(0)
    sc = (er * (sc_fast - sc_slow) + sc_slow)**2
    kama = [series.iloc[0]]
    for i in range(1, len(series)):
        kama.append(kama[-1] + sc.iloc[i] * (series.iloc[i] - kama[-1]))
    return pd.Series(kama, index=series.index)

# LISTA DEFINITIVA 128 ASSET ESTRATTI DAL TUO CSV
assets_data = [
    {"t": "LQQ", "n": "Amundi Nasdaq-100 2x", "c": "indici azionari"},
    {"t": "CL2", "n": "Amundi MSCI USA 2x", "c": "indici azionari"},
    {"t": "XS2L", "n": "Xtrackers S&P 500 2x", "c": "indici azionari"},
    {"t": "LBUL", "n": "Gold 2x Daily", "c": "materie"},
    {"t": "QQQ3", "n": "Nasdaq 100 3x Daily", "c": "indici azionari"},
    {"t": "3LGO", "n": "Gold 3x Daily", "c": "materie"},
    {"t": "3LIL", "n": "Oil 3x Daily", "c": "materie"},
    {"t": "3LSI", "n": "Silver 3x Daily", "c": "materie"},
    {"t": "3UP", "n": "S&P 500 3x Daily", "c": "indici azionari"},
    {"t": "3BRA", "n": "Brent 3x Daily", "c": "materie"},
    {"t": "3LSU", "n": "Sugar 3x Daily", "c": "materie"},
    {"t": "3LCO", "n": "Copper 3x Daily", "c": "materie"},
    {"t": "3LNI", "n": "Nickel 3x Daily", "c": "materie"},
    {"t": "3LCP", "n": "Coffee 3x Daily", "c": "materie"},
    {"t": "3LWE", "n": "Wheat 3x Daily", "c": "materie"},
    {"t": "3LCOR", "n": "Corn 3x Daily", "c": "materie"},
    {"t": "3LNA", "n": "Natural Gas 3x Daily", "c": "materie"},
    {"t": "3BTY", "n": "Treasury 7-10Y 3x Short", "c": "Bond"},
    {"t": "2TRV", "n": "Travel & Leisure 2x", "c": "settori"},
    {"t": "2CAR", "n": "Automobiles 2x", "c": "settori"},
    {"t": "3EDS", "n": "Aerospace & Defense 3x Short", "c": "settori"},
    {"t": "3EMS", "n": "Emerging Markets 3x Short", "c": "indici azionari"},
    {"t": "3UBS", "n": "Bund 30Y 3x Short", "c": "Bond"},
    {"t": "3BUS", "n": "Bund 10Y 3x Short", "c": "Bond"},
    {"t": "3UBR", "n": "Uber 3x Long", "c": "Azioni"},
    {"t": "3XOM", "n": "Exxon 3x Long", "c": "Azioni"},
    {"t": "3AMZ", "n": "Amazon 3x Long", "c": "Azioni"},
    {"t": "3APL", "n": "Apple 3x Long", "c": "Azioni"},
    {"t": "3MSF", "n": "Microsoft 3x Long", "c": "Azioni"},
    {"t": "3TSL", "n": "Tesla 3x Long", "c": "Azioni"},
    {"t": "3GOO", "n": "Alphabet 3x Long", "c": "Azioni"},
    {"t": "3MET", "n": "Meta 3x Long", "c": "Azioni"},
    {"t": "3NVD", "n": "Nvidia 3x Long", "c": "Azioni"},
    {"t": "3NFL", "n": "Netflix 3x Long", "c": "Azioni"},
    {"t": "3ALB", "n": "Alibaba 3x Long", "c": "Azioni"},
    {"t": "3BA", "n": "Boeing 3x Long", "c": "Azioni"},
    {"t": "3DIS", "n": "Disney 3x Long", "c": "Azioni"},
    {"t": "3PYP", "n": "PayPal 3x Long", "c": "Azioni"},
    {"t": "3V", "n": "Visa 3x Long", "c": "Azioni"},
    {"t": "3MA", "n": "Mastercard 3x Long", "c": "Azioni"},
    {"t": "3JPM", "n": "JPMorgan 3x Long", "c": "Azioni"},
    {"t": "3GS", "n": "Goldman Sachs 3x Long", "c": "Azioni"},
    {"t": "3C", "n": "Citigroup 3x Long", "c": "Azioni"},
    {"t": "3WMT", "n": "Walmart 3x Long", "c": "Azioni"},
    {"t": "3PEP", "n": "PepsiCo 3x Long", "c": "Azioni"},
    {"t": "3KO", "n": "Coca-Cola 3x Long", "c": "Azioni"},
    {"t": "3MCD", "n": "McDonald's 3x Long", "c": "Azioni"},
    {"t": "3SBU", "n": "Starbucks 3x Long", "c": "Azioni"},
    {"t": "3NKE", "n": "Nike 3x Long", "c": "Azioni"},
    {"t": "3INTC", "n": "Intel 3x Long", "c": "Azioni"},
    {"t": "3AMD", "n": "AMD 3x Long", "c": "Azioni"},
    {"t": "3CRM", "n": "Salesforce 3x Long", "c": "Azioni"},
    {"t": "3ORC", "n": "Oracle 3x Long", "c": "Azioni"},
    {"t": "3IBM", "n": "IBM 3x Long", "c": "Azioni"},
    {"t": "3BAH", "n": "Berkshire 3x Long", "c": "Azioni"},
    {"t": "3CAT", "n": "Caterpillar 3x Long", "c": "Azioni"},
    {"t": "3GE", "n": "GE 3x Long", "c": "Azioni"},
    {"t": "3UPS", "n": "UPS 3x Long", "c": "Azioni"},
    {"t": "3FDX", "n": "FedEx 3x Long", "c": "Azioni"},
    {"t": "3PFE", "n": "Pfizer 3x Long", "c": "Azioni"},
    {"t": "3MRK", "n": "Merck 3x Long", "c": "Azioni"},
    {"t": "3JNJ", "n": "J&J 3x Long", "c": "Azioni"},
    {"t": "3LLY", "n": "Eli Lilly 3x Long", "c": "Azioni"},
    {"t": "3UNH", "n": "UnitedHealth 3x Long", "c": "Azioni"},
    {"t": "3COST", "n": "Costco 3x Long", "c": "Azioni"},
    {"t": "3HD", "n": "Home Depot 3x Long", "c": "Azioni"},
    {"t": "3ABV", "n": "AbbVie 3x Long", "c": "Azioni"},
    {"t": "3TMO", "n": "Thermo Fisher 3x Long", "c": "Azioni"},
    {"t": "3ACN", "n": "Accenture 3x Long", "c": "Azioni"},
    {"t": "3ADBE", "n": "Adobe 3x Long", "c": "Azioni"},
    {"t": "3TXN", "n": "Texas Instruments 3x Long", "c": "Azioni"},
    {"t": "3AVGO", "n": "Broadcom 3x Long", "c": "Azioni"},
    {"t": "3QCOM", "n": "Qualcomm 3x Long", "c": "Azioni"},
    {"t": "3HON", "n": "Honeywell 3x Long", "c": "Azioni"},
    {"t": "3LMT", "n": "Lockheed 3x Long", "c": "Azioni"},
    {"t": "3UPS", "n": "UPS 3x Long", "c": "Azioni"},
    {"t": "3DE", "n": "John Deere 3x Long", "c": "Azioni"},
    {"t": "3BX", "n": "Blackstone 3x Long", "c": "Azioni"},
    {"t": "3MS", "n": "Morgan Stanley 3x Long", "c": "Azioni"},
    {"t": "3BLK", "n": "BlackRock 3x Long", "c": "Azioni"},
    {"t": "3SCHW", "n": "Schwab 3x Long", "c": "Azioni"},
    {"t": "3AXP", "n": "Amex 3x Long", "c": "Azioni"},
    {"t": "3CVS", "n": "CVS Health 3x Long", "c": "Azioni"},
    {"t": "3LOW", "n": "Lowe's 3x Long", "c": "Azioni"},
    {"t": "3MDLZ", "n": "Mondelez 3x Long", "c": "Azioni"},
    {"t": "3ABNB", "n": "Airbnb 3x Long", "c": "Azioni"},
    {"t": "3UBER", "n": "Uber 3x Long", "c": "Azioni"},
    {"t": "3PTON", "n": "Peloton 3x Long", "c": "Azioni"},
    {"t": "3DASH", "n": "DoorDash 3x Long", "c": "Azioni"},
    {"t": "3COIN", "n": "Coinbase 3x Long", "c": "Azioni"},
    {"t": "3PLTR", "n": "Palantir 3x Long", "c": "Azioni"},
    {"t": "3SQ", "n": "Block 3x Long", "c": "Azioni"},
    {"t": "3SNOW", "n": "Snowflake 3x Long", "c": "Azioni"},
    {"t": "3SHOP", "n": "Shopify 3x Long", "c": "Azioni"},
    {"t": "3NET", "n": "Cloudflare 3x Long", "c": "Azioni"},
    {"t": "3ZS", "n": "Zscaler 3x Long", "c": "Azioni"},
    {"t": "3OKTA", "n": "Okta 3x Long", "c": "Azioni"},
    {"t": "3MDB", "n": "MongoDB 3x Long", "c": "Azioni"},
    {"t": "3DDOG", "n": "Datadog 3x Long", "c": "Azioni"},
    {"t": "3TEAM", "n": "Atlassian 3x Long", "c": "Azioni"},
    {"t": "3CRWD", "n": "Crowdstrike 3x Long", "c": "Azioni"},
    {"t": "3ZM", "n": "Zoom 3x Long", "c": "Azioni"},
    {"t": "3DOCU", "n": "DocuSign 3x Long", "c": "Azioni"},
    {"t": "3TWLO", "n": "Twilio 3x Long", "c": "Azioni"},
    {"t": "3ROKU", "n": "Roku 3x Long", "c": "Azioni"},
    {"t": "3SNAP", "n": "Snap 3x Long", "c": "Azioni"},
    {"t": "3PINS", "n": "Pinterest 3x Long", "c": "Azioni"},
    {"t": "3TTD", "n": "The Trade Desk 3x Long", "c": "Azioni"},
    {"t": "3SPOT", "n": "Spotify 3x Long", "c": "Azioni"},
    {"t": "3U", "n": "Unity 3x Long", "c": "Azioni"},
    {"t": "3DKNG", "n": "DraftKings 3x Long", "c": "Azioni"},
    {"t": "3AFRM", "n": "Affirm 3x Long", "c": "Azioni"},
    {"t": "3GME", "n": "GameStop 3x Long", "c": "Azioni"},
    {"t": "3AMC", "n": "AMC 3x Long", "c": "Azioni"},
    {"t": "3RIVN", "n": "Rivian 3x Long", "c": "Azioni"},
    {"t": "3LCID", "n": "Lucid 3x Long", "c": "Azioni"},
    {"t": "3NIO", "n": "Nio 3x Long", "c": "Azioni"},
    {"t": "3BABA", "n": "Alibaba 3x Long", "c": "Azioni"},
    {"t": "3JD", "n": "JD.com 3x Long", "c": "Azioni"},
    {"t": "3BIDU", "n": "Baidu 3x Long", "c": "Azioni"},
    {"t": "3PDD", "n": "Pinduoduo 3x Long", "c": "Azioni"},
    {"t": "3XPEV", "n": "Xpeng 3x Long", "c": "Azioni"},
    {"t": "3LI", "n": "Li Auto 3x Long", "c": "Azioni"},
    {"t": "3KWEB", "n": "China Internet 3x Long", "c": "Azioni"},
    {"t": "BTC-USD", "n": "Bitcoin", "c": "crypto"},
    {"t": "ETH-USD", "n": "Ethereum", "c": "crypto"}
]

results = []
print(f"Inizio elaborazione di {len(assets_data)} asset...")

for asset in assets_data:
    found = False
    for suffix in [".MI", ".PA", ".L", ""]:
        full_t = asset["t"] + suffix
        try:
            data = yf.Ticker(full_t).history(period="8mo")
            if not data.empty and len(data) > 40:
                kv = get_kama(data['Close'], 10, 5, 20)
                kl = get_kama(data['Close'], 10, 2, 30)
                h_sub = data.tail(40)
                results.append({
                    "ticker": asset["t"], "nome": asset["n"], "categoria": asset["c"],
                    "price": round(data['Close'].iloc[-1], 3),
                    "kama_v": round(kv.iloc[-1], 3), "kama_l": round(kl.iloc[-1], 3),
                    "history": {
                        "dates": h_sub.index.strftime('%d/%m').tolist(),
                        "prices": h_sub['Close'].round(3).tolist(),
                        "kv": kv.tail(40).round(3).tolist(),
                        "kl": kl.tail(40).round(3).tolist()
                    }
                })
                print(f"OK: {full_t}")
                found = True
                break
        except: continue
    time.sleep(0.2)

output = {"last_update": datetime.now().strftime("%d/%m/%Y %H:%M"), "data": results}
with open('data.json', 'w') as f:
    json.dump(output, f, indent=2)
print("Fatto.")
