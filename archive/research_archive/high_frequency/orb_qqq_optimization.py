"""
Opening Range Breakout - QQQ Optimization

Baseline on QQQ (Q1 2024):
- Sharpe: -0.26 (very close to breakeven!)
- Win Rate: 25.9%
- Trades/Day: 4.1
- Avg Win: 0.226%
- Avg Loss: -0.081%

Goal: Optimize to push Sharpe positive

Parameters to test:
1. Range period (10, 15, 20, 30 minutes)
2. Profit targets (0.25%, 0.30%, 0.35%, 0.40%)
3. Stop losses (0.15%, 0.20%, 0.25%)
4. Hold times (30, 45, 60 minutes)
"""

import requests
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from dotenv import load_dotenv
import json
import os

load_dotenv()
FMP_API_KEY = os.getenv('FMP_API_KEY')
FRICTION_BPS = 1.0

def fetch_1min_data(symbol, date):
    url = "https://financialmodelingprep.com/stable/historical-chart/1min"
    params = {'symbol': symbol, 'from': date, 'to': date, 'apikey': FMP_API_KEY}
    try:
        response = requests.get(url, params=params, timeout=15)
        if response.status_code == 200:
            return response.json()
    except:
        pass
    return []

def orb_qqq(df, range_minutes=15, profit_target=0.30, stop_loss=0.20, max_hold_minutes=60):
    """Opening Range Breakout for QQQ"""
    if len(df) < 50:
        return []
    
    df['time'] = pd.to_datetime(df['date'])
    df['hour'] = df['time'].dt.hour
    df['minute'] = df['time'].dt.minute
    
    open_idx = None
    for i in range(len(df)):
        if df.loc[i, 'hour'] == 9 and df.loc[i, 'minute'] >= 30:
            open_idx = i
            break
    
    if open_idx is None or open_idx + range_minutes >= len(df):
        return []
    
    range_end_idx = open_idx + range_minutes
    opening_high = df.loc[open_idx:range_end_idx, 'high'].max()
    opening_low = df.loc[open_idx:range_end_idx, 'low'].min()
    
    trades = []
    position = None
    
    for i in range(range_end_idx + 1, len(df)):
        if df.loc[i, 'hour'] >= 12 or (df.loc[i, 'hour'] == 11 and df.loc[i, 'minute'] >= 30):
            if position:
                pnl_pct = (df.loc[i, 'close'] - position['entry_price']) / position['entry_price'] * 100
                if position['type'] == 'short':
                    pnl_pct = -pnl_pct
                pnl_pct -= FRICTION_BPS / 100
                trades.append({'pnl_pct': pnl_pct, 'win': pnl_pct > 0})
                position = None
            break
        
        if position:
            hold_min = i - position['entry_idx']
            pnl_pct = (df.loc[i, 'close'] - position['entry_price']) / position['entry_price'] * 100
            if position['type'] == 'short':
                pnl_pct = -pnl_pct
            
            exit_reason = None
            if pnl_pct >= profit_target:
                exit_reason = 'target'
            elif pnl_pct <= -stop_loss:
                exit_reason = 'stop_loss'
            elif position['type'] == 'long' and df.loc[i, 'close'] < opening_high:
                exit_reason = 'return_to_range'
            elif position['type'] == 'short' and df.loc[i, 'close'] > opening_low:
                exit_reason = 'return_to_range'
            elif hold_min >= max_hold_minutes:
                exit_reason = 'timeout'
            
            if exit_reason:
                pnl_pct -= FRICTION_BPS / 100
                trades.append({'pnl_pct': pnl_pct, 'win': pnl_pct > 0})
                position = None
        
        if not position:
            if df.loc[i, 'close'] > opening_high:
                position = {'type': 'long', 'entry_price': df.loc[i, 'close'], 'entry_idx': i}
            elif df.loc[i, 'close'] < opening_low:
                position = {'type': 'short', 'entry_price': df.loc[i, 'close'], 'entry_idx': i}
    
    return trades

def generate_trading_days(start_date, end_date):
    current = datetime.strptime(start_date, '%Y-%m-%d')
    end = datetime.strptime(end_date, '%Y-%m-%d')
    trading_days = []
    while current <= end:
        if current.weekday() < 5:
            trading_days.append(current.strftime('%Y-%m-%d'))
        current += timedelta(days=1)
    return trading_days

print("="*80)
print("OPENING RANGE BREAKOUT - QQQ OPTIMIZATION")
print("="*80)
print("\nBaseline: Sharpe -0.26 (very close!)")

test_dates = generate_trading_days('2024-01-02', '2024-03-31')
print(f"Testing on Q1 2024: {len(test_dates)} potential days")

print("Loading QQQ data...")
all_dfs = []
for date in test_dates[:30]:
    bars = fetch_1min_data('QQQ', date)
    if len(bars) >= 50:
        all_dfs.append(pd.DataFrame(bars).sort_values('date').reset_index(drop=True))

