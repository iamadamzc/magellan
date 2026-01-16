"""
Liquidity Grab / Stop-Run Scalping - Parameter Optimization

Strategy Concept:
- Identify when price breaks a key level (triggering stops)
- Enter when price quickly reverses (liquidity grab complete)
- This is a "fade the breakout" strategy

Key Patterns:
1. Break above recent high → Fast rejection → Short
2. Break below recent low → Fast reclaim → Long
3. "Wick plays" - long wicks indicate stop hunts

Parameters to optimize:
- Lookback period for highs/lows: 5, 10, 15, 20 bars
- Rejection speed: 1-3 bars
- Profit target: 0.15% to 0.40%
- Stop loss: 0.15% to 0.30%
- Hold time: 5 to 15 minutes
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

def liquidity_grab_strategy(df, lookback=10, rejection_bars=2, profit_target=0.25, 
                            stop_loss=0.20, hold_minutes=10, min_wick_pct=0.10):
    """
    Liquidity Grab / Stop-Run Strategy
    
    Entry: Price breaks level, then quickly reverses
    Exit: Profit target, stop loss, or time
    """
    if len(df) < 30:
        return []
    
    # Calculate rolling highs/lows
    df['high_roll'] = df['high'].rolling(lookback).max()
    df['low_roll'] = df['low'].rolling(lookback).min()
    
    # Wick analysis
    df['upper_wick'] = (df['high'] - df[['open', 'close']].max(axis=1)) / df['close'] * 100
    df['lower_wick'] = (df[['open', 'close']].min(axis=1) - df['low']) / df['close'] * 100
    
    # Time
    df['time'] = pd.to_datetime(df['date'])
    df['hour'] = df['time'].dt.hour
    
    trades = []
    position = None
    
    for i in range(lookback + 5, len(df)):
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
            # Time filter
            if 12 <= df.loc[i, 'hour'] < 14:
                continue
            
            # Look for stop-run patterns
            
            # Pattern 1: Break high then reject (within rejection_bars)
            if i >= rejection_bars:
                recent_high = df.loc[i-rejection_bars:i-1, 'high'].max()
                prev_high_roll = df.loc[i-1, 'high_roll']
                
                # Did we break above the rolling high recently?
                if recent_high > prev_high_roll:
                    # Is current close back below that high? (rejection)
                    if df.loc[i, 'close'] < prev_high_roll:
                        # Enter short (fade the breakout)
                        position = {'type': 'short', 'entry_price': df.loc[i, 'close'], 'entry_idx': i}
                        continue
            
            # Pattern 2: Break low then reclaim
            if i >= rejection_bars:
                recent_low = df.loc[i-rejection_bars:i-1, 'low'].min()
                prev_low_roll = df.loc[i-1, 'low_roll']
                
                # Did we break below the rolling low recently?
                if recent_low < prev_low_roll:
                    # Is current close back above that low? (reclaim)
                    if df.loc[i, 'close'] > prev_low_roll:
                        # Enter long (fade the breakdown)
                        position = {'type': 'long', 'entry_price': df.loc[i, 'close'], 'entry_idx': i}
                        continue
            
            # Pattern 3: Large wick (stop hunt indicator)
            if df.loc[i, 'upper_wick'] > min_wick_pct:
                # Large upper wick = rejection of highs
                position = {'type': 'short', 'entry_price': df.loc[i, 'close'], 'entry_idx': i}
            elif df.loc[i, 'lower_wick'] > min_wick_pct:
                # Large lower wick = rejection of lows
                position = {'type': 'long', 'entry_price': df.loc[i, 'close'], 'entry_idx': i}
    
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
print("LIQUIDITY GRAB / STOP-RUN SCALPING - PARAMETER OPTIMIZATION")
print("="*80)

# Test on Q1 2024
test_dates = generate_trading_days('2024-01-02', '2024-03-31')
print(f"\nTesting on Q1 2024: {len(test_dates)} potential days")

print("Loading data...")
all_dfs = []
for date in test_dates[:30]:
    bars = fetch_1min_data('SPY', date)
    if len(bars) >= 50:
        all_dfs.append(pd.DataFrame(bars).sort_values('date').reset_index(drop=True))

print(f"Loaded {len(all_dfs)} days of data")

# Parameter grid
param_grid = [
    # Conservative (strict filters)
    {'lookback': 15, 'rejection_bars': 2, 'profit_target': 0.30, 'stop_loss': 0.25, 'hold_minutes': 10, 'min_wick_pct': 0.15},
    {'lookback': 20, 'rejection_bars': 2, 'profit_target': 0.35, 'stop_loss': 0.25, 'hold_minutes': 12, 'min_wick_pct': 0.20},
    
    # Moderate
    {'lookback': 10, 'rejection_bars': 2, 'profit_target': 0.25, 'stop_loss': 0.20, 'hold_minutes': 10, 'min_wick_pct': 0.12},
    {'lookback': 10, 'rejection_bars': 3, 'profit_target': 0.25, 'stop_loss': 0.20, 'hold_minutes': 10, 'min_wick_pct': 0.10},
    
    # Aggressive (more signals)
    {'lookback': 5, 'rejection_bars': 2, 'profit_target': 0.20, 'stop_loss': 0.15, 'hold_minutes': 8, 'min_wick_pct': 0.08},
    {'lookback': 8, 'rejection_bars': 3, 'profit_target': 0.22, 'stop_loss': 0.18, 'hold_minutes': 10, 'min_wick_pct': 0.10},
]

results = []

print("\nTesting parameter combinations...")
for idx, params in enumerate(param_grid, 1):
    all_trades = []
    
    for df in all_dfs:
        trades = liquidity_grab_strategy(df.copy(), **params)
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
        
        print(f"\nConfig {idx}: Lookback={params['lookback']}, Rej={params['rejection_bars']}, Target={params['profit_target']:.2f}%")
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
    print(f"{'Rank':<5s} | {'Lookback':>9s} | {'Target':>7s} | {'Trades/Day':>11s} | {'Win%':>6s} | {'Sharpe':>7s}")
    print("-" * 70)
    
    for idx, r in enumerate(sorted_results[:3], 1):
        p = r['params']
        status = "✅" if r['sharpe'] > 0 else "❌"
        print(f"{idx:<5d} | {p['lookback']:>9d} | {p['profit_target']:>6.2f}% | {r['trades_per_day']:>11.1f} | {r['win_rate']:>5.1f}% | {r['sharpe']:>7.2f} {status}")
    
    best = sorted_results[0]
    
    if best['sharpe'] > 0:
        print(f"\n🎯 PROFITABLE CONFIG FOUND!")
        print(f"   Sharpe: {best['sharpe']:.2f}")
        print(f"   Parameters: {best['params']}")
        print(f"\n   Next: Test on full 2024+2025")
    else:
        print(f"\n❌ No profitable configs in Q1 2024")
        print(f"   Best Sharpe: {best['sharpe']:.2f}")
        print(f"\n   Move to next strategy type")

# Save
with open('liquidity_grab_optimization_results.json', 'w') as f:
    json.dump(results, f, indent=2)

print(f"\n✅ Saved to liquidity_grab_optimization_results.json")
