"""
Hourly Swing - WFA with Trend Filters (Enhanced)
Period: 2020-2025

ENHANCEMENTS:
1. NVDA/TSLA: Price > 200-Hour SMA (Trend Filter)
2. GLD: VIX > 20 (Fear Filter)
3. AMZN: ATR > 20-day average (Volatility Filter)

Objective: Validate if filters improve Sharpe and reduce catastrophic drawdowns (e.g., TSLA 2022 -63%)
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
ASSETS = {
    'NVDA': {'filter': 'trend', 'rsi_params': [14, 21, 28], 'bands': [(55,45), (60,40), (65,35)]},
    'TSLA': {'filter': 'trend', 'rsi_params': [14, 21, 28], 'bands': [(55,45), (60,40), (65,35)]},
    'GLD': {'filter': 'vix', 'rsi_params': [14, 21, 28], 'bands': [(60,40), (65,35), (70,30)]},
    'AMZN': {'filter': 'atr', 'rsi_params': [14, 21, 28], 'bands': [(55,45), (60,40), (65,35)]}
}

YEARS = range(2020, 2026)
CSV_OUT = Path(__file__).parent / 'filtered_wfa_results.csv'
TRANSACTION_COST_BPS = 5.0

client = AlpacaDataClient()

def fetch_vix_data():
    """Fetch VIX data for GLD filter"""
    print("  Fetching VIX data...")
    dfs = []
    for year in YEARS:
        try:
            d = client.fetch_historical_bars('^VIX', TimeFrame.Hour, f"{year}-01-01", f"{year}-12-31", feed='sip')
            if d is not None and not d.empty: dfs.append(d)
        except:
            pass
    if dfs:
        vix_df = pd.concat(dfs).sort_index()
        vix_df = vix_df[~vix_df.index.duplicated(keep='first')]
        return vix_df['close']
    return pd.Series()

def backtest_with_filter(data, rsi_period, upper, lower, filter_type='none', vix_series=None):
    """Backtest with optional filters"""
    # RSI
    delta = data['close'].diff()
    gains = delta.where(delta > 0, 0.0)
    losses = (-delta).where(delta < 0, 0.0)
    avg_gain = gains.ewm(span=rsi_period, adjust=False).mean()
    avg_loss = losses.ewm(span=rsi_period, adjust=False).mean()
    rs = avg_gain / avg_loss.replace(0, np.inf)
    rsi_vals = (100 - (100 / (1 + rs))).values
    prices = data['close'].values
    
    # Filters
    if filter_type == 'trend':
        # 200-Hour SMA
        sma_200 = data['close'].rolling(200).mean().values
        trend_filter = prices > sma_200
    elif filter_type == 'vix':
        # VIX > 20
        if vix_series is not None and not vix_series.empty:
            # Align VIX to data index
            vix_aligned = vix_series.reindex(data.index, method='ffill').fillna(15).values
            trend_filter = vix_aligned > 20
        else:
            trend_filter = np.ones(len(data), dtype=bool)
    elif filter_type == 'atr':
        # ATR > 20-day average
        high = data['high'].values
        low = data['low'].values
        close_prev = np.roll(prices, 1)
        tr = np.maximum(high - low, np.abs(high - close_prev), np.abs(low - close_prev))
        atr = pd.Series(tr).rolling(14).mean().values
        atr_avg = pd.Series(atr).rolling(20*6).mean().values  # 20 days * 6 hours
        trend_filter = atr > atr_avg
    else:
        trend_filter = np.ones(len(data), dtype=bool)
    
    # Simulation
    cash, shares, position = 10000.0, 0, 0
    equity = []
    start_val = cash
    
    c_entry = 1 + (TRANSACTION_COST_BPS/10000)
    c_exit = 1 - (TRANSACTION_COST_BPS/10000)
    
    for i in range(len(data)):
        if i < max(rsi_period, 200):
            equity.append(cash)
            continue
            
        cur_rsi = rsi_vals[i]
        price = prices[i]
        filter_ok = trend_filter[i]
        
        # Only enter if filter passes
        if position == 0 and cur_rsi > upper and filter_ok:
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
    sharpe = (r.mean() / r.std() * np.sqrt(252*6.5)) if r.std() > 0 else 0
    return sharpe, ret

# Fetch VIX once
vix_series = fetch_vix_data()

# MAIN LOOP
all_results = []
print(f"\nStarting Filtered WFA on {len(ASSETS)} assets...")

for symbol, config in ASSETS.items():
    print(f"\nProcessing {symbol} (Filter: {config['filter']})...")
    
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
    is_scores, oos_scores = [], []
    
    for i, w in enumerate(windows):
        train = raw_df[(raw_df.index >= w['train_start']) & (raw_df.index <= w['train_end'])]
        test = raw_df[(raw_df.index >= w['test_start']) & (raw_df.index <= w['test_end'])]
        if len(test) < 24: continue
        
        best_s = -999
        best_p = None
        for rsi in config['rsi_params']:
            for b in config['bands']:
                s, _ = backtest_with_filter(train, rsi, b[0], b[1], config['filter'], vix_series)
                if s > best_s:
                    best_s = s
                    best_p = (rsi, b)
        
        if best_p:
            oos_s, oos_r = backtest_with_filter(test, best_p[0], best_p[1][0], best_p[1][1], config['filter'], vix_series)
            is_scores.append(best_s)
            oos_scores.append(oos_s)
            all_results.append({
                'symbol': symbol,
                'filter': config['filter'],
                'window': i,
                'date': w['test_start'].date(),
                'is_sharpe': best_s,
                'oos_sharpe': oos_s,
                'oos_ret': oos_r
            })

    if is_scores:
        print(f"  Avg IS Sharpe: {np.mean(is_scores):.2f} | Avg OOS Sharpe: {np.mean(oos_scores):.2f}")

res_df = pd.DataFrame(all_results)
res_df.to_csv(CSV_OUT, index=False)
print(f"\nSaved Filtered Results to {CSV_OUT}")

# Summary
print("\n" + "="*80)
print("FILTER IMPACT SUMMARY")
print("="*80)
for symbol in ASSETS.keys():
    sym_data = res_df[res_df['symbol'] == symbol]
    if not sym_data.empty:
        avg_oos = sym_data['oos_sharpe'].mean()
        print(f"{symbol}: Avg OOS Sharpe = {avg_oos:.2f}")
