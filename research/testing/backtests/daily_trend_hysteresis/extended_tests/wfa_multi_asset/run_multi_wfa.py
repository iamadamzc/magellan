"""
Daily Trend Hysteresis - Multi-Asset WFA (13 Assets)
Period: 2020-2025

Assets: SPY, QQQ, IWM, AAPL, MSFT, GOOGL, AMZN, NVDA, META, TSLA, GLD, XLE, TLT
Logic: Long-Only RSI Hysteresis
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
CSV_OUT = Path(__file__).parent / 'multi_asset_wfa_results.csv'

client = AlpacaDataClient()

def backtest(df, rsi_period, upper, lower):
    # RSI
    delta = df['close'].diff()
    gains = delta.where(delta > 0, 0.0)
    losses = (-delta).where(delta < 0, 0.0)
    avg_gain = gains.ewm(span=rsi_period, adjust=False).mean()
    avg_loss = losses.ewm(span=rsi_period, adjust=False).mean()
    rs = avg_gain / avg_loss.replace(0, np.inf)
    rsi_vals = (100 - (100 / (1 + rs))).values
    prices = df['close'].values
    
    cash, shares, position = 10000.0, 0, 0
    equity = []
    start_val = cash
    
    for i in range(len(df)):
        if i < rsi_period:
            equity.append(cash)
            continue
            
        cur_rsi = rsi_vals[i]
        price = prices[i]
        
        if position == 0 and cur_rsi > upper:
            shares = cash / price
            cash = 0
            position = 1
        elif position == 1 and cur_rsi < lower:
            cash = shares * price
            shares = 0
            position = 0
            
        equity.append(cash + (shares * price))
        
    equity = np.array(equity)
    if len(equity) < 2: return 0, 0
    
    ret = (equity[-1] / start_val) - 1
    # Annualized Sharpe (Daily)
    s = pd.Series(equity)
    r = s.pct_change().dropna()
    sharpe = (r.mean() / r.std() * np.sqrt(252)) if r.std() > 0 else 0
    return sharpe, ret

# MAIN LOOP
all_results = []
print(f"Starting Multi-Asset WFA on {len(ASSETS)} assets...")

for symbol in ASSETS:
    print(f"\nProcessing {symbol}...")
    
    # 1. Fetch Data Chunked
    dfs = []
    for year in YEARS:
        try:
            d = client.fetch_historical_bars(symbol, TimeFrame.Day, f"{year}-01-01", f"{year}-12-31", feed='sip')
            if d is not None and not d.empty: dfs.append(d)
        except: pass
    
    if not dfs:
        print(f"  ❌ No data for {symbol}")
        continue
        
    raw_df = pd.concat(dfs)
    raw_df = raw_df[~raw_df.index.duplicated(keep='first')].sort_index()
    
    # 2. WFA Windows (6m train, 3m test)
    start_dt = raw_df.index[0]
    end_dt = raw_df.index[-1]
    curr = start_dt
    windows = []
    
    while curr < end_dt:
        te = curr + timedelta(days=180)
        test_e = te + timedelta(days=90)
        if te >= end_dt: break
        windows.append({'train_start': curr, 'train_end': te, 'test_start': te+timedelta(days=1), 'test_end': min(test_e, end_dt)})
        curr += timedelta(days=90)
        
    # 3. Optimize & Test
    param_grid = {'rsi': [14, 21, 28], 'bands': [(55,45), (60,40), (65,35), (70,30)]}
    
    symbol_sharpes_is = []
    symbol_sharpes_oos = []
    
    for i, w in enumerate(windows):
        train_df = raw_df[(raw_df.index >= w['train_start']) & (raw_df.index <= w['train_end'])]
        test_df = raw_df[(raw_df.index >= w['test_start']) & (raw_df.index <= w['test_end'])]
        
        if test_df.empty: continue
        
        # Train
        best_sharpe = -999
        best_p = None
        for rsi in param_grid['rsi']:
            for b in param_grid['bands']:
                s, _ = backtest(train_df, rsi, b[0], b[1])
                if s > best_sharpe:
                    best_sharpe = s
                    best_p = (rsi, b)
                    
        # Test
        if best_p:
            oos_s, oos_r = backtest(test_df, best_p[0], best_p[1][0], best_p[1][1])
            symbol_sharpes_is.append(best_sharpe)
            symbol_sharpes_oos.append(oos_s)
            
            all_results.append({
                'symbol': symbol,
                'window': i,
                'date': w['test_start'].date(),
                'is_sharpe': best_sharpe,
                'oos_sharpe': oos_s,
                'oos_ret': oos_r
            })
            
    # Quick Stat per symbol
    if symbol_sharpes_is:
        avg_is = np.mean(symbol_sharpes_is)
        avg_oos = np.mean(symbol_sharpes_oos)
        print(f"  Avg IS Sharpe: {avg_is:.2f} | Avg OOS Sharpe: {avg_oos:.2f}")

# Save
res_df = pd.DataFrame(all_results)
res_df.to_csv(CSV_OUT, index=False)
print(f"\nSaved Multi-Asset Results to {CSV_OUT}")
