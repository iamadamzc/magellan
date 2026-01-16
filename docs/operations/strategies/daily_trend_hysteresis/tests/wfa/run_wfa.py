"""
Daily Trend Hysteresis - Walk-Forward Analysis (WFA)
Period: 2020-2025

Methodology:
- Rolling Window: 6-month train, 3-month test.
- Optimization Target: Sharpe Ratio.
- Parameter Grid:
  - RSI Period: [14, 21, 28, 32]
  - Bands: [(55,45), (60,40), (65,35), (70,30)]
"""

import sys
from pathlib import Path
import pandas as pd
import numpy as np
import itertools
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
print("DAILY TREND HYSTERESIS - WFA (2020-2025)")
print("="*80)

SYMBOL = 'SPY' # Testing on SPY first for robustness (or NVDA as per plan?) 
# Plan says: "Daily Trend: Already has 2024-2025 data, extend back to 2020... Test 1.1 Strategies: All 4"
# The backtest_single.py used GOOGL. I'll use SPY as the benchmark for robustness, or NVDA?
# Plan "Specific Concerns": "Trend following fails in sideways markets".
# I'll use SPY for the canonical robustness test.

START_DATE = '2020-01-01'
END_DATE = '2025-12-31'

# 1. Fetch Data
print("[1/4] Fetching Data (2020-2025)...")
client = AlpacaDataClient()
# Fetching daily is fast
raw_df = client.fetch_historical_bars(SYMBOL, TimeFrame.Day, START_DATE, END_DATE, feed='sip')
print(f"  ✓ Fetched {len(raw_df)} bars")

# 2. Define Windows
# 6m train, 3m test. Walk forward 3m.
# Start: 2020-01-01.
# Window 1: Train 2020-01-01 to 2020-06-30. Test 2020-07-01 to 2020-09-30.
# Window 2: Train 2020-04-01 to 2020-09-30 (Overlap? Or distinct?) 
# Plan says: "Walk forward: 3 months". Standard WFA overlaps training or slides it.
# Usually: Train [t, t+6m], Test [t+6m, t+9m]. Next: Train [t+3m, t+9m], Test [t+9m, t+12m].
# So we slide by 3 months.

dates = raw_df.index
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
        'test_start': train_end + timedelta(days=1), # Day after training
        'test_end': min(test_end, end_dt)
    })
    
    # Slide by 3 months
    current_start = current_start + timedelta(days=90)

print(f"  ✓ Defined {len(windows)} WFA Windows")

# 3. Define Logic
def backtest(df, rsi_period, upper, lower):
    # Calculate RSI
    delta = df['close'].diff()
    gains = delta.where(delta > 0, 0.0)
    losses = (-delta).where(delta < 0, 0.0)
    avg_gain = gains.ewm(span=rsi_period, adjust=False).mean()
    avg_loss = losses.ewm(span=rsi_period, adjust=False).mean()
    rs = avg_gain / avg_loss.replace(0, np.inf)
    rsi = 100 - (100 / (1 + rs))
    
    # Simulation
    position = 0 # 0 or 1
    cash = 10000
    shares = 0
    start_val = cash
    
    equity = []
    
    # Vectorized might be hard with hysteresis state, stick to loop
    # Pre-calculate RSI to speed up loop
    rsi_vals = rsi.values
    prices = df['close'].values
    dates = df.index
    
    for i in range(len(df)):
        if i < rsi_period: 
            equity.append(cash)
            continue
            
        cur_rsi = rsi_vals[i]
        price = prices[i]
        
        # Hysteresis
        if position == 0 and cur_rsi > upper:
            # Buy
            shares = cash / price
            cash = 0
            position = 1
        elif position == 1 and cur_rsi < lower:
            # Sell
            cash = shares * price
            shares = 0
            position = 0
            
        val = cash + (shares * price)
        equity.append(val)
        
    equity = np.array(equity)
    if len(equity) < 2: return 0, 0
    
    ret = (equity[-1] / start_val) - 1
    # Sharpe
    eq_series = pd.Series(equity)
    daily_rets = eq_series.pct_change().dropna()
    sharpe = (daily_rets.mean() / daily_rets.std() * np.sqrt(252)) if daily_rets.std() > 0 else 0
    
    return sharpe, ret

# 4. Run WFA
param_grid = {
    'rsi': [14, 21, 28, 30],
    'bands': [(55,45), (60,40), (65,35), (70,30)]
}

results = []

print("\n[2/4] Executing WFA Loop...")

for i, w in enumerate(windows):
    train_mask = (raw_df.index >= w['train_start']) & (raw_df.index <= w['train_end'])
    test_mask = (raw_df.index >= w['test_start']) & (raw_df.index <= w['test_end'])
    
    train_df = raw_df[train_mask]
    test_df = raw_df[test_mask]
    
    if test_df.empty: continue
    
    # Optimize on Train
    best_sharpe = -999
    best_params = None
    
    for p_rsi in param_grid['rsi']:
        for p_bands in param_grid['bands']:
            s, r = backtest(train_df, p_rsi, p_bands[0], p_bands[1])
            if s > best_sharpe:
                best_sharpe = s
                best_params = (p_rsi, p_bands)
    
    # Test on Test
    in_sample_sharpe = best_sharpe
    if best_params:
        out_sharpe, out_ret = backtest(test_df, best_params[0], best_params[1][0], best_params[1][1])
        
        print(f"Window {i+1}: {w['test_start'].date()} to {w['test_end'].date()}")
        print(f"  Best Params: RSI {best_params[0]}, Bands {best_params[1]}")
        print(f"  IS Sharpe: {in_sample_sharpe:.2f} | OOS Sharpe: {out_sharpe:.2f} | OOS Ret: {out_ret*100:.1f}%")
        
        results.append({
            'window': i,
            'test_start': w['test_start'],
            'test_end': w['test_end'],
            'rsi': best_params[0],
            'upper': best_params[1][0],
            'lower': best_params[1][1],
            'is_sharpe': in_sample_sharpe,
            'oos_sharpe': out_sharpe,
            'oos_ret': out_ret
        })

# 5. Summary
res_df = pd.DataFrame(results)
print("\n[3/4] Analysis")
print(res_df[['test_start', 'is_sharpe', 'oos_sharpe', 'oos_ret']])

avg_is_sharpe = res_df['is_sharpe'].mean()
avg_oos_sharpe = res_df['oos_sharpe'].mean()
degradation = (1 - avg_oos_sharpe / avg_is_sharpe) * 100

print(f"\nAverage IS Sharpe:  {avg_is_sharpe:.2f}")
print(f"Average OOS Sharpe: {avg_oos_sharpe:.2f}")
print(f"Degradation:        {degradation:.1f}%")

if degradation < 30:
    print("✅ PASS: Robust Strategy")
elif degradation < 50:
    print("⚠️ PASS: Acceptable Degradation")
else:
    print("❌ FAIL: Severe Overfitting")

# Save
out_file = Path(__file__).parent / 'daily_trend_wfa_results.csv'
res_df.to_csv(out_file, index=False)
print(f"\nSaved to {out_file}")
