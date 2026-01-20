"""
Hourly Swing - WFA with Hard Stop Loss
Period: 2020-2025

ENHANCEMENTS:
1. Hard Stop Loss: 3% (exit if position down 3% from entry)
2. Time Stop: 24 hours (exit if no profit after 24 hours)
3. Transaction Costs: 5 bps (0.05%)

Objective: Validate if stop-loss risk management improves Sharpe and prevents catastrophic drawdowns
"""

import sys
from pathlib import Path
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

script_path = Path(__file__).resolve()
project_root = script_path.parents[6]
sys.path.insert(0, str(project_root))

from dotenv import load_dotenv
load_dotenv()
from src.data_handler import AlpacaDataClient
from alpaca.data.timeframe import TimeFrame

# CONFIG
ASSETS = ['NVDA', 'TSLA', 'GLD', 'AMZN']
YEARS = range(2020, 2026)
CSV_OUT = Path(__file__).parent / 'stop_loss_wfa_results.csv'
TRANSACTION_COST_BPS = 5.0
HARD_STOP_PCT = 3.0  # 3% hard stop
TIME_STOP_HOURS = 24  # 24-hour time stop

client = AlpacaDataClient()

def backtest_with_stops(data, rsi_period, upper, lower):
    """Backtest with Hard Stop Loss and Time Stop"""
    # RSI
    delta = data['close'].diff()
    gains = delta.where(delta > 0, 0.0)
    losses = (-delta).where(delta < 0, 0.0)
    avg_gain = gains.ewm(span=rsi_period, adjust=False).mean()
    avg_loss = losses.ewm(span=rsi_period, adjust=False).mean()
    rs = avg_gain / avg_loss.replace(0, np.inf)
    rsi_vals = (100 - (100 / (1 + rs))).values
    prices = data['close'].values
    timestamps = data.index
    
    # Simulation
    cash, shares, position = 10000.0, 0, 0
    equity = []
    start_val = cash
    
    entry_price = None
    entry_time = None
    
    c_entry = 1 + (TRANSACTION_COST_BPS/10000)
    c_exit = 1 - (TRANSACTION_COST_BPS/10000)
    
    for i in range(len(data)):
        if i < rsi_period:
            equity.append(cash)
            continue
            
        cur_rsi = rsi_vals[i]
        price = prices[i]
        cur_time = timestamps[i]
        
        # Entry Logic
        if position == 0 and cur_rsi > upper:
            shares = cash / (price * c_entry)
            cash = 0
            position = 1
            entry_price = price
            entry_time = cur_time
        
        # Exit Logic (RSI, Hard Stop, Time Stop)
        elif position == 1:
            # Calculate current P&L
            current_pnl_pct = ((price - entry_price) / entry_price) * 100
            hours_held = (cur_time - entry_time).total_seconds() / 3600
            
            # Exit conditions
            exit_signal = False
            exit_reason = None
            
            # 1. RSI Exit (normal)
            if cur_rsi < lower:
                exit_signal = True
                exit_reason = 'rsi'
            
            # 2. Hard Stop Loss (3%)
            elif current_pnl_pct < -HARD_STOP_PCT:
                exit_signal = True
                exit_reason = 'stop_loss'
            
            # 3. Time Stop (24 hours with no profit)
            elif hours_held > TIME_STOP_HOURS and current_pnl_pct < 0:
                exit_signal = True
                exit_reason = 'time_stop'
            
            if exit_signal:
                cash = shares * price * c_exit
                shares = 0
                position = 0
                entry_price = None
                entry_time = None
        
        equity.append(cash + (shares * price))
        
    equity = np.array(equity)
    if len(equity) < 2: return 0, 0
    
    ret = (equity[-1] / start_val) - 1
    s = pd.Series(equity)
    r = s.pct_change().dropna()
    sharpe = (r.mean() / r.std() * np.sqrt(252*6.5)) if r.std() > 0 else 0
    
    # Calculate Max Drawdown
    running_max = s.expanding().max()
    drawdown = (s - running_max) / running_max
    max_dd = drawdown.min() * 100
    
    return sharpe, ret, max_dd

# MAIN LOOP
all_results = []
print(f"\nStarting Stop-Loss WFA on {len(ASSETS)} assets...")

for symbol in ASSETS:
    print(f"\nProcessing {symbol}...")
    
    # Fetch Data
    dfs = []
    for year in YEARS:
        try:
            d = client.fetch_historical_bars(symbol, TimeFrame.Hour, f"{year}-01-01", f"{year}-12-31", feed='sip')
            if d is not None and not d.empty: dfs.append(d)
        except: pass
    
    if not dfs: continue
    raw_df = pd.concat(dfs).sort_index()
    raw_df = raw_df[~raw_df.index.duplicated(keep='first')]

    # Force Resample
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
    is_scores, oos_scores, oos_dds = [], [], []
    
    for i, w in enumerate(windows):
        train = raw_df[(raw_df.index >= w['train_start']) & (raw_df.index <= w['train_end'])]
        test = raw_df[(raw_df.index >= w['test_start']) & (raw_df.index <= w['test_end'])]
        if len(test) < 24: continue
        
        best_s = -999
        best_p = None
        for rsi in param_grid['rsi']:
            for b in param_grid['bands']:
                s, _, _ = backtest_with_stops(train, rsi, b[0], b[1])
                if s > best_s:
                    best_s = s
                    best_p = (rsi, b)
        
        if best_p:
            oos_s, oos_r, oos_dd = backtest_with_stops(test, best_p[0], best_p[1][0], best_p[1][1])
            is_scores.append(best_s)
            oos_scores.append(oos_s)
            oos_dds.append(oos_dd)
            all_results.append({
                'symbol': symbol,
                'window': i,
                'date': w['test_start'].date(),
                'is_sharpe': best_s,
                'oos_sharpe': oos_s,
                'oos_ret': oos_r,
                'oos_max_dd': oos_dd
            })

    if is_scores:
        avg_dd = np.mean(oos_dds)
        print(f"  Avg IS Sharpe: {np.mean(is_scores):.2f} | Avg OOS Sharpe: {np.mean(oos_scores):.2f} | Avg Max DD: {avg_dd:.2f}%")

res_df = pd.DataFrame(all_results)
res_df.to_csv(CSV_OUT, index=False)
print(f"\nSaved Stop-Loss Results to {CSV_OUT}")

# Summary
print("\n" + "="*80)
print("STOP-LOSS IMPACT SUMMARY")
print("="*80)
for symbol in ASSETS:
    sym_data = res_df[res_df['symbol'] == symbol]
    if not sym_data.empty:
        avg_oos = sym_data['oos_sharpe'].mean()
        avg_dd = sym_data['oos_max_dd'].mean()
        worst_dd = sym_data['oos_max_dd'].min()
        print(f"{symbol}: Avg OOS Sharpe = {avg_oos:.2f} | Avg DD = {avg_dd:.2f}% | Worst DD = {worst_dd:.2f}%")
