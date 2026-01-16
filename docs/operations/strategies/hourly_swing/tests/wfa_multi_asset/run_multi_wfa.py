"""
Hourly Swing - Multi-Asset WFA (13 Assets)
Period: 2020-2025

Assets: SPY, QQQ, IWM, AAPL, MSFT, GOOGL, AMZN, NVDA, META, TSLA, GLD, XLE, TLT
Logic: Hourly RSI Hysteresis
"""

import sys
from pathlib import Path
import pandas as pd
import numpy as np
import time
from datetime import datetime, timedelta

script_path = Path(__file__).resolve()
project_root = script_path.parents[6]
sys.path.insert(0, str(project_root))

from dotenv import load_dotenv
load_dotenv()
from src.data_handler import AlpacaDataClient
from alpaca.data.timeframe import TimeFrame

# CONFIG
ASSETS = ['SPY', 'QQQ', 'IWM', 'AAPL', 'MSFT', 'GOOGL', 'AMZN', 'NVDA', 'META', 'TSLA', 'GLD', 'XLE', 'TLT']
YEARS = range(2020, 2026)
CSV_OUT = Path(__file__).parent / 'multi_asset_hourly_results.csv'
TRANSACTION_COST_BPS = 5.0

client = AlpacaDataClient()

def backtest(data, rsi_period, upper, lower):
    delta = data['close'].diff()
    gains = delta.where(delta > 0, 0.0)
    losses = (-delta).where(delta < 0, 0.0)
    avg_gain = gains.ewm(span=rsi_period, adjust=False).mean()
    avg_loss = losses.ewm(span=rsi_period, adjust=False).mean()
    rs = avg_gain / avg_loss.replace(0, np.inf)
    rsi = (100 - (100 / (1 + rs))).values
    prices = data['close'].values
    
    cash, shares, position = 10000.0, 0, 0
    equity = []
    start_val = cash
    
    c_entry = 1 + (TRANSACTION_COST_BPS/10000)
    c_exit = 1 - (TRANSACTION_COST_BPS/10000)
    
    for i in range(len(data)):
        if i < rsi_period:
            equity.append(cash)
            continue
            
        cur_rsi = rsi[i]
        price = prices[i]
        
        if position == 0 and cur_rsi > upper:
            shares = cash / (price * c_entry)
            cash = 0
            position = 1
        elif position == 1 and cur_rsi < lower:
            cash = shares * price * c_exit
            shares = 0
            position = 0
        
        equity.append(cash + (shares * price))
        
    equity = np.array(equity)
    if len(equity) < 2: return 0, 0
    
    ret = (equity[-1] / start_val) - 1
    s = pd.Series(equity)
    r = s.pct_change().dropna()
    # Hourly Sharpe (252 * 6.5)
    sharpe = (r.mean() / r.std() * np.sqrt(252*6.5)) if r.std() > 0 else 0
    return sharpe, ret

# MAIN LOOP
all_results = []
print(f"Starting Multi-Asset Hourly WFA...")

for symbol in ASSETS:
    print(f"\nProcessing {symbol}...")
    
    dfs = []
    for year in YEARS:
        try:
            d = client.fetch_historical_bars(symbol, TimeFrame.Hour, f"{year}-01-01", f"{year}-12-31", feed='sip')
            if d is not None and not d.empty: dfs.append(d)
        except: pass
    
    if not dfs: continue
    raw_df = pd.concat(dfs).sort_index()
    raw_df = raw_df[~raw_df.index.duplicated(keep='first')]

    # Force Resample if needed
    if len(raw_df) > 50000:
        raw_df = raw_df.resample('1h').agg({'open':'first','high':'max','low':'min','close':'last','volume':'sum'}).dropna()
    
    # Windows
    start_dt = raw_df.index[0]
    end_dt = raw_df.index[-1]
    curr = start_dt
    windows = []
    while curr < end_dt:
        te = curr + timedelta(days=180)
        test_e = te + timedelta(days=90)
        if te >= end_dt: break
        windows.append({'train_start': curr, 'train_end': te, 'test_start': te+timedelta(hours=1), 'test_end': min(test_e, end_dt)})
        curr += timedelta(days=90)
        
    # Test
    param_grid = {'rsi': [14, 21, 28], 'bands': [(55,45), (60,40), (65,35)]}
    is_scores, oos_scores = [], []
    
    for i, w in enumerate(windows):
        train = raw_df[(raw_df.index >= w['train_start']) & (raw_df.index <= w['train_end'])]
        test = raw_df[(raw_df.index >= w['test_start']) & (raw_df.index <= w['test_end'])]
        if len(test) < 24: continue
        
        best_s = -999
        best_p = None
        for rsi in param_grid['rsi']:
            for b in param_grid['bands']:
                s, _ = backtest(train, rsi, b[0], b[1])
                if s > best_s:
                    best_s = s
                    best_p = (rsi, b)
        
        if best_p:
            oos_s, oos_r = backtest(test, best_p[0], best_p[1][0], best_p[1][1])
            is_scores.append(best_s)
            oos_scores.append(oos_s)
            all_results.append({'symbol': symbol, 'window': i, 'date': w['test_start'].date(), 'is_sharpe': best_s, 'oos_sharpe': oos_s, 'oos_ret': oos_r})

    if is_scores:
        print(f"  Avg IS Sharpe: {np.mean(is_scores):.2f} | Avg OOS Sharpe: {np.mean(oos_scores):.2f}")

res_df = pd.DataFrame(all_results)
res_df.to_csv(CSV_OUT, index=False)
print(f"\nSaved Hourly Results to {CSV_OUT}")
