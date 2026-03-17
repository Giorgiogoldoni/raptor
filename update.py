import yfinance as yf
import pandas as pd
import numpy as np
import json
from datetime import datetime
import time

# --- LISTA INTEGRALE ASSET ---
TICKERS_CONFIG = [
    {"t": "3OIS.MI", "n": "3x Short Oil", "c": "COMMODITIES"},
    {"t": "LOIL.MI", "n": "2x Long Oil", "c": "COMMODITIES"},
    {"t": "SOIL.MI", "n": "2x Short Oil", "c": "COMMODITIES"},
    {"t": "LWEA.MI", "n": "2x Long Wheat", "c": "COMMODITIES"},
    {"t": "3TYS.MI", "n": "3x Short US 10Y", "c": "BONDS"},
    {"t": "3TYL.MI", "n": "3x Long US 10Y", "c": "BONDS"},
    {"t": "LSUG.MI", "n": "2x Long Sugar", "c": "COMMODITIES"},
    {"t": "2STR.MI", "n": "2x Short Treas", "c": "BONDS"},
    {"t": "2TRV.MI", "n": "2x Long Treas", "c": "BONDS"},
    {"t": "2OIG.MI", "n": "2x Long Oil Gas", "c": "COMMODITIES"},
    {"t": "2CAR.MI", "n": "2x Long Carbon", "c": "COMMODITIES"},
    {"t": "3EDS.MI", "n": "3x Short EuroStoxx", "c": "INDICI LEVA"},
    {"t": "3EDF.MI", "n": "3x Long EuroStoxx", "c": "INDICI LEVA"},
    {"t": "3SIS.MI", "n": "3x Short Silver", "c": "COMMODITIES"},
    {"t": "3SIL.MI", "n": "3x Long Silver", "c": "COMMODITIES"},
    {"t": "LSIL.MI", "n": "2x Long Silver", "c": "COMMODITIES"},
    {"t": "SSIL.MI", "n": "2x Short Silver", "c": "COMMODITIES"},
    {"t": "VIXL.MI", "n": "2x Long VIX", "c": "VOLATILITÀ"},
    {"t": "3USS.MI", "n": "3x Short S&P 500", "c": "INDICI LEVA"},
    {"t": "3USL.MI", "n": "3x Long S&P 500", "c": "INDICI LEVA"},
    {"t": "LPLA.MI", "n": "2x Long Platinum", "c": "COMMODITIES"},
    {"t": "LNIK.MI", "n": "2x Long Nickel", "c": "COMMODITIES"},
    {"t": "SNIK.MI", "n": "2x Short Nickel", "c": "COMMODITIES"},
    {"t": "3NGS.MI", "n": "3x Short Nat Gas", "c": "COMMODITIES"},
    {"t": "3NGL.MI", "n": "3x Long Nat Gas", "c": "COMMODITIES"},
    {"t": "LNGA.MI", "n": "2x Long Nat Gas", "c": "COMMODITIES"},
    {"t": "SNGA.MI", "n": "2x Short Nat Gas", "c": "COMMODITIES"},
    {"t": "QQQS.MI", "n": "3x Short Nasdaq", "c": "INDICI LEVA"},
    {"t": "QQQ3.MI", "n": "3x Long Nasdaq", "c": "INDICI LEVA"},
    {"t": "3GOS.MI", "n": "3x Short Gold", "c": "COMMODITIES"},
    {"t": "3GOL.MI", "n": "3x Long Gold", "c": "COMMODITIES"},
    {"t": "LBUL.MI", "n": "2x Long Gold", "c": "COMMODITIES"},
    {"t": "SBUL.MI", "n": "2x Short Gold", "c": "COMMODITIES"},
    {"t": "3ITL.MI", "n": "3x Long FTSE MIB", "c": "INDICI LEVA"},
    {"t": "3BAL.MI", "n": "3x Long Banks", "c": "SETTORIALI"},
    {"t": "3EUS.MI", "n": "3x Short EUR/USD", "c": "FOREX"},
    {"t": "3EUL.MI", "n": "3x Long EUR/USD", "c": "FOREX"},
    {"t": "3EMS.MI", "n": "3x Short Em. Markets", "c": "INDICI LEVA"},
    {"t": "3EML.MI", "n": "3x Long Em. Markets", "c": "INDICI LEVA"},
    {"t": "3DES.MI", "n": "3x Short DAX", "c": "INDICI LEVA"},
    {"t": "3DEL.MI", "n": "3x Long DAX", "c": "INDICI LEVA"},
    {"t": "LCOR.MI", "n": "2x Long Corn", "c": "COMMODITIES"},
    {"t": "LCOP.MI", "n": "2x Long Copper", "c": "COMMODITIES"},
    {"t": "LCFE.MI", "n": "2x Long Coffee", "c": "COMMODITIES"},
    {"t": "LCOC.MI", "n": "2x Long Cocoa", "c": "COMMODITIES"},
    {"t": "3UBS.MI", "n": "3x Short Brent", "c": "COMMODITIES"},
    {"t": "3BUS.MI", "n": "3x Long Brent", "c": "COMMODITIES"},
    {"t": "3BRS.MI", "n": "3x Short Brazil", "c": "INDICI LEVA"},
    {"t": "LAGR.MI", "n": "2x Long Agriculture", "c": "COMMODITIES"},
    {"t": "LQQ.PA", "n": "Nasdaq 2x Long", "c": "ETF LEVA"},
    {"t": "BTC-USD", "n": "Bitcoin", "c": "CRYPTO"},
    {"t": "ETH-USD", "n": "Ethereum", "c": "CRYPTO"}
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
        df = yf.download(asset['t'], period="200d", interval="1d", progress=False)
        if df.empty or len(df) < 50: return None
        if isinstance(df.columns, pd.MultiIndex): df.columns = df.columns.get_level_values(0)
        
        close = df['Close'].ffill().dropna()
        kv_all = calcola_kama(close, 10, 5, 20)
        kl_all = calcola_kama(close, 10, 2, 30)

        last_p, last_kv, last_kl = float(close.iloc[-1]), float(kv_all[-1]), float(kl_all[-1])
        
        return {
            "ticker": asset['t'], "nome": asset['n'], "categoria": asset['c'],
            "price": round(last_p, 3), "kama_v": round(last_kv, 3), "kama_l": round(last_kl, 3),
            "status": "BUY" if last_p > last_kv > last_kl else ("SELL" if last_p < last_kv < last_kl else "WAIT"),
            "signal_date": datetime.now().strftime("%d/%m/%Y"),
            "history": {
                "prices": [round(float(x), 2) for x in close.tail(180).values],
                "kv": [round(float(x), 2) for x in kv_all[-180:]],
                "kl": [round(float(x), 2) for x in kl_all[-180:]],
                "dates": close.tail(180).index.strftime('%d/%m').tolist()
            }
        }
    except: return None

results = []
for a in TICKERS_CONFIG:
    res = process_asset(a)
    if res: results.append(res)
    time.sleep(0.4)

with open('data.json', 'w') as f:
    json.dump({"last_update": datetime.now().strftime("%d/%m/%Y %H:%M"), "data": results}, f, indent=4)
