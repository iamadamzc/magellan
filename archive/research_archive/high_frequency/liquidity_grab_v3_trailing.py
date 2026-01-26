"""
Liquidity Grab V3 - Final Refinement

Key insight from V2: 60% win rate achieved but avg wins too small!

Problem: Exits happening too early (timeouts) before targets hit

Solution V3:
1. Trailing stops - lock in profits as they develop
2. Scale out - take partial profits at smaller levels
3. Momentum confirmation - only enter if momentum supports the reversal
4. Wider initial stops but trail aggressively
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

def liquidity_grab_v3(df, lookback=10, rejection_bars=3, 
                     initial_target=0.20, trail_trigger=0.10, trail_distance=0.05,
                     stop_loss=0.18, hold_minutes=15):
    """
    Liquidity Grab V3 - Trailing stops + early profit taking
    
    Logic:
    - Enter on stop-run pattern
    - If profit reaches trail_trigger (0.10%), activate trailing stop
    - Trail at trail_distance (0.05%) behind high water mark
    - Hard stop at stop_loss (0.18%)
    - Timeout at hold_minutes
    """
    if len(df) < 30:
        return []
    
    df['high_roll'] = df['high'].rolling(lookback).max()
    df['low_roll'] = df['low'].rolling(lookback).min()
    df['upper_wick'] = (df['high'] - df[['open', 'close']].max(axis=1)) / df['close'] * 100
    df['lower_wick'] = (df[['open', 'close']].min(axis=1) - df['low']) / df['close'] * 100
    df['time'] = pd.to_datetime(df['date'])
    df['hour'] = df['time'].dt.hour
    
    # Momentum for confirmation
    df['momentum_3'] = (df['close'] - df['close'].shift(3)) / df['close'].shift(3) * 100
    
    trades = []
    position = None
    
    for i in range(lookback + 5, len(df)):
        if position:
            hold_min = i - position['entry_idx']
            pnl_pct = (df.loc[i, 'close'] - position['entry_price']) / position['entry_price'] * 100
            if position['type'] == 'short':
                pnl_pct = -pnl_pct
            
            # Update high water mark
            if pnl_pct > position['high_water_mark']:
                position['high_water_mark'] = pnl_pct
            
            # Activate trailing stop if profit > trail_trigger
            if position['high_water_mark'] >= trail_trigger:
                position['trailing_active'] = True
            
            exit_reason = None
            
            # Trailing stop exit
            if position['trailing_active']:
                if pnl_pct < position['high_water_mark'] - trail_distance:
                    exit_reason = 'trailing_stop'
            
            # Initial target hit
            if pnl_pct >= initial_target:
                exit_reason = 'target'
            
            # Hard stop
            elif pnl_pct <= -stop_loss:
                exit_reason = 'stop_loss'
            
            # Timeout
            elif hold_min >= hold_minutes:
                exit_reason = 'timeout'
            
            if exit_reason:
                pnl_pct -= FRICTION_BPS / 100
                trades.append({
                    'pnl_pct': pnl_pct,
                    'win': pnl_pct > 0,
                    'hold_min': hold_min,
                    'exit_reason': exit_reason,
                    'high_water_mark': position['high_water_mark']
                })
                position = None
        
        if not position:
            if 12 <= df.loc[i, 'hour'] < 14:
                continue
            
            # Pattern 1: Break high then reject WITH negative momentum
            if i >= rejection_bars:
                recent_high = df.loc[i-rejection_bars:i-1, 'high'].max()
                prev_high_roll = df.loc[i-1, 'high_roll']
                
                if recent_high > prev_high_roll and df.loc[i, 'close'] < prev_high_roll:
                    # Momentum confirmation: should be turning negative
                    if pd.notna(df.loc[i, 'momentum_3']) and df.loc[i, 'momentum_3'] < 0:
                        position = {
                            'type': 'short',
                            'entry_price': df.loc[i, 'close'],
                            'entry_idx': i,
                            'high_water_mark': 0,
                            'trailing_active': False
                        }
                        continue
            
            # Pattern 2: Break low then reclaim WITH positive momentum
            if i >= rejection_bars:
                recent_low = df.loc[i-rejection_bars:i-1, 'low'].min()
                prev_low_roll = df.loc[i-1, 'low_roll']
                
                if recent_low < prev_low_roll and df.loc[i, 'close'] > prev_low_roll:
                    # Momentum confirmation: should be turning positive
                    if pd.notna(df.loc[i, 'momentum_3']) and df.loc[i, 'momentum_3'] > 0:
                        position = {
                            'type': 'long',
                            'entry_price': df.loc[i, 'close'],
                            'entry_idx': i,
                            'high_water_mark': 0,
                            'trailing_active': False
                        }
                        continue
    
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
print("LIQUIDITY GRAB V3 - TRAILING STOPS + MOMENTUM CONFIRMATION")
print("="*80)

test_dates = generate_trading_days('2024-01-02', '2024-03-31')
print(f"\nTesting on Q1 2024: {len(test_dates)} potential days")

print("Loading data...")
all_dfs = []
for date in test_dates[:30]:
    bars = fetch_1min_data('SPY', date)
    if len(bars) >= 50:
        all_dfs.append(pd.DataFrame(bars).sort_values('date').reset_index(drop=True))

print(f"Loaded {len(all_dfs)} days of data")

# Parameter grid for trailing stops
param_grid = [
    # Conservative trailing
    {'lookback': 10, 'rejection_bars': 3, 'initial_target': 0.25, 'trail_trigger': 0.12, 'trail_distance': 0.06, 'stop_loss': 0.18, 'hold_minutes': 15},
    {'lookback': 10, 'rejection_bars': 3, 'initial_target': 0.30, 'trail_trigger': 0.15, 'trail_distance': 0.08, 'stop_loss': 0.20, 'hold_minutes': 18},
    
    # Aggressive trailing
    {'lookback': 10, 'rejection_bars': 3, 'initial_target': 0.20, 'trail_trigger': 0.08, 'trail_distance': 0.04, 'stop_loss': 0.15, 'hold_minutes': 12},
    {'lookback': 8, 'rejection_bars': 2, 'initial_target': 0.22, 'trail_trigger': 0.10, 'trail_distance': 0.05, 'stop_loss': 0.16, 'hold_minutes': 12},
    
    # Moderate
    {'lookback': 10, 'rejection_bars': 3, 'initial_target': 0.25, 'trail_trigger': 0.10, 'trail_distance': 0.05, 'stop_loss': 0.17, 'hold_minutes': 15},
    {'lookback': 12, 'rejection_bars': 3, 'initial_target': 0.28, 'trail_trigger': 0.12, 'trail_distance': 0.06, 'stop_loss': 0.18, 'hold_minutes': 15},
]

results = []

print("\nTesting trailing stop configurations...")
for idx, params in enumerate(param_grid, 1):
    all_trades = []
    
    for df in all_dfs:
        trades = liquidity_grab_v3(df.copy(), **params)
        all_trades.extend(trades)
    
    if all_trades and len(all_trades) >= 5:
        pnls = [t['pnl_pct'] for t in all_trades]
        wins = [t for t in all_trades if t['win']]
        losses = [t for t in all_trades if not t['win']]
        
        avg_pnl = np.mean(pnls)
        std_pnl = np.std(pnls)
        sharpe = (avg_pnl / std_pnl * np.sqrt(252 * len(all_trades) / len(all_dfs))) if std_pnl > 0 else 0
        win_rate = len(wins) / len(all_trades) * 100
        trades_per_day = len(all_trades) / len(all_dfs)
        
        avg_win = np.mean([t['pnl_pct'] for t in wins]) if wins else 0
        avg_loss = np.mean([t['pnl_pct'] for t in losses]) if losses else 0
        
        # Count exit reasons
        trailing_exits = sum(1 for t in all_trades if t['exit_reason'] == 'trailing_stop')
        target_exits = sum(1 for t in all_trades if t['exit_reason'] == 'target')
        
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
            'total_return': sum(pnls),
            'trailing_exits': trailing_exits,
            'target_exits': target_exits
        }
        results.append(result)
        
        print(f"\nConfig {idx}: Target={params['initial_target']:.2f}%, Trail@{params['trail_trigger']:.2f}% by {params['trail_distance']:.2f}%")
        print(f"  Trades: {len(all_trades)} ({trades_per_day:.1f}/day) | Win%: {win_rate:.1f}% | Sharpe: {sharpe:.2f}")
        print(f"  Avg Win: {avg_win:.3f}% | Avg Loss: {avg_loss:.3f}%")
        print(f"  Exits: {target_exits} targets, {trailing_exits} trails")
    else:
        print(f"\nConfig {idx}: Insufficient trades ({len(all_trades) if all_trades else 0})")

# Summary
print("\n" + "="*80)
print("V3 TRAILING STOP RESULTS")
print("="*80)

if results:
    sorted_results = sorted(results, key=lambda x: x['sharpe'], reverse=True)
    
    print(f"\nTop 3 by Sharpe:")
    print(f"{'Rank':<5s} | {'Target':>7s} | {'Trail@':>8s} | {'Trades/Day':>11s} | {'Win%':>6s} | {'Sharpe':>7s}")
    print("-" * 75)
    
    for idx, r in enumerate(sorted_results[:3], 1):
        p = r['params']
        status = "✅" if r['sharpe'] > 0 else "⚠️" if r['sharpe'] > -2 else "❌"
        print(f"{idx:<5d} | {p['initial_target']:>6.2f}% | {p['trail_trigger']:>7.2f}% | {r['trades_per_day']:>11.1f} | {r['win_rate']:>5.1f}% | {r['sharpe']:>7.2f} {status}")
    
    best = sorted_results[0]
    
    print(f"\n{'='*80}")
    print("BEST V3 CONFIGURATION")
    print(f"{'='*80}")
    print(f"Sharpe: {best['sharpe']:.2f}")
    print(f"Win Rate: {best['win_rate']:.1f}%")
    print(f"Avg Win: {best['avg_win']:.3f}%")
    print(f"Avg Loss: {best['avg_loss']:.3f}%")
    print(f"Trades/Day: {best['trades_per_day']:.1f}")
    print(f"Target Exits: {best['target_exits']}")
    print(f"Trailing Exits: {best['trailing_exits']}")
    
    if best['sharpe'] > 0:
        print(f"\n🎯 **PROFITABLE!** Test on full 2024+2025")
    elif best['sharpe'] > -1.5:
        print(f"\n⚠️  **VERY CLOSE!** Consider full year test")
    else:
        print(f"\n❌ Move to next strategy type")

# Save
with open('liquidity_grab_v3_results.json', 'w') as f:
    json.dump(results, f, indent=2)

print(f"\n✅ Saved to liquidity_grab_v3_results.json")