print(f"Loaded {len(all_dfs)} days")

# Parameter grid
param_grid = [
    # Baseline
    {'range_minutes': 15, 'profit_target': 0.30, 'stop_loss': 0.20, 'max_hold_minutes': 60},
    
    # Larger targets
    {'range_minutes': 15, 'profit_target': 0.35, 'stop_loss': 0.20, 'max_hold_minutes': 60},
    {'range_minutes': 15, 'profit_target': 0.40, 'stop_loss': 0.20, 'max_hold_minutes': 75},
    
    # Tighter stops
    {'range_minutes': 15, 'profit_target': 0.30, 'stop_loss': 0.15, 'max_hold_minutes': 60},
    {'range_minutes': 15, 'profit_target': 0.35, 'stop_loss': 0.15, 'max_hold_minutes': 60},
    
    # Different range periods
    {'range_minutes': 10, 'profit_target': 0.30, 'stop_loss': 0.20, 'max_hold_minutes': 60},
    {'range_minutes': 20, 'profit_target': 0.30, 'stop_loss': 0.20, 'max_hold_minutes': 60},
    {'range_minutes': 30, 'profit_target': 0.35, 'stop_loss': 0.20, 'max_hold_minutes': 60},
]

results = []

print("\nTesting QQQ-optimized parameters...")
for idx, params in enumerate(param_grid, 1):
    all_trades = []
    
    for df in all_dfs:
        trades = orb_qqq(df.copy(), **params)
        all_trades.extend(trades)
    
    if all_trades and len(all_trades) >= 5:
        pnls = [t['pnl_pct'] for t in all_trades]
        wins = [t for t in all_trades if t['win']]
        
        avg_pnl = np.mean(pnls)
        std_pnl = np.std(pnls)
        sharpe = (avg_pnl / std_pnl * np.sqrt(252 * len(all_trades) / len(all_dfs))) if std_pnl > 0 else 0
        win_rate = len(wins) / len(all_trades) * 100
        trades_per_day = len(all_trades) / len(all_dfs)
        
        avg_win = np.mean([t['pnl_pct'] for t in wins]) if wins else 0
        avg_loss = np.mean([t['pnl_pct'] for t in [t for t in all_trades if not t['win']]]) if len(all_trades) > len(wins) else 0
        
        result = {
            'config': idx,
            'params': params,
            'trades': len(all_trades),
            'trades_per_day': trades_per_day,
            'win_rate': win_rate,
            'avg_pnl': avg_pnl,
            'avg_win': avg_win,
            'avg_loss': avg_loss,
            'sharpe': sharpe,
            'total_return': sum(pnls)
        }
        results.append(result)
        
        print(f"\nConfig {idx}: Range={params['range_minutes']}min, Target={params['profit_target']:.2f}%, Stop={params['stop_loss']:.2f}%")
        print(f"  Trades: {len(all_trades)} ({trades_per_day:.1f}/day) | Win%: {win_rate:.1f}% | Sharpe: {sharpe:.2f}")
    else:
        print(f"\nConfig {idx}: Insufficient trades ({len(all_trades) if all_trades else 0})")

# Summary
print("\n" + "="*80)
print("QQQ OPTIMIZATION RESULTS")
print("="*80)

if results:
    sorted_results = sorted(results, key=lambda x: x['sharpe'], reverse=True)
    
    print(f"\nTop 5 by Sharpe:")
    print(f"{'Rank':<5s} | {'Range':>6s} | {'Target':>7s} | {'Stop':>6s} | {'T/Day':>6s} | {'Win%':>6s} | {'Sharpe':>7s}")
    print("-" * 75)
    
    for idx, r in enumerate(sorted_results[:5], 1):
        p = r['params']
        status = "✅" if r['sharpe'] > 0 else "⚠️" if r['sharpe'] > -1 else "❌"
        print(f"{idx:<5d} | {p['range_minutes']:>5d}m | {p['profit_target']:>6.2f}% | {p['stop_loss']:>5.2f}% | {r['trades_per_day']:>6.1f} | {r['win_rate']:>5.1f}% | {r['sharpe']:>7.2f} {status}")
    
    best = sorted_results[0]
    
    print(f"\n{'='*80}")
    print("BEST QQQ CONFIGURATION")
    print(f"{'='*80}")
    print(f"Sharpe: {best['sharpe']:.2f}")
    print(f"Parameters: {best['params']}")
    
    if best['sharpe'] > 0:
        print(f"\n🎯 **PROFITABLE!** Test on full 2024+2025")
    elif best['sharpe'] > -0.5:
        print(f"\n⚠️  **VERY CLOSE!** Test on full year anyway")
    else:
        print(f"\n❌ Still negative")

with open('orb_qqq_optimization_results.json', 'w') as f:
    json.dump(results, f, indent=2)

print(f"\n✅ Saved to orb_qqq_optimization_results.json")
