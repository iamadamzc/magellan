"""
Hourly Swing Trading - Walk-Forward Analysis (WFA)
Period: 2020-2025

Methodology:
- Rolling Window: 6-month train, 3-month test (matches Daily Trend WFA for comparability).
- Target: TSLA (High Beta) for stress testing.
- Features: Hourly RSI with Hysteresis.
- Params: RSI Period [14, 21, 28], Bands [(55,45), (60,40), (65,35)].
"""

import sys
from pathlib import Path
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

# Setup Project Root
script_path = Path(__file__).resolve()
project_root = script_path.parents[6]
sys.path.insert(0, str(project_root))

from dotenv import load_dotenv
load_dotenv()

from src.data_handler import AlpacaDataClient
from alpaca.data.timeframe import TimeFrame

print("="*80)
print("HOURLY SWING - WFA (2020-2025)")
print("="*80)

SYMBOL = 'TSLA'
START_DATE = '2020-01-01'
END_DATE = '2025-12-31'
TRANSACTION_COST_BPS = 5.0  # 0.05% per trade

# 1. Fetch Data (Chunked)
print(f"[1/4] Fetching 1-Hour Data for {SYMBOL} (2020-2025)...")
client = AlpacaDataClient()
years = range(2020, 2026)
dfs = []

for year in years:
    print(f"  Fetching {year}...")
    start = f"{year}-01-01"
    end = f"{year}-12-31"
    try:
        yearly_df = client.fetch_historical_bars(SYMBOL, TimeFrame.Hour, start, end, feed='sip')
        if yearly_df is not None and not yearly_df.empty:
            dfs.append(yearly_df)
    except Exception as e:
        print(f"  ⚠️ Error fetching {year}: {e}")

if not dfs:
    print("❌ Failed to fetch any data.")
    sys.exit(1)

raw_df = pd.concat(dfs)
raw_df = raw_df[~raw_df.index.duplicated(keep='first')]
raw_df.sort_index(inplace=True)
print(f"  ✓ Total Fetched: {len(raw_df)} bars")

# Resample check
if len(raw_df) > 50000: # Rough check for 1-min data
    print("  ⚠️ Force resampling to 1-Hour...")
    df = raw_df.resample('1h').agg({
        'open': 'first', 'high': 'max', 'low': 'min', 'close': 'last', 'volume': 'sum'
    }).dropna()
else:
    df = raw_df

# 2. Define Windows
dates = df.index
start_dt = dates[0]
end_dt = dates[-1]

windows = []
current_start = start_dt

while current_start < end_dt:
    train_end = current_start + timedelta(days=180) # 6 months
    test_end = train_end + timedelta(days=90) # 3 months
    
    if train_end >= end_dt:
        break
        
    windows.append({
        'train_start': current_start,
        'train_end': train_end,
        'test_start': train_end + timedelta(hours=1),
        'test_end': min(test_end, end_dt)
    })
    
    current_start = current_start + timedelta(days=90)

print(f"  ✓ Defined {len(windows)} WFA Windows")

# 3. Logic
def backtest(data, rsi_period, upper, lower):
    # RSI Calc
    delta = data['close'].diff()
    gains = delta.where(delta > 0, 0.0)
    losses = (-delta).where(delta < 0, 0.0)
    avg_gain = gains.ewm(span=rsi_period, adjust=False).mean()
    avg_loss = losses.ewm(span=rsi_period, adjust=False).mean()
    rs = avg_gain / avg_loss.replace(0, np.inf)
    rsi_series = 100 - (100 / (1 + rs))
    
    rsi = rsi_series.values
    prices = data['close'].values
    
    cash = 10000.0
    shares = 0
    position = 0 # 0=flat, 1=long
    start_val = cash
    
    equity = []
    
    cost_factor_entry = 1 + (TRANSACTION_COST_BPS/10000)
    cost_factor_exit = 1 - (TRANSACTION_COST_BPS/10000)
    
    for i in range(len(data)):
        if i < rsi_period:
            equity.append(cash)
            continue
            
        cur_rsi = rsi[i]
        price = prices[i]
        
        if position == 0 and cur_rsi > upper:
            # Buy
            shares = cash / (price * cost_factor_entry)
            cash = 0
            position = 1
        elif position == 1 and cur_rsi < lower:
            # Sell
            cash = shares * price * cost_factor_exit
            shares = 0
            position = 0
            
        val = cash + (shares * price)
        equity.append(val)
        
    equity = np.array(equity)
    if len(equity) < 2: return 0, 0
    
    total_ret = (equity[-1] / start_val) - 1
    
    # Sharpe (approx annualized for hourly)
    # 252 * 6.5 hours = ~1638 bars/year
    # But data might include pre-market? Alpaca '1Hour' is usually limited to market hours?
    # Usually standard is 252*6.5 for equity hours.
    eq_s = pd.Series(equity)
    rets = eq_s.pct_change().dropna()
    sharpe = (rets.mean() / rets.std() * np.sqrt(252*6.5)) if rets.std() > 0 else 0
    
    return sharpe, total_ret

# 4. WFA Loop
param_grid = {
    'rsi': [14, 21, 28],
    'bands': [(55,45), (60,40), (65,35), (70,30)]
}

results = []
print("\n[2/4] Executing WFA Loop...")

for i, w in enumerate(windows):
    train_mask = (df.index >= w['train_start']) & (df.index <= w['train_end'])
    test_mask = (df.index >= w['test_start']) & (df.index <= w['test_end'])
    
    train_df = df[train_mask]
    test_df = df[test_mask]
    
    if len(test_df) < 24: continue # Skip if tiny data
    
    # Train
    best_sharpe = -999
    best_params = None
    
    for p_rsi in param_grid['rsi']:
        for p_bands in param_grid['bands']:
            s, r = backtest(train_df, p_rsi, p_bands[0], p_bands[1])
            if s > best_sharpe:
                best_sharpe = s
                best_params = (p_rsi, p_bands)
    
    # Test
    if best_params:
        out_sharpe, out_ret = backtest(test_df, best_params[0], best_params[1][0], best_params[1][1])
        
        print(f"Window {i+1} ({w['test_start'].date()}): IS {best_sharpe:.2f} | OOS {out_sharpe:.2f} | Ret {out_ret*100:.1f}% | Params {best_params}")
        
        results.append({
            'window': i,
            'start': w['test_start'],
            'is_sharpe': best_sharpe,
            'oos_sharpe': out_sharpe,
            'oos_ret': out_ret
        })

# 5. Analysis
res_df = pd.DataFrame(results)
print("\n[3/4] Analysis Support")

avg_is = res_df['is_sharpe'].mean()
avg_oos = res_df['oos_sharpe'].mean()
deg = (1 - avg_oos/avg_is)*100

print(f"Avg IS Sharpe:  {avg_is:.2f}")
print(f"Avg OOS Sharpe: {avg_oos:.2f}")
print(f"Degradation:    {deg:.1f}%")

if deg < 30: print("✅ PASS: Robust")
elif deg < 50: print("⚠️ MARGINAL")
else: print("❌ FAIL: Overfit")

out_file = Path(__file__).parent / 'hourly_wfa_results.csv'
res_df.to_csv(out_file, index=False)
print(f"Saved to {out_file}")
