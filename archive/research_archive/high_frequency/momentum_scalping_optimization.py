"""
Momentum Scalping - Proper Testing & Optimization

Strategy Concept:
- Jump on very short bursts of directional movement
- Exit quickly before momentum fades

Triggers to test:
1. Volume spikes (>1.5x, 2x, 2.5x average)
2. Price momentum thresholds (0.10%, 0.15%, 0.20%, 0.25%)
3. Tape acceleration (rate of change increasing)

Parameters to optimize:
- Momentum lookback: 3, 5, 10 bars
- Momentum threshold: 0.10% to 0.30%
- Volume multiplier: 1.5x to 3x
- Profit target: 0.15% to 0.40%
- Stop loss: 0.10% to 0.25%
- Hold time: 2 to 10 minutes

Goal: Find if ANY parameter combination is profitable
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
FRICTION_BPS = 4.1

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

def momentum_scalping_strategy(df, lookback=5, mom_threshold=0.15, vol_multiplier=2.0,
                               profit_target=0.20, stop_loss=0.15, hold_minutes=5):
    """
    Momentum Scalping with tunable parameters
    
    Entry: Strong momentum + volume spike
    Exit: Profit target, stop loss, or time
    """
    if len(df) < 30:
        return []
    
    # Calculate momentum
    df['momentum'] = (df['close'] - df['close'].shift(lookback)) / df['close'].shift(lookback) * 100
    
    # Volume filter
    df['vol_sma'] = df['volume'].rolling(20).mean()
    df['vol_spike'] = df['volume'] > vol_multiplier * df['vol_sma']
    
    # Time
    df['time'] = pd.to_datetime(df['date'])
    df['hour'] = df['time'].dt.hour
    
    trades = []
    position = None
    
    for i in range(30, len(df)):
        if position:
            hold_min = i - position['entry_idx']
            pnl_pct = (df.loc[i, 'close'] - position['entry_price']) / position['entry_price'] * 100
            if position['type'] == 'short':
                pnl_pct = -pnl_pct
            
            # Exit conditions
            exit_reason = None
            if pnl_pct >= profit_target:
                exit_reason = 'target'
            elif pnl_pct <= -stop_loss:
                exit_reason = 'stop_loss'
            elif hold_min >= hold_minutes:
                exit_reason = 'timeout'
            
            if exit_reason:
                pnl_pct -= FRICTION_BPS / 100
                trades.append({
                    'pnl_pct': pnl_pct,
                    'win': pnl_pct > 0,
                    'hold_min': hold_min,
                    'exit_reason': exit_reason
                })
                position = None
        
        if not position:
            # Time filter (avoid lunch)
            if 12 <= df.loc[i, 'hour'] < 14:
                continue
            
            # Volume spike required
            if not df.loc[i, 'vol_spike']:
                continue
            
            # Momentum signals
            mom = df.loc[i, 'momentum']
            if pd.notna(mom):
                if mom > mom_threshold:
                    position = {'type': 'long', 'entry_price': df.loc[i, 'close'], 'entry_idx': i}
                elif mom < -mom_threshold:
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
print("MOMENTUM SCALPING - PARAMETER OPTIMIZATION")
print("="*80)

# Test on sample of 2024 for speed
test_dates = generate_trading_days('2024-01-02', '2024-03-31')  # Q1 2024
print(f"\nTesting on Q1 2024: {len(test_dates)} potential days")

# Load data once
print("Loading data...")
all_dfs = []
for date in test_dates[:30]:  # First 30 days for speed
    bars = fetch_1min_data('SPY', date)
    if len(bars) >= 50:
        all_dfs.append(pd.DataFrame(bars).sort_values('date').reset_index(drop=True))

print(f"Loaded {len(all_dfs)} days of data")

# Parameter grid
param_grid = [
    # Conservative (fewer trades)
    {'lookback': 5, 'mom_threshold': 0.20, 'vol_multiplier': 2.5, 'profit_target': 0.25, 'stop_loss': 0.20, 'hold_minutes': 5},
    {'lookback': 5, 'mom_threshold': 0.25, 'vol_multiplier': 2.5, 'profit_target': 0.30, 'stop_loss': 0.20, 'hold_minutes': 5},
    {'lookback': 5, 'mom_threshold': 0.30, 'vol_multiplier': 3.0, 'profit_target': 0.35, 'stop_loss': 0.25, 'hold_minutes': 5},
    
    # Moderate
    {'lookback': 5, 'mom_threshold': 0.15, 'vol_multiplier': 2.0, 'profit_target': 0.20, 'stop_loss': 0.15, 'hold_minutes': 5},
    {'lookback': 3, 'mom_threshold': 0.15, 'vol_multiplier': 2.0, 'profit_target': 0.20, 'stop_loss': 0.15, 'hold_minutes': 3},
    
    # Aggressive (more trades)
    {'lookback': 3, 'mom_threshold': 0.10, 'vol_multiplier': 1.5, 'profit_target': 0.15, 'stop_loss': 0.10, 'hold_minutes': 3},
    {'lookback': 5, 'mom_threshold': 0.12, 'vol_multiplier': 1.8, 'profit_target': 0.18, 'stop_loss': 0.12, 'hold_minutes': 4},
]

results = []

print("\nTesting parameter combinations...")
for idx, params in enumerate(param_grid, 1):
    all_trades = []
    
    for df in all_dfs:
        trades = momentum_scalping_strategy(df.copy(), **params)
        all_trades.extend(trades)
    
    if all_trades and len(all_trades) >= 5:
        pnls = [t['pnl_pct'] for t in all_trades]
        wins = [t for t in all_trades if t['win']]
        
        avg_pnl = np.mean(pnls)
        std_pnl = np.std(pnls)
        sharpe = (avg_pnl / std_pnl * np.sqrt(252 * len(all_trades) / len(all_dfs))) if std_pnl > 0 else 0
        win_rate = len(wins) / len(all_trades) * 100
        trades_per_day = len(all_trades) / len(all_dfs)
        
        result = {
            'config': idx,
            'params': params,
            'trades': len(all_trades),
            'trades_per_day': trades_per_day,
            'win_rate': win_rate,
            'avg_pnl': avg_pnl,
            'sharpe': sharpe,
            'total_return': sum(pnls)
        }
        results.append(result)
        
        print(f"\nConfig {idx}: Mom={params['mom_threshold']:.2f}%, Vol={params['vol_multiplier']:.1f}x, Target={params['profit_target']:.2f}%")
        print(f"  Trades: {len(all_trades)} ({trades_per_day:.1f}/day) | Win%: {win_rate:.1f}% | Sharpe: {sharpe:.2f} | Return: {sum(pnls):.2f}%")
    else:
        print(f"\nConfig {idx}: Insufficient trades ({len(all_trades) if all_trades else 0})")

# Summary
print("\n" + "="*80)
print("OPTIMIZATION RESULTS")
print("="*80)

if results:
    sorted_results = sorted(results, key=lambda x: x['sharpe'], reverse=True)
    
    print(f"\nTop 3 by Sharpe:")
    print(f"{'Rank':<5s} | {'Mom%':>6s} | {'Vol':>5s} | {'Target':>7s} | {'Trades/Day':>11s} | {'Win%':>6s} | {'Sharpe':>7s}")
    print("-" * 80)
    
    for idx, r in enumerate(sorted_results[:3], 1):
        p = r['params']
        status = "✅" if r['sharpe'] > 0 else "❌"
        print(f"{idx:<5d} | {p['mom_threshold']:>5.2f}% | {p['vol_multiplier']:>4.1f}x | {p['profit_target']:>6.2f}% | {r['trades_per_day']:>11.1f} | {r['win_rate']:>5.1f}% | {r['sharpe']:>7.2f} {status}")
    
    best = sorted_results[0]
    
    if best['sharpe'] > 0:
        print(f"\n🎯 PROFITABLE CONFIG FOUND!")
        print(f"   Sharpe: {best['sharpe']:.2f}")
        print(f"   Parameters: {best['params']}")
        print(f"\n   Next: Test on full 2024+2025 to validate")
    else:
        print(f"\n❌ No profitable configs in Q1 2024 sample")
        print(f"   Best Sharpe: {best['sharpe']:.2f} (still negative)")
        print(f"\n   Options:")
        print(f"   1. Test on full year anyway (might improve)")
        print(f"   2. Try different parameter ranges")
        print(f"   3. Move to next strategy type")

# Save
with open('momentum_scalping_optimization_results.json', 'w') as f:
    json.dump(results, f, indent=2)

print(f"\n✅ Saved to momentum_scalping_optimization_results.json")
